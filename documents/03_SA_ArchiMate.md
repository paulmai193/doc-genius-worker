# Solution Architecture Design Document  

## 1. Executive Summary  

### 1.1 Solution Overview  
The **AI Digital Worker Factory** delivers a serverless, AWS‑native micro‑service that ingests a NopCommerce source‑code package and a JSON feature‑description, then automatically produces high‑quality technical specifications (Software Requirements Specification / Functional Specification).  The worker is orchestrated with **AWS Step Functions**, performs AI‑driven text generation via **Amazon Bedrock (Claude‑Instant)**, formats output to Markdown and PDF, stores artifacts temporarily in encrypted **Amazon S3**, records job metadata in **Amazon DynamoDB**, and notifies callers through **Amazon SNS**.  The entire flow is exposed through a **REST API** powered by **Amazon API Gateway**.  

### 1.2 Architecture Approach  
* **Serverless‑first** – All compute is Lambda; state is persisted in S3/DynamoDB; no servers to provision or patch.  
* **Event‑driven orchestration** – Step Functions coordinates the workflow, implements retries, and guarantees compensation (cleanup).  
* **AI‑enabled core** – Bedrock provides the LLM, keeping data inside the AWS boundary (EU‐West‑1) for compliance.  
* **Security by design** – SSE‑KMS encryption, VPC endpoints for S3 & Bedrock, IAM least‑privilege roles, immutable CloudTrail audit logs, 24‑hour auto‑delete lifecycle.  

### 1.3 Key Design Decisions  

| Decision | Rationale |
|----------|-----------|
| Use **Claude‑Instant** on Bedrock | Lowest LLM cost, sufficient token length for spec generation, fast latency (< 1 s per request). |
| Store source and output in **S3** with **SSE‑KMS** | Meets ISO 27001 encryption‑at‑rest, enables easy lifecycle policies for automatic deletion. |
| Orchestrate with **Step Functions** (Standard) | Provides visual workflow, built‑in error handling, and native integration with Lambda and SNS. |
| Persist job state in **DynamoDB** (single table) | Low‑latency reads for status polling, serverless scaling, point‑in‑time recovery. |
| Expose **REST API** via **API Gateway** (IAM auth) | Simple integration for developers, supports future Cognito or API‑key auth without code changes. |
| Use **CloudWatch custom metrics** | Enables SLA monitoring (latency, success rate) and cost‑aware alerts. |
| Implement **CDK (TypeScript)** for IaC | Consistent, testable infrastructure, easy to extend for multi‑region rollout. |

### 1.4 Implementation Readiness Assessment  

| Area | Status | Comments |
|------|--------|----------|
| **Requirements** | ✅ Complete (BRD & EA Doc) | All functional, non‑functional, compliance items captured. |
| **Design** | ✅ Approved | Architecture board sign‑off (Phase A–F). |
| **Team Skillset** | ✅ Ready | Python (Lambda), TypeScript (CDK), Prompt Engineering for Bedrock. |
| **Tooling** | ✅ Set | AWS CLI, CDK, SAM‑local for Lambda testing, Postman for API. |
| **Budget** | ✅ Within $150 PoC limit | Cost model built on free‑tier + Bedrock usage estimate. |
| **Timeline** | ✅ 2 days (48 h) | Detailed work‑breakdown aligns with hackathon schedule. |


---

## 2. System Context & Requirements  

### 2.1 System Context Diagram  

```
[Client] --> (API Gateway) --> (Step Functions)
                                   |
        +--------------------------+---------------------------+
        |                          |                           |
   (Lambda: Source Loader)   (Lambda: Spec Generator)    (Lambda: Cleanup)
        |                          |                           |
        v                          v                           v
   S3: Input bucket          Bedrock (Claude‑Instant)    S3: Output bucket
        |                                                      |
        +-------------------+-------------------+--------------+
                            |                   |
                     DynamoDB (Job Table)   SNS (Notifications)
                            |
                      CloudWatch (Metrics/Logs)
```  

### 2.2 Functional Requirements Summary  

| # | Requirement | Description |
|---|-------------|-------------|
| **F‑01** | **Trigger Generation** | POST `/generate-spec` accepts a ZIP of source code and a JSON feature descriptor; returns a job‑ID. |
| **F‑02** | **Status Query** | GET `/job-status/{jobId}` returns job state (`Pending`, `Running`, `Succeeded`, `Failed`) and a presigned download URL if successful. |
| **F‑03** | **AI Spec Creation** | Lambda reads inputs, builds a Bedrock prompt, receives SRS/Functional Spec text, formats to Markdown and PDF. |
| **F‑04** | **Secure Temporary Storage** | Input archive and generated artefacts stored in encrypted S3 buckets with 24 h TTL. |
| **F‑05** | **Automatic Cleanup** | Cleanup Lambda deletes source archive (and optionally output) after TTL or on failure. |
| **F‑06** | **Notification** | SNS publishes success/failure messages containing job metadata and download URL (if any). |
| **F‑07** | **Metrics & Auditing** | CloudWatch captures processing time, success count, and error count; CloudTrail logs all API actions. |
| **F‑08** | **Scalability** | System can process up to 5 docs/day in PoC; design supports horizontal scaling to > 10 docs/day. |

### 2.3 Non‑Functional Requirements  

