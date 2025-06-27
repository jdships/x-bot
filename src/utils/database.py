"""Database management for the X bot."""

import sqlite3
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class Tweet:
    """Tweet data model."""
    id: str
    text: str
    author_username: str
    author_id: str
    created_at: datetime
    public_metrics: Dict[str, int]
    context_annotations: List[Dict] = None
    referenced_tweets: List[Dict] = None


@dataclass
class InteractionRecord:
    """Interaction record data model."""
    id: int
    tweet_id: str
    interaction_type: str  # like, reply, retweet
    timestamp: datetime
    reasoning: str
    response_text: Optional[str] = None


class Database:
    """Database manager for the X bot."""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        # Extract path from sqlite URL
        if database_url.startswith("sqlite:///"):
            self.db_path = database_url[10:]
        else:
            self.db_path = "xbot.db"
            
    async def initialize(self):
        """Initialize database tables."""
        logger.info("Initializing database...")
        
        # Run in thread to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, self._create_tables
        )
        
    def _create_tables(self):
        """Create database tables if they don't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Personality profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS personality_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dimension TEXT NOT NULL,
                score REAL NOT NULL,
                confidence REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # User data table (your tweets, likes, etc.)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Processed tweets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_tweets (
                tweet_id TEXT PRIMARY KEY,
                processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interaction log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interaction_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tweet_id TEXT NOT NULL,
                interaction_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reasoning TEXT,
                response_text TEXT,
                success BOOLEAN DEFAULT TRUE
            )
        ''')
        
        # Content analysis cache
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS content_analysis (
                tweet_id TEXT PRIMARY KEY,
                relevance_score REAL,
                quality_score REAL,
                sentiment_score REAL,
                topics TEXT,
                analysis_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Rate limiting table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rate_limits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action_type TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(action_type, timestamp)
            )
        ''')
        
        conn.commit()
        conn.close()
        
    async def save_personality_profile(self, profile: Dict[str, Dict[str, float]]):
        """Save personality analysis results."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._save_personality_profile, profile
        )
        
    def _save_personality_profile(self, profile: Dict[str, Dict[str, float]]):
        """Save personality profile to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Clear existing profile
        cursor.execute('DELETE FROM personality_profile')
        
        # Insert new profile
        for dimension, data in profile.items():
            cursor.execute('''
                INSERT INTO personality_profile (dimension, score, confidence)
                VALUES (?, ?, ?)
            ''', (dimension, data.get('score', 0.0), data.get('confidence', 0.0)))
            
        conn.commit()
        conn.close()
        
    async def get_personality_profile(self) -> Optional[Dict[str, Dict[str, float]]]:
        """Get personality profile from database."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._get_personality_profile
        )
        
    def _get_personality_profile(self) -> Optional[Dict[str, Dict[str, float]]]:
        """Get personality profile from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT dimension, score, confidence FROM personality_profile
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return None
            
        profile = {}
        for dimension, score, confidence in rows:
            profile[dimension] = {
                'score': score,
                'confidence': confidence
            }
            
        return profile
        
    async def save_user_data(self, data: List[Dict[str, Any]]):
        """Save user's X data."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._save_user_data, data
        )
        
    def _save_user_data(self, data: List[Dict[str, Any]]):
        """Save user data to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for item in data:
            cursor.execute('''
                INSERT OR REPLACE INTO user_data 
                (tweet_id, content, interaction_type, timestamp, metadata)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                item['tweet_id'],
                item['content'],
                item['interaction_type'],
                item['timestamp'],
                json.dumps(item.get('metadata', {}))
            ))
            
        conn.commit()
        conn.close()
        
    async def is_tweet_processed(self, tweet_id: str) -> bool:
        """Check if tweet has already been processed."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._is_tweet_processed, tweet_id
        )
        
    def _is_tweet_processed(self, tweet_id: str) -> bool:
        """Check if tweet is already processed."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT 1 FROM processed_tweets WHERE tweet_id = ?',
            (tweet_id,)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
        
    async def mark_tweet_processed(self, tweet_id: str):
        """Mark tweet as processed."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._mark_tweet_processed, tweet_id
        )
        
    def _mark_tweet_processed(self, tweet_id: str):
        """Mark tweet as processed in database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR IGNORE INTO processed_tweets (tweet_id) VALUES (?)',
            (tweet_id,)
        )
        
        conn.commit()
        conn.close()
        
    async def log_interaction(self, interaction_type: str, tweet_id: str, 
                            reasoning: str, response_text: Optional[str] = None):
        """Log an interaction."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._log_interaction, interaction_type, tweet_id, reasoning, response_text
        )
        
    def _log_interaction(self, interaction_type: str, tweet_id: str, 
                        reasoning: str, response_text: Optional[str] = None):
        """Log interaction to database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO interaction_log 
            (tweet_id, interaction_type, reasoning, response_text)
            VALUES (?, ?, ?, ?)
        ''', (tweet_id, interaction_type, reasoning, response_text))
        
        conn.commit()
        conn.close()
        
    async def get_recent_interactions(self, hours: int = 24) -> List[InteractionRecord]:
        """Get recent interactions."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._get_recent_interactions, hours
        )
        
    def _get_recent_interactions(self, hours: int) -> List[InteractionRecord]:
        """Get recent interactions from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute('''
            SELECT id, tweet_id, interaction_type, timestamp, reasoning, response_text
            FROM interaction_log
            WHERE timestamp > ?
            ORDER BY timestamp DESC
        ''', (since,))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            records.append(InteractionRecord(
                id=row[0],
                tweet_id=row[1],
                interaction_type=row[2],
                timestamp=datetime.fromisoformat(row[3]),
                reasoning=row[4],
                response_text=row[5]
            ))
            
        return records
        
    async def can_perform_action(self, action_type: str, max_per_hour: int) -> bool:
        """Check if action is within rate limits."""
        return await asyncio.get_event_loop().run_in_executor(
            None, self._can_perform_action, action_type, max_per_hour
        )
        
    def _can_perform_action(self, action_type: str, max_per_hour: int) -> bool:
        """Check rate limits for action."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Count actions in the last hour
        since = datetime.now() - timedelta(hours=1)
        
        cursor.execute('''
            SELECT COUNT(*) FROM interaction_log
            WHERE interaction_type = ? AND timestamp > ?
        ''', (action_type, since))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count < max_per_hour
        
    async def cleanup_old_data(self, days: int = 90):
        """Clean up old data from database."""
        await asyncio.get_event_loop().run_in_executor(
            None, self._cleanup_old_data, days
        )
        
    def _cleanup_old_data(self, days: int):
        """Clean up old data from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = datetime.now() - timedelta(days=days)
        
        # Clean up old processed tweets
        cursor.execute(
            'DELETE FROM processed_tweets WHERE processed_at < ?',
            (cutoff,)
        )
        
        # Clean up old interaction logs
        cursor.execute(
            'DELETE FROM interaction_log WHERE timestamp < ?',
            (cutoff,)
        )
        
        # Clean up old content analysis
        cursor.execute(
            'DELETE FROM content_analysis WHERE created_at < ?',
            (cutoff,)
        )
        
        conn.commit()
        conn.close()
        
        logger.info(f"Cleaned up data older than {days} days")
