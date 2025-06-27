"""Data collector for gathering user's X data."""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class DataCollector:
    """Collects user's X data for personality analysis."""
    
    def __init__(self, config, db, twitter_client):
        self.config = config
        self.db = db
        self.twitter_client = twitter_client
        
    async def collect_user_data(self) -> Dict[str, Any]:
        """Collect all user data for personality analysis."""
        logger.info(f"Starting data collection for @{self.config.bot_username}")
        
        # Get user info
        user_info = await self.twitter_client.get_user_info(self.config.bot_username)
        if not user_info:
            logger.error(f"Failed to get user info for @{self.config.bot_username}")
            return {}
            
        # Collect different types of data
        user_tweets = await self._collect_user_tweets()
        user_likes = await self._collect_user_likes(user_info.id)
        
        # Prepare data for analysis
        collected_data = {
            'user_info': {
                'username': user_info.username,
                'name': user_info.name,
                'bio': user_info.description,
                'metrics': user_info.public_metrics
            },
            'tweets': user_tweets,
            'likes': user_likes,
            'total_interactions': len(user_tweets) + len(user_likes)
        }
        
        # Save to database
        await self._save_collected_data(collected_data)
        
        logger.info(f"Data collection complete: {len(user_tweets)} tweets, {len(user_likes)} likes")
        return collected_data
        
    async def _collect_user_tweets(self) -> List[Dict[str, Any]]:
        """Collect user's tweets."""
        try:
            count = self.config.get('personality.tweet_analysis_count', 1000)
            tweets = await self.twitter_client.get_user_tweets(
                self.config.bot_username, 
                count=count
            )
            
            tweet_data = []
            for tweet in tweets:
                tweet_data.append({
                    'tweet_id': tweet.id,
                    'content': tweet.text,
                    'interaction_type': 'tweet',
                    'timestamp': tweet.created_at,
                    'metadata': {
                        'public_metrics': tweet.public_metrics,
                        'context_annotations': tweet.context_annotations or []
                    }
                })
                
            return tweet_data
            
        except Exception as e:
            logger.error(f"Failed to collect user tweets: {e}")
            return []
            
    async def _collect_user_likes(self, user_id: str) -> List[Dict[str, Any]]:
        """Collect user's liked tweets."""
        try:
            count = self.config.get('personality.tweet_analysis_count', 1000) // 2  # Collect fewer likes
            likes = await self.twitter_client.get_user_likes(user_id, count=count)
            
            like_data = []
            for tweet in likes:
                like_data.append({
                    'tweet_id': tweet.id,
                    'content': tweet.text,
                    'interaction_type': 'like',
                    'timestamp': tweet.created_at,
                    'metadata': {
                        'original_author': tweet.author.username,
                        'public_metrics': tweet.public_metrics,
                        'context_annotations': tweet.context_annotations or []
                    }
                })
                
            return like_data
            
        except Exception as e:
            logger.error(f"Failed to collect user likes: {e}")
            return []
            
    async def _save_collected_data(self, data: Dict[str, Any]):
        """Save collected data to database."""
        try:
            # Combine tweets and likes for storage
            all_interactions = data['tweets'] + data['likes']
            
            if all_interactions:
                await self.db.save_user_data(all_interactions)
                logger.info(f"Saved {len(all_interactions)} interactions to database")
            else:
                logger.warning("No interactions to save")
                
        except Exception as e:
            logger.error(f"Failed to save collected data: {e}")
            
    async def update_recent_interactions(self) -> bool:
        """Update with recent user interactions."""
        try:
            logger.info("Updating recent interactions...")
            
            # Get recent tweets (last 50)
            recent_tweets = await self.twitter_client.get_user_tweets(
                self.config.bot_username, 
                count=50
            )
            
            # Get user info for likes
            user_info = await self.twitter_client.get_user_info(self.config.bot_username)
            if user_info:
                recent_likes = await self.twitter_client.get_user_likes(
                    user_info.id, 
                    count=25
                )
            else:
                recent_likes = []
            
            # Process and save new data
            new_data = []
            
            for tweet in recent_tweets:
                new_data.append({
                    'tweet_id': tweet.id,
                    'content': tweet.text,
                    'interaction_type': 'tweet',
                    'timestamp': tweet.created_at,
                    'metadata': {
                        'public_metrics': tweet.public_metrics,
                        'context_annotations': tweet.context_annotations or []
                    }
                })
                
            for tweet in recent_likes:
                new_data.append({
                    'tweet_id': tweet.id,
                    'content': tweet.text,
                    'interaction_type': 'like',
                    'timestamp': tweet.created_at,
                    'metadata': {
                        'original_author': tweet.author.username,
                        'public_metrics': tweet.public_metrics,
                        'context_annotations': tweet.context_annotations or []
                    }
                })
            
            if new_data:
                await self.db.save_user_data(new_data)
                logger.info(f"Updated with {len(new_data)} recent interactions")
                return True
            else:
                logger.info("No new interactions to update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update recent interactions: {e}")
            return False