| Category | Requirement | Target |
|----------|-------------|--------|
| **Performance** | End‑to‑end latency ≤ 2 min per document (incl. LLM inference). | ≤ 120 000 ms |
| **Availability** | ≥ 99 % during business hours (08:00‑18:00 UTC). | 99 % |
| **Security** | SSE‑KMS encryption at rest, TLS 1.2 in transit, IAM least‑privilege, VPC endpoints. | ISO 27001 aligned |
| **Compliance** | Data residency in `eu‑west‑1`, auto‑delete ≤ 24 h, audit logs retained 30 days. | GDPR & ISO 27001 |
| **Scalability** | Stateless Lambdas, DynamoDB auto‑scales, S3 unlimited. | Horizontal scale |
| **Maintainability** | IaC via CDK, unit tests ≥ 80 % coverage, documentation in Confluence. | Code quality |
| **Cost** | ≤ $150 AWS spend for PoC. | Budget compliance |
| **Observability** | CloudWatch dashboards for `DocsGenerated`, `ProcessingTimeMs`, `FailedJobs`. | Real‑time monitoring |

### 2.4 Constraints and Assumptions  

| Constraint | Detail |
|------------|--------|
| **AWS‑only** | Only native AWS services (Bedrock, Lambda, Step Functions, S3, DynamoDB, SNS, KMS, CloudWatch). |
| **Stateless Lambdas** | No local file persistence; all state persisted externally. |
| **Timebox** | PoC must be delivered within 48 h from start. |
| **Data Size** | Input ZIP ≤ 50 MB (API Gateway limit). |
| **Region** | All resources in `eu‑west‑1` to satisfy data‑sovereignty. |
| **No external SaaS** | No third‑party APIs; Bedrock is the only external AI service. |
| **Free‑tier budget** | Design assumes free‑tier limits for Lambda, S3, DynamoDB; Bedrock usage monitored. |

---

## 3. Architecture Principles & Standards  

### 3.1 Design Principles  

| # | Principle | Statement |
|---|------------|-----------|
| **P‑01** | **Secure‑by‑Design** | All data encrypted, minimal IAM privileges, immutable audit trails. |
| **P‑02** | **Serverless‑First** | Prefer Lambda, Step Functions, S3, DynamoDB over managed servers. |
| **P‑03** | **AI‑Enabled Automation** | AI core (Bedrock) is the only point of human‑free decision making. |
| **P‑04** | **Reusability** | Build modular Service Building Blocks (SBB) that can be reused for other AI pipelines. |
| **P‑05** | **Observability** | Emit metrics, logs, and traces for every transaction. |
| **P‑06** | **Cost‑Efficiency** | Use the least expensive Bedrock model that meets quality; enable auto‑scaling only when needed. |
| **P‑07** | **Compliance Alignment** | Architecture must satisfy ISO 27001, GDPR, and AWS Well‑Architected Security pillar. |

### 3.2 Technology Standards  

| Domain | Standard |
|--------|----------|
| **Infrastructure as Code** | AWS CDK (TypeScript) ≥ v2, version‑controlled in Git. |
| **Runtime** | Python 3.11 for Lambda; compatible with Bedrock SDK. |
| **API Design** | OpenAPI 3.0, JSON‑Schema validation, versioning via `/v1/`. |
| **Logging** | Structured JSON logs sent to CloudWatch Logs; include `requestId`, `jobId`, `level`. |
| **Metrics** | CloudWatch custom namespace `DigitalWorkerFactory`. |
| **Security** | IAM policies use `aws:RequestedRegion` condition; KMS key policy restricts to service roles. |
| **Testing** | PyTest for unit tests, SAM local for integration, Postman collection for API smoke tests. |

### 3.3 Integration Standards  

| Layer | Standard |
|-------|----------|
| **API ↔ Lambda** | AWS Proxy integration (Lambda‑proxy). |
| **Lambda ↔ Bedrock** | AWS SDK `boto3` `bedrock-runtime` client, request/response JSON. |
| **Step Functions ↔ Lambda** | Input/Output passed as JSON; error handling via `Catch` blocks. |
| **S3 ↔ Lambda** | Use pre‑signed URLs for direct download; no public bucket exposure. |
| **SNS ↔ External** | Message format `application/json`; optional HTTPS subscription for Slack/Teams webhook. |
| **DynamoDB ↔ Lambda** | Single‑table design, PK=`JobId`, GSI on `Status`. |

### 3.4 Security Standards  

| Control | Implementation |
|----------|----------------|
| **Authentication** | API Gateway IAM auth (signed request) or Cognito‑User‑Pools (optional). |
| **Authorization** | IAM role per Lambda (`SourceLoaderRole`, `SpecGeneratorRole`, `CleanupRole`) with least‑privilege policies. |
| **Encryption at Rest** | SSE‑KMS with CMK `alias/digital-worker-key`. |
| **Encryption in Transit** | TLS 1.2 enforced by API Gateway and S3 VPC endpoints. |
| **Network Isolation** | VPC endpoints for S3, Bedrock; Lambda functions placed in private subnets. |
| **Audit Logging** | CloudTrail captures all S3/DynamoDB/Bedrock actions; logs retained 30 days. |
| **Threat Detection** | GuardDuty enabled; Lambda runtime scanning via Amazon Inspector (on‑demand). |
| **Data Retention** | S3 lifecycle rule: `Delete after 1 day`; DynamoDB TTL for completed jobs (`ExpiresAt`). |

---

## 4. High‑Level Architecture Design  

### 4.1 Architecture Pattern Selection  

| Pattern | Why Chosen |
|---------|------------|
| **Event‑Driven Serverless** | Decouples ingestion, AI processing, and cleanup; automatically scales with demand. |
| **Micro‑service (single purpose)** | Each Lambda has a single responsibility (loader, generator, cleaner). |
| **Command‑Query Responsibility Segregation (CQRS)** | Separate write path (job creation) from read path (status query) via DynamoDB. |
| **Circuit Breaker (within Step Functions)** | `Catch` blocks handle Bedrock failures and trigger compensation. |

### 4.2 System Architecture Overview  

