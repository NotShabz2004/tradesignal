# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Create .env File

Create a file named `.env` in the project root with the following content:

```
# Google Gemini API Key
# Get yours from: https://makersuite.google.com/app/apikey
GEMINI_API_KEY=your_gemini_api_key_here

# Telegram Bot Token
# Get yours from: @BotFather on Telegram
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Telegram Chat ID
# Get yours from: @userinfobot on Telegram
TELEGRAM_CHAT_ID=your_telegram_chat_id_here
```

Replace the placeholder values with your actual API keys.

## Step 3: Run the Monitor

```bash
python monitor.py
```

That's it! The monitor will start checking prices every 10 minutes.

For detailed instructions, see README.md

