# AWS Infrastructure Setup Guide

Complete instructions for setting up DynamoDB, Lambda, and API Gateway for the System Status Manager app.

## Prerequisites

- AWS Account with admin or appropriate IAM permissions
- AWS CLI installed and configured
- Basic understanding of AWS services

## Architecture Overview

```
API Gateway (REST API)
        ↓
 Lambda Function (Python)
        ↓
  DynamoDB Table (GenericSystems)
```

---

## Step 1: Create DynamoDB Table

### Via AWS Console

1. Go to **DynamoDB** in AWS Console
2. Click **Create table**
3. Configure:
   - **Table name**: `GenericSystems`
   - **Partition key**: `systemKey` (String)
   - **Table settings**: Default settings
4. Click **Create table**
5. Wait for table to become ACTIVE

### Via AWS CLI

```bash
aws dynamodb create-table \
  --table-name GenericSystems \
  --attribute-definitions \
    AttributeName=systemKey,AttributeType=S \
  --key-schema \
    AttributeName=systemKey,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region eu-west-2
```

### Add Initial Data

```bash
# Add paymentSystem
aws dynamodb put-item \
  --table-name GenericSystems \
  --item '{
    "systemKey": {"S": "paymentSystem"},
    "operationalState": {"BOOL": true}
  }' \
  --region eu-west-2

# Add customerWebsite
aws dynamodb put-item \
  --table-name GenericSystems \
  --item '{
    "systemKey": {"S": "customerWebsite"},
    "operationalState": {"BOOL": true}
  }' \
  --region eu-west-2
```

### Verify Data

```bash
aws dynamodb scan \
  --table-name GenericSystems \
  --region eu-west-2
```

---

## Step 2: Create IAM Role for Lambda

### Via AWS Console

1. Go to **IAM** → **Roles**
2. Click **Create role**
3. Select **Lambda** as trusted entity
4. Click **Next**
5. Attach policies:
   - `AWSLambdaBasicExecutionRole` (for CloudWatch Logs)
   - Create custom policy for DynamoDB:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-2:*:table/GenericSystems"
    }
  ]
}
```

6. Name the role: `LambdaDynamoDBSystemStatusRole`
7. Click **Create role**

### Via AWS CLI

Create policy file `lambda-dynamodb-policy.json`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "arn:aws:dynamodb:eu-west-2:*:table/GenericSystems"
    }
  ]
}
```

Create the role:
```bash
aws iam create-role \
  --role-name LambdaDynamoDBSystemStatusRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'

aws iam put-role-policy \
  --role-name LambdaDynamoDBSystemStatusRole \
  --policy-name DynamoDBSystemStatusPolicy \
  --policy-document file://lambda-dynamodb-policy.json
```

---

## Step 3: Create Lambda Function

### Via AWS Console

1. Go to **Lambda** → **Functions**
2. Click **Create function**
3. Configure:
   - **Function name**: `updateSystemStatus`
   - **Runtime**: Python 3.11 (or latest)
   - **Architecture**: x86_64
   - **Execution role**: Use existing role → `LambdaDynamoDBSystemStatusRole`
4. Click **Create function**
5. In the code editor, paste the contents of [`lambda/lambda_function.py`](lambda/lambda_function.py)
6. Click **Deploy**
7. Go to **Configuration** → **Environment variables**
8. Add:
   - **Key**: `DYNAMODB_TABLE_NAME`
   - **Value**: `GenericSystems`
9. Save

### Via AWS CLI

Create deployment package:
```bash
# Clone this repo
git clone https://github.com/RichardUzzellZD/dynamodb-system-status-manager.git
cd dynamodb-system-status-manager/lambda

# Create zip
zip -r lambda.zip lambda_function.py

# Get the IAM role ARN
ROLE_ARN=$(aws iam get-role --role-name LambdaDynamoDBSystemStatusRole --query 'Role.Arn' --output text)

# Create Lambda function
aws lambda create-function \
  --function-name updateSystemStatus \
  --runtime python3.11 \
  --role $ROLE_ARN \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://lambda.zip \
  --environment Variables={DYNAMODB_TABLE_NAME=GenericSystems} \
  --region eu-west-2
```

### Test the Lambda

Create test event `test-get.json`:
```json
{
  "httpMethod": "GET",
  "queryStringParameters": {
    "systemKey": "paymentSystem"
  }
}
```

Test via Console or CLI:
```bash
aws lambda invoke \
  --function-name updateSystemStatus \
  --payload file://test-get.json \
  --region eu-west-2 \
  response.json

cat response.json
```

---

## Step 4: Create API Gateway

### Via AWS Console

1. Go to **API Gateway**
2. Click **Create API** → **REST API** (not Private)
3. Click **Build**
4. Configure:
   - **API name**: `SystemStatusAPI`
   - **Endpoint type**: Regional
5. Click **Create API**

#### Create Resource

