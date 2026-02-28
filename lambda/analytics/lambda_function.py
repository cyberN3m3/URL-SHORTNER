import json
import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
analytics_table = dynamodb.Table(os.environ['ANALYTICS_TABLE'])
urls_table = dynamodb.Table(os.environ['URLS_TABLE'])

def decimal_default(obj):
    """Convert Decimal to float for JSON"""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    """
    Get analytics for a short code
    GET /analytics/{short_code}
    """
    
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Content-Type': 'application/json'
    }
    
    try:
        # Get short code
        path_params = event.get('pathParameters', {})
        short_code = path_params.get('short_code', '') if path_params else ''
        
        if not short_code:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({'error': 'Short code required'})
            }
        
        # Get URL info
        url_response = urls_table.get_item(Key={'short_code': short_code})
        
        if 'Item' not in url_response:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({'error': 'Short code not found'})
            }
        
        url_item = url_response['Item']
        
        # Query analytics
        analytics_response = analytics_table.query(
            KeyConditionExpression=Key('short_code').eq(short_code),
            Limit=1000
        )
        
        clicks = analytics_response.get('Items', [])
        
        # Calculate statistics
        total_clicks = len(clicks)
        unique_ips = len(set(click.get('ip_address', 'unknown') for click in clicks))
        
        # Referrers breakdown
        referrers = {}
        for click in clicks:
            ref = click.get('referer', 'direct')
            if ref not in referrers:
                referrers[ref] = 0
            referrers[ref] += 1
        
        # Sort referrers by count
        top_referrers = dict(sorted(referrers.items(), key=lambda x: x[1], reverse=True)[:10])
        
        # Recent clicks (last 10)
        recent_clicks = sorted(
            clicks,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        )[:10]
        
        # Clean recent clicks for response
        recent_clicks_clean = []
        for click in recent_clicks:
            recent_clicks_clean.append({
                'timestamp': click.get('timestamp', ''),
                'referer': click.get('referer', 'direct'),
                'user_agent': click.get('user_agent', 'unknown')[:50] + '...' if len(click.get('user_agent', '')) > 50 else click.get('user_agent', 'unknown')
            })
        
        # Build response
        analytics = {
            'short_code': short_code,
            'original_url': url_item.get('original_url', ''),
            'created_at': url_item.get('created_at', ''),
            'total_clicks': total_clicks,
            'unique_visitors': unique_ips,
            'click_count': int(url_item.get('click_count', 0)),
            'referrers': top_referrers,
            'recent_clicks': recent_clicks_clean
        }
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(analytics, default=decimal_default)
        }
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({'error': f'Server error: {str(e)}'})
        }