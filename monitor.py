"""
Main monitoring loop for TradeSignal
Runs every 10 minutes to check prices and send alerts
"""
import logging
import time
import signal
import sys
import asyncio
from datetime import datetime
from typing import Dict, Optional
import requests
from config import (
    COINGECKO_API_URL, COINS, CURRENCY, CHECK_INTERVAL_MINUTES,
    PRICE_CHANGE_THRESHOLD, DATABASE_FILE, LOG_FILE, LOG_LEVEL,
    validate_config
)
from database import Database
from ai_analyzer import AIAnalyzer
from telegram_bot import TelegramBot

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

class TradeSignalMonitor:
    def __init__(self):
        """Initialize the monitoring system"""
        logger.info("Initializing TradeSignal Monitor...")
        
        # Validate configuration
        try:
            validate_config()
        except ValueError as e:
            logger.error(f"Configuration error: {e}")
            sys.exit(1)
        
        # Initialize components
        self.database = Database(DATABASE_FILE)
        self.ai_analyzer = AIAnalyzer()
        self.telegram_bot = TelegramBot(self.database)
        self.running = True
        
        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("TradeSignal Monitor initialized successfully")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    def fetch_prices(self) -> Optional[Dict[str, Dict]]:
        """
        Fetch current prices from CoinGecko API
        
        Returns:
            Dict with coin data or None if failed
        """
        params = {
            "ids": ",".join(COINS),
            "vs_currencies": CURRENCY,
            "include_24hr_change": "true"
        }
        
        for attempt in range(3):
            try:
                logger.debug(f"Fetching prices from CoinGecko (attempt {attempt + 1})")
                response = requests.get(COINGECKO_API_URL, params=params, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Successfully fetched prices from CoinGecko")
                return data
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Failed to fetch prices (attempt {attempt + 1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                logger.error("Failed to fetch prices after 3 attempts")
                return None
    
    def calculate_changes(self, current_prices: Dict[str, Dict]) -> Dict[str, float]:
        """
        Calculate price changes from last check
        
        Returns:
            Dict with change percentages for each coin
        """
        last_check = self.database.get_last_price_check()
        
        if not last_check:
            logger.info("No previous price check found, skipping change calculation")
            return {coin: 0.0 for coin in COINS}
        
        changes = {}
        for coin in COINS:
            current_price = current_prices.get(coin, {}).get("usd", 0)
            last_price = last_check.get(f"{coin}_price", 0)
            
            if last_price > 0:
                change = ((current_price - last_price) / last_price) * 100
                changes[coin] = change
            else:
                changes[coin] = 0.0
        
        return changes
    
    async def process_price_changes(self, prices: Dict[str, Dict], 
                                   changes_10min: Dict[str, float]):
        """
        Process price changes and decide if alerts should be sent
        """
        # Check if any coin has significant change
        significant_changes = {
            coin: change for coin, change in changes_10min.items()
            if abs(change) >= PRICE_CHANGE_THRESHOLD
        }
        
        if not significant_changes:
            logger.debug("No significant price changes detected")
            return
        
        logger.info(f"Significant price changes detected: {significant_changes}")
        
        # Get feedback history for AI context
        feedback_history = self.database.get_recent_feedback(limit=10)
        
        # Prepare data for AI
        price_dict = {coin: prices.get(coin, {}).get("usd", 0) for coin in COINS}
        changes_24h = {
            coin: prices.get(coin, {}).get("usd_24h_change", 0) or 0
            for coin in COINS
        }
        
        # Ask AI for each significant change
        for coin, change in significant_changes.items():
            try:
                # Get AI decision
                decision = self.ai_analyzer.analyze_price_change(
                    price_dict,
                    changes_10min,
                    changes_24h,
                    feedback_history
                )
                
                if not decision:
                    logger.warning(f"Failed to get AI decision for {coin}")
                    continue
                
                # Save decision to database
                self.database.save_decision(
                    coin=coin,
                    price_change=change,
                    should_alert=decision["should_alert"],
                    reason=decision.get("reason", ""),
                    confidence=decision.get("confidence", 50)
                )
                
                # If AI says we should alert, send it
                if decision["should_alert"]:
                    price = price_dict[coin]
                    alert_id = self.database.save_alert(
                        coin=coin,
                        price=price,
                        change_percent=change,
                        ai_reason=decision.get("reason", ""),
                        ai_confidence=decision.get("confidence", 50)
                    )
                    
                    # Send Telegram alert
                    success = await self.telegram_bot.send_alert(
                        coin=coin,
                        price=price,
                        change_percent=change,
                        reason=decision.get("reason", "Significant price movement detected"),
                        confidence=decision.get("confidence", 50),
                        alert_id=alert_id
                    )
                    
                    if success:
                        logger.info(f"Alert sent for {coin}: ${price} ({change:+.2f}%)")
                    else:
                        logger.error(f"Failed to send alert for {coin}")
                else:
                    logger.info(f"AI decided not to alert for {coin} (confidence: {decision.get('confidence', 0)}%)")
                    
            except Exception as e:
                logger.error(f"Error processing price change for {coin}: {e}")
                continue
    
    async def run_check(self):
        """Run a single price check cycle"""
        logger.info("=" * 50)
        logger.info(f"Starting price check at {datetime.now().isoformat()}")
        
        # Fetch current prices
        price_data = self.fetch_prices()
        if not price_data:
            logger.warning("Skipping this check due to API failure")
            return
        
        # Extract prices
        prices = {}
        for coin in COINS:
            if coin in price_data:
                prices[coin] = price_data[coin]
            else:
                logger.warning(f"Price data missing for {coin}")
                prices[coin] = {"usd": 0, "usd_24h_change": 0}
        
        # Calculate changes from last check
        changes_10min = self.calculate_changes(price_data)
        
        # Save price check to database
        price_dict = {coin: prices[coin].get("usd", 0) for coin in COINS}
        self.database.save_price_check(price_dict, changes_10min)
        
        logger.info(f"Prices: BTC=${price_dict['bitcoin']:,.2f}, "
                   f"ETH=${price_dict['ethereum']:,.2f}, "
                   f"SOL=${price_dict['solana']:,.2f}")
        logger.info(f"10min changes: BTC={changes_10min['bitcoin']:+.2f}%, "
                   f"ETH={changes_10min['ethereum']:+.2f}%, "
                   f"SOL={changes_10min['solana']:+.2f}%")
        
        # Process changes and send alerts if needed
        await self.process_price_changes(price_data, changes_10min)
        
        logger.info("Price check completed")
    
    async def run(self):
        """Main monitoring loop"""
        logger.info("Starting TradeSignal Monitor...")
        logger.info(f"Check interval: {CHECK_INTERVAL_MINUTES} minutes")
        logger.info(f"Price change threshold: {PRICE_CHANGE_THRESHOLD}%")
        
        # Start Telegram bot in background
        await self.telegram_bot.start()
        
        # Send startup message
        try:
            await self.telegram_bot.bot.send_message(
                chat_id=self.telegram_bot.chat_id,
                text="🚀 TradeSignal Monitor started!\n\nMonitoring Bitcoin, Ethereum, and Solana every 10 minutes."
            )
        except Exception as e:
            logger.warning(f"Failed to send startup message: {e}")
        
        # Run initial check immediately
        await self.run_check()
        
        # Main loop
        while self.running:
            try:
                # Wait for next check (convert minutes to seconds)
                wait_seconds = CHECK_INTERVAL_MINUTES * 60
                logger.info(f"Waiting {CHECK_INTERVAL_MINUTES} minutes until next check...")
                
                # Sleep in small increments to allow graceful shutdown
                for _ in range(wait_seconds):
                    if not self.running:
                        break
                    await asyncio.sleep(1)
                
                if not self.running:
                    break
                    
                # Run price check
                await self.run_check()
                    
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                if self.running:
                    await asyncio.sleep(60)  # Wait 1 minute before retrying
        
        # Cleanup
        logger.info("Shutting down TradeSignal Monitor...")
        await self.telegram_bot.stop()
        self.database.close()
        logger.info("Shutdown complete")

async def main():
    """Main entry point"""
    monitor = TradeSignalMonitor()
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

