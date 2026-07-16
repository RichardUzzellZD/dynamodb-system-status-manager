# AWS Setup Guide for DynamoDB System Status Manager

This guide provides complete step-by-step instructions for setting up the AWS infrastructure required by the Zendesk app.

## Overview

You'll create:
1. **DynamoDB Table** - Stores system operational states
2. **IAM Role** - Grants Lambda permissions to access DynamoDB
3. **Lambda Function** - Handles GET and POST requests
4. **API Gateway** - Provides HTTPS endpoints with API key authentication
5. **API Key** - Secures access to the API

**Estimated Setup Time**: 30-45 minutes

## Prerequisites

- AWS Account with administrator access
- AWS Console access or AWS CLI configured
- Basic familiarity with AWS services

---

## Step 1: Create DynamoDB Table

### Option A: AWS Console

1. **Navigate to DynamoDB**
   - Open AWS Console
   - Search for "DynamoDB" and click
   - Click "Create table"

2. **Configure Table**
   - **Table name**: `GenericSystems`
   - **Partition key**: `systemKey` (String)
   - **Sort key**: Leave empty
   - **Table settings**: Default settings
   - Click "Create table"

3. **Wait for Creation**
   - Status should change to "Active" (takes ~1 minute)

4. **Add Sample Data**
   - Click on the table name
   - Go to "Explore table items"
   - Click "Create item"
   - Add:
     ```json
     {
       "systemKey": "paymentSystem",
       "operationalState": true
     }
     ```
   - Click "Create item" again and add:
     ```json
     {
       "systemKey": "customerWebsite",
       "operationalState": true
     }
     ```

### Option B: AWS CLI

```bash
# Create table
aws dynamodb create-table \
    --table-name GenericSystems \
    --attribute-definitions AttributeName=systemKey,AttributeType=S \
    --key-schema AttributeName=systemKey,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --region eu-west-2

# Wait for table to become active
aws dynamodb wait table-exists --table-name GenericSystems --region eu-west-2

# Add sample items
aws dynamodb put-item \
    --table-name GenericSystems \
    --item '{"systemKey": {"S": "paymentSystem"}, "operationalState": {"BOOL": true}}' \
    --region eu-west-2

aws dynamodb put-item \
    --table-name GenericSystems \
    --item '{"systemKey": {"S": "customerWebsite"}, "operationalState": {"BOOL": true}}' \
    --region eu-west-2
```

**Verify**:
```bash
aws dynamodb scan --table-name GenericSystems --region eu-west-2
```

---

## Step 2: Create IAM Role for Lambda

### Option A: AWS Console

1. **Navigate to IAM**
   - Open AWS Console → IAM
   - Click "Roles" → "Create role"

2. **Select Trusted Entity**
   - **Trusted entity type**: AWS service
   - **Use case**: Lambda
   - Click "Next"

3. **Attach Permissions**
   - Search and select: `AWSLambdaBasicExecutionRole`
   - Click "Next"

4. **Name the Role**
   - **Role name**: `LambdaDynamoDBSystemStatusRole`
   - **Description**: "Allows Lambda to read/write GenericSystems DynamoDB table"
   - Click "Create role"

5. **Add DynamoDB Permissions**
   - Find your newly created role
   - Click on the role name
   - Click "Add permissions" → "Create inline policy"
   - Click "JSON" tab
   - Paste:
     ```json
     {
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Action": [
             "dynamodb:GetItem",
             "dynamodb:UpdateItem"
           ],
           "Resource": "arn:aws:dynamodb:eu-west-2:228449306526:table/GenericSystems"
         }
       ]
     }
     ```
   - **Replace** `228449306526` with your AWS account ID
   - Click "Review policy"
   - **Policy name**: `DynamoDBGenericSystemsAccess`
   - Click "Create policy"

### Option B: AWS CLI

```bash
# Create trust policy file
cat > lambda-trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF

# Create role
aws iam create-role \
    --role-name LambdaDynamoDBSystemStatusRole \
    --assume-role-policy-document file://lambda-trust-policy.json

# Attach basic execution policy
aws iam attach-role-policy \
    --role-name LambdaDynamoDBSystemStatusRole \
    --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create DynamoDB access policy
cat > dynamodb-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-2:YOUR_ACCOUNT_ID:table/GenericSystems"
    }
  ]
}
EOF

# IMPORTANT: Replace YOUR_ACCOUNT_ID with your actual AWS account ID

# Attach DynamoDB policy
aws iam put-role-policy \
    --role-name LambdaDynamoDBSystemStatusRole \
    --policy-name DynamoDBGenericSystemsAccess \
    --policy-document file://dynamodb-policy.json
```