* **API Layer** – Amazon API Gateway (REST, IAM auth).  
* **Orchestration Layer** – AWS Step Functions Standard workflow.  
* **Processing Layer** – Three Lambda functions (Source Loader, Spec Generator, Cleanup).  
* **AI Layer** – Amazon Bedrock (Claude‑Instant).  
* **Storage Layer** – Two S3 buckets (input, output) with KMS encryption; DynamoDB for job metadata.  
* **Notification Layer** – Amazon SNS topic `DigitalWorkerEvents`.  
* **Observability Layer** – CloudWatch Metrics, Logs, Alarms; CloudTrail for audit.  

### 4.3 Component Architecture  

| Component | Responsibility | Input | Output |
|-----------|----------------|-------|--------|
| **API Gateway** | Accepts HTTP requests, performs auth, forwards to Step Functions. | Multipart/form‑data (ZIP + JSON) | HTTP 202 + `jobId` |
| **Step Functions** | Coordinates workflow, retries, error handling. | `jobId` | Invokes Lambdas, updates DynamoDB. |
| **Source Loader Lambda** | Validates payload, writes ZIP & JSON to `digital-worker-input`. | Raw request body | S3 object keys stored in DynamoDB. |
| **Spec Generator Lambda** | Retrieves objects, builds prompt, calls Bedrock, formats result, writes output to `digital-worker-output`. | S3 keys (input) | PDF/MD object key, status = `Succeeded`/`Failed`. |
| **Cleanup Lambda** | Runs on a timer (24 h) or immediate on failure; deletes source ZIP and optionally output. | DynamoDB `ExpiresAt` | Deleted objects, audit log entry. |
| **DynamoDB Job Table** | Stores job metadata, status, timestamps, S3 keys. | – | Queryable by API for status. |
| **SNS Topic** | Publishes success/failure messages (jobId, URL, error). | Lambda publish call | Email/Webhook subscription. |
| **CloudWatch** | Captures custom metrics (`DocsGenerated`, `ProcessingTimeMs`, `FailedJobs`). | Lambda `put_metric_data` | Dashboard & alarms. |

### 4.4 Integration Architecture  

* **API ↔ Step Functions** – Direct integration via `StartExecution`.  
* **Step Functions ↔ Lambdas** – `Task` states, JSON input/output mapping.  
* **Lambda ↔ Bedrock** – AWS SDK call `invoke_model`; prompt includes source‑code excerpts and feature JSON.  
* **Lambda ↔ S3** – `boto3` `put_object`/`get_object` using VPC endpoint.  
* **Lambda ↔ DynamoDB** – `put_item`, `update_item`, `query` on `JobId`.  
* **Lambda ↔ SNS** – `publish` to `DigitalWorkerEvents`.  

---

## 5. Technology Stack Design  

### 5.1 Technology Selection Rationale  

| Layer | Technology | Why Chosen |
|-------|-------------|-----------|
| **Frontend (optional UI)** | Static HTML + vanilla JS (no framework) – served from S3 website bucket. | Minimal footprint for PoC, no extra compute. |
| **API** | Amazon API Gateway (REST) | Native serverless, request validation, IAM auth, throttling. |
| **Compute** | AWS Lambda (Python 3.11) | Pay‑per‑use, instant scaling, easy integration with AWS services. |
| **AI Engine** | Amazon Bedrock – Claude‑Instant (`anthropic.claude-v2:1`) | Cost‑effective, within‑region, no model training required. |
| **Orchestration** | AWS Step Functions (Standard) | Visual workflow, built‑in retries, error handling. |
| **Storage** | Amazon S3 (Standard‑IA) with SSE‑KMS | Infinite durability, lifecycle policies, encryption. |
| **Metadata DB** | Amazon DynamoDB (On‑Demand) | Low‑latency reads for status polling, auto‑scales, TTL support. |
| **Messaging** | Amazon SNS (Standard) | Simple pub/sub for notifications, integrates with email/webhook. |
| **Observability** | Amazon CloudWatch (Metrics/Logs) + AWS X‑Ray (optional) | End‑to‑end tracing, alarm definition. |
| **IaC** | AWS CDK (TypeScript) | Strong typing, reusable constructs, unit‑testable. |
| **Security** | AWS KMS, IAM, VPC endpoints, GuardDuty, CloudTrail | Full compliance coverage. |
| **CI/CD** | AWS CodePipeline + CodeBuild (Docker image for CDK) | Automated deployment on push to `main`. |

### 5.2 Technology Integration Approach  

* **Compatibility** – All services use the same AWS SDK version (boto3 1.34.x) in Python; CDK generates CloudFormation templates that are natively compatible.  
* **Integration Patterns** – Request‑Response (API ↔ Lambda), Event‑Driven (Step Functions → Lambda), Pub/Sub (Lambda → SNS).  
* **Risk Assessment** –  
  * *Bedrock model cost* – mitigated by using Claude‑Instant and limiting token count.  
  * *Lambda timeout* – set to 300 s (max) with retry logic in Step Functions.  
  * *S3 bucket exposure* – enforce block‑public‑access, use presigned URLs only.  

---

## 6. Detailed Component Design  

### 6.1 Frontend Components (optional)  

| Component | Description |
|-----------|-------------|
| **Upload Form** | HTML `<form>` with two file inputs (`archive.zip`, `descriptor.json`). Submits via `fetch` to `/generate-spec`. |
| **Status Panel** | Polls `/job-status/{jobId}` every 5 s, displays spinner, success/failure message, download button. |
| **Error Toasts** | Shows validation errors returned by API (e.g., file size > 50 MB). |
| **State Management** | Minimal – store `jobId` in browser `sessionStorage`. |
| **Accessibility** | ARIA labels on inputs, keyboard‑navigable, color contrast > 4.5:1. |

### 6.2 Backend Services Design  

