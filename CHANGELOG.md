# Changelog

All notable changes to the DynamoDB System Status Manager app are documented in this file.

## [1.0] - V4 - 2026-07-16

### Changed
- **Architecture Migration**: Switched from AWS Signature V4 direct DynamoDB access to API Gateway + Lambda pattern
  - Reason: Signature V4 was overly complex for a simple status toggle app
  - New pattern is more maintainable and follows AWS best practices

### Fixed
- **Field Naming Consistency**: Fixed mismatch between app and DynamoDB field names
  - Issue: App was sending `operational` (String) but DynamoDB expected `operationalState` (Boolean)
  - Fix: Updated `dynamoApi.js` to use `operationalState` for both GET and POST requests
  - Added JSON parsing fallback: `typeof res === 'string' ? JSON.parse(res) : res`

### Added
- Lambda function (`lambda_function.py`) to handle GET and POST requests
- API Gateway REST API with API key authentication
- Comprehensive error handling in Lambda function
- CORS support for cross-origin requests

## [0.3] - V3 - 2026-07-15

### Changed
- Attempted AWS Signature V4 implementation
- Created `awsSig4.js` utility for request signing

### Issues
- "Forbidden" errors due to field name mismatches
- Complexity of managing AWS credentials in Zendesk
- Decided to migrate to API Gateway pattern instead

## [0.2] - V2 - 2026-07-14

### Added
- Direct DynamoDB integration using Zendesk secure proxy
- System cards with operational status badges
- Toggle functionality with loading states

### Changed
- Improved UI with color-coded status indicators
- Added success/error notifications

## [0.1] - V1 - 2026-07-13

### Added
- Initial app creation via Zendesk App Builder
- Basic UI with system status display
- Mock data for development
- Integration plan for DynamoDB

### Features
- Display current operational status for paymentSystem and customerWebsite
- Visual indicators (colors/icons) for operational vs non-operational states
- Refresh button to reload statuses

---

## Architecture Evolution

### Version 1-2: Direct DynamoDB (Failed)
```
Zendesk App → AWS Credentials → DynamoDB
```
**Problems**:
- Exposed AWS credentials in Zendesk settings (security risk)
- Complex credential management
- No API layer for future extensibility

### Version 3: AWS Signature V4 (Complex)
```
Zendesk App → Zendesk Proxy → AWS Signature V4 → DynamoDB
```
**Problems**:
- Overly complex for simple use case
- Field naming mismatches caused "Forbidden" errors
- Hard to debug and maintain

### Version 4: API Gateway + Lambda (Current) ✅
```
Zendesk App → API Gateway (API Key) → Lambda → DynamoDB
```
**Benefits**:
- Simple API key authentication
- Lambda handles all AWS logic
- Easy to test and debug
- Follows AWS best practices
- Extensible for future features

---

## Known Issues

None currently.

## Planned Features

- [ ] Support for additional systems beyond paymentSystem and customerWebsite
- [ ] Timestamp tracking for last status change
- [ ] User audit log (who changed what and when)
- [ ] Bulk status updates
- [ ] Integration with Zendesk triggers for auto-notifications

## Migration Notes

### Upgrading from V3 to V4

If you're upgrading from a previous version:

1. **Complete AWS Setup**:
   - Create API Gateway and Lambda function (see AWS_SETUP.md)
   - Update manifest.json with new API Gateway domain

2. **Update App Settings**:
   - Replace AWS credentials with single API key
   - Remove `awsAccessKeyId`, `awsSecretAccessKey`, `awsRegion` parameters
   - Add `webhookSecret` parameter with API Gateway API key

3. **Update DynamoDB Schema** (if needed):
   - Ensure field is named `operationalState` (not `operational`)
   - Ensure data type is Boolean (not String)
   - Update existing items:
     ```bash
     aws dynamodb update-item \
       --table-name GenericSystems \
       --key '{"systemKey": {"S": "paymentSystem"}}' \
       --update-expression "SET operationalState = :val REMOVE operational" \
       --expression-attribute-values '{":val": {"BOOL": true}}'
     ```

4. **Test Integration**:
   - Verify GET and POST requests work with curl
   - Test in Zendesk app
   - Check CloudWatch logs for errors

---

## Support

For questions or issues, contact: richard.uzzell@zendesk.com