---

## Step 3: Create Lambda Function

### Option A: AWS Console

1. **Navigate to Lambda**
   - Open AWS Console → Lambda
   - Click "Create function"

2. **Configure Function**
   - **Function name**: `updateSystemStatus`
   - **Runtime**: Python 3.12 (or latest Python 3.x)
   - **Architecture**: x86_64
   - **Permissions**: Use an existing role
   - **Existing role**: `LambdaDynamoDBSystemStatusRole`
   - Click "Create function"

3. **Add Function Code**
   - Scroll down to "Code source"
   - Replace the default code with the contents of `lambda/lambda_function.py` (see below)
   - Click "Deploy"

4. **Configure Environment**
   - No environment variables needed
   - **Timeout**: 30 seconds (Configuration → General configuration → Edit)
   - **Memory**: 128 MB (default is fine)

### Lambda Function Code

Create file: `lambda/lambda_function.py`

```python
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
```

### Option B: AWS CLI

```bash
# Create deployment package
mkdir lambda-package
cd lambda-package
# Copy the lambda_function.py code above into lambda_function.py
zip -r function.zip lambda_function.py

# Get IAM role ARN
ROLE_ARN=$(aws iam get-role --role-name LambdaDynamoDBSystemStatusRole --query 'Role.Arn' --output text)

# Create Lambda function
aws lambda create-function \
    --function-name updateSystemStatus \
    --runtime python3.12 \
    --role $ROLE_ARN \
    --handler lambda_function.lambda_handler \
    --zip-file fileb://function.zip \
    --timeout 30 \
    --region eu-west-2
```

### Test the Lambda

**Test GET request**:
```json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "systemKey": "paymentSystem"
  }
}
```

**Expected response**:
```json
{
  "statusCode": 200,
  "body": "{\"operationalState\": \"True\"}"
}
```

---

## Step 4: Create API Gateway

This is the most complex step - follow carefully!

### Option A: AWS Console

#### 4.1: Create REST API

1. **Navigate to API Gateway**
   - Open AWS Console → API Gateway
   - Click "Create API"

2. **Choose REST API**
   - Find "REST API" (NOT "REST API Private")
   - Click "Build"

3. **Configure API**
   - **Protocol**: REST
   - **Create new API**: New API
   - **API name**: `SystemStatusAPI`
   - **Description**: "API for DynamoDB system status management"
   - **Endpoint Type**: Regional
   - Click "Create API"

#### 4.2: Create Resource

1. **Create Resource Path**
   - Click "Actions" → "Create Resource"
   - **Resource Name**: `update-operational-state`
   - **Resource Path**: `/update-operational-state`
   - **Enable API Gateway CORS**: ✅ Check this box
   - Click "Create Resource"

#### 4.3: Create GET Method

1. **Add GET Method**
   - With `/update-operational-state` selected
   - Click "Actions" → "Create Method"
   - Select "GET" from dropdown
   - Click the checkmark ✓

2. **Configure GET Integration**
   - **Integration type**: Lambda Function
   - **Use Lambda Proxy integration**: ✅ Check this
   - **Lambda Region**: eu-west-2
   - **Lambda Function**: `updateSystemStatus`
   - Click "Save"
   - Click "OK" on the permission prompt

3. **Enable CORS for GET**
   - Click on the GET method
   - Click "Method Response"
   - Expand "200" response
   - Add response headers:
     - `Access-Control-Allow-Origin`
     - Click "Add Header" for each

#### 4.4: Create POST Method

1. **Add POST Method**
   - With `/update-operational-state` selected
   - Click "Actions" → "Create Method"
   - Select "POST" from dropdown
   - Click the checkmark ✓

2. **Configure POST Integration**
   - **Integration type**: Lambda Function
   - **Use Lambda Proxy integration**: ✅ Check this
   - **Lambda Region**: eu-west-2
   - **Lambda Function**: `updateSystemStatus`
   - Click "Save"
   - Click "OK" on the permission prompt

#### 4.5: Deploy API

