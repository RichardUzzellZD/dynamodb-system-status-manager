# Changelog

All notable changes to the DynamoDB System Status Manager app are documented in this file.

## [1.0.0] - 2026-04-17

### Version 4 (Final Release)

**Fixed:**
- API response field mapping: Changed from `operational` to `operationalState`
- POST request now sends `operationalState` as boolean instead of string
- Added JSON parsing for ZAF client responses (handles both string and object responses)
- Resolved "Forbidden" error by correctly formatting request payload

**Technical Details:**
- `fetchSystems()` now reads `parsed.operationalState` from API response
- `updateOperationalStatus()` sends `operationalState: newValue === 'true'` (boolean)
- Added `typeof res === 'string' ? JSON.parse(res) : res` fallback

---

## [0.3.0] - 2026-04-17

### Version 3

**Added:**
- API key authentication via `x-api-key` header
- Secure manifest parameter `webhookSecret` for storing API key
- ZAF secure proxy for requests (`secure: true`)
- Required headers for secure requests:
  - `X-Zendesk-UA-Override: none`
  - `X-Requested-With: ''`

**Changed:**
- All API requests now include API key in header
- Requests routed through Zendesk proxy for security

---

## [0.2.0] - 2026-04-16

### Version 2

**Changed:**
- **Complete refactor**: Removed AWS Signature V4 signing
- Replaced direct DynamoDB calls with API Gateway webhook
- Simplified architecture to use REST API endpoint

**Removed:**
- `utils/awsSig4.js` - No longer needed with API Gateway
- AWS credential parameters (`awsAccessKeyId`, `awsSecretAccessKey`, `awsRegion`)
- Direct DynamoDB SDK calls

**Added:**
- Simple GET/POST requests to API Gateway
- Domain whitelist for `89td2u0ux0.execute-api.eu-west-2.amazonaws.com`
- GET endpoint for fetching system status: `?systemKey=paymentSystem`
- POST endpoint for updating status: `{ systemKey, operationalState }`

**Benefits:**
- No AWS credentials stored in Zendesk app
- Simpler security model (API key only)
- Easier to maintain and debug
- Better separation of concerns

---

## [0.1.0] - 2026-04-16

### Version 1 (Initial Release)

**Initial Features:**
- Display operational status for `paymentSystem` and `customerWebsite`
- Toggle status between true/false with button clicks
- Visual status badges (green for operational, red for offline)
- Success/error notifications
- Direct integration with DynamoDB using AWS Signature V4

**Architecture (Version 1):**
- AWS Signature V4 signing for DynamoDB requests
- BatchGetItem for fetching multiple systems
- UpdateItem for toggling status
- Secure credential storage via manifest parameters

**Files Created:**
- `App.jsx` - Main app component with system cards
- `utils/awsSig4.js` - AWS Signature V4 signing utility
- `utils/dynamoApi.js` - DynamoDB API wrapper
- `components/SystemCard.jsx` - Individual system status card
- `styles/AppStyles.js` - Styled components
- `constants.js` - System keys and table configuration
- `mock.js` - Mock data for testing

---

## Architecture Evolution

### Version 1: Direct DynamoDB
```
Zendesk App → AWS Signature V4 → DynamoDB
```
**Pros**: Direct access, no intermediary
**Cons**: AWS credentials in app, complex signing, harder to secure

### Version 2-4: API Gateway + Lambda
```
Zendesk App → API Gateway → Lambda → DynamoDB
```
**Pros**: 
- Simple API key authentication
- No AWS credentials in Zendesk
- Lambda provides business logic layer
- Easier to monitor and debug
- Better security model

---

## Development Notes

### Key Lessons Learned

1. **Field Naming Consistency**: Always align frontend/backend field names
   - Started with `operational` (string)
   - Migrated to `operationalState` (boolean)
   - Required careful mapping in `dynamoApi.js`

2. **ZAF Client Response Handling**: The Zendesk client can return responses as either:
   - Pre-parsed objects
   - JSON strings
   - Solution: Add `typeof res === 'string' ? JSON.parse(res) : res`

3. **Secure Requests**: When using `secure: true` in ZAF requests:
   - Must include `X-Zendesk-UA-Override: none`
   - Must include `X-Requested-With: ''`
   - Enables server-side secret resolution

4. **API Gateway Authentication**: 
   - API keys simpler than AWS Signature V4
   - Usage plans provide rate limiting
   - Easier to rotate keys

---

## Migration Guide

### From Version 1 to Version 2+

If you have Version 1 installed:

1. **AWS Setup**: Follow [AWS_SETUP.md](AWS_SETUP.md) to create:
   - API Gateway REST API
   - Lambda function
   - API key

2. **Update App**:
   - Uninstall Version 1
   - Install Version 2+
   - Remove old AWS credentials from settings
   - Add new API key as `webhookSecret`

3. **DynamoDB Schema**:
   - No changes needed
   - Table structure remains the same

---

## Future Roadmap

- [ ] Add more system types beyond payment/website
- [ ] System health metrics and uptime tracking
- [ ] Status change history log
- [ ] Automated health checks
- [ ] Multi-region support
- [ ] Slack/email notifications on status changes
- [ ] Bulk operations (mark all offline)
- [ ] Custom system names via settings

---

## License

MIT License - Copyright (c) 2026 Richard Uzzell

## Contributors

- Richard Uzzell (richard.uzzell@zendesk.com) - Initial development
