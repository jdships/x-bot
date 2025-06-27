"""X API client for the bot."""

import tweepy
import asyncio
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger


@dataclass
class Tweet:
    """Tweet data model."""
    id: str
    text: str
    author: 'User'
    created_at: datetime
    public_metrics: Dict[str, int]
    context_annotations: List[Dict] = None
    referenced_tweets: List[Dict] = None


@dataclass  
class User:
    """User data model."""
    id: str
    username: str
    name: str
    description: str = ""
    public_metrics: Dict[str, int] = None


class TwitterClient:
    """X API client wrapper."""
    
    def __init__(self, config):
        self.config = config
        self.api_v1 = None
        self.api_v2 = None
        self._initialize_clients()
        
    def _initialize_clients(self):
        """Initialize X API clients."""
        try:
            # Twitter API v1.1 client (for likes, retweets, etc.)
            auth = tweepy.OAuthHandler(
                self.config.twitter.api_key,
                self.config.twitter.api_secret
            )
            auth.set_access_token(
                self.config.twitter.access_token,
                self.config.twitter.access_token_secret
            )
            self.api_v1 = tweepy.API(auth, wait_on_rate_limit=True)
            
            # Twitter API v2 client (for advanced features)
            self.api_v2 = tweepy.Client(
                bearer_token=self.config.twitter.bearer_token,
                consumer_key=self.config.twitter.api_key,
                consumer_secret=self.config.twitter.api_secret,
                access_token=self.config.twitter.access_token,
                access_token_secret=self.config.twitter.access_token_secret,
                wait_on_rate_limit=True
            )
            
            logger.info("X API clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize X API clients: {e}")
            raise
            
    async def verify_credentials(self) -> bool:
        """Verify X API credentials."""
        try:
            # Run in thread to avoid blocking
            user = await asyncio.get_event_loop().run_in_executor(
                None, self.api_v1.verify_credentials
            )
            if user:
                logger.info(f"Verified credentials for @{user.screen_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to verify credentials: {e}")
            return False
            
    async def get_user_tweets(self, username: str, count: int = 100) -> List[Tweet]:
        """Get tweets from a specific user."""
        try:
            def _get_tweets():
                tweets = []
                user_tweets = tweepy.Paginator(
                    self.api_v2.get_users_tweets,
                    username=username,
                    max_results=min(count, 100),
                    tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                    user_fields=['username', 'name', 'description', 'public_metrics']
                ).flatten(limit=count)
                
                for tweet in user_tweets:
                    # Get user info
                    user_response = self.api_v2.get_user(username=username, user_fields=['username', 'name', 'description', 'public_metrics'])
                    user_data = user_response.data
                    
                    user = User(
                        id=str(user_data.id),
                        username=user_data.username,
                        name=user_data.name,
                        description=user_data.description or "",
                        public_metrics=user_data.public_metrics
                    )
                    
                    tweets.append(Tweet(
                        id=str(tweet.id),
                        text=tweet.text,
                        author=user,
                        created_at=tweet.created_at,
                        public_metrics=tweet.public_metrics,
                        context_annotations=getattr(tweet, 'context_annotations', [])
                    ))
                    
                return tweets
                
            return await asyncio.get_event_loop().run_in_executor(None, _get_tweets)
            
        except Exception as e:
            logger.error(f"Failed to get user tweets: {e}")
            return []
            
    async def get_user_likes(self, user_id: str, count: int = 100) -> List[Tweet]:
        """Get tweets liked by a user."""
        try:
            def _get_likes():
                tweets = []
                liked_tweets = tweepy.Paginator(
                    self.api_v2.get_liked_tweets,
                    id=user_id,
                    max_results=min(count, 100),
                    tweet_fields=['created_at', 'public_metrics', 'context_annotations'],
                    user_fields=['username', 'name', 'description']
                ).flatten(limit=count)
                
                for tweet in liked_tweets:
                    # For simplicity, create a basic user object
                    user = User(
                        id="unknown",
                        username="unknown",
                        name="Unknown User"
                    )
                    
                    tweets.append(Tweet(
                        id=str(tweet.id),
                        text=tweet.text,
                        author=user,
                        created_at=tweet.created_at,
                        public_metrics=tweet.public_metrics,
                        context_annotations=getattr(tweet, 'context_annotations', [])
                    ))
                    
                return tweets
                
            return await asyncio.get_event_loop().run_in_executor(None, _get_likes)
            
        except Exception as e:
            logger.error(f"Failed to get user likes: {e}")
            return []
            
    async def get_timeline_tweets(self, count: int = 50) -> List[Tweet]:
        """Get tweets from user's timeline."""
        try:
            def _get_timeline():
                tweets = []
                timeline = self.api_v1.home_timeline(count=count, include_rts=True, tweet_mode='extended')
                
                for tweet in timeline:
                    user = User(
                        id=str(tweet.user.id),
                        username=tweet.user.screen_name,
                        name=tweet.user.name,
                        description=tweet.user.description or ""
                    )
                    
                    tweets.append(Tweet(
                        id=str(tweet.id),
                        text=tweet.full_text,
                        author=user,
                        created_at=tweet.created_at,
                        public_metrics={
                            'retweet_count': tweet.retweet_count,
                            'favorite_count': tweet.favorite_count,
                            'reply_count': 0  # Not available in v1.1
                        }
                    ))
                    
                return tweets
                
            return await asyncio.get_event_loop().run_in_executor(None, _get_timeline)
            
        except Exception as e:
            logger.error(f"Failed to get timeline tweets: {e}")
            return []
            
    async def get_mentions(self, count: int = 20) -> List[Tweet]:
        """Get mentions of the bot."""
        try:
            def _get_mentions():
                tweets = []
                mentions = self.api_v1.mentions_timeline(count=count, tweet_mode='extended')
                
                for tweet in mentions:
                    user = User(
                        id=str(tweet.user.id),
                        username=tweet.user.screen_name,
                        name=tweet.user.name,
                        description=tweet.user.description or ""
                    )
                    
                    tweets.append(Tweet(
                        id=str(tweet.id),
                        text=tweet.full_text,
                        author=user,
                        created_at=tweet.created_at,
                        public_metrics={
                            'retweet_count': tweet.retweet_count,
                            'favorite_count': tweet.favorite_count,
                            'reply_count': 0
                        }
                    ))
                    
                return tweets
                
            return await asyncio.get_event_loop().run_in_executor(None, _get_mentions)
            
        except Exception as e:
            logger.error(f"Failed to get mentions: {e}")
            return []
            
    async def like_tweet(self, tweet_id: str) -> bool:
        """Like a tweet."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.api_v1.create_favorite, tweet_id
            )
            logger.info(f"Liked tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to like tweet {tweet_id}: {e}")
            return False
            
    async def retweet(self, tweet_id: str) -> bool:
        """Retweet a tweet."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.api_v1.retweet, tweet_id
            )
            logger.info(f"Retweeted tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to retweet tweet {tweet_id}: {e}")
            return False
            
    async def reply_to_tweet(self, tweet_id: str, text: str) -> bool:
        """Reply to a tweet."""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self.api_v1.update_status, text, tweet_id
            )
            logger.info(f"Replied to tweet {tweet_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to reply to tweet {tweet_id}: {e}")
            return False
            
    async def get_user_info(self, username: str) -> Optional[User]:
        """Get user information."""
        try:
            def _get_user():
                user_response = self.api_v2.get_user(
                    username=username,
                    user_fields=['username', 'name', 'description', 'public_metrics']
                )
                user_data = user_response.data
                
                return User(
                    id=str(user_data.id),
                    username=user_data.username,
                    name=user_data.name,
                    description=user_data.description or "",
                    public_metrics=user_data.public_metrics
                )
                
            return await asyncio.get_event_loop().run_in_executor(None, _get_user)
            
        except Exception as e:
            logger.error(f"Failed to get user info for {username}: {e}")
            return None
