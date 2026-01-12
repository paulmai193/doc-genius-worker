# DocGenius Worker

An AWS-native serverless application that automatically generates technical specifications from NopCommerce source code using AI.

## Architecture

- **API Gateway**: REST endpoints for job submission and status
- **Step Functions**: Orchestrates the document generation workflow
- **Lambda Functions**: Core business logic (API handler, spec generator, cleanup, notifications)
- **Amazon Bedrock**: AI-powered document generation using Claude-Instant
- **S3**: Encrypted temporary storage for input/output files
- **DynamoDB**: Job metadata and status tracking
- **SNS**: Event notifications

## Prerequisites

- AWS CLI configured with appropriate permissions
- Node.js 18+ and npm
- AWS CDK v2 installed globally: `npm install -g aws-cdk`

## Deployment

1. Install dependencies:
```bash
npm install
```

2. Bootstrap CDK (first time only):
```bash
cdk bootstrap
```

3. Deploy the stack:
```bash
cdk deploy
```

4. Note the API Gateway URL from the output.

## Usage

### Submit a Document Generation Job

```bash
curl -X POST https://your-api-url/generate-spec \
  -H "Content-Type: application/json" \
  -d '{
    "archive": "base64-encoded-zip-content",
    "descriptor": {
      "moduleName": "ShoppingCart",
      "version": "1.0",
      "features": [
        {
          "id": "cart-001",
          "description": "Add items to shopping cart"
        }
      ]
    }
  }'
```

Response:
```json
{
  "jobId": "uuid-here"
}
```

### Check Job Status

```bash
curl https://your-api-url/job-status/{jobId}
```

Response:
```json
{
  "jobId": "uuid-here",
  "status": "Succeeded",
  "downloadUrl": "presigned-s3-url"
}
```

## API Endpoints

- `POST /generate-spec` - Submit source code and feature descriptor
- `GET /job-status/{jobId}` - Get job status and download URL

## Job Statuses

- `Pending` - Job created, waiting to start
- `Running` - AI is generating the specification
- `Succeeded` - Document generated successfully
- `Failed` - Error occurred during processing

## Security Features

- All data encrypted at rest with KMS
- Automatic cleanup after 24 hours
- IAM-based access control
- VPC endpoints for secure communication
- No data leaves EU-West-1 region

## Monitoring

The application emits CloudWatch metrics:
- `DocsGenerated` - Number of successful generations
- `ProcessingTimeMs` - Time taken to generate documents
- `FailedJobs` - Number of failed jobs

## Cost Optimization

- Uses Claude-Instant (lowest cost Bedrock model)
- Serverless architecture (pay-per-use)
- Automatic cleanup prevents storage cost buildup
- Designed to stay within AWS free tier limits

## Cleanup

To remove all resources:
```bash
cdk destroy
```

## Architecture Compliance

This implementation follows the specifications in:
- Enterprise Architecture Document (TOGAF10)
- Business Requirements Document (BABOK)
- Solution Architecture Design Document
- Technical Architecture Design Document

All functional requirements (FR-01 through FR-08) and user stories (US-001 through US-005) are implemented according to the documented specifications.