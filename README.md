# DynamoDB System Status Manager

A Zendesk ticket sidebar app that allows agents to toggle system operational status stored in AWS DynamoDB via API Gateway and Lambda.

![App Version](https://img.shields.io/badge/version-1.0-blue.svg)
![Framework](https://img.shields.io/badge/Zendesk_Framework-2.0-green.svg)
![AWS](https://img.shields.io/badge/AWS-DynamoDB%20%7C%20Lambda%20%7C%20API%20Gateway-orange.svg)

## Overview

This app provides a simple interface for support agents to view and update the operational status of critical systems directly from Zendesk tickets. It connects to AWS DynamoDB through API Gateway and Lambda, providing real-time status updates with visual feedback.

## Features

✅ **Real-time Status Display**
- View current operational status for multiple systems
- Color-coded status badges (green for operational, red for offline)
- Visual status indicators with icons

✅ **One-Click Toggle**
- Change system status from operational to offline (or vice versa)
- Immediate visual feedback during updates
- Success/error notifications

✅ **Systems Tracked**
- Payment System
- Customer Website
- *(Easily extensible to additional systems)*

✅ **Secure AWS Integration**
- API Gateway with API key authentication
- Lambda function for DynamoDB operations
- Secure credential management via Zendesk settings

## Architecture

```
┌─────────────────┐
│  Zendesk App    │
│   (React UI)    │
└────────┬────────┘
         │
         │ HTTPS + API Key
         ↓
┌─────────────────┐
│  API Gateway    │
│   /prod/update  │
│                 │
│  GET  - Fetch   │
│  POST - Update  │
└────────┬────────┘
         │
         │ Invokes
         ↓
┌─────────────────┐
│ Lambda Function │
│  (Python 3.x)   │
└────────┬────────┘
         │
         │ Read/Write
         ↓
┌─────────────────┐
│    DynamoDB     │
│ GenericSystems  │
│                 │
│ systemKey (PK)  │
│ operationalState│
└─────────────────┘
```

## Data Model

**DynamoDB Table**: `GenericSystems`

| Field | Type | Description |
|-------|------|-------------|
| `systemKey` | String (PK) | Unique identifier for the system |
| `operationalState` | Boolean | Current operational status (true/false) |

**Example Items**:
```json
{
  "systemKey": "paymentSystem",
  "operationalState": true
}

{
  "systemKey": "customerWebsite",
  "operationalState": false
}
```

## API Endpoints

### GET Request - Fetch System Status

**Endpoint**: `GET /prod/update-operational-state?systemKey={key}`

**Headers**:
- `x-api-key`: Your API Gateway API key
- `Content-Type`: application/json

**Response**:
```json
{
  "operationalState": "true"
}
```

### POST Request - Update System Status

**Endpoint**: `POST /prod/update-operational-state`

**Headers**:
- `x-api-key`: Your API Gateway API key
- `Content-Type`: application/json

**Body**:
```json
{
  "systemKey": "paymentSystem",
  "operationalState": true
}
```

**Response**:
```json
{
  "message": "Operational state updated successfully"
}
```

## Installation

### Prerequisites

1. **AWS Account** with permissions to create:
   - DynamoDB tables
   - Lambda functions
   - API Gateway APIs
   - IAM roles

2. **Zendesk Account** with:
   - Administrator access
   - Ability to install private apps

### Step 1: AWS Setup

**Follow the comprehensive [AWS_SETUP.md](AWS_SETUP.md) guide** which covers:

1. Creating the DynamoDB table
2. Setting up IAM roles and permissions
3. Deploying the Lambda function
4. Configuring API Gateway (REST API)
5. Creating and securing API keys
6. Testing the complete integration

**Important**: Complete all AWS setup steps before installing the Zendesk app.

### Step 2: Install Zendesk App

1. **Download this repository** as a ZIP file

2. **Navigate to Zendesk Admin Center**
   - Go to: Apps and integrations → Apps → Zendesk Support apps
   - Click "Upload private app"

3. **Upload the ZIP file**
   - Select the downloaded ZIP
   - Click "Upload"

4. **Configure App Settings**
   - **Webhook Secret**: Enter your API Gateway API key
     - Find this in: AWS Console → API Gateway → API Keys
     - This is stored securely and never exposed in the UI

5. **Install the App**
   - Choose which ticket views should display the app
   - Recommended: All ticket views for agent access

### Step 3: Test the Integration

1. Open any ticket in Zendesk
2. Look for the "System Status" app in the right sidebar
3. Verify that both systems are displayed:
   - Payment System
   - Customer Website
4. Try toggling a status:
   - Click "Set Offline" on an operational system
   - Verify the status updates in the UI
   - Check DynamoDB to confirm the change

## Usage

### For Support Agents

**Viewing System Status**:
- Open any ticket
- Check the "System Status" app in the right sidebar
- Green badge = Operational
- Red badge = Offline

**Updating System Status**:
1. Click "Set Offline" to mark a system as down
2. Click "Set Operational" to restore a system
3. Wait for the success confirmation message
4. Use "Refresh" button to manually reload statuses

### For Administrators

**Adding New Systems**:
1. Add item to DynamoDB table with:
   - `systemKey`: Unique identifier (e.g., "emailSystem")
   - `operationalState`: true or false
2. Update `constants.js` in the app source:
   ```javascript
   const SYSTEM_KEYS = ["paymentSystem", "customerWebsite", "emailSystem"];
   const SYSTEM_LABELS = {
     paymentSystem: "Payment System",
     customerWebsite: "Customer Website",
     emailSystem: "Email System"
   };
   ```
3. Re-package and update the Zendesk app

**Monitoring**:
- Check CloudWatch Logs for Lambda execution logs
- Monitor API Gateway metrics for request counts
- Review DynamoDB item history if versioning is enabled

## Configuration

### App Settings

**Secure Settings** (configured during installation):
- `webhookSecret`: API Gateway API key for authentication

### Customization

**API Endpoint** (`constants.js`):
```javascript
const WEBHOOK_BASE_URL = "https://89td2u0ux0.execute-api.eu-west-2.amazonaws.com/prod";
```

**System List** (`constants.js`):
```javascript
const SYSTEM_KEYS = ["paymentSystem", "customerWebsite"];
const SYSTEM_LABELS = {
  paymentSystem: "Payment System",
  customerWebsite: "Customer Website"
};
```

**Domain Whitelist** (`manifest.json`):
```json
"domainWhitelist": [
  "89td2u0ux0.execute-api.eu-west-2.amazonaws.com"
]
```

## Troubleshooting

### App Shows "Failed to load systems"

**Possible causes**:
1. **Incorrect API key**
   - Verify the API key in app settings matches AWS
   - Check: AWS Console → API Gateway → API Keys

2. **API Gateway not deployed**
   - Ensure you've deployed the API to the "prod" stage
   - Check: API Gateway → Stages → prod

3. **CORS issues**
   - Verify CORS is enabled on API Gateway
   - Required headers: `Access-Control-Allow-Origin: *`

4. **Lambda execution errors**
   - Check CloudWatch Logs for Lambda errors
   - Verify IAM role has DynamoDB permissions

### "Forbidden" Error on Status Toggle

**Possible causes**:
1. **Missing API key**
   - Ensure API key is configured in Zendesk app settings
   - Verify the API key is active in AWS

2. **Usage plan not attached**
   - Check: API Gateway → Usage Plans
   - Ensure the plan is associated with the "prod" stage

### Status Not Updating in DynamoDB

**Check**:
1. Lambda CloudWatch Logs for errors
2. IAM role permissions for `dynamodb:UpdateItem`
3. Field name matching (`operationalState` not `operational`)
4. Data type (Boolean, not String)

### Getting More Details

**Enable Debug Logging**:
1. Check browser console (F12) for error messages
2. Review Lambda logs in CloudWatch:
   ```
   AWS Console → CloudWatch → Log Groups → /aws/lambda/[function-name]
   ```
3. Check API Gateway execution logs:
   ```
   API Gateway → Stages → prod → Logs/Tracing
   ```

## Security Considerations

### API Key Management
- ✅ API keys are stored securely in Zendesk settings
- ✅ Keys are marked as `secure: true` in manifest
- ✅ Keys are never exposed in browser console or UI
- ⚠️ Rotate API keys periodically (recommended: every 90 days)

### AWS Security
- ✅ Lambda uses IAM role with least-privilege permissions
- ✅ API Gateway enforces API key authentication
- ✅ DynamoDB access restricted to Lambda role only
- ⚠️ Consider enabling DynamoDB encryption at rest
- ⚠️ Enable CloudTrail for audit logging

### Network Security
- ✅ All communications use HTTPS
- ✅ Domain whitelist prevents unauthorized origins
- ✅ CORS configured for API Gateway

## Development

### Project Structure

```
dynamodb-system-status-manager/
├── README.md                    # This file
├── AWS_SETUP.md                 # AWS infrastructure setup guide
├── CHANGELOG.md                 # Version history
├── manifest.json                # Zendesk app manifest
├── translations/
│   └── en.json                  # English translations
├── lambda/
│   └── lambda_function.py       # Lambda handler code
└── assets/
    ├── index.html               # Bundled React app
    ├── logo.png                 # App icon (large)
    └── logo-small.png           # App icon (small)
```

### Tech Stack

**Frontend**:
- React 18
- Zendesk Garden UI Components
- Styled Components
- Zendesk Apps Framework SDK 2.0

**Backend**:
- AWS Lambda (Python 3.x)
- Amazon DynamoDB
- Amazon API Gateway (REST API)
- AWS IAM

### Local Development

This app was built using **Zendesk App Builder**, which provides:
- Live preview environment
- Automatic bundling and compilation
- Mock data for testing
- Error reporting and debugging

To modify the app, use the App Builder interface or:
1. Extract source files from `index.html`
2. Edit component files
3. Rebuild using Zendesk ZAT (Zendesk App Tools)

## Version History

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

**Current Version**: 1.0 (V4)
- ✅ Switched from AWS Signature V4 to API Gateway + Lambda
- ✅ Fixed field naming: `operationalState` (Boolean)
- ✅ Added JSON parsing fallback for API responses
- ✅ Improved error handling and user feedback

## Support

### Getting Help

1. **Check this README** for common issues
2. **Review AWS_SETUP.md** for infrastructure questions
3. **Check CloudWatch Logs** for runtime errors
4. **Review CHANGELOG.md** for known issues

### Reporting Issues

When reporting issues, include:
- Zendesk app version
- Error message from browser console
- Lambda CloudWatch logs (if applicable)
- Steps to reproduce

## License

This is a private Zendesk app for internal use.

## Credits

**Author**: Richard Uzzell (richard.uzzell@zendesk.com)

**Built with**:
- Zendesk App Builder
- AWS Services (Lambda, DynamoDB, API Gateway)
- React and Zendesk Garden UI

---

**Need help with AWS setup?** → See [AWS_SETUP.md](AWS_SETUP.md) for detailed instructions.