1. Click **Actions** → **Create Resource**
2. Resource name: `update-operational-state`
3. Click **Create Resource**

#### Create GET Method

1. Select `/update-operational-state` resource
2. Click **Actions** → **Create Method** → **GET**
3. Configure:
   - **Integration type**: Lambda Function
   - **Use Lambda Proxy integration**: ✓ (checked)
   - **Lambda Function**: `updateSystemStatus`
   - **Region**: eu-west-2
4. Click **Save**
5. Click **OK** to give API Gateway permission to invoke Lambda

#### Create POST Method

1. Select `/update-operational-state` resource
2. Click **Actions** → **Create Method** → **POST**
3. Configure same as GET
4. Click **Save**

#### Enable CORS

1. Select `/update-operational-state` resource
2. Click **Actions** → **Enable CORS**
3. Keep default settings
4. Click **Enable CORS and replace existing CORS headers**

#### Deploy API

1. Click **Actions** → **Deploy API**
2. **Deployment stage**: `[New Stage]`
3. **Stage name**: `prod`
4. Click **Deploy**
5. **Note the Invoke URL**: `https://XXXXX.execute-api.eu-west-2.amazonaws.com/prod`

---

## Step 5: Add API Key Authentication

### Create API Key

1. In API Gateway, go to **API Keys**
2. Click **Actions** → **Create API Key**
3. Name: `ZendeskAppKey`
4. Click **Save**
5. Click **Show** and copy the API key (you'll need this for Zendesk)

### Create Usage Plan

1. Go to **Usage Plans**
2. Click **Create**
3. Name: `ZendeskAppPlan`
4. Click **Next**
5. Add API Stage: Select `SystemStatusAPI` → `prod`
6. Click **Next**
7. Add API Key: Select `ZendeskAppKey`
8. Click **Done**

### Require API Key on Methods

1. Go back to **APIs** → **SystemStatusAPI**
2. Select **GET** method under `/update-operational-state`
3. Click **Method Request**
4. Set **API Key Required**: true
5. Click the checkmark to save
6. Repeat for **POST** method
7. **Deploy API** again (Actions → Deploy API → prod)

---

## Step 6: Test the Complete Setup

### Test GET Request

```bash
API_KEY="your-api-key-here"
API_URL="https://89td2u0ux0.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state"

curl -X GET \
  "${API_URL}?systemKey=paymentSystem" \
  -H "x-api-key: ${API_KEY}"
```

Expected response:
```json
{
  "RecordFound": "true",
  "systemKey": "paymentSystem",
  "operationalState": "true"
}
```

### Test POST Request

```bash
curl -X POST \
  "${API_URL}" \
  -H "x-api-key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{
    "systemKey": "paymentSystem",
    "operationalState": false
  }'
```

Expected response:
```json
{
  "success": true,
  "systemKey": "paymentSystem",
  "operationalState": false
}
```

### Verify in DynamoDB

```bash
aws dynamodb get-item \
  --table-name GenericSystems \
  --key '{"systemKey": {"S": "paymentSystem"}}' \
  --region eu-west-2
```

---

## Summary

You should now have:

- ✅ DynamoDB table `GenericSystems` with 2 systems
- ✅ Lambda function `updateSystemStatus` with DynamoDB permissions
- ✅ API Gateway `SystemStatusAPI` with GET/POST methods
- ✅ API Key for authentication
- ✅ Deployed to `prod` stage

**API Endpoint**: `https://XXXXX.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state`
**API Key**: Copy from API Gateway console

---

## Next Steps

1. Copy the API endpoint URL
2. Copy the API key
3. Follow [INSTALLATION.md](INSTALLATION.md) to install the Zendesk app
4. Enter the API key as the `webhookSecret` during app installation

---

## Troubleshooting

### Lambda returns "Unable to import module"
- Check runtime is Python 3.11
- Verify handler is `lambda_function.lambda_handler`

### API Gateway returns 403 Forbidden
- Verify API key is included in `x-api-key` header
- Check API key is added to usage plan
- Ensure methods require API key

### Lambda can't access DynamoDB
- Check IAM role has `dynamodb:GetItem` and `dynamodb:UpdateItem` permissions
- Verify table name matches environment variable

### CORS errors in browser
- Ensure CORS is enabled on API Gateway
- Redeploy API after enabling CORS

---

## Cost Estimate

**Monthly costs for 1,000 status checks:**
- DynamoDB: $0.25 (PAY_PER_REQUEST)
- Lambda: $0.20 (1GB memory, 1 second duration)
- API Gateway: $3.50 (REST API requests)
- **Total**: ~$4/month for light usage

---

## Security Best Practices

1. **Rotate API keys** regularly (every 90 days)
2. **Enable CloudWatch Logs** for Lambda debugging
3. **Set up CloudWatch Alarms** for Lambda errors
4. **Use least-privilege IAM policies**
5. **Enable AWS CloudTrail** for audit logging
6. **Consider AWS WAF** for API Gateway protection