| Service | Responsibility | Key Functions |
|---------|----------------|----------------|
| **Source Loader Lambda** | Validate payload, store files, create job record. | `validate_schema()`, `s3_put_object()`, `dynamodb_put_job()` |
| **Spec Generator Lambda** | Prompt construction, Bedrock call, formatting, output storage. | `build_prompt()`, `bedrock_invoke()`, `markdown_to_pdf()`, `s3_put_output()` |
| **Cleanup Lambda** | Time‑based deletion of source archive (and optionally output). | `dynamodb_query_expired()`, `s3_delete_object()`, `log_deletion()` |
| **Status API Lambda** (integrated via API Gateway) | Retrieve job state, generate presigned URL if success. | `dynamodb_get_job()`, `s3_generate_presigned_url()` |

*All Lambdas share a common utility layer (`utils/`): logging, error handling, KMS encryption helpers, and constants (bucket names, KMS key ARN).*

### 6.3 Integration Components  

| Component | Design Details |
|-----------|----------------|
| **API Gateway** | **REST** model, stage `dev` → `v1`; request validation schema for multipart/form‑data; throttling 10 TPS; IAM auth (signing v4). |
| **Step Functions** | **State Machine**: `ValidateInput` → `LoadSource` → `GenerateSpec` → `StoreOutput` → `NotifySuccess` → `ScheduleCleanup`. Each state has `Catch` that routes to `NotifyFailure` → `ScheduleCleanup`. |
| **Message Broker (SNS)** | Topic `DigitalWorkerEvents`; subscription options: email (for judges), HTTP endpoint (for future webhook). Message schema: `{jobId, status, url?, errorMessage}`. |
| **Event Handling** | Cleanup Lambda triggered by **EventBridge** rule `cron(0 * * * ? *)` (hourly) plus a **Step Functions** `Wait for 24h` state on success path. |

---

## 7. API Design Specifications  

### 7.1 API Architecture  

* **Versioning** – All endpoints under `/v1/`.  
* **Security** – IAM‑signed requests (`AWS4-HMAC`); optional Cognito token for external UI.  
* **Rate Limiting** – 10 requests / second per principal, configurable via API Gateway usage plans.  

### 7.2 API Specifications  

| Method | URI | Description | Request | Response | Errors |
|--------|-----|-------------|---------|----------|--------|
| **POST** | `/v1/generate-spec` | Submit source ZIP + feature JSON; starts job. | Multipart/form‑data: `archive` (ZIP), `descriptor` (JSON). | `202 Accepted` `{ "jobId": "<uuid>" }` | `400 Bad Request` (validation), `401 Unauthorized`, `413 Payload Too Large` |
| **GET** | `/v1/job-status/{jobId}` | Retrieve current status and (if ready) download URL. | – | `200 OK` `{ "jobId": "<uuid>", "status": "Pending|Running|Succeeded|Failed", "downloadUrl": "<presigned>", "errorMessage": "…" }` | `404 Not Found`, `401 Unauthorized` |
| **GET** | `/v1/health` | Liveness / readiness probe. | – | `200 OK` `{ "status": "OK" }` | – |

#### Request/Response Data Models (plain text)  

**GenerateSpecRequest**  
- `archive`: binary ZIP file (max 50 MB)  
- `descriptor`: JSON object adhering to schema: `{ "moduleName": "string", "features": [{ "id": "string", "description": "string" }], "version": "string" }`  

**JobStatusResponse**  
- `jobId`: UUID string  
- `status`: Enum (`Pending`, `Running`, `Succeeded`, `Failed`)  
- `downloadUrl` (optional): HTTPS presigned URL, expires in 24 h  
- `errorMessage` (optional): string  

**ErrorResponse**  
- `code`: HTTP status code  
- `message`: human‑readable description  
- `details` (optional): array of field‑level errors  

### 7.3 Authentication & Authorization  

| Mechanism | Details |
|-----------|---------|
| **IAM** | Caller must sign request with AWS Signature V4; IAM policy grants `execute-api:Invoke` on `/v1/*`. |
| **Cognito (optional)** | User pools for external UI; JWT in `Authorization: Bearer <token>`; API Gateway authorizer validates token. |
| **Scope** | No fine‑grained scopes; all authorized principals can create jobs and query their own jobs (jobId is opaque). |
| **Rate‑limit enforcement** | API Gateway usage plans + per‑principal throttling. |

---

## 8. Database Design  

### 8.1 Data Model Design  

#### Conceptual Model  

- **Job** (PK = JobId) – encapsulates the entire lifecycle.  
- **SourceAsset** – reference to the ZIP stored in input bucket.  
- **GeneratedAsset** – reference to PDF/Markdown stored in output bucket.  

#### Logical Model  

| Table | Partition Key | Sort Key | Attributes |
|-------|----------------|----------|------------|
| **DigitalWorkerJobs** | `JobId` (String UUID) | `Metadata` (static) | `Status`, `SubmitTime`, `StartTime`, `EndTime`, `InputKey`, `OutputKey`, `PresignedUrl`, `ErrorMessage`, `ExpiresAt` (TTL) |

#### Physical Considerations  

- **Capacity Mode** – On‑Demand (auto‑scales, no RCUs/WCUs planning).  
- **TTL** – `ExpiresAt` set to `SubmitTime + 30 days` for audit retention.  
- **Indexes** – Global Secondary Index `StatusIndex` (PK = `Status`) for cleanup queries.  

### 8.2 Database Schema Design  

| Attribute | Type | Description | Index |
|----------|------|-------------|-------|
| `JobId` | String (UUID) | Primary identifier. | PK |
| `Status` | String (enum) | `Pending`, `Running`, `Succeeded`, `Failed`. | GSI `StatusIndex` |
| `SubmitTime` | Number (epoch ms) | When API received request. | – |
| `StartTime` | Number (epoch ms) | When generation started (Step Functions). | – |
| `EndTime` | Number (epoch ms) | When job completed. | – |
| `InputKey` | String | S3 object key in input bucket. | – |
| `OutputKey` | String | S3 object key in output bucket (PDF/MD). | – |
| `PresignedUrl` | String | Temporary URL (valid 24 h). | – |
| `ErrorMessage` | String | Populated on failure. | – |
| `ExpiresAt` | Number (epoch) | TTL for automatic expiry. | – |

