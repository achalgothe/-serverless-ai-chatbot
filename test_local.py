#!/usr/bin/env python3
"""
Local testing script for the chatbot Lambda function
"""
import json
import os
from src.functions.chat import handler


def test_chat():
    """Test the chat function locally"""
    # Mock API Gateway event
    event = {
        'body': json.dumps({
            'message': 'Hello! What can you do?',
            'session_id': 'test-session-123'
        }),
        'pathParameters': {},
        'queryStringParameters': {},
        'headers': {
            'Content-Type': 'application/json'
        }
    }
    
    context = type('Context', (), {
        'function_name': 'chat',
        'memory_limit_in_mb': 256,
        'invoked_function_arn': 'arn:aws:lambda:us-east-1:123456789012:function:chat',
        'aws_request_id': 'test-request-id'
    })()
    
    print("Testing chat function...")
    print("=" * 50)
    
    response = handler(event, context)
    
    print(f"Status Code: {response['statusCode']}")
    print(f"Response: {json.dumps(json.loads(response['body']), indent=2)}")
    
    return response


if __name__ == '__main__':
    # Load environment variables from .env file if exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("python-dotenv not installed, using system environment variables")
    
    test_chat()
