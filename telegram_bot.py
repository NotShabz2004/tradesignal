"""
Telegram Bot for sending alerts and handling user feedback
"""
import asyncio
import logging
from typing import Optional
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_MAX_RETRIES
from database import Database

logger = logging.getLogger(__name__)

class TelegramBot:
    def __init__(self, database: Database):
        """Initialize Telegram bot"""
        if not TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN is not set in configuration")
        
        self.database = database
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.chat_id = TELEGRAM_CHAT_ID
        
        # Create application for handling callbacks
        self.application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        
        # Register callback handler for feedback buttons
        self.application.add_handler(CallbackQueryHandler(self.handle_feedback))
        
        logger.info("Telegram bot initialized")
    
    async def start(self):
        """Start the bot application"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
        logger.info("Telegram bot started and polling")
    
    async def stop(self):
        """Stop the bot application"""
        await self.application.updater.stop()
        await self.application.stop()
        await self.application.shutdown()
        logger.info("Telegram bot stopped")
    
    def _format_alert_message(self, coin: str, price: float, change_percent: float,
                             reason: str, confidence: int) -> str:
        """Format alert message for Telegram"""
        coin_emoji = {
            "bitcoin": "₿",
            "ethereum": "Ξ",
            "solana": "◎"
        }
        
        coin_name = coin.capitalize()
        emoji = coin_emoji.get(coin, "🚀")
        change_emoji = "📈" if change_percent > 0 else "📉"
        
        message = f"{emoji} {coin_name} Alert!\n\n"
        message += f"Price: ${price:,.2f}\n"
        message += f"Change: {change_emoji} {change_percent:+.2f}% (10 min)\n"
        message += f"Confidence: {confidence}%\n\n"
        message += f"Reason: {reason}"
        
        return message
    
    async def send_alert(self, coin: str, price: float, change_percent: float,
                        reason: str, confidence: int, alert_id: int) -> bool:
        """
        Send alert to Telegram user with feedback buttons
        
        Returns:
            True if sent successfully, False otherwise
        """
        message = self._format_alert_message(coin, price, change_percent, reason, confidence)
        
        # Create inline keyboard with feedback buttons
        keyboard = [
            [
                InlineKeyboardButton("👍 Helpful", callback_data=f"feedback_{alert_id}_helpful"),
                InlineKeyboardButton("👎 Not Helpful", callback_data=f"feedback_{alert_id}_not_helpful")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        for attempt in range(TELEGRAM_MAX_RETRIES):
            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message,
                    reply_markup=reply_markup,
                    parse_mode="HTML"
                )
                logger.info(f"Alert sent successfully: {coin} at ${price}")
                return True
                
            except Exception as e:
                logger.warning(f"Failed to send Telegram message (attempt {attempt + 1}): {e}")
                if attempt < TELEGRAM_MAX_RETRIES - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                logger.error(f"Failed to send Telegram message after {TELEGRAM_MAX_RETRIES} attempts")
                return False
    
    async def handle_feedback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user feedback button clicks"""
        query = update.callback_query
        
        # Acknowledge the button press
        await query.answer()
        
        try:
            # Parse callback data: feedback_{alert_id}_{feedback_type}
            data = query.data
            if not data.startswith("feedback_"):
                return
            
            parts = data.split("_")
            if len(parts) != 3:
                return
            
            alert_id = int(parts[1])
            feedback_type = parts[2]
            
            if feedback_type not in ["helpful", "not_helpful"]:
                return
            
            # Update database
            self.database.update_alert_feedback(alert_id, feedback_type)
            
            # Send confirmation message
            emoji = "👍" if feedback_type == "helpful" else "👎"
            confirmation = f"{emoji} Thank you for your feedback!"
            await query.edit_message_text(
                text=query.message.text + f"\n\n{confirmation}",
                reply_markup=None
            )
            
            logger.info(f"Received feedback for alert #{alert_id}: {feedback_type}")
            
        except Exception as e:
            logger.error(f"Error handling feedback: {e}")
            await query.answer("Error processing feedback. Please try again.", show_alert=True)