### 8.3 Data Integration Design  

| Process | Source | Target | Transformation |
|---------|--------|--------|----------------|
| **Job Creation** | API request | DynamoDB `DigitalWorkerJobs` | Insert with `Status=Pending`, compute `ExpiresAt`. |
| **Status Update** | Step Functions → Lambda | DynamoDB `Status` attribute | Atomic `UpdateItem` with condition expression. |
| **Cleanup Query** | EventBridge (hourly) | DynamoDB `Status=Succeeded` & `EndTime+24h <= now` | Scan via GSI, then invoke Cleanup Lambda. |
| **Quality Checks** (future) | Generated PDF/MD | S3 → Lambda validation function | Parse Markdown, verify required sections, write result to DynamoDB `QualityScore`. |
| **Audit Export** | DynamoDB (TTL) | Amazon S3 (CSV) via Data Export Job (optional) | Export daily snapshot for compliance. |

---

## 9. Processing Flow Design  

### 9.1 Core Business Flows  

1. **Job Submission** – Client POST `/generate-spec`. API validates, stores payload to input bucket, creates DynamoDB record, starts Step Functions execution.  
2. **Source Loading** – `SourceLoader` Lambda validates schema, writes objects, updates job status to `Running`.  
3. **Specification Generation** – `SpecGenerator` Lambda retrieves source, builds prompt, calls Bedrock, receives spec text, converts to Markdown → PDF, stores output, updates job status to `Succeeded`.  
4. **Notification** – On success/failure, Step Functions publishes to SNS; success includes presigned URL.  
5. **Cleanup Scheduling** – Step Functions adds a `Wait 24h` state; after wait, `Cleanup` Lambda deletes source ZIP (and optionally output).  

#### Exception Handling  

* **Bedrock Failure** – `Catch` redirects to `NotifyFailure` → `ScheduleCleanup`.  
* **Validation Error** – Immediate `Fail` state; job status set to `Failed`; no cleanup needed (input not stored).  
* **Timeout** – Lambda timeout triggers Step Functions `Catch` → `NotifyFailure`.  

### 9.2 System Integration Flows  

| Flow | Trigger | Components Involved | Data Movement |
|------|---------|--------------------|---------------|
| **API → Step Functions** | HTTP POST | API GW → Step Functions `StartExecution` | JobId passed as execution input. |
| **Step Functions → Lambda** | State transition | SF Task → Lambda (Loader/Generator/Cleaner) | JSON payload via `InputPath`. |
| **Lambda → Bedrock** | Prompt call | SpecGenerator Lambda → Bedrock `invoke_model` | Prompt string, receives generated spec text. |
| **Lambda ↔ S3** | File IO | Loader/Generator/Cleaner → S3 (PUT/GET/DELETE) | Binary ZIP, Markdown, PDF. |
| **Lambda ↔ DynamoDB** | Metadata CRUD | All Lambdas → DynamoDB `PutItem/UpdateItem/GetItem` | Job record updates. |
| **Lambda → SNS** | Notification | Generator/Cleaner → SNS `Publish` | JSON message with status & URL. |
| **EventBridge → Cleanup** | Hourly schedule + 24 h wait | EventBridge → Cleanup Lambda | Queries DynamoDB for expired jobs. |

---

## 10. Module Design Specifications  

### 10.1 Core Modules  

| Module | Entry Point | Key Functions | Interfaces |
|--------|------------|----------------|------------|
| **Auth Module** | API Gateway authorizer | IAM signature verification, optional Cognito JWT validation. | API Gateway |
| **Job Management** | `job_handler.py` (Lambda) | `create_job()`, `update_status()`, `fetch_status()`. | DynamoDB, API GW |
| **Source Loader** | `source_loader.py` | `validate_payload()`, `store_to_s3()`. | S3, DynamoDB |
| **Spec Generator** | `spec_generator.py` | `build_prompt()`, `invoke_bedrock()`, `format_output()`, `store_output()`. | Bedrock, S3, DynamoDB |
| **Cleanup Worker** | `cleanup_worker.py` | `find_expired_jobs()`, `delete_s3_objects()`. | DynamoDB, S3, CloudWatch |
| **Notification Service** | `notify.py` | `publish_success()`, `publish_failure()`. | SNS |

### 10.2 Integration Modules  

| Module | Purpose | External Dependency |
|--------|---------|----------------------|
| **API Gateway Integration** | HTTP entry, request validation, throttling. | API GW |
| **Step Functions State Machine** | Orchestration, retries, compensation. | AWS Step Functions |
| **EventBridge Scheduler** | Hourly trigger for cleanup, 24 h wait state. | EventBridge |
| **SNS Subscription** | Deliver notifications to email/webhook. | SNS |

---

## 11. Infrastructure Design  

### 11.1 Deployment Architecture  

| Environment | Resources | Isolation |
|------------|-----------|-----------|
| **Development** | Full CDK stack deployed in AWS account `fhm-dev`; VPC with private subnets for Lambdas, public S3 static website for UI. | Separate AWS account, IAM roles distinct from prod. |
| **Testing** | Same stack with `dev` parameters but isolated DynamoDB table (`DigitalWorkerJobs-test`). | Parameter overrides. |
| **Production** | Stack deployed in `fhm-prod` account, VPC isolated, using dedicated KMS CMK, SNS topic with production email list. | Strict IAM, GuardDuty enabled. |

### 11.2 Infrastructure Components  

