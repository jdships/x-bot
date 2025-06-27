"""Content generator for creating responses."""

import openai
from typing import Optional, Dict, Any
from loguru import logger


class ContentGenerator:
    """Generates content based on user's personality."""
    
    def __init__(self, config, db):
        self.config = config
        self.db = db
        self.openai_client = openai.OpenAI(api_key=config.openai.api_key)
        
    async def generate_reply(self, tweet: 'Tweet', decision: Dict[str, Any]) -> Optional[str]:
        """Generate a reply to a tweet."""
        try:
            # Get personality profile
            personality = await self.db.get_personality_profile()
            
            # Create prompt for response generation
            prompt = self._create_response_prompt(tweet, personality, decision)
            
            # Generate response using AI
            response = self.openai_client.chat.completions.create(
                model=self.config.openai.model,
                messages=[
                    {"role": "system", "content": "You are a helpful and engaging X user. Generate natural responses."},
                    {"role": "user", "content": prompt}
                ],
                temperature=self.config.openai.temperature,
                max_tokens=self.config.openai.max_tokens
            )
            
            reply_text = response.choices[0].message.content.strip()
            
            # Ensure reply fits X character limit
            if len(reply_text) > 280:
                reply_text = reply_text[:277] + "..."
                
            logger.info(f"Generated reply: {reply_text}")
            return reply_text
            
        except Exception as e:
            logger.error(f"Failed to generate reply: {e}")
            return None
            
    def _create_response_prompt(self, tweet: 'Tweet', personality: Dict, decision: Dict) -> str:
        """Create prompt for response generation."""
        personality_desc = ""
        if personality:
            humor = personality.get('humor_level', {}).get('score', 0.5)
            formality = personality.get('formality', {}).get('score', 0.5)
            
            if humor > 0.7:
                personality_desc += "Be humorous and witty. "
            if formality < 0.3:
                personality_desc += "Be casual and informal. "
            else:
                personality_desc += "Be professional but friendly. "
        
        return f"""
{personality_desc}

Respond to this tweet: "{tweet.text}"

Author: @{tweet.author.username}
Context: {decision.get('reasoning', 'General response')}

Generate a helpful, engaging reply that fits the user's personality. Keep it under 280 characters.
"""
