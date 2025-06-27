# 🤖 Personalized X Bot

> An X (formerly Twitter) bot that analyzes your personality from your existing tweets and interactions, then automatically engages with content that matches your style, humor, and preferences.

## 🎯 What This Bot Does

1. **Analyzes Your Personality** - Scrapes your tweets, likes, and bio to understand your writing style, humor, topics of interest, and interaction patterns
2. **Builds a Personality Model** - Uses GPT-4 to create a detailed personality profile scoring you on dimensions like humor, formality, technical depth, etc.
3. **Makes Smart Decisions** - Automatically likes, replies to, and retweets content based on your learned preferences
4. **Stays in Character** - Generates replies that match your authentic voice and style
5. **Respects Limits** - Built-in rate limiting and safety features to avoid spam behavior

## 🚀 Quick Start

### Prerequisites

- **Python 3.9+**
- **X Developer Account** with API access ($200+/month for Basic tier)
- **OpenAI API Key** (~$20-50/month usage)

### Installation

```bash
# Clone the repository
git clone https://github.com/jdships/x-bot.git
cd x-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual API keys (see Configuration section)
```

### Configuration

Edit `.env` with your real API credentials:

```bash
# X API Keys (from https://developer.twitter.com/)
TWITTER_API_KEY=your_actual_api_key
TWITTER_API_SECRET=your_actual_api_secret
TWITTER_ACCESS_TOKEN=your_actual_access_token
TWITTER_ACCESS_TOKEN_SECRET=your_actual_access_token_secret
TWITTER_BEARER_TOKEN=your_actual_bearer_token

# OpenAI API Key (from https://platform.openai.com/)
OPENAI_API_KEY=your_actual_openai_api_key

# Your Configuration
BOT_USERNAME=your_x_username_without_@
DRY_RUN=true  # Set to false when ready to go live
```

### Run the Bot

```bash
# Test your configuration first
python setup_and_run.py

# If tests pass, run the bot
python main.py
```

## 💰 API Costs (Important!)

### X API (Required)
- **Free Tier**: 100 reads/month ⚠️ **Not sufficient - even light users need paid plan**
- **Basic**: $200/month - 10K reads, 3K posts ✅ **Minimum needed for any usage**
- **Pro**: $5,000/month - 1M reads, 300K posts ✅ **Recommended for active use**

**Why even light users need paid plans:**
- Timeline monitoring: ~3,000 API calls/month (every 15 mins)
- Mention checking: ~8,600 API calls/month (every 5 mins)  
- Even 100 tweets + 50 likes = 11,750+ calls/month (110x over free limit)

### OpenAI API (Required)
- **Personality Analysis**: ~$5-10 one-time for initial analysis
- **Daily Usage**: ~$10-30/month depending on reply frequency

### 💡 Cost-Saving Options for Light Users

**Option 1: Reduce Monitoring Frequency**
```yaml
# config.yaml - Check less often to save API calls
schedule:
  timeline_check_interval: 60    # Once per hour instead of 15 mins
  mentions_check_interval: 30    # Every 30 mins instead of 5 mins
```

**Option 2: Manual Mode**
- Run bot manually when you want it to engage
- Use `DRY_RUN=true` to test without posting
- No continuous monitoring (saves ~90% of API calls)

**Option 3: Lite Mode**
```bash
# .env - Enable ultra-low API usage mode
LITE_MODE=true  # Reduces monitoring to every 4+ hours
```
- Automatically reduces all monitoring frequencies by 4x
- Analyze personality once, then minimal monitoring
- Could potentially work with free tier for very light usage
- Perfect for users who just want occasional engagement

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Data Collector │────│ Personality      │────│ Decision Engine │
│                 │    │ Analyzer (GPT-4) │    │                 │
│ • Your tweets   │    │                  │    │ • Like?         │
│ • Your likes    │    │ • Humor level    │    │ • Reply?        │
│ • Your bio      │    │ • Formality      │    │ • Retweet?      │
│ • Interaction   │    │ • Tech depth     │    │ • Confidence    │
│   patterns      │    │ • Controversy    │    │   score         │
└─────────────────┘    │   tolerance      │    └─────────────────┘
                       │ • Emoji usage    │             │
                       │ • Topics         │             ▼
                       └──────────────────┘    ┌─────────────────┐
                                │              │ Content         │
                                ▼              │ Generator       │
                       ┌──────────────────┐    │                 │
                       │ SQLite Database  │    │ • Match style   │
                       │                  │    │ • Keep context  │
                       │ • Profile data   │    │ • Under 280     │
                       │ • Interaction    │    │   chars         │
                       │   history        │    │ • Safety filter │
                       │ • Processed      │    └─────────────────┘
                       │   tweets         │             │
                       └──────────────────┘             ▼
                                                                                                 ┌─────────────────┐
                                                 │ X API           │
                                                 │                 │
                                                 │ • Post reply    │
                                                 │ • Like tweet    │
                                                 │ • Retweet       │
                                                 │ • Rate limited  │
                                                 └─────────────────┘