1. **Create Deployment**
   - Click "Actions" → "Deploy API"
   - **Deployment stage**: [New Stage]
   - **Stage name**: `prod`
   - **Stage description**: "Production"
   - Click "Deploy"

2. **Note the Invoke URL**
   - You'll see: `https://[api-id].execute-api.eu-west-2.amazonaws.com/prod`
   - **Save this URL** - you'll need it for the Zendesk app

#### 4.6: Configure API Key Requirement

1. **Require API Key for GET**
   - Go back to "Resources"
   - Click on "GET" method under `/update-operational-state`
   - Click "Method Request"
   - Expand "API Key Required"
   - Change to: `true`
   - Click the checkmark ✓

2. **Require API Key for POST**
   - Click on "POST" method
   - Click "Method Request"
   - Expand "API Key Required"
   - Change to: `true`
   - Click the checkmark ✓

3. **Re-deploy API**
   - Click "Actions" → "Deploy API"
   - **Deployment stage**: prod
   - Click "Deploy"

### Option B: AWS CLI

```bash
# Create REST API
API_ID=$(aws apigateway create-rest-api \
    --name SystemStatusAPI \
    --description "API for DynamoDB system status management" \
    --region eu-west-2 \
    --query 'id' \
    --output text)

echo "API ID: $API_ID"

# Get root resource ID
ROOT_ID=$(aws apigateway get-resources \
    --rest-api-id $API_ID \
    --region eu-west-2 \
    --query 'items[0].id' \
    --output text)

# Create resource
RESOURCE_ID=$(aws apigateway create-resource \
    --rest-api-id $API_ID \
    --parent-id $ROOT_ID \
    --path-part update-operational-state \
    --region eu-west-2 \
    --query 'id' \
    --output text)

# Create GET method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --authorization-type NONE \
    --api-key-required \
    --region eu-west-2

# Create POST method
aws apigateway put-method \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --authorization-type NONE \
    --api-key-required \
    --region eu-west-2

# Get Lambda ARN
LAMBDA_ARN=$(aws lambda get-function \
    --function-name updateSystemStatus \
    --region eu-west-2 \
    --query 'Configuration.FunctionArn' \
    --output text)

# Set up Lambda integration for GET
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method GET \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region eu-west-2

# Set up Lambda integration for POST
aws apigateway put-integration \
    --rest-api-id $API_ID \
    --resource-id $RESOURCE_ID \
    --http-method POST \
    --type AWS_PROXY \
    --integration-http-method POST \
    --uri "arn:aws:apigateway:eu-west-2:lambda:path/2015-03-31/functions/${LAMBDA_ARN}/invocations" \
    --region eu-west-2

# Grant API Gateway permission to invoke Lambda
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query 'Account' --output text)

aws lambda add-permission \
    --function-name updateSystemStatus \
    --statement-id apigateway-get \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:eu-west-2:${AWS_ACCOUNT_ID}:${API_ID}/*/GET/update-operational-state" \
    --region eu-west-2

aws lambda add-permission \
    --function-name updateSystemStatus \
    --statement-id apigateway-post \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:eu-west-2:${AWS_ACCOUNT_ID}:${API_ID}/*/POST/update-operational-state" \
    --region eu-west-2

# Deploy API
aws apigateway create-deployment \
    --rest-api-id $API_ID \
    --stage-name prod \
    --region eu-west-2

echo "API Endpoint: https://${API_ID}.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state"
```

---

## Step 5: Create API Key and Usage Plan

### Option A: AWS Console

#### 5.1: Create API Key

1. **Navigate to API Keys**
   - In API Gateway console
   - Click "API Keys" in the left menu
   - Click "Actions" → "Create API key"

2. **Configure Key**
   - **Name**: `ZendeskAppKey`
   - **Description**: "API key for Zendesk System Status app"
   - **API key**: Auto generate
   - Click "Save"

