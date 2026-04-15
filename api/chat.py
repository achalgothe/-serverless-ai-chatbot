import json
import os
from groq import Groq


def handler(request):
    """Vercel serverless function for chat"""
    if request.method == 'POST':
        try:
            body = json.loads(request.body.decode('utf-8'))
            message = body.get('message', '').strip()
            session_id = body.get('session_id', f'session_{int(request.headers.get("x-timestamp", 0))}')

            if not message:
                return {
                    'statusCode': 400,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*'
                    },
                    'body': json.dumps({
                        'success': False,
                        'error': 'Message is required'
                    })
                }

            # Initialize Groq client
            client = Groq(api_key=os.environ.get('GROQ_API_KEY'))

            # Get AI response
            response = client.chat.completions.create(
                model='llama-3.3-70b-versatile',
                messages=[
                    {'role': 'system', 'content': 'You are a helpful AI assistant. Be concise and friendly.'},
                    {'role': 'user', 'content': message}
                ],
                max_tokens=500,
                temperature=0.7
            )

            ai_response = response.choices[0].message.content.strip()

            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'data': {
                        'session_id': session_id,
                        'response': ai_response,
                        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
                    }
                })
            }

        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': False,
                    'error': str(e)
                })
            }
    else:
        return {
            'statusCode': 405,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': 'Method not allowed'})
        }
