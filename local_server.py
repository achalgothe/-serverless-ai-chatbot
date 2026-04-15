#!/usr/bin/env python3
"""
Local development server that simulates API Gateway
Run this to test the chatbot locally without AWS deployment
"""
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.functions.chat import handler as chat_handler
from src.functions.getConversations import handler as get_conversations_handler
from src.functions.deleteConversation import handler as delete_conversation_handler
from src.functions.analytics import handler as analytics_handler
from src.utils.response import error_response

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)

# Set default values for local development
os.environ.setdefault('DYNAMODB_TABLE', 'chatbot-conversations-dev')
os.environ.setdefault('REGION', 'us-east-1')
os.environ.setdefault('AWS_LAMBDA_FUNCTION_NAME', 'chat-local')
os.environ.setdefault('AWS_DEFAULT_REGION', 'us-east-1')

# Verify OpenAI key is loaded
if os.environ.get('OPENAI_API_KEY'):
    print("✅ OpenAI API Key loaded successfully")
else:
    print("⚠️  OpenAI API Key not found")

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)  # Enable CORS for all routes


@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        body = request.get_json()
        
        # Simulate API Gateway event
        event = {
            'body': str(body),
            'pathParameters': {},
            'queryStringParameters': {},
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
        # Fix: convert body to JSON string
        import json
        event['body'] = json.dumps(body)
        
        context = create_mock_context('chat')
        response = chat_handler(event, context)
        
        return jsonify(json.loads(response['body'])), response['statusCode']
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/conversations/<session_id>', methods=['GET'])
def get_conversations(session_id):
    """Get conversation history endpoint"""
    try:
        event = {
            'pathParameters': {'sessionId': session_id}
        }
        
        context = create_mock_context('getConversations')
        response = get_conversations_handler(event, context)
        
        import json
        return jsonify(json.loads(response['body'])), response['statusCode']
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/conversations/<session_id>', methods=['DELETE'])
def delete_conversation(session_id):
    """Delete conversation endpoint"""
    try:
        event = {
            'pathParameters': {'sessionId': session_id}
        }
        
        context = create_mock_context('deleteConversation')
        response = delete_conversation_handler(event, context)
        
        import json
        return jsonify(json.loads(response['body'])), response['statusCode']
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/analytics', methods=['GET'])
def analytics():
    """Analytics endpoint"""
    try:
        event = {}
        
        context = create_mock_context('analytics')
        response = analytics_handler(event, context)
        
        import json
        return jsonify(json.loads(response['body'])), response['statusCode']
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'Serverless AI Chatbot (Local)',
        'openai_configured': bool(os.environ.get('OPENAI_API_KEY'))
    })


@app.route('/')
def index():
    """Serve the frontend chat UI"""
    return send_from_directory('frontend', 'index.html')


def create_mock_context(function_name):
    """Create mock Lambda context"""
    class MockContext:
        def __init__(self, name):
            self.function_name = name
            self.memory_limit_in_mb = 256
            self.invoked_function_arn = f'arn:aws:lambda:us-east-1:123456789012:function:{name}'
            self.aws_request_id = 'local-test-id'
    return MockContext(function_name)


if __name__ == '__main__':
    # Check if OpenAI key is set
    if not os.environ.get('OPENAI_API_KEY'):
        print("\n⚠️  WARNING: OPENAI_API_KEY not set!")
        print("Please create a .env file with your OpenAI API key\n")
        print("Example:")
        print("  OPENAI_API_KEY=sk-your-key-here\n")
    
    print("\n" + "="*60)
    print("🤖 Serverless AI Chatbot - Local Development Server")
    print("="*60)
    print("\n🌐 Server running at: http://localhost:3000")
    print("\n💡 Open your browser and visit: http://localhost:3000")
    print("   The chat UI will be available there!")
    print("\n📋 API endpoints:")
    print("  POST   http://localhost:3000/chat")
    print("  GET    http://localhost:3000/conversations/<session_id>")
    print("  DELETE http://localhost:3000/conversations/<session_id>")
    print("  GET    http://localhost:3000/analytics")
    print("  GET    http://localhost:3000/health")
    print("\n" + "="*60 + "\n")
    
    # Install flask if not available
    try:
        import flask
    except ImportError:
        print("Installing Flask...")
        os.system('pip install flask python-dotenv')

    app.run(debug=True, host='0.0.0.0', port=3000)