| Component | Size/Configuration | Reason |
|-----------|---------------------|--------|
| **VPC** | Single VPC `10.0.0.0/16`, private subnets `10.0.1.0/24` & `10.0.2.0/24`. | Enables VPC endpoints, isolates Lambdas. |
| **VPC Endpoints** | S3, Bedrock (private DNS). | No internet egress, data stays in region. |
| **Lambda Functions** | Memory 256 MB (loader) → 1024 MB (generator), timeout 300 s, reserved concurrency 5. | Sufficient for Bedrock latency, prevents cold‑start burst. |
| **S3 Buckets** | `digital-worker-input` (Standard‑IA), `digital-worker-output` (Standard‑IA). Both with `BlockPublicAccess`, `Versioning` disabled, `Lifecycle` delete after 1 day. |
| **DynamoDB** | On‑Demand, point‑in‑time recovery enabled, TTL on `ExpiresAt`. |
| **SNS Topic** | `DigitalWorkerEvents` – no DLQ for PoC, future DLQ optional. |
| **CloudWatch** | Log groups per Lambda, metric filter for errors, dashboard `DigitalWorkerFactory`. |
| **IAM Roles** | `SourceLoaderRole`, `SpecGeneratorRole`, `CleanupRole`, `APIGatewayExecutionRole`. Each role has explicit `s3:PutObject`, `dynamodb:UpdateItem` etc. |
| **KMS Key** | Customer‑managed CMK `alias/digital-worker-key` with rotation enabled. |
| **CodePipeline** | Source (GitHub) → Build (CodeBuild – CDK synth & deploy) → Deploy (CloudFormation). |
| **Monitoring** | CloudWatch Alarms on `ProcessingTimeMs > 120 s` and `FailedJobs > 0`. |

### 11.3 DevOps Design  

| Stage | Tool | Artifact |
|-------|------|----------|
| **Source Control** | GitHub (main branch) | CDK code, Lambda source, OpenAPI spec. |
| **Build** | AWS CodeBuild (Docker image `aws/codebuild/standard:6.0`) | Synthesized CloudFormation template. |
| **Deploy** | AWS CodePipeline → CloudFormation Stack Set | Environments `dev`, `prod`. |
| **Testing** | SAM local for Lambda unit tests; Postman collection for API integration. |
| **Static Analysis** | Bandit (security), Pylint (style), cfn‑nag (CFN security). |
| **Rollback** | CloudFormation stack rollback on failure; versioned S3 bucket for artefacts. |
| **Secrets Management** | AWS Secrets Manager (if future API keys needed), otherwise KMS for CMK. |

---

## 12. Security Architecture Design  

### 12.1 Security Framework  

| Layer | Controls |
|-------|----------|
| **Identity & Access Management** | IAM roles per Lambda, least‑privilege policies, API Gateway IAM auth, optional Cognito for UI. |
| **Network** | VPC with private subnets, VPC endpoints for S3 & Bedrock, no Internet gateway for Lambdas. |
| **Data Protection** | SSE‑KMS on S3, TLS 1.2 for all data in‑flight, encrypted environment variables (AWS KMS). |
| **Logging & Monitoring** | CloudTrail (all API calls), CloudWatch Logs (structured JSON), GuardDuty alerts. |
| **Compliance** | ISO 27001 Annex A.8 (encryption), GDPR (region‑locked data, 24 h purge). |
| **Incident Response** | Automated SNS alarm to Security Ops on `FailedJobs` > 0, CloudWatch alarm on unusual S3 delete activity. |
| **Patch Management** | Lambda runtime automatically updated by AWS; CDK version pinning. |

### 12.2 Security Implementation  

| Control | Implementation Detail |
|----------|------------------------|
| **IAM Policies** | `SourceLoaderRole` – `s3:PutObject` on `digital-worker-input/*`, `dynamodb:PutItem` on `DigitalWorkerJobs`. `SpecGeneratorRole` – `s3:GetObject` on input, `s3:PutObject` on output, `bedrock:InvokeModel`, `dynamodb:UpdateItem`. |
| **KMS CMK** | Alias `digital-worker-key`; key policy allows only the three Lambda roles and the CloudTrail service. |
| **S3 Bucket Policies** | Deny any `s3:GetObject` unless request comes from VPC endpoint; `s3:DeleteObject` allowed only for `CleanupRole`. |
| **API Gateway Authorizer** | IAM authorizer; optional Cognito user pool for external UI with scopes `digitalworker:generate`. |
| **Step Functions State Machine** | `LoggingConfiguration` enabled, logs to CloudWatch; `TracingConfiguration` (X‑Ray) optional for deep diagnostics. |
| **GuardDuty** | Enabled at account level; alerts routed to SNS `SecurityAlerts`. |
| **Encryption in Transit** | All SDK calls use HTTPS; API Gateway enforces TLS 1.2. |
| **Audit Trail** | CloudTrail logs exported to a dedicated S3 bucket with immutable retention (30 days). |
| **Data Retention Enforcement** | S3 lifecycle rule `Expiration: 1 day`; DynamoDB TTL for job records (30 days). |

---

## 13. Performance & Scalability Design  

### 13.1 Performance Architecture  

| Requirement | Design Feature |
|-------------|-----------------|
| **Latency ≤ 2 min** | Lambda timeout 300 s, Bedrock model selected for fastest inference, warm‑up via provisioned concurrency (optional). |
| **Cold‑Start Minimisation** | Use Python runtime, keep deployment package < 50 MB, enable **Provisioned Concurrency** for generator Lambda (5 concurrent) in prod. |
| **Caching** | Not required for PoC; future version could cache common prompt fragments in DynamoDB. |
| **Throughput** | API Gateway throttling 10 TPS per principal; DynamoDB on‑demand scales automatically. |
| **Cost Optimisation** | Use Free‑Tier S3/CloudWatch, Bedrock `Claude‑Instant` (lowest price per token). |

### 13.2 Scalability Design  

