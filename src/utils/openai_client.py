import os
from openai import OpenAI


_openai_client = None


def get_openai_client():
    """Get OpenAI client with API key from environment"""
    global _openai_client
    
    if _openai_client is not None:
        return _openai_client
    
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        # Return None for local testing without OpenAI
        print("⚠️  Warning: OPENAI_API_KEY not set. AI features disabled.")
        return None
    
    _openai_client = OpenAI(api_key=api_key)
    return _openai_client
