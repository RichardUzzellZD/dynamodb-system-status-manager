import json
import boto3
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='eu-west-2')
table = dynamodb.Table('GenericSystems')

def lambda_handler(event, context):
    """
    Handle GET and POST requests for system operational status
    
    GET: Fetch operational status for a specific system
    POST: Update operational status for a specific system
    """
    
    print(f"Received event: {json.dumps(event)}")
    
    # Determine HTTP method
    http_method = event.get('httpMethod') or event.get('requestContext', {}).get('http', {}).get('method')
    
    if http_method == 'GET':
        return handle_get_request(event)
    elif http_method == 'POST':
        return handle_post_request(event)
    else:
        return {
            'statusCode': 405,
            'headers': cors_headers(),
            'body': json.dumps({'error': 'Method not allowed'})
        }

def handle_get_request(event):
    """
    GET request: Fetch system status from DynamoDB
    Query parameter: systemKey
    """
    try:
        # Extract systemKey from query parameters
        query_params = event.get('queryStringParameters', {})
        system_key = query_params.get('systemKey') if query_params else None
        
        if not system_key:
            return error_response(400, 'Missing systemKey parameter')
        
        print(f"Fetching status for system: {system_key}")
        
        # Query DynamoDB
        response = table.get_item(Key={'systemKey': system_key})
        
        if 'Item' not in response:
            return error_response(404, f'System not found: {system_key}')
        
        item = response['Item']
        operational_state = item.get('operationalState')
        
        # Convert Boolean to string for compatibility
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'operationalState': str(operational_state)
            })
        }
        
    except Exception as e:
        print(f"Error in GET request: {str(e)}")
        return error_response(500, f'Internal error: {str(e)}')

def handle_post_request(event):
    """
    POST request: Update system status in DynamoDB
    Body: {"systemKey": "paymentSystem", "operationalState": true}
    """
    try:
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        system_key = body.get('systemKey')
        operational_state = body.get('operationalState')
        
        if not system_key:
            return error_response(400, 'Missing systemKey in request body')
        
        if operational_state is None:
            return error_response(400, 'Missing operationalState in request body')
        
        # Validate operationalState is boolean
        if not isinstance(operational_state, bool):
            return error_response(400, 'operationalState must be a boolean (true/false)')
        
        print(f"Updating {system_key} to operationalState={operational_state}")
        
        # Update DynamoDB
        table.update_item(
            Key={'systemKey': system_key},
            UpdateExpression='SET operationalState = :state',
            ExpressionAttributeValues={':state': operational_state},
            ReturnValues='UPDATED_NEW'
        )
        
        return {
            'statusCode': 200,
            'headers': cors_headers(),
            'body': json.dumps({
                'message': 'Operational state updated successfully',
                'systemKey': system_key,
                'operationalState': operational_state
            })
        }
        
    except json.JSONDecodeError:
        return error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        print(f"Error in POST request: {str(e)}")
        return error_response(500, f'Internal error: {str(e)}')

def cors_headers():
    """Return CORS headers for API Gateway"""
    return {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, x-api-key'
    }

def error_response(status_code, message):
    """Return formatted error response"""
    return {
        'statusCode': status_code,
        'headers': cors_headers(),
        'body': json.dumps({'error': message})
    }