| Dimension | Scaling Mechanism |
|-----------|-------------------|
| **Compute** | Lambda auto‑scales; reserved concurrency caps to protect downstream Bedrock quota. |
| **Storage** | S3 unlimited, DynamoDB on‑demand scales with request volume. |
| **Message** | SNS standard topic unlimited subscribers. |
| **Orchestration** | Step Functions Standard can handle > 10 k concurrent executions; limit set via service quota if needed. |
| **Horizontal Scaling** | Additional generator Lambdas can be deployed in parallel (different alias versions) to increase throughput. |
| **Load Distribution** | API Gateway automatically distributes incoming requests across regional edge locations. |

---

## 14. Implementation Strategy  

### 14.1 Development Approach  

| Phase | Activities | Owner | Duration |
|-------|------------|-------|----------|
| **Setup** | Create AWS accounts, CI/CD pipeline, CDK repo. | DevOps | 4 h |
| **Infrastructure** | Write CDK stack (VPC, buckets, DynamoDB, Step Functions, IAM). | Architect / DevOps | 8 h |
| **Lambda Development** | Implement Source Loader, Spec Generator (prompt engineering), Cleanup. | Backend Engineers | 12 h |
| **API Layer** | Define OpenAPI spec, configure API GW authorizer, test with Postman. | API Engineer | 4 h |
| **Observability** | CloudWatch dashboards, alarms, structured logging. | Ops | 2 h |
| **Security Hardening** | Apply KMS, VPC endpoints, bucket policies, audit logs. | Security Champion | 2 h |
| **Testing** | Unit tests, integration tests, end‑to‑end PoC run (2 modules). | QA | 4 h |
| **Demo Preparation** | Build presentation script, record video, collect metrics. | Product Owner | 2 h |
| **Rollback & Cleanup** | Verify cleanup Lambda works, test 24 h expiry (fast‑forward). | DevOps | 2 h |
| **Total** | – | – | **48 h** (2 days) |

### 14.2 Deployment Strategy  

| Step | Action | Tool |
|------|--------|------|
| **1** | Push CDK code to `main` branch. | GitHub |
| **2** | CodePipeline triggers, CodeBuild synthesises CloudFormation. | AWS CodePipeline |
| **3** | CloudFormation creates/updates stack (`DigitalWorkerFactory-dev`). | CloudFormation |
| **4** | Smoke test API via Postman collection. | Postman |
| **5** | Promote to `prod` after judges sign‑off – manual approval in pipeline. | CodePipeline (manual stage) |
| **6** | Blue‑Green switch (if needed) – create new version of Step Functions, update API GW stage alias. | API GW stage variables |
| **Rollback** | If deployment fails, CloudFormation auto‑rolls back; previous Lambda versions remain accessible. | CloudFormation |

---

## 15. Quality Assurance Framework  

### 15.1 Testing Strategy  

| Test Type | Scope | Tools |
|-----------|-------|-------|
| **Unit Tests** | Lambda functions (payload validation, prompt builder, S3 helpers). | PyTest, coverage ≥ 80 % |
| **Integration Tests** | End‑to‑end flow: POST → Step Functions → output PDF. | SAM local + Docker, Postman collection |
| **Performance Tests** | Measure processing latency under load (5 concurrent jobs). | Locust or Artillery (run against API GW) |
| **Security Tests** | IAM policy simulation, S3 bucket policy validation, token leakage. | IAM Access Analyzer, `aws policies simulate-principal-policy` |
| **Compliance Checks** | Verify KMS encryption, TTL, audit log presence. | AWS Config rules (`s3-bucket-server-side-encryption`, `dynamodb-point-in-time-recovery-enabled`) |
| **User Acceptance** | Judges review generated docs against quality checklist. | Manual review, score sheet. |

### 15.2 Quality Gates  

| Gate | Criteria | Enforcer |
|------|----------|----------|
| **Code Review** | All PRs approved by at least one senior engineer + Security Champion. | GitHub |
| **Static Analysis** | No high‑severity findings from Bandit, cfn‑nag, Pylint. | CI pipeline |
| **Test Coverage** | ≥ 80 % unit, ≥ 70 % integration. | CI pipeline (fail on lower) |
| **Performance** | 95 % of runs ≤ 2 min latency. | Load test report |
| **Security** | No open S3 bucket, KMS keys attached, IAM least‑privilege. | AWS Config compliance report |
| **Approval** | Architecture Review Board sign‑off before prod deploy. | ARB meeting minutes |

---

## 16. Risk Assessment & Mitigation  

### 16.1 Technical Risks  

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| **Bedrock quota exhaustion** | Jobs fail, SLA breach. | Implement throttling in Step Functions, request higher quota early. |
| **Prompt hallucination → inaccurate specs** | Low quality, judge penalty. | Add post‑generation validation rules; iterate prompt library; human reviewer fallback. |
| **Lambda cold start latency** | Increased latency > 2 min. | Use provisioned concurrency for generator Lambda in prod; keep package small. |
| **S3 lifecycle mis‑configuration** | Source code retained > 24 h → compliance breach. | Enable CloudFormation‑driven lifecycle rule; test with automated delete validation. |
| **IAM over‑privilege** | Potential data leak. | Run IAM Access Analyzer, enforce least‑privilege policies, peer review. |

### 16.2 Contingency Plans  

* **Bedrock failure** – Switch to fallback model `Claude‑v1` (still within AWS).  
* **Unexpected cost spike** – Enable AWS Budgets alerts at 80 % of $150; automatically disable Bedrock calls via Lambda environment flag.  
* **Source‑code leakage** – Immediate manual purge via S3 console; incident response run‑book executed.  

---

## 17. Implementation Roadmap  

### 17.1 Phase Planning  