```

## 🔧 How It Works

### 1. Initial Setup (First Run)
1. **Data Collection**: Fetches your last 1000 tweets and 500 likes
2. **Personality Analysis**: GPT-4 analyzes your content and scores you on:
   - `humor_level` (0.0-1.0) - How funny/witty you are
   - `formality` (0.0-1.0) - How formal vs casual you are
   - `enthusiasm` (0.0-1.0) - How energetic your posts are
   - `technical_depth` (0.0-1.0) - How technical your content is
   - `controversy_tolerance` (0.0-1.0) - How much you engage with controversial topics
   - `emoji_usage` (0.0-1.0) - How frequently you use emojis
   - `hashtag_usage` (0.0-1.0) - How often you use hashtags

3. **Profile Storage**: Saves your personality model to local SQLite database

### 2. Ongoing Operation
1. **Timeline Monitoring**: Checks your timeline every hour (configurable - more frequent = higher costs)
2. **Content Analysis**: Evaluates each tweet for:
   - Relevance to your interests
   - Engagement potential
   - Alignment with your personality
3. **Decision Making**: Uses personality model to decide whether to like, reply, or retweet
4. **Content Generation**: Creates replies that match your authentic voice
5. **Action Execution**: Performs actions (respecting rate limits)

## 🛡️ Safety Features

- **DRY_RUN Mode**: Test everything without actually posting (enabled by default)
- **Rate Limiting**: Respects X's API limits and bot-friendly timeouts
- **Content Filtering**: Avoids controversial or inappropriate content
- **Manual Override**: Easy to stop or modify behavior
- **Interaction Logging**: All actions logged for review
- **Confidence Scoring**: Only acts when confident about decisions

## 📁 Project Structure

```
x-bot/
├── main.py                     # Main bot orchestrator
├── setup_and_run.py           # Configuration tester and runner
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
├── src/
│   ├── twitter_api/
│   │   └── client.py        # X API wrapper
│   ├── personality_analyzer/
│   │   └── analyzer.py      # GPT-4 personality analysis
│   ├── data_collector/
│   │   └── collector.py     # Tweet/like data collection
│   ├── decision_engine/
│   │   └── engine.py        # Decision logic for interactions
│   ├── content_generator/
│   │   └── generator.py     # Reply generation
│   └── utils/
│       ├── config.py        # Configuration management
│       └── database.py      # SQLite database operations
└── logs/                    # Bot activity logs (auto-created)
```

## ⚙️ Configuration Options

Edit `config.yaml` to customize behavior:

```yaml
schedule:
  timeline_check_interval: 15    # Minutes between timeline checks
  mentions_check_interval: 5     # Minutes between mention checks

interactions:
  like_criteria:
    min_engagement_score: 0.6    # Minimum score to like
  reply_criteria:
    min_engagement_score: 0.8    # Minimum score to reply
  retweet_criteria:
    min_engagement_score: 0.9    # Minimum score to retweet

personality:
  tweet_analysis_count: 1000     # Tweets to analyze for personality
```

## 🚨 Troubleshooting

### Common Issues

**API Authentication Errors**
```bash
# Test your API keys
python setup_and_run.py
```

**Rate Limit Exceeded**
- Bot automatically waits when hitting limits
- Reduce frequency in config.yaml if needed

**No Personality Data Found**
- Bot will automatically analyze on first run
- Delete `xbot.db` to force re-analysis

**Permission Errors**
```bash
# Make sure you have the right X API permissions
# Check your X Developer Portal app settings
```

### Getting Help

1. Check the logs in `logs/bot.log`
2. Run in DRY_RUN mode to test without posting
3. Use `python setup_and_run.py` to validate configuration

## 🗄️ Database Setup

### **SQLite Database (No Setup Required!)**

The bot uses **SQLite** - a local file-based database that requires **zero installation**:

```bash
DATABASE_URL=sqlite:///xbot.db  # Creates local file 'xbot.db'
```

**What happens automatically:**
1. 📁 **Creates** `xbot.db` file in your project directory on first run
2. 🏗️ **Creates tables** for personality data, interactions, and logs
3. 🔄 **No configuration needed** - SQLite comes with Python!

**Database stores:**
- **Personality Profile** - Your analyzed writing style, humor, preferences
- **User Data** - Your collected tweets, likes, and interactions  
- **Interaction Log** - Record of all bot actions (likes, replies, retweets)
- **Processed Tweets** - Tracks what's been analyzed (avoids duplicates)
- **Rate Limiting** - Prevents API abuse

### **Alternative Database Options**

```bash
# Different local file name
DATABASE_URL=sqlite:///my_bot_data.db

# Memory database (faster, but loses data when stopped)
DATABASE_URL=sqlite:///:memory:

# PostgreSQL for advanced users
DATABASE_URL=postgresql://user:password@localhost/database_name
```

## 📊 Monitoring

The bot logs all activity to `logs/bot.log` and stores interaction data in `xbot.db`:

```bash
# View recent activity
tail -f logs/bot.log

# Check database contents (requires sqlite3)
sqlite3 xbot.db ".tables"  # List all tables
sqlite3 xbot.db "SELECT * FROM personality_profile;"  # View your personality model
sqlite3 xbot.db "SELECT * FROM interaction_log ORDER BY timestamp DESC LIMIT 10;"  # Recent actions
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## ⚖️ Ethics & Compliance

- **Transparency**: Bot behavior is clearly documented and logged
- **Rate Limiting**: Respects X's API limits and ToS
- **Content Quality**: Focuses on engaging meaningfully, not spamming
- **User Control**: Easy to monitor, modify, or disable
- **Privacy**: All data stored locally, not shared with third parties

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🔗 Related

- [X Developer Documentation](https://developer.twitter.com/en/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Tweepy Documentation](https://docs.tweepy.org/)

---

**⚠️ Disclaimer**: This bot is for educational and personal use. Users are responsible for compliance with X's Terms of Service and applicable laws. Use responsibly and transparently.
