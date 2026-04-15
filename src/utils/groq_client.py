import os
from groq import Groq


_groq_client = None


def get_groq_client():
    """Get Groq client with API key from environment"""
    global _groq_client
    
    if _groq_client is not None:
        return _groq_client
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        # Return None for local testing without Groq
        print("⚠️  Warning: GROQ_API_KEY not set. AI features disabled.")
        return None
    
    _groq_client = Groq(api_key=api_key)
    return _groq_client