| Phase | Duration | Milestones |
|-------|----------|------------|
| **Phase 0 – Foundations** | 0.5 day | AWS accounts, IAM baseline, CI/CD pipeline set up. |
| **Phase 1 – Infrastructure** | 0.5 day | CDK stack deployed (VPC, buckets, DynamoDB, Step Functions). |
| **Phase 2 – Core Logic** | 1 day | Lambda functions coded, prompt library completed, unit tests passing. |
| **Phase 3 – Integration & API** | 0.5 day | API GW configured, OpenAPI spec published, end‑to‑end test passes. |
| **Phase 4 – Security & Compliance** | 0.25 day | KMS policies, S3 lifecycle, GuardDuty enabled, audit logs verified. |
| **Phase 5 – Performance & Scaling** | 0.25 day | Load test runs, provisioned concurrency set, CloudWatch alarms configured. |
| **Phase 6 – Demo & Handover** | 0.25 day | Demo video, documentation uploaded, sign‑off collected. |

### 17.2 Resource Requirements  

| Role | Count | Skills |
|------|-------|--------|
| **Solution Architect** | 1 | TOGAF, AWS architecture, security. |
| **Backend Engineer** | 2 | Python, Lambda, Bedrock prompt engineering, CDK. |
| **DevOps Engineer** | 1 | CI/CD (CodePipeline), IAM, VPC, monitoring. |
| **QA Engineer** | 1 | Testing frameworks, performance testing, quality checklist. |
| **Security Champion** | 1 (part‑time) | ISO 27001, KMS, audit. |
| **Product Owner / Judge Liaison** | 1 | Requirements, demo coordination. |

---

## 18. Appendices  

### 18.1 Technology Evaluation Matrix  

| Technology | Cost | Maturity | Fit for PoC | Comments |
|------------|------|----------|-------------|----------|
| **Amazon Bedrock – Claude‑Instant** | $0.0008 per 1k tokens (approx.) | GA | ✔︎ | Cheapest LLM, suitable for short specs. |
| **AWS Lambda** | Pay‑per‑invocation (free tier) | GA | ✔︎ | Serverless, aligns with constraints. |
| **AWS Step Functions** | $0.025 per 1,000 state transitions | GA | ✔︎ | Orchestration, retries, compensation. |
| **Amazon S3** | $0.023 per GB‑month (Standard‑IA) | GA | ✔︎ | Durable storage, lifecycle rules. |
| **Amazon DynamoDB** | $0.25 per WCU/RCU (on‑demand) | GA | ✔︎ | Low‑latency metadata store. |
| **Amazon SNS** | $0.50 per 1 M publishes | GA | ✔︎ | Simple notification channel. |
| **AWS CDK** | Open source | GA | ✔︎ | IaC, ties to AWS well‑architected. |

### 18.2 Architecture Decision Records (ADRs)  

| ADR # | Decision | Alternatives Considered | Rationale |
|------|----------|------------------------|-----------|
| **ADR‑01** | Use **Claude‑Instant** over **Titan** or **Claude‑2** | Titan (higher cost), Claude‑2 (higher latency) | Cost‑effective while meeting quality; prompt engineering mitigates capability gap. |
| **ADR‑02** | **Step Functions Standard** over **Express** | Express (cheaper, limited execution time) | Need > 5 min timeout for potential retries; Standard supports longer runs and visual debugging. |
| **ADR‑03** | **S3 Lifecycle** vs **Lambda scheduled deletion** | Lambda‑only cleanup (more code) | Lifecycle is native, zero‑code, guaranteed; Lambda retained for immediate failure cleanup. |
| **ADR‑04** | **API Gateway IAM auth** vs **Custom authorizer** | Cognito, Lambda authorizer | IAM is native, no extra code; sufficient for PoC. Future UI may add Cognito. |
| **ADR‑05** | **Provisioned Concurrency** vs **Cold start** | Pure on‑demand (cheaper) | PoC tolerates cold start; production will enable provisioned concurrency for latency SLA. |

### 18.3 Reference Architectures  

* **AWS Serverless Application Model (SAM) – CI/CD pipeline** – used as baseline for CDK conversion.  
* **AI‑Driven Document Generation Blueprint** – internal FHM reference for prompt design.  

### 18.4 Detailed Specifications (excerpt)  

**Prompt Template (Markdown)**  

```
You are a technical writer for a .NET e‑commerce platform. 
Given the following source‑code snippets (up to 200 lines each) and a JSON feature description, produce a Software Requirements Specification (SRS) section that includes:

1. Overview
2. Functional Requirements (use numbered list)
3. Non‑Functional Requirements (performance, security)
4. Data Model (if applicable)
5. API Endpoints (if any)

Follow the template below and keep the total length ≤ 3000 words.

[Insert source snippets here]

[Insert feature JSON here]
```

**Lambda Environment Variables**  

| Variable | Description |
|----------|-------------|
| `INPUT_BUCKET` | Name of the S3 bucket for source archives. |
| `OUTPUT_BUCKET` | Name of the S3 bucket for generated docs. |
| `KMS_KEY_ARN` | ARN of the CMK used for SSE‑KMS. |
| `BEDROCK_MODEL_ID` | Bedrock model identifier (`anthropic.claude-v2:1`). |
| `MAX_TOKENS` | Max tokens for Bedrock response (e.g., `4000`). |
| `JOB_TABLE` | DynamoDB table name. |

**CloudWatch Dashboard Widgets**  

| Widget | Metric |
|--------|--------|
| **DocsGenerated** | Sum of `DigitalWorkerFactory DocsGenerated` (1‑hour period). |
| **ProcessingTimeMs** | Average of `ProcessingTimeMs`. |
| **FailedJobs** | Count of `FailedJobs`. |
| **Lambda Errors** | Sum of `Errors` for each Lambda function. |
| **Bedrock Cost** | Custom metric (tokens × price) – optional. |

---  

**End of Document**.