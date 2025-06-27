"""Configuration management for the X bot."""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class TwitterConfig:
    """X API configuration."""
    api_key: str
    api_secret: str
    access_token: str
    access_token_secret: str
    bearer_token: str


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 280


@dataclass
class RateLimits:
    """Rate limiting configuration."""
    likes_per_hour: int = 50
    replies_per_hour: int = 10
    retweets_per_hour: int = 5


class Config:
    """Main configuration class."""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._load_config()
        self._load_env_vars()
        
    def _load_config(self):
        """Load configuration from YAML file."""
        if self.config_path.exists():
            with open(self.config_path, 'r') as f:
                self.yaml_config = yaml.safe_load(f)
        else:
            self.yaml_config = {}
            
    def _load_env_vars(self):
        """Load configuration from environment variables."""
        # X API configuration
        self.twitter = TwitterConfig(
            api_key=os.getenv("TWITTER_API_KEY", ""),
            api_secret=os.getenv("TWITTER_API_SECRET", ""),
            access_token=os.getenv("TWITTER_ACCESS_TOKEN", ""),
            access_token_secret=os.getenv("TWITTER_ACCESS_TOKEN_SECRET", ""),
            bearer_token=os.getenv("TWITTER_BEARER_TOKEN", "")
        )
        
        # OpenAI configuration
        self.openai = OpenAIConfig(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            model=os.getenv("PERSONALITY_MODEL", "gpt-4"),
            temperature=float(os.getenv("RESPONSE_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("MAX_RESPONSE_LENGTH", "280"))
        )
        
        # Bot configuration
        self.bot_username = os.getenv("BOT_USERNAME", "")
        self.bot_name = os.getenv("BOT_NAME", "PersonalizedXBot")
        self.debug_mode = os.getenv("DEBUG_MODE", "true").lower() == "true"
        self.dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
        self.lite_mode = os.getenv("LITE_MODE", "false").lower() == "true"
        
        # Database
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///xbot.db")
        
        # Rate limits
        self.rate_limits = RateLimits(
            likes_per_hour=int(os.getenv("MAX_LIKES_PER_HOUR", "50")),
            replies_per_hour=int(os.getenv("MAX_TWEETS_PER_HOUR", "10")),
            retweets_per_hour=int(os.getenv("MAX_RETWEETS_PER_HOUR", "5"))
        )
        
        # Content filtering
        self.min_engagement_score = float(os.getenv("MIN_ENGAGEMENT_SCORE", "0.6"))
        self.avoid_controversial = os.getenv("AVOID_CONTROVERSIAL_TOPICS", "true").lower() == "true"
        self.safe_mode = os.getenv("SAFE_MODE", "true").lower() == "true"
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value from YAML config."""
        keys = key.split('.')
        value = self.yaml_config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
                
        return value
        
    @property
    def timeline_check_interval(self) -> int:
        """Timeline check interval in minutes."""
        return self.get('schedule.timeline_check_interval', 15)
        
    @property
    def mentions_check_interval(self) -> int:
        """Mentions check interval in minutes."""
        return self.get('schedule.mentions_check_interval', 5)
        
    @property
    def preferred_topics(self) -> List[str]:
        """List of preferred topics."""
        return self.get('content.preferred_topics', [])
        
    @property
    def avoided_topics(self) -> List[str]:
        """List of topics to avoid."""
        return self.get('content.avoided_topics', [])
        
    @property
    def personality_dimensions(self) -> List[str]:
        """List of personality dimensions to track."""
        return self.get('personality.dimensions', [])
        
    @property
    def like_criteria(self) -> Dict[str, Any]:
        """Criteria for liking tweets."""
        return self.get('interactions.like_criteria', {})
        
    @property
    def reply_criteria(self) -> Dict[str, Any]:
        """Criteria for replying to tweets."""
        return self.get('interactions.reply_criteria', {})
        
    @property
    def retweet_criteria(self) -> Dict[str, Any]:
        """Criteria for retweeting."""
        return self.get('interactions.retweet_criteria', {})
        
    def validate(self) -> bool:
        """Validate configuration."""
        if not self.twitter.api_key:
            print("Error: TWITTER_API_KEY not set")
            return False
            
        if not self.twitter.api_secret:
            print("Error: TWITTER_API_SECRET not set")
            return False
            
        if not self.twitter.access_token:
            print("Error: TWITTER_ACCESS_TOKEN not set")
            return False
            
        if not self.twitter.access_token_secret:
            print("Error: TWITTER_ACCESS_TOKEN_SECRET not set")
            return False
            
        if not self.openai.api_key:
            print("Error: OPENAI_API_KEY not set")
            return False
            
        if not self.bot_username:
            print("Error: BOT_USERNAME not set")
            return False
            
        return True
