import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
urls_table = dynamodb.Table(os.environ['URLS_TABLE'])
analytics_table = dynamodb.Table(os.environ['ANALYTICS_TABLE'])

def lambda_handler(event, context):
    """
    Redirect to original URL and track analytics
    GET /{short_code}
    """
    
    print(f"Event received: {json.dumps(event)}")
    
    try:
        # Get short code from path parameters
        path_parameters = event.get('pathParameters', {})
        short_code = path_parameters.get('short_code', '') if path_parameters else ''
        
        # Also check rawPath as fallback
        if not short_code:
            raw_path = event.get('rawPath', '')
            if raw_path and raw_path != '/':
                short_code = raw_path.strip('/')
        
        print(f"Short code extracted: {short_code}")
        
        if not short_code:
            return {
                'statusCode': 400,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': '<html><body><h1>400 - Bad Request</h1><p>Short code required</p></body></html>'
            }
        
        # Get URL from DynamoDB
        print(f"Looking up short code in DynamoDB: {short_code}")
        response = urls_table.get_item(Key={'short_code': short_code})
        
        if 'Item' not in response:
            print(f"Short code not found: {short_code}")
            return {
                'statusCode': 404,
                'headers': {
                    'Content-Type': 'text/html',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': '''
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <title>404 - Not Found</title>
                        <style>
                            body {
                                font-family: 'Inter', system-ui, sans-serif;
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
                                padding: 40px;
                                background: rgba(255, 255, 255, 0.1);
                                border-radius: 20px;
                                backdrop-filter: blur(10px);
                            }
                            h1 { font-size: 72px; margin: 0; }
                            p { font-size: 20px; opacity: 0.9; margin-top: 16px; }
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
        
        print(f"Found original URL: {original_url}")
        
        # Update click count
        try:
            urls_table.update_item(
                Key={'short_code': short_code},
                UpdateExpression='SET click_count = if_not_exists(click_count, :zero) + :inc',
                ExpressionAttributeValues={':inc': 1, ':zero': 0}
            )
            print("Click count updated")
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
                    'expires_at': int(datetime.now().timestamp() + (365 * 24 * 60 * 60))
                }
            )
            print("Analytics tracked")
        except Exception as e:
            print(f"Error tracking analytics: {e}")
        
        # IMPORTANT: Return 301 redirect with Location header
        print(f"Redirecting to: {original_url}")
        return {
            'statusCode': 301,
            'headers': {
                'Location': original_url,
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Content-Type': 'text/html'
            },
            'body': ''
        }
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'text/html',
                'Access-Control-Allow-Origin': '*'
            },
            'body': f'<html><body><h1>500 - Server Error</h1><p>Error: {str(e)}</p></body></html>'
        }