"""
Local SQLite database implementation for development
Falls back to DynamoDB in production
"""
import os
import json
import sqlite3
from datetime import datetime


class LocalDB:
    """SQLite-based local database for development"""
    
    def __init__(self, db_name='chatbot_local.db'):
        self.db_name = db_name
        self._init_db()
    
    def _init_db(self):
        """Initialize database tables"""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    sessionId TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    message TEXT NOT NULL,
                    role TEXT NOT NULL,
                    PRIMARY KEY (sessionId, timestamp)
                )
            ''')
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_session 
                ON conversations(sessionId)
            ''')
    
    def query(self, KeyConditionExpression=None, ExpressionAttributeValues=None, 
              ScanIndexForward=True, Limit=None, Select=None, 
              ProjectionExpression=None, ExclusiveStartKey=None):
        """Query the database (simplified implementation)"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Get session ID from expression values
            session_id = None
            if ExpressionAttributeValues:
                session_id = list(ExpressionAttributeValues.values())[0]
            
            if session_id and 'sessionId' in (KeyConditionExpression or ''):
                # Query specific session
                query = "SELECT * FROM conversations WHERE sessionId = ? ORDER BY timestamp"
                if not ScanIndexForward:
                    query += " DESC"
                if Limit:
                    query += f" LIMIT {Limit}"
                cursor.execute(query, (session_id,))
            else:
                # Scan all
                cols = ProjectionExpression.split(', ') if ProjectionExpression else '*'
                query = f"SELECT {', '.join(cols) if isinstance(cols, list) else '*'} FROM conversations"
                cursor.execute(query)
            
            rows = cursor.fetchall()
            
            # Convert to DynamoDB-like format
            items = []
            for row in rows:
                if len(row) == 4:
                    items.append({
                        'sessionId': row[0],
                        'timestamp': row[1],
                        'message': row[2],
                        'role': row[3]
                    })
                elif len(row) == 1:
                    items.append({'sessionId': row[0]})
            
            return {'Items': items, 'Count': len(items)}
    
    def put_item(self, Item):
        """Insert an item"""
        with sqlite3.connect(self.db_name) as conn:
            conn.execute(
                'INSERT OR REPLACE INTO conversations (sessionId, timestamp, message, role) VALUES (?, ?, ?, ?)',
                (Item['sessionId'], Item['timestamp'], Item['message'], Item['role'])
            )
    
    def scan(self, ProjectionExpression=None, Select=None, ExclusiveStartKey=None):
        """Scan the table"""
        return self.query(ProjectionExpression=ProjectionExpression, Select=Select, 
                         ExclusiveStartKey=ExclusiveStartKey)
    
    def batch_writer(self):
        """Return a batch writer"""
        return BatchWriter(self)


class BatchWriter:
    """Handle batch operations"""
    
    def __init__(self, db):
        self.db = db
        self.operations = []
    
    def delete_item(self, Key):
        """Queue a delete operation"""
        self.operations.append(('delete', Key))
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Execute all queued operations"""
        with sqlite3.connect(self.db.db_name) as conn:
            for op_type, key in self.operations:
                if op_type == 'delete':
                    conn.execute(
                        'DELETE FROM conversations WHERE sessionId = ? AND timestamp = ?',
                        (key['sessionId'], key['timestamp'])
                    )
        return False


class MockTable:
    """Mock table that wraps LocalDB"""
    
    def __init__(self, table_name):
        self.db = LocalDB()
        self.table_name = table_name
    
    def query(self, **kwargs):
        return self.db.query(**kwargs)
    
    def put_item(self, **kwargs):
        return self.db.put_item(**kwargs)
    
    def scan(self, **kwargs):
        return self.db.scan(**kwargs)
    
    def batch_writer(self):
        return self.db.batch_writer()


def get_dynamodb_resource():
    """Get database resource - SQLite for local, DynamoDB for production"""
    # Use SQLite for local development
    if not os.environ.get('AWS_EXECUTION_ENV'):
        return MockDBResource()
    
    # Use DynamoDB for production
    import boto3
    return boto3.resource(
        'dynamodb',
        region_name=os.environ.get('REGION', 'us-east-1')
    )


class MockDBResource:
    """Mock DynamoDB resource for local development"""
    
    def Table(self, table_name):
        return MockTable(table_name)
