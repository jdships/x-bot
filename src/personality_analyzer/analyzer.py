"""Personality analyzer for building user profile."""

import openai
import json
from typing import Dict, Any, Optional
from loguru import logger


class PersonalityAnalyzer:
    """Analyzes user data to build personality profile."""
    
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.openai_client = openai.OpenAI(api_key=config.openai.api_key)
        
    async def has_personality_data(self) -> bool:
        """Check if personality data exists."""
        profile = await self.db.get_personality_profile()
        return profile is not None
        
    async def analyze(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze user data and create personality profile."""
        try:
            logger.info("Starting personality analysis...")
            
            # Prepare data for analysis
            tweets_text = "\n".join([tweet['content'] for tweet in user_data.get('tweets', [])])
            likes_text = "\n".join([like['content'] for like in user_data.get('likes', [])])
            bio = user_data.get('user_info', {}).get('bio', '')
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(bio, tweets_text, likes_text)
            
            # Get AI analysis
            response = self.openai_client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "You are a personality analyst. Analyze the user's social media data and provide insights."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            personality_profile = self._parse_analysis(analysis_text)
            
            # Save to database
            if personality_profile:
                await self.db.save_personality_profile(personality_profile)
                logger.info("Personality analysis complete and saved")
                return personality_profile
            else:
                logger.error("Failed to parse personality analysis")
                return None
                
        except Exception as e:
            logger.error(f"Personality analysis failed: {e}")
            return None
            
    def _create_analysis_prompt(self, bio: str, tweets: str, likes: str) -> str:
        """Create prompt for personality analysis."""
        return f"""
Analyze this user's personality based on their social media activity:

BIO: {bio[:500]}

RECENT TWEETS (sample):
{tweets[:2000]}

RECENT LIKES (sample):
{likes[:2000]}

Please analyze and rate the following personality dimensions on a scale of 0.0 to 1.0:

1. humor_level - How humorous/funny they are
2. formality - How formal vs casual their communication is
3. enthusiasm - How enthusiastic/energetic they are
4. technical_depth - How technical/detailed their content is
5. controversy_tolerance - How willing they are to engage with controversial topics
6. emoji_usage - How frequently they use emojis
7. hashtag_usage - How frequently they use hashtags

Respond in JSON format:
{{
    "humor_level": {{"score": 0.7, "confidence": 0.8}},
    "formality": {{"score": 0.3, "confidence": 0.9}},
    ...
}}
"""
    
    def _parse_analysis(self, analysis_text: str) -> Optional[Dict[str, Dict[str, float]]]:
        """Parse AI analysis response."""
        try:
            # Try to extract JSON from response
            start = analysis_text.find('{')
            end = analysis_text.rfind('}') + 1
            
            if start != -1 and end != -1:
                json_str = analysis_text[start:end]
                return json.loads(json_str)
            else:
                # Fallback: create basic profile
                logger.warning("Could not parse AI response, using fallback profile")
                return {
                    "humor_level": {"score": 0.5, "confidence": 0.5},
                    "formality": {"score": 0.5, "confidence": 0.5},
                    "enthusiasm": {"score": 0.5, "confidence": 0.5},
                    "technical_depth": {"score": 0.5, "confidence": 0.5},
                    "controversy_tolerance": {"score": 0.3, "confidence": 0.5},
                    "emoji_usage": {"score": 0.5, "confidence": 0.5},
                    "hashtag_usage": {"score": 0.5, "confidence": 0.5}
                }
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from analysis: {e}")
            return None
