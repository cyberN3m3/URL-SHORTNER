import json
import boto3
import os
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
urls_table = dynamodb.Table(os.environ['URLS_TABLE'])
analytics_table = dynamodb.Table(os.environ['ANALYTICS_TABLE'])

def lambda_handler(event, context):
    """
    Redirect to original URL and track analytics
    GET /{short_code}
    """
    
    try:
        # Get short code from path
        path_params = event.get('pathParameters', {})
        short_code = path_params.get('short_code', '') if path_params else ''
        
        if not short_code:
            return {
                'statusCode': 400,
                'headers': {'Content-Type': 'text/html'},
                'body': '<html><body><h1>400 - Bad Request</h1><p>Short code required</p></body></html>'
            }
        
        # Get URL from DynamoDB
        response = urls_table.get_item(Key={'short_code': short_code})
        
        if 'Item' not in response:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'text/html'},
                'body': '''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>404 - Not Found</title>
                        <style>
                            body {
                                font-family: system-ui;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                height: 100vh;
                                margin: 0;
                                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                color: white;
                            }
                            .container {
                                text-align: center;
                            }
                            h1 { font-size: 72px; margin: 0; }
                            p { font-size: 24px; opacity: 0.9; }
                            a { color: white; text-decoration: underline; }
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>404</h1>
                            <p>Short URL not found or expired</p>
                            <a href="/">← Go Home</a>
                        </div>
                    </body>
                    </html>
                '''
            }
        
        item = response['Item']
        original_url = item['original_url']
        
        # Update click count
        try:
            urls_table.update_item(
                Key={'short_code': short_code},
                UpdateExpression='SET click_count = if_not_exists(click_count, :zero) + :inc',
                ExpressionAttributeValues={':inc': 1, ':zero': 0}
            )
        except Exception as e:
            print(f"Error updating click count: {e}")
        
        # Track analytics
        try:
            request_context = event.get('requestContext', {})
            http_context = request_context.get('http', {})
            headers = event.get('headers', {})
            
            analytics_table.put_item(
                Item={
                    'short_code': short_code,
                    'timestamp': datetime.now().isoformat(),
                    'ip_address': http_context.get('sourceIp', 'unknown'),
                    'user_agent': headers.get('user-agent', 'unknown'),
                    'referer': headers.get('referer', 'direct'),
                    'expires_at': int((datetime.now().timestamp()) + (365 * 24 * 60 * 60))
                }
            )
        except Exception as e:
            print(f"Error tracking analytics: {e}")
        
        # Redirect
        return {
            'statusCode': 301,
            'headers': {
                'Location': original_url,
                'Content-Type': 'text/html'
            },
            'body': f'<html><body>Redirecting to <a href="{original_url}">{original_url}</a>...</body></html>'
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'text/html'},
            'body': '<html><body><h1>500 - Server Error</h1><p>Something went wrong</p></body></html>'
        }