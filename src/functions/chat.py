import json
import os
import uuid
from datetime import datetime
from openai import OpenAI
import boto3
from botocore.exceptions import ClientError
from src.utils.response import success_response, error_response
from src.utils.dynamodb import get_dynamodb_resource
from src.utils.openai_client import get_openai_client
from src.utils.groq_client import get_groq_client

dynamodb = get_dynamodb_resource()
table_name = os.environ.get('DYNAMODB_TABLE', 'chatbot-conversations-dev')
table = dynamodb.Table(table_name) if hasattr(dynamodb, 'Table') else dynamodb
groq_client = get_groq_client()
openai_client = get_openai_client()  # Kept as fallback

# Log which AI provider is active
if groq_client:
    print("✅ Groq AI provider initialized (FREE)")
elif openai_client:
    print("✅ OpenAI provider initialized")
else:
    print("⚠️  No AI provider configured - running in mock mode")


def handler(event, context):
    """
    Main chat handler function
    Receives chat messages, sends to OpenAI, stores conversation
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        message = body.get('message', '').strip()
        session_id = body.get('session_id', str(uuid.uuid4()))
        
        if not message:
            return error_response(
                message="Message is required",
                status_code=400
            )
        
        # Get conversation history for context
        conversation_history = get_conversation_history(session_id)
        
        # Generate AI response
        ai_response = generate_ai_response(conversation_history, message)
        
        # Store user message
        store_message(session_id, message, 'user')
        
        # Store AI response
        store_message(session_id, ai_response, 'assistant')
        
        # Log for analytics
        log_analytics(session_id, message, ai_response)
        
        return success_response(
            data={
                'session_id': session_id,
                'response': ai_response,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Error in chat handler: {str(e)}")
        return error_response(
            message=f"Internal server error: {str(e)}",
            status_code=500
        )


def get_conversation_history(session_id):
    """Retrieve last 10 messages for context"""
    try:
        response = table.query(
            KeyConditionExpression='sessionId = :sid',
            ExpressionAttributeValues={':sid': session_id},
            ScanIndexForward=True,
            Limit=10
        )
        
        messages = []
        for item in response.get('Items', []):
            messages.append({
                'role': item['role'],
                'content': item['message']
            })
        
        return messages
    except ClientError as e:
        print(f"Error getting conversation history: {e}")
        return []


def generate_ai_response(history, user_message):
    """Call AI API to generate response - Groq (free) or OpenAI as fallback"""
    try:
        if not groq_client and not openai_client:
            # Mock response for local testing without any AI
            return f"[Local Testing Mode] You said: '{user_message}'. Get a free API key from https://console.groq.com to enable AI."
        
        messages = [
            {
                'role': 'system',
                'content': 'You are a helpful AI assistant. Be concise and friendly.'
            }
        ]
        messages.extend(history)
        messages.append({'role': 'user', 'content': user_message})
        
        # Try Groq first (free tier)
        if groq_client:
            try:
                response = groq_client.chat.completions.create(
                    model='llama-3.3-70b-versatile',
                    messages=messages,
                    max_tokens=500,
                    temperature=0.7
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                print(f"Groq error, trying OpenAI: {e}")
        
        # Fallback to OpenAI
        if openai_client:
            response = openai_client.chat.completions.create(
                model='gpt-3.5-turbo',
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        
        return "No AI provider configured."
        
    except Exception as e:
        print(f"Error calling AI: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return f"Error: {str(e)}"


def store_message(session_id, message, role):
    """Store message in DynamoDB"""
    try:
        timestamp = datetime.utcnow().isoformat()
        table.put_item(
            Item={
                'sessionId': session_id,
                'timestamp': timestamp,
                'message': message,
                'role': role
            }
        )
    except ClientError as e:
        print(f"Error storing message: {e}")


def log_analytics(session_id, user_message, ai_response):
    """Log analytics data"""
    try:
        # Could be extended with CloudWatch custom metrics
        print(json.dumps({
            'event': 'chat_message',
            'session_id': session_id,
            'user_message_length': len(user_message),
            'ai_response_length': len(ai_response),
            'timestamp': datetime.utcnow().isoformat()
        }))
    except Exception as e:
        print(f"Error logging analytics: {e}")
