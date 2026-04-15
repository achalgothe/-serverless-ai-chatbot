import os
from src.utils.local_db import get_dynamodb_resource as get_local_db


def get_dynamodb_resource():
    """Get database resource - SQLite for local, DynamoDB for production"""
    # For local development without AWS, use SQLite
    if not os.environ.get('AWS_EXECUTION_ENV'):
        local_db = get_local_db()
        return local_db
    
    # Use DynamoDB for production
    import boto3
    return boto3.resource(
        'dynamodb',
        region_name=os.environ.get('REGION', 'us-east-1')
    )
