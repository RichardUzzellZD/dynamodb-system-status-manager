"""
DynamoDB System Status Manager - Lambda Function
Handles GET and POST requests from API Gateway to manage system operational status

GET: Fetch system status from DynamoDB
POST: Update system operational state in DynamoDB

Environment Variables:
- DYNAMODB_TABLE_NAME: GenericSystems (default)

DynamoDB Schema:
- systemKey (String, Primary Key): System identifier
- operationalState (Boolean): true = operational, false = offline

Author: Richard Uzzell
Email: richard.uzzell@zendesk.com
"""

import json
import boto3
import os
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'GenericSystems')
table = dynamodb.Table(table_name)

def decimal_to_string(obj):
    """Convert Decimal objects to string for JSON serialization"""
    if isinstance(obj, Decimal):
        return str(obj)
    return obj

def lambda_handler(event, context):
    """
    Main Lambda handler for system status management
    
    Handles two types of requests:
    1. GET - Fetch system status
       Query params: systemKey
       
    2. POST - Update system status
       Body: { "systemKey": "...", "operationalState": true/false }
    
    Returns:
        dict: Response with system status or error
    """
    
    try:
        print(f"Event received: {json.dumps(event)}")
        
        # Determine request method
        http_method = event.get('httpMethod', event.get('requestContext', {}).get('http', {}).get('method', 'POST'))
        
        if http_method == 'GET':
            return handle_get_request(event)
        elif http_method == 'POST':
            return handle_post_request(event)
        else:
            return {
                'statusCode': 405,
                'body': json.dumps({'error': 'Method not allowed'}),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
            
    except Exception as e:
        print(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

def handle_get_request(event):
    """
    Handle GET request to fetch system status
    
    Query params:
        systemKey: System identifier (paymentSystem, customerWebsite, etc.)
    
    Returns:
        200: Success with system data
        400: Missing systemKey
        404: System not found
    """
    try:
        # Extract systemKey from query parameters
        query_params = event.get('queryStringParameters', {}) or {}
        system_key = query_params.get('systemKey')
        
        print(f"GET request - Looking up systemKey: {system_key}")
        
        if not system_key:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing systemKey parameter'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Query DynamoDB
        response = table.get_item(
            Key={'systemKey': system_key}
        )
        
        # Check if item was found
        if 'Item' not in response:
            print(f"System not found: {system_key}")
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'System not found',
                    'systemKey': system_key,
                    'RecordFound': 'false'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        item = response['Item']
        print(f"System found: {system_key}, operationalState: {item.get('operationalState')}")
        
        # Prepare response
        result = {
            'RecordFound': 'true',
            'systemKey': item.get('systemKey'),
            'operationalState': str(item.get('operationalState', 'false'))
        }
        
        # Include all other attributes from DynamoDB
        for key, value in item.items():
            if key not in result:
                if isinstance(value, Decimal):
                    result[key] = str(value)
                else:
                    result[key] = value
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(f"Error in handle_get_request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to fetch system status',
                'message': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }

def handle_post_request(event):
    """
    Handle POST request to update system status
    
    Body:
        {
            "systemKey": "paymentSystem",
            "operationalState": true/false
        }
    
    Returns:
        200: Success with updated data
        400: Missing required fields
        500: Update failed
    """
    try:
        # Parse request body
        body = event.get('body', '{}')
        if isinstance(body, str):
            body = json.loads(body)
        
        system_key = body.get('systemKey')
        operational_state = body.get('operationalState')
        
        print(f"POST request - Updating systemKey: {system_key}, operationalState: {operational_state}")
        
        # Validate input
        if not system_key:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing systemKey in request body'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        if operational_state is None:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing operationalState in request body'
                }),
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                }
            }
        
        # Convert to boolean if string
        if isinstance(operational_state, str):
            operational_state = operational_state.lower() == 'true'
        
        # Update DynamoDB
        response = table.update_item(
            Key={'systemKey': system_key},
            UpdateExpression='SET operationalState = :state',
            ExpressionAttributeValues={
                ':state': operational_state
            },
            ReturnValues='ALL_NEW'
        )
        
        updated_item = response.get('Attributes', {})
        print(f"Update successful: {system_key} = {operational_state}")
        
        # Prepare response
        result = {
            'success': True,
            'systemKey': updated_item.get('systemKey'),
            'operationalState': updated_item.get('operationalState')
        }
        
        return {
            'statusCode': 200,
            'body': json.dumps(result),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
        
    except Exception as e:
        print(f"Error in handle_post_request: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to update system status',
                'message': str(e)
            }),
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            }
        }
