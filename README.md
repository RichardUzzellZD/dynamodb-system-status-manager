# DynamoDB System Status Manager

A Zendesk ticket sidebar application that enables support agents to view and toggle the operational status of critical systems stored in AWS DynamoDB. The app integrates seamlessly with AWS API Gateway and Lambda to provide real-time system status management.

![Version](https://img.shields.io/badge/version-1.0-blue)
![Zendesk](https://img.shields.io/badge/Zendesk-App%20Builder-green)
![AWS](https://img.shields.io/badge/AWS-Lambda%20%7C%20DynamoDB%20%7C%20API%20Gateway-orange)
![License](https://img.shields.io/badge/license-MIT-green)

## 📋 Overview

This app provides support agents with quick visibility and control over critical system statuses directly from Zendesk tickets. Agents can:

- **View** real-time operational status of multiple systems
- **Toggle** status between operational and offline with one click
- **Monitor** payment systems, customer websites, and other critical infrastructure
- **Track** changes with visual indicators (green/red status badges)
- **Receive** instant feedback with success/error notifications

## ✨ Key Features

### 🎯 System Status Management

- **Real-Time Status Display**: Fetch current operational state from DynamoDB
- **Visual Status Indicators**:
  - 🟢 Green badge for "Operational" (true)
  - 🔴 Red badge for "Offline" (false)
- **One-Click Toggle**: Switch between operational/offline states
- **Instant Feedback**: Success/error notifications after each action

### 🏗️ Architecture

```
Zendesk Ticket Sidebar
        ↓
   App Interface
        ↓
  API Gateway (AWS)
        ↓
 Lambda Function (Python)
        ↓
  DynamoDB Table (GenericSystems)
```

### 🔐 Security

- **Secure API Key**: Webhook secret stored encrypted in Zendesk
- **Server-Side Proxy**: All requests routed through Zendesk's secure proxy
- **IAM Permissions**: Lambda uses role-based access to DynamoDB
- **Domain Whitelist**: Only approved API Gateway endpoint allowed

### 📦 Systems Tracked

**Default Systems:**
- `paymentSystem` - Payment processing infrastructure
- `customerWebsite` - Public-facing customer website

**DynamoDB Schema:**
- **systemKey** (String, Primary Key): System identifier
- **operationalState** (Boolean): true = Operational, false = Offline

## 🚀 Quick Start

### Prerequisites

- Zendesk Support account (Professional or Enterprise)
- AWS Account with permissions for:
  - DynamoDB
  - Lambda
  - API Gateway
  - IAM roles
- Admin access to Zendesk

### Installation

1. **Set up AWS infrastructure** (see [AWS_SETUP.md](AWS_SETUP.md))
2. **Install the Zendesk app** (see [INSTALLATION.md](INSTALLATION.md))
3. **Configure the webhook secret**
4. **Test the integration**

## 🏗️ AWS Architecture

### DynamoDB Table

**Table Name**: `GenericSystems`
**Region**: `eu-west-2` (London)
**Primary Key**: `systemKey` (String)

**Table Structure:**
```json
{
  "systemKey": "paymentSystem",
  "operationalState": true
}
```

**Sample Items:**
| systemKey | operationalState |
|-----------|-----------------|
| paymentSystem | true |
| customerWebsite | true |

### Lambda Function

**Function Name**: `fetchSystemData` or `updateSystemData`
**Runtime**: Python 3.x
**Handler**: `lambda_function.lambda_handler`

**Environment Variables:**
- `DYNAMODB_TABLE_NAME`: GenericSystems

**IAM Permissions Required:**
- `dynamodb:GetItem`
- `dynamodb:UpdateItem`

See [lambda/lambda_function.py](lambda/lambda_function.py) for complete code.

### API Gateway

**Endpoint**: `https://89td2u0ux0.execute-api.eu-west-2.amazonaws.com/prod/update-operational-state`

**Methods:**
- **GET**: Fetch system status
  ```
  GET /update-operational-state?systemKey=paymentSystem
  ```
  
- **POST**: Update system status
  ```json
  {
    "systemKey": "paymentSystem",
    "operationalState": false
  }
  ```

**Authentication**: `x-api-key` header with API key

See [AWS_SETUP.md](AWS_SETUP.md) for detailed setup instructions.

## 📖 Usage Guide

### For Support Agents

**Viewing System Status:**
1. Open any ticket in Zendesk
2. Look for "DynamoDB System Status Manager" in the right sidebar
3. View current status of all systems:
   - 🟢 Green "Operational" badge = System is running
   - 🔴 Red "Offline" badge = System is down

**Toggling System Status:**
1. Find the system you want to update
2. Click the toggle button:
   - "Set Offline" (if currently operational)
   - "Set Operational" (if currently offline)
3. Wait for confirmation message
4. Status badge updates automatically

**Example Scenarios:**

**Scenario 1: Payment System Outage**
- Customer reports payment failure
- Agent opens ticket
- Agent sees "Payment System" card
- Clicks "Set Offline" to mark system as down
- Other agents now see offline status
- After fix, click "Set Operational"

**Scenario 2: Website Maintenance**
- Planned website maintenance begins
- Agent sets "Customer Website" to offline
- All agents see offline badge
- After maintenance, toggle back to operational

## 🔧 Configuration

### Zendesk App Settings

During installation, you'll be prompted for:

**webhookSecret** (Required, Secure)
- The API key for your AWS API Gateway endpoint
- Stored encrypted in Zendesk
- Never exposed in client-side code

### Adding More Systems

To track additional systems:

1. **Add to DynamoDB:**
   ```bash
   aws dynamodb put-item \
     --table-name GenericSystems \
     --item '{"systemKey": {"S": "emailService"}, "operationalState": {"BOOL": true}}'
   ```

2. **Update the app:**
   - Modify `constants.js` in the bundled `index.html`
   - Add new system key to `SYSTEM_KEYS` array
   - Re-package and re-upload the app

See [CUSTOMIZATION.md](CUSTOMIZATION.md) for detailed instructions.

## 🛠️ Technical Details

### Technology Stack

- **Frontend**: React 18, Zendesk Garden UI components
- **Backend**: AWS Lambda (Python 3.x)
- **Database**: AWS DynamoDB
- **API**: AWS API Gateway (REST API)
- **Auth**: API Key (x-api-key header)
- **SDK**: Zendesk App Framework SDK 2.0

### API Request Flow

**Fetch Status (GET):**
```javascript
// App makes request
GET /update-operational-state?systemKey=paymentSystem
Headers: { 'x-api-key': '<secret>' }

// Lambda queries DynamoDB
table.get_item(Key={'systemKey': 'paymentSystem'})

// Returns
{ "systemKey": "paymentSystem", "operationalState": "true", "RecordFound": "true" }
```

**Update Status (POST):**
```javascript
// App makes request
POST /update-operational-state
Body: { "systemKey": "paymentSystem", "operationalState": false }
Headers: { 'x-api-key': '<secret>' }

// Lambda updates DynamoDB
table.update_item(Key={'systemKey': 'paymentSystem'}, ...)

// Returns
{ "success": true, "systemKey": "paymentSystem", "operationalState": false }
```

### Error Handling

**Common Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `Forbidden (403)` | Invalid API key | Check webhook secret in app settings |
| `System not found` | systemKey doesn't exist in DynamoDB | Add item to DynamoDB table |
| `NetworkError` | API Gateway unreachable | Check domain whitelist in manifest |
| `Timeout` | Lambda cold start or DynamoDB throttling | Retry request |

## 📂 Repository Structure

```
dynamodb-system-status-manager/
├── README.md                      # This file
├── AWS_SETUP.md                   # AWS infrastructure setup guide
├── INSTALLATION.md                # Zendesk app installation
├── CUSTOMIZATION.md               # How to customize
├── CHANGELOG.md                   # Version history
├── manifest.json                  # App configuration
├── translations/
│   └── en.json                    # English translations
├── assets/
│   ├── index.html                 # Bundled React app
│   ├── logo.png                   # App icon (large)
│   └── logo-small.png             # App icon (small)
└── lambda/
    ├── lambda_function.py         # Lambda handler code
    ├── requirements.txt           # Python dependencies
    └── README.md                  # Lambda deployment guide
```

## 🐛 Troubleshooting

### App shows "Forbidden" error

**Cause**: Invalid API key or missing header
**Solution**:
1. Go to Admin Center → Apps → DynamoDB System Status Manager → Settings
2. Re-enter the webhook secret (API key)
3. Save and refresh the ticket page

### Status doesn't update after toggle

**Cause**: Lambda not updating DynamoDB
**Solution**:
1. Check Lambda CloudWatch logs for errors
2. Verify Lambda has IAM permissions for `dynamodb:UpdateItem`
3. Test Lambda function directly in AWS Console

### "System not found" error

**Cause**: systemKey doesn't exist in DynamoDB
**Solution**:
```bash
aws dynamodb put-item \
  --table-name GenericSystems \
  --item '{"systemKey": {"S": "paymentSystem"}, "operationalState": {"BOOL": true}}'
```

### API Gateway returns 500 error

**Cause**: Lambda function error
**Solution**:
1. Check CloudWatch Logs for the Lambda function
2. Verify environment variable `DYNAMODB_TABLE_NAME` is set
3. Test Lambda with sample event in AWS Console

## 📜 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/RichardUzzellZD/dynamodb-system-status-manager/issues)
- **AWS Docs**: [DynamoDB](https://docs.aws.amazon.com/dynamodb/) | [Lambda](https://docs.aws.amazon.com/lambda/) | [API Gateway](https://docs.aws.amazon.com/apigateway/)
- **Zendesk Docs**: [Apps Framework](https://developer.zendesk.com/documentation/apps/)
- **Email**: richard.uzzell@zendesk.com

## 🎯 Roadmap

- [ ] Add more system types (database, email service, etc.)
- [ ] System health metrics (uptime percentage)
- [ ] Status change history log
- [ ] Automated status checks via CloudWatch
- [ ] Multi-region support
- [ ] Slack/email notifications on status changes
- [ ] Bulk toggle (mark all systems offline)
- [ ] Custom system names via app settings

---

**Built with ❤️ for Zendesk + AWS integration**
