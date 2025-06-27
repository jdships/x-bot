#!/usr/bin/env python3
"""
Personalized Twitter Bot
A bot that learns your personality and interaction style to automatically engage with content.
"""

import asyncio
import sys
import signal
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import Config
from utils.database import Database
from twitter_api.client import TwitterClient
from personality_analyzer.analyzer import PersonalityAnalyzer
from data_collector.collector import DataCollector
from decision_engine.engine import DecisionEngine
from content_generator.generator import ContentGenerator


class TwitterBot:
    """Main Twitter bot orchestrator."""
    
    def __init__(self):
        self.config = Config()
        self.db = Database(self.config.database_url)
        self.twitter_client = TwitterClient(self.config)
        self.personality_analyzer = PersonalityAnalyzer(self.config, self.db)
        self.data_collector = DataCollector(self.config, self.db, self.twitter_client)
        self.content_generator = ContentGenerator(self.config, self.db)
        self.decision_engine = DecisionEngine(self.config, self.db)
        self.running = False
        
    async def initialize(self):
        """Initialize the bot and all components."""
        logger.info("Initializing Twitter Bot...")
        
        # Initialize database
        await self.db.initialize()
        
        # Verify Twitter API connection
        if not await self.twitter_client.verify_credentials():
            logger.error("Failed to verify Twitter credentials")
            return False
            
        # Check if personality analysis is needed
        if not await self.personality_analyzer.has_personality_data():
            logger.info("No personality data found. Starting personality analysis...")
            await self.analyze_personality()
            
        logger.info("Bot initialization complete!")
        return True
        
    async def analyze_personality(self):
        """Analyze user's personality from their Twitter data."""
        logger.info("Collecting user data for personality analysis...")
        
        # Collect user's tweets, likes, and replies
        user_data = await self.data_collector.collect_user_data()
        
        if not user_data:
            logger.error("Failed to collect user data")
            return False
            
        # Analyze personality
        personality_profile = await self.personality_analyzer.analyze(user_data)
        
        if personality_profile:
            logger.info(f"Personality analysis complete: {personality_profile}")
            return True
        else:
            logger.error("Personality analysis failed")
            return False
            
    async def run(self):
        """Main bot loop."""
        self.running = True
        logger.info("Starting bot main loop...")
        
        while self.running:
            try:
                # Check timeline for new content
                await self.process_timeline()
                
                # Check mentions
                await self.process_mentions()
                
                # Wait before next iteration (longer in lite mode to save API calls)
                interval = self.config.timeline_check_interval
                if self.config.lite_mode:
                    interval = max(interval * 4, 240)  # At least 4 hours in lite mode
                await asyncio.sleep(interval * 60)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(60)  # Wait a minute before retrying
                
    async def process_timeline(self):
        """Process timeline tweets and decide on interactions."""
        logger.debug("Processing timeline...")
        
        # Get recent timeline tweets
        tweets = await self.twitter_client.get_timeline_tweets()
        
        for tweet in tweets:
            # Skip if already processed
            if await self.db.is_tweet_processed(tweet.id):
                continue
                
            # Analyze tweet and decide on action
            decision = await self.decision_engine.analyze_tweet(tweet)
            
            if decision.should_like:
                await self.like_tweet(tweet, decision)
                
            if decision.should_reply:
                await self.reply_to_tweet(tweet, decision)
                
            if decision.should_retweet:
                await self.retweet_tweet(tweet, decision)
                
            # Mark tweet as processed
            await self.db.mark_tweet_processed(tweet.id)
            
    async def process_mentions(self):
        """Process mentions and replies."""
        logger.debug("Processing mentions...")
        
        mentions = await self.twitter_client.get_mentions()
        
        for mention in mentions:
            if await self.db.is_tweet_processed(mention.id):
                continue
                
            # Analyze mention and generate response
            decision = await self.decision_engine.analyze_mention(mention)
            
            if decision.should_reply:
                await self.reply_to_tweet(mention, decision)
                
            await self.db.mark_tweet_processed(mention.id)
            
    async def like_tweet(self, tweet, decision):
        """Like a tweet."""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would like tweet: {tweet.text[:50]}...")
            return
            
        success = await self.twitter_client.like_tweet(tweet.id)
        if success:
            logger.info(f"Liked tweet by @{tweet.author.username}")
            await self.db.log_interaction("like", tweet.id, decision.reasoning)
        else:
            logger.error(f"Failed to like tweet {tweet.id}")
            
    async def reply_to_tweet(self, tweet, decision):
        """Reply to a tweet."""
        # Generate response
        response_text = await self.content_generator.generate_reply(tweet, decision)
        
        if not response_text:
            logger.warning(f"Failed to generate response for tweet {tweet.id}")
            return
            
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would reply to @{tweet.author.username}: {response_text}")
            return
            
        success = await self.twitter_client.reply_to_tweet(tweet.id, response_text)
        if success:
            logger.info(f"Replied to @{tweet.author.username}")
            await self.db.log_interaction("reply", tweet.id, decision.reasoning, response_text)
        else:
            logger.error(f"Failed to reply to tweet {tweet.id}")
            
    async def retweet_tweet(self, tweet, decision):
        """Retweet a tweet."""
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would retweet: {tweet.text[:50]}...")
            return
            
        success = await self.twitter_client.retweet(tweet.id)
        if success:
            logger.info(f"Retweeted tweet by @{tweet.author.username}")
            await self.db.log_interaction("retweet", tweet.id, decision.reasoning)
        else:
            logger.error(f"Failed to retweet tweet {tweet.id}")
            
    def stop(self):
        """Stop the bot."""
        self.running = False
        logger.info("Bot stopping...")


async def main():
    """Main function."""
    # Load environment variables
    load_dotenv()
    
    # Setup logging
    logger.add("logs/bot.log", rotation="1 day", retention="1 week")
    logger.info("Starting Personalized Twitter Bot")
    
    # Create bot instance
    bot = TwitterBot()
    
    # Setup signal handlers
    def signal_handler(signum, frame):
        logger.info(f"Received signal {signum}")
        bot.stop()
        
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Initialize and run bot
    if await bot.initialize():
        await bot.run()
    else:
        logger.error("Failed to initialize bot")
        sys.exit(1)
        
    logger.info("Bot shutdown complete")


if __name__ == "__main__":
    asyncio.run(main())
