#!/usr/bin/env python3
"""Setup script to test configuration and run the bot."""

import sys
import os
import asyncio
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.config import Config
from dotenv import load_dotenv

def check_environment():
    """Check if environment is properly set up."""
    print("🔍 Checking environment setup...")
    
    # Load environment variables
    load_dotenv()
    
    # Check for .env file
    if not Path('.env').exists():
        print("❌ .env file not found. Please copy .env.example to .env and add your API keys.")
        return False
    
    # Check configuration
    try:
        config = Config()
        if not config.validate():
            print("❌ Configuration validation failed. Please check your API keys in .env file.")
            return False
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False
    
    print("✅ Environment setup looks good!")
    return True

def check_api_keys():
    """Check if API keys are properly set."""
    print("🔑 Checking API keys...")
    
    required_keys = [
        'TWITTER_API_KEY',
        'TWITTER_API_SECRET', 
        'TWITTER_ACCESS_TOKEN',
        'TWITTER_ACCESS_TOKEN_SECRET',
        'TWITTER_BEARER_TOKEN',
        'OPENAI_API_KEY',
        'BOT_USERNAME'
    ]
    
    missing_keys = []
    for key in required_keys:
        value = os.getenv(key)
        if not value or value == f"your_{key.lower()}_here" or "your_" in value:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ Missing or invalid API keys: {', '.join(missing_keys)}")
        print("Please update your .env file with real API keys.")
        return False
    
    print("✅ All API keys appear to be set!")
    return True

async def test_twitter_connection():
    """Test X API connection."""
    print("🐦 Testing X API connection...")
    
    try:
        from twitter_api.client import TwitterClient
        config = Config()
        
        client = TwitterClient(config)
        success = await client.verify_credentials()
        
        if success:
            print("✅ X API connection successful!")
            return True
        else:
            print("❌ X API connection failed.")
            return False
            
    except Exception as e:
        print(f"❌ X API test failed: {e}")
        return False

async def test_openai_connection():
    """Test OpenAI API connection."""
    print("🤖 Testing OpenAI API connection...")
    
    try:
        import openai
        config = Config()
        
        client = openai.OpenAI(api_key=config.openai.api_key)
        
        # Simple test call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use cheaper model for testing
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        
        if response.choices:
            print("✅ OpenAI API connection successful!")
            return True
        else:
            print("❌ OpenAI API connection failed.")
            return False
            
    except Exception as e:
        print(f"❌ OpenAI API test failed: {e}")
        return False

async def run_bot():
    """Run the main bot."""
    print("🚀 Starting the bot...")
    
    try:
        # Import main bot
        from main import main
        await main()
        
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user.")
    except Exception as e:
        print(f"❌ Bot failed to run: {e}")

async def main():
    """Main setup and run function."""
    print("=" * 50)
    print("🤖 Twitter Bot Setup and Runner")
    print("=" * 50)
    
    # Check environment
    if not check_environment():
        return False
    
    # Check API keys
    if not check_api_keys():
        return False
    
    # Test connections
    twitter_ok = await test_twitter_connection()
    openai_ok = await test_openai_connection()
    
    if not (twitter_ok and openai_ok):
        print("\n❌ API connection tests failed. Please check your credentials.")
        return False
    
    print("\n✅ All tests passed! Ready to run the bot.")
    
    # Ask user if they want to run the bot
    response = input("\nDo you want to start the bot now? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        print("\n🚀 Starting bot...")
        await run_bot()
    else:
        print("\n👍 Setup complete. Run 'python main.py' when ready.")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
