import json
import os
import boto3
from botocore.exceptions import ClientError
from src.utils.response import success_response, error_response
from src.utils.dynamodb import get_dynamodb_resource

dynamodb = get_dynamodb_resource()
table_name = os.environ.get('DYNAMODB_TABLE', 'chatbot-conversations-dev')
table = dynamodb.Table(table_name) if hasattr(dynamodb, 'Table') else dynamodb


def handler(event, context):
    """
    Get conversation history for a session
    """
    try:
        session_id = event.get('pathParameters', {}).get('sessionId')
        
        if not session_id:
            return error_response(
                message="Session ID is required",
                status_code=400
            )
        
        # Query all messages for this session
        response = table.query(
            KeyConditionExpression='sessionId = :sid',
            ExpressionAttributeValues={':sid': session_id},
            ScanIndexForward=True
        )
        
        messages = []
        for item in response.get('Items', []):
            messages.append({
                'timestamp': item['timestamp'],
                'message': item['message'],
                'role': item['role']
            })
        
        return success_response(
            data={
                'session_id': session_id,
                'messages': messages,
                'count': len(messages)
            }
        )
        
    except ClientError as e:
        print(f"Error retrieving conversations: {e}")
        return error_response(
            message=f"Error retrieving conversations: {str(e)}",
            status_code=500
        )
