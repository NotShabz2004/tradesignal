# TradeSignal - Autonomous Crypto Monitoring Agent

A production-ready autonomous cryptocurrency monitoring system that uses AI to intelligently alert you about significant price movements in Bitcoin, Ethereum, and Solana.

## 🚀 Features

- **Automatic Price Monitoring**: Checks prices every 10 minutes from CoinGecko (FREE API)
- **AI-Powered Decisions**: Uses Google Gemini AI to decide when alerts are truly important
- **Telegram Integration**: Sends alerts directly to your Telegram with feedback buttons
- **Learning System**: Uses your feedback (👍/👎) to improve future alert decisions
- **Production Ready**: Comprehensive error handling, logging, and graceful shutdown
- **Free Tier Compatible**: Uses only free APIs (Gemini, CoinGecko, Telegram)

## 📋 Prerequisites

- Python 3.11 or higher
- Google Gemini API key (free from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Telegram Chat ID (from [@userinfobot](https://t.me/userinfobot))

## 🛠️ Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Then edit `.env` and add your API keys:
   ```
   GEMINI_API_KEY=your_actual_gemini_key
   TELEGRAM_BOT_TOKEN=your_actual_bot_token
   TELEGRAM_CHAT_ID=your_actual_chat_id
   ```

## 🔑 Getting API Keys

### Google Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key to your `.env` file

### Telegram Bot Token
1. Open Telegram and search for [@BotFather](https://t.me/BotFather)
2. Send `/newbot` and follow the instructions
3. Copy the bot token to your `.env` file

### Telegram Chat ID
1. Open Telegram and search for [@userinfobot](https://t.me/userinfobot)
2. Start a conversation with the bot
3. It will reply with your Chat ID
4. Copy the Chat ID to your `.env` file

## 🚀 Running Locally

```bash
python monitor.py
```

The monitor will:
- Start checking prices every 10 minutes
- Send you a startup message on Telegram
- Automatically detect significant price changes (>3%)
- Use AI to decide if alerts are worth sending
- Store all data in `tradesignal.db` SQLite database

## 📊 How It Works

1. **Price Fetching**: Every 10 minutes, fetches Bitcoin, Ethereum, and Solana prices from CoinGecko
2. **Change Detection**: Calculates percentage change from the last check
3. **AI Analysis**: If any coin changes >3%, asks Gemini AI:
   - Should we alert the user?
   - Which coin is most significant?
   - What's the confidence level?
   - What's a good reason for the alert?
4. **Alert Sending**: If AI says yes, sends formatted alert to Telegram with 👍/👎 buttons
5. **Feedback Learning**: Your feedback is stored and used to improve future decisions

## 🗄️ Database Schema

The system uses SQLite with three main tables:

- **price_checks**: Stores all price checks with timestamps
- **alerts**: Stores all sent alerts with user feedback
- **decisions**: Stores all AI decisions (even when no alert was sent)

## 🚂 Deploying to Railway

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Create a new project** and connect your GitHub repository

3. **Add environment variables** in Railway dashboard:
   - `GEMINI_API_KEY`
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

4. **Deploy**: Railway will automatically detect the `railway.json` and `Procfile` and deploy your app

5. **Monitor**: Check the Railway logs to see your monitor running

## 📁 Project Structure

```
tradesignal/
├── monitor.py          # Main monitoring loop
├── ai_analyzer.py      # Gemini AI integration
├── telegram_bot.py     # Telegram bot with feedback
├── database.py         # SQLite database operations
├── config.py           # Configuration management
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variable template
├── railway.json        # Railway deployment config
├── Procfile           # Process definition
└── README.md          # This file
```

## ⚙️ Configuration

Edit `config.py` to customize:

- `CHECK_INTERVAL_MINUTES`: How often to check prices (default: 10)
- `PRICE_CHANGE_THRESHOLD`: Minimum change % to consider (default: 3.0%)
- `GEMINI_MODEL`: Which Gemini model to use (default: "gemini-pro")

## 📝 Logging

Logs are written to:
- Console (stdout)
- File: `tradesignal.log`

Log levels: DEBUG, INFO, WARNING, ERROR

## 🐛 Troubleshooting

### "Configuration errors" on startup
- Make sure your `.env` file exists and has all three required keys
- Check that there are no extra spaces or quotes around the values

### "Failed to fetch prices"
- CoinGecko API might be temporarily down
- Check your internet connection
- The system will retry automatically

### "Failed to send Telegram message"
- Verify your `TELEGRAM_BOT_TOKEN` is correct
- Make sure you've started a conversation with your bot
- Check that `TELEGRAM_CHAT_ID` is correct

### "Error calling Gemini API"
- Verify your `GEMINI_API_KEY` is correct
- Check if you've exceeded the free tier limits (1500 requests/day)
- The system will retry automatically

## 💰 Cost Analysis

**Free Tier Limits:**
- CoinGecko: 10-50 calls/minute (we use ~6/hour) ✅
- Gemini: 1500 requests/day (we use ~10-20/day) ✅
- Telegram: Unlimited ✅

**Total Cost: $0/month** 🎉

## 🔒 Security Notes

- Never commit your `.env` file to version control
- Keep your API keys secret
- The `.env` file is already in `.gitignore` (if you add one)

## 📈 Future Enhancements

Possible improvements:
- Support for more cryptocurrencies
- Customizable price thresholds per coin
- Multiple Telegram chat support
- Web dashboard for viewing history
- Email alerts as backup
- Price prediction based on patterns

## 📄 License

This project is open source and available for personal and commercial use.

## 🤝 Contributing

Feel free to submit issues, fork the repository, and create pull requests!

## 📧 Support

If you encounter any issues:
1. Check the logs in `tradesignal.log`
2. Verify all API keys are correct
3. Make sure you're using Python 3.11+
4. Check that all dependencies are installed

---

**Happy Trading! 📈🚀**

