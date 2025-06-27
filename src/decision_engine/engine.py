"""Decision engine for determining bot actions."""

from typing import Dict, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class Decision:
    """Decision result for tweet interaction."""
    should_reply: bool = False
    should_like: bool = False
    should_retweet: bool = False
    reasoning: str = ""
    confidence: float = 0.0


class DecisionEngine:
    """Determines when and how the bot should interact."""
    
    def __init__(self, config, db):
        self.config = config
        self.db = db
        
    async def analyze_tweet(self, tweet) -> Decision:
        """Analyze tweets for possible interactions."""
        decision = Decision()
        
        # Get personality profile for context
        personality = await self.db.get_personality_profile()
        
        # Analyze tweet content
        tweet_text = tweet.text.lower()
        
        # Decision logic based on personality and content
        if self._meets_criteria_for_reply(tweet, personality):
            decision.should_reply = True
            decision.reasoning += "Fits reply criteria. "
            decision.confidence += 0.3
        
        if self._meets_criteria_for_like(tweet, personality):
            decision.should_like = True
            decision.reasoning += "Meets like criteria. "
            decision.confidence += 0.2
        
        if self._meets_criteria_for_retweet(tweet, personality):
            decision.should_retweet = True
            decision.reasoning += "Meets retweet criteria. "
            decision.confidence += 0.4
        
        logger.debug(f"Decision for tweet {tweet.id}: Reply={decision.should_reply}, Like={decision.should_like}, Retweet={decision.should_retweet}, Confidence={decision.confidence:.2f}")
        return decision

    def _meets_criteria_for_reply(self, tweet, personality) -> bool:
        """Determine if tweet meets criteria for reply."""
        tweet_text = tweet.text.lower()
        
        # Basic criteria
        if "?" in tweet.text:  # Questions
            return True
            
        # Personality-based criteria
        if personality:
            humor_level = personality.get('humor_level', {}).get('score', 0.5)
            if humor_level > 0.7 and any(word in tweet_text for word in ['funny', 'lol', 'joke', 'humor']):
                return True
                
            technical_depth = personality.get('technical_depth', {}).get('score', 0.5)
            if technical_depth > 0.6 and any(word in tweet_text for word in ['tech', 'programming', 'code', 'software']):
                return True
        
        return False
        
    def _meets_criteria_for_like(self, tweet, personality) -> bool:
        """Determine if a tweet meets criteria for liking."""
        tweet_text = tweet.text.lower()
        
        # Basic positive indicators
        positive_words = ['thank', 'awesome', 'great', 'excellent', 'amazing', 'love', 'brilliant']
        if any(word in tweet_text for word in positive_words):
            return True
            
        # Check engagement metrics
        if hasattr(tweet, 'public_metrics'):
            metrics = tweet.public_metrics
            like_count = metrics.get('like_count', 0)
            retweet_count = metrics.get('retweet_count', 0)
            
            # Like popular content (but not too popular to avoid spam)
            if 10 <= like_count <= 1000 and retweet_count > 5:
                return True
        
        return False
        
    def _meets_criteria_for_retweet(self, tweet, personality) -> bool:
        """Determine if a tweet meets criteria for retweeting."""
        tweet_text = tweet.text.lower()
        
        # Avoid retweeting retweets
        if tweet_text.startswith('rt @') or 'via @' in tweet_text:
            return False
            
        # Look for valuable content
        valuable_indicators = ['tutorial', 'guide', 'tip', 'resource', 'useful', 'important']
        if any(word in tweet_text for word in valuable_indicators):
            return True
            
        # Check if it's from a verified or high-engagement account
        if hasattr(tweet, 'author') and hasattr(tweet.author, 'public_metrics'):
            author_metrics = tweet.author.public_metrics or {}
            followers = author_metrics.get('followers_count', 0)
            if followers > 10000:  # High-influence account
                return True
        
        return False
    
    async def analyze_mention(self, mention) -> Decision:
        """Analyze mentions for responses."""
        decision = Decision()
        decision.should_reply = True
        decision.reasoning = 'Responding to mention'
        decision.confidence = 0.9
        
        # Also consider liking mentions as courtesy
        decision.should_like = True
        decision.reasoning += ' and liking mention'
        
        return decision
