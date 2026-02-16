"""
Configuration settings for TradeSignal
Loads environment variables and provides configuration constants
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# CoinGecko API Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price"
COINS = ["bitcoin", "ethereum", "solana"]
CURRENCY = "usd"

# Monitoring Configuration
CHECK_INTERVAL_MINUTES = 10
PRICE_CHANGE_THRESHOLD = 0.1  # Alert if price changes by more than 0.1% (testing mode - triggers on almost any movement)

# Gemini AI Configuration
GEMINI_MODEL = "gemini-2.5-flash-lite"
GEMINI_MAX_RETRIES = 3
GEMINI_TIMEOUT = 30

# Telegram Configuration
TELEGRAM_MAX_RETRIES = 3
TELEGRAM_TIMEOUT = 30

# Database Configuration
DATABASE_FILE = "tradesignal.db"

# Logging Configuration
LOG_FILE = "tradesignal.log"
LOG_LEVEL = "INFO"

# Validation
def validate_config():
    """Validate that all required configuration is present"""
    errors = []
    
    if not GEMINI_API_KEY:
        errors.append("GEMINI_API_KEY is not set")
    
    if not TELEGRAM_BOT_TOKEN:
        errors.append("TELEGRAM_BOT_TOKEN is not set")
    
    if not TELEGRAM_CHAT_ID:
        errors.append("TELEGRAM_CHAT_ID is not set")

    if errors:
        raise ValueError(f"Configuration errors: {', '.join(errors)}")
    
    return True