3. **Copy the API Key**
   - Click "Show" to reveal the key
   - **Copy this value** - you'll need it for Zendesk
   - Store it securely (you can't retrieve it later)

#### 5.2: Create Usage Plan

1. **Navigate to Usage Plans**
   - Click "Usage Plans" in the left menu
   - Click "Create"

2. **Configure Plan**
   - **Name**: `SystemStatusPlan`
   - **Description**: "Usage plan for system status API"
   - **Throttling**: 
     - Rate: 10 requests/second
     - Burst: 20 requests
   - **Quota**: 
     - 10000 requests per day
   - Click "Next"

3. **Add API Stage**
   - Click "Add API Stage"
   - **API**: SystemStatusAPI
   - **Stage**: prod
   - Click the checkmark ✓
   - Click "Next"

4. **Add API Key**
   - Click "Add API Key to Usage Plan"
   - Select `ZendeskAppKey`
   - Click the checkmark ✓
   - Click "Done"

### Option B: AWS CLI

```bash
# Create API key
API_KEY=$(aws apigateway create-api-key \
    --name ZendeskAppKey \
    --description "API key for Zendesk System Status app" \
    --enabled \
    --region eu-west-2 \
    --query 'id' \
    --output text)

# Get the actual key value
API_KEY_VALUE=$(aws apigateway get-api-key \
    --api-key $API_KEY \
    --include-value \
    --region eu-west-2 \
    --query 'value' \
    --output text)

echo "API Key ID: $API_KEY"
echo "API Key Value: $API_KEY_VALUE"
echo "SAVE THIS KEY VALUE - you'll need it for Zendesk!"

# Create usage plan
USAGE_PLAN_ID=$(aws apigateway create-usage-plan \
    --name SystemStatusPlan \
    --description "Usage plan for system status API" \
    --throttle rateLimit=10,burstLimit=20 \
    --quota limit=10000,period=DAY \
    --region eu-west-2 \
    --query 'id' \
    --output text)

# Associate API stage with usage plan
aws apigateway create-usage-plan-key \
    --usage-plan-id $USAGE_PLAN_ID \
    --key-id $API_KEY \
    --key-type API_KEY \
    --region eu-west-2

# Link usage plan to API stage
aws apigateway update-usage-plan \
    --usage-plan-id $USAGE_PLAN_ID \
    --patch-operations \
        op=add,path=/apiStages,value=${API_ID}:prod \
    --region eu-west-2
```

---

## Step 6: Test the Complete Integration

### Test with curl

**Replace** these values:
- `YOUR_API_ID`: From Step 4
- `YOUR_API_KEY`: From Step 5

#### Test GET Request

```bash
curl -X GET \
  "https://YOUR_API_ID.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state?systemKey=paymentSystem" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json"
```

**Expected response**:
```json
{"operationalState": "True"}
```

#### Test POST Request

```bash
curl -X POST \
  "https://YOUR_API_ID.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state" \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "systemKey": "paymentSystem",
    "operationalState": false
  }'
```

**Expected response**:
```json
{
  "message": "Operational state updated successfully",
  "systemKey": "paymentSystem",
  "operationalState": false
}
```

#### Verify in DynamoDB

```bash
aws dynamodb get-item \
    --table-name GenericSystems \
    --key '{"systemKey": {"S": "paymentSystem"}}' \
    --region eu-west-2
```

Should show:
```json
{
  "Item": {
    "systemKey": {"S": "paymentSystem"},
    "operationalState": {"BOOL": false}
  }
}
```

---

## Step 7: Update Zendesk App Configuration

### Update manifest.json

1. Open `manifest.json` in your app files

2. Update the `domainWhitelist` with your API Gateway domain:
   ```json
   "domainWhitelist": [
     "YOUR_API_ID.execute-api.eu-west-2.amazonaws.com"
   ]
   ```

3. Ensure the `parameters` section includes:
   ```json
   "parameters": [
     {
       "name": "webhookSecret",
       "type": "text",
       "secure": true,
       "required": true
     }
   ]
   ```

### Update constants.js (in app source)

If you have access to the app source code:

```javascript
const WEBHOOK_BASE_URL = "https://YOUR_API_ID.execute-api.eu-west-2.amazonaws.com/prod";
const UPDATE_ENDPOINT = `${WEBHOOK_BASE_URL}/update-operational-state`;
```

**Note**: The current app has this hardcoded to `89td2u0ux0`. You'll need to rebuild with your new API ID.

---

## Complete Setup Checklist

- [ ] DynamoDB table `GenericSystems` created
- [ ] Sample data added (paymentSystem, customerWebsite)
- [ ] IAM role `LambdaDynamoDBSystemStatusRole` created
- [ ] IAM role has DynamoDB permissions
- [ ] Lambda function `updateSystemStatus` created
- [ ] Lambda function code deployed
- [ ] Lambda function uses correct IAM role
- [ ] API Gateway `SystemStatusAPI` created
- [ ] Resource `/update-operational-state` created
- [ ] GET method configured with Lambda integration
- [ ] POST method configured with Lambda integration
- [ ] API key requirement enabled for both methods
- [ ] API deployed to `prod` stage
- [ ] API key created and saved
- [ ] Usage plan created and linked to API stage
- [ ] API key added to usage plan
- [ ] Tested GET request with curl
- [ ] Tested POST request with curl
- [ ] Verified DynamoDB updates
- [ ] Updated Zendesk app manifest with correct API domain
- [ ] API key configured in Zendesk app settings

---

## Troubleshooting

### "Forbidden" Error

**Cause**: Missing or invalid API key

**Fix**:
1. Verify API key is included in request: `x-api-key` header
2. Check API key is active in AWS Console
3. Ensure usage plan is linked to the `prod` stage
4. Verify API key is added to the usage plan

### "Internal Server Error" (500)

**Cause**: Lambda execution error

**Fix**:
1. Check CloudWatch Logs:
   ```
   AWS Console → CloudWatch → Log Groups → /aws/lambda/updateSystemStatus
   ```
2. Common issues:
   - IAM role missing DynamoDB permissions
   - DynamoDB table name mismatch
   - Invalid JSON in request body

### "Missing Authentication Token"

**Cause**: Wrong API endpoint or stage

**Fix**:
1. Verify you're using: `/prod/update-operational-state`
2. Ensure API is deployed to `prod` stage
3. Check API ID in the URL matches your API

### CORS Errors

**Cause**: Missing CORS headers

**Fix**:
1. Verify Lambda returns CORS headers in response
2. Check `cors_headers()` function in Lambda code
3. Ensure API Gateway has "Enable CORS" enabled for resource

### Data Type Mismatch

**Cause**: DynamoDB field type doesn't match app expectations

**Fix**:
1. `operationalState` MUST be Boolean in DynamoDB (not String)
2. Check item:
   ```bash
   aws dynamodb get-item --table-name GenericSystems \
       --key '{"systemKey": {"S": "paymentSystem"}}'
   ```
3. If it shows `"operationalState": {"S": "true"}`, it's wrong (String)
4. Should be: `"operationalState": {"BOOL": true}`

---

## Security Best Practices

### Rotate API Keys

```bash
# Create new API key
NEW_KEY=$(aws apigateway create-api-key \
    --name ZendeskAppKey-2 \
    --enabled \
    --region eu-west-2 \
    --query 'id' \
    --output text)

# Add to usage plan
aws apigateway create-usage-plan-key \
    --usage-plan-id $USAGE_PLAN_ID \
    --key-id $NEW_KEY \
    --key-type API_KEY \
    --region eu-west-2

# Update Zendesk app with new key
# Then delete old key:
aws apigateway delete-api-key \
    --api-key $OLD_KEY_ID \
    --region eu-west-2
```

### Enable CloudWatch Logging

1. API Gateway → Settings
2. CloudWatch log role ARN: Create IAM role for API Gateway
3. Per-stage logging: Enable for `prod` stage

### Enable DynamoDB Point-in-Time Recovery

```bash
aws dynamodb update-continuous-backups \
    --table-name GenericSystems \
    --point-in-time-recovery-specification PointInTimeRecoveryEnabled=true \
    --region eu-west-2
```

---

## Cost Estimation

**Monthly costs** (assuming low usage):

- **DynamoDB**: ~$0.30/month
  - 1,000 reads/month
  - 500 writes/month
  - On-demand pricing

- **Lambda**: ~$0.00/month
  - 1,000 invocations/month
  - 128MB memory, 100ms average duration
  - Within free tier (1M requests/month)

- **API Gateway**: ~$0.04/month
  - 1,000 API calls/month
  - Within free tier first 12 months

**Total**: ~$0.34/month (after free tier expires)

---

## Next Steps

1. ✅ Complete all setup steps above
2. ✅ Test with curl commands
3. → Install Zendesk app (see main README.md)
4. → Test end-to-end from Zendesk
5. → Add monitoring and alerts (optional)
6. → Document for your team

---

**Questions?** Check the main [README.md](README.md) troubleshooting section.
