import json
import os
import boto3
from datetime import datetime, timedelta
from src.utils.response import success_response, error_response
from src.utils.dynamodb import get_dynamodb_resource

dynamodb = get_dynamodb_resource()
table_name = os.environ.get('DYNAMODB_TABLE', 'chatbot-conversations-dev')
table = dynamodb.Table(table_name) if hasattr(dynamodb, 'Table') else dynamodb

# Only initialize CloudWatch if we have AWS credentials
try:
    if os.environ.get('AWS_ACCESS_KEY_ID') or os.environ.get('AWS_DEFAULT_REGION'):
        cloudwatch = boto3.client('cloudwatch', region_name=os.environ.get('REGION', 'us-east-1'))
    else:
        cloudwatch = None
except:
    cloudwatch = None


def handler(event, context):
    """
    Get analytics data about chatbot usage
    """
    try:
        # Get total conversations (scan unique session IDs)
        scan = table.scan(Select='COUNT')
        total_messages = scan['Count']
        
        # Get unique sessions
        unique_sessions = get_unique_sessions()
        
        # Get CloudWatch metrics if available
        cloudwatch_metrics = get_cloudwatch_metrics()
        
        return success_response(
            data={
                'total_messages': total_messages,
                'unique_sessions': unique_sessions,
                'cloudwatch_metrics': cloudwatch_metrics,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        print(f"Error getting analytics: {e}")
        return error_response(
            message=f"Error getting analytics: {str(e)}",
            status_code=500
        )


def get_unique_sessions():
    """Get count of unique conversation sessions"""
    try:
        response = table.scan(
            ProjectionExpression='sessionId'
        )
        
        sessions = set()
        for item in response.get('Items', []):
            sessions.add(item['sessionId'])
        
        # Handle pagination
        while 'LastEvaluatedKey' in response:
            response = table.scan(
                ProjectionExpression='sessionId',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            for item in response.get('Items', []):
                sessions.add(item['sessionId'])
        
        return len(sessions)
    except Exception as e:
        print(f"Error getting unique sessions: {e}")
        return 0


def get_cloudwatch_metrics():
    """Get metrics from CloudWatch"""
    if not cloudwatch:
        return {'note': 'CloudWatch not configured for local development'}
    
    try:
        # Example: Get Lambda invocation metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName='Invocations',
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': os.environ.get('AWS_LAMBDA_FUNCTION_NAME', '')
                }
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=['Sum']
        )
        
        return {
            'invocations_24h': sum(dp['Sum'] for dp in response.get('Datapoints', []))
        }
    except Exception as e:
        print(f"Error getting CloudWatch metrics: {e}")
        return {}
