import json
import boto3
import os
import string
import random
from datetime import datetime, timedelta
from urllib.parse import urlparse

dynamodb = boto3.resource('dynamodb')
urls_table = dynamodb.Table(os.environ['URLS_TABLE'])

def generate_short_code(length=6):
    """Generate random alphanumeric short code"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def is_valid_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme in ['http', 'https'], result.netloc])
    except:
        return False

def lambda_handler(event, context):
    """
    Create shortened URL
    POST /shorten
    Body: {"url": "https://example.com", "custom_code": "optional"}
    """
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'POST, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    try:
        # Parse body
        if isinstance(event.get('body'), str):
            body = json.loads(event['body'])
        else:
            body = event.get('body', {})
        
        original_url = body.get('url', '').strip()
        custom_code = body.get('custom_code', '').strip()
        
        # Validate URL
        if not original_url:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'URL is required'})
            }
        
        if not is_valid_url(original_url):
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Invalid URL format. Must start with http:// or https://'})
            }
        
        # Generate or validate short code
        if custom_code:
            if not custom_code.isalnum() or len(custom_code) < 3 or len(custom_code) > 20:
                return {
                    'statusCode': 400,
                    'headers': headers,
                    'body': json.dumps({'error': 'Custom code must be 3-20 alphanumeric characters'})
                }
            short_code = custom_code
        else:
            short_code = generate_short_code()
            
            # Retry if collision (unlikely but possible)
            for _ in range(5):
                try:
                    response = urls_table.get_item(Key={'short_code': short_code})
                    if 'Item' not in response:
                        break
                    short_code = generate_short_code()
                except:
                    break
        
        # Calculate expiry (90 days)
        expires_at = int((datetime.now() + timedelta(days=90)).timestamp())
        
        # Save to DynamoDB
        try:
            urls_table.put_item(
                Item={
                    'short_code': short_code,
                    'original_url': original_url,
                    'created_at': datetime.now().isoformat(),
                    'expires_at': expires_at,
                    'click_count': 0
                },
                ConditionExpression='attribute_not_exists(short_code)'
            )
        except dynamodb.meta.client.exceptions.ConditionalCheckFailedException:
            return {
                'statusCode': 409,
                'headers': headers,
                'body': json.dumps({'error': 'Short code already exists. Try another custom code.'})
            }
        
        # Return success
        return {
            'statusCode': 201,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'short_code': short_code,
                'original_url': original_url,
                'created_at': datetime.now().isoformat(),
                'expires_in_days': 90
            })
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }
        