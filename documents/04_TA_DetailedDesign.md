# Technical Architecture Design Document  

## 1. Executive Summary  

### 1.1 Purpose  
This document translates every **Functional Requirement (FR)** and **User Story (US)** from the Business Requirements Document (BRD) into a concrete, AWS‑native technical design that aligns 100 % with the **Solution Architecture (SA)** described in *Solution Architecture Design Document* (SA Sections 1‑9). It provides the blueprint for developers, DevOps, and security engineers to implement the **AI Digital Worker Factory** within the 48‑hour PoC window of the FHM Hackathon Q4.  

### 1.2 Scope  
* Scope covers the design of all API endpoints, Lambda functions, Step Functions workflow, data models (DynamoDB & S3), monitoring, security controls, and CI/CD pipelines required to satisfy **FR‑01 – FR‑08** and **US‑001 – US‑005**.  
* Out‑of‑scope: multi‑region replication, downstream integration with Confluence, and paid‑tier Bedrock model upgrades (future phases).  

### 1.3 Architecture Alignment Overview  

| SA Section | What it Provides | How It Is Consumed by the Design |
|------------|------------------|-----------------------------------|
| **SA 2.1 (System Context Diagram)** | High‑level component map (API GW → Step Functions → Lambdas → Bedrock ↔ S3/DynamoDB/SNS) | All FRs reference these same components; the design never deviates from the diagram. |
| **SA 3 (Key Design Decisions)** | Choice of Claude‑Instant, SSE‑KMS, Standard Step Functions, CDK IaC | Each FR‑specific Lambda uses the Bedrock model, KMS‑encrypted S3 buckets, and CDK‑generated IAM roles. |
| **SA 4 (Technology Standards)** | Runtime (Python 3.11), API style (OpenAPI 3.0), logging format (JSON) | All API contracts, Lambda code, and CloudWatch metrics follow these standards. |
| **SA 5 (Infrastructure Components)** | VPC with endpoints, KMS CMK, lifecycle policies, CloudWatch alarms | Security and observability aspects of every FR implement these resources. |
| **SA 9 (Implementation Strategy)** | 48‑hour phased plan, CI/CD via CodePipeline, automated tests | The roadmap and deployment model below mirror this strategy. |

---  

## 2. Technical Design Principles  

### 2.1 Design Principles from SA  

| # | Principle (SA) | Application in This Design |
|---|----------------|----------------------------|
| **P‑01 (Secure‑by‑Design)** | Encryption‑at‑rest, IAM least‑privilege, VPC endpoints | All S3 buckets use SSE‑KMS, Lambda roles grant only needed actions, Bedrock accessed via VPC endpoint. |
| **P‑02 (Serverless‑First)** | No EC2; Lambda + Step Functions | Every FR is implemented as a Lambda or Step Functions state. |
| **P‑03 (AI‑Enabled Automation)** | Bedrock core for text generation | FR‑01/FR‑02/FR‑03 use Claude‑Instant via `bedrock-runtime`. |
| **P‑04 (Reusability)** | Service‑building blocks (SBB) | “Source Loader”, “Spec Generator”, and “Cleanup” Lambdas are reusable SBBs. |
| **P‑05 (Observability)** | CloudWatch metrics, X‑Ray tracing | FR‑07 defines custom metrics; all Lambdas emit JSON logs & trace IDs. |
| **P‑06 (Cost‑Efficiency)** | Use cheapest Bedrock model, free‑tier services | Claude‑Instant selected; Lambda memory tuned to 256 – 1024 MB to avoid over‑provisioning. |
| **P‑07 (Compliance)** | ISO 27001, GDPR, data‑residency | All resources deployed in `eu‑west‑1`, KMS keys retain audit logs, S3 lifecycle = 24 h. |

### 2.2 Technical Standards  

| Domain | Standard |
|--------|----------|
| **Infrastructure as Code** | AWS CDK (TypeScript) v2 – all SA resources declared in `infra/` |
| **Runtime** | Python 3.11 for Lambdas (managed layers) |
| **API** | OpenAPI 3.0, JSON‑Schema validation via API Gateway |
| **Logging** | Structured JSON (`{timestamp, requestId, jobId, level, message}`) to CloudWatch |
| **Metrics** | Custom namespace `DigitalWorkerFactory` (see FR‑07) |
| **Security** | IAM role‑based access, KMS CMK `alias/digital-worker-key`, VPC endpoints for S3 & Bedrock |
| **Testing** | PyTest ≥ 80 % coverage, SAM‑local integration, Postman collection for API contract |
| **Packaging** | Lambda zip ≤ 50 MB (API Gateway payload limit) |

### 2.3 Design Patterns Applied  

| Pattern | Where Used |
|---------|------------|
| **Command‑Query Separation** | `POST /generate-spec` (command) vs `GET /job-status/{id}` (query) |
| **Circuit Breaker (SF)** | Step Functions `Catch` blocks route Bedrock failures to `NotifyFailure` |
| **Compensation Transaction** | `Cleanup` Lambda acts as compensating action for any failure |
| **Factory Method** | Spec Generator Lambda builds the Bedrock prompt based on module type |
| **Observer** | SNS topic `DigitalWorkerEvents` notifies external subscribers |
| **Adapter** | Lambda adapters translate Bedrock JSON response into Markdown → PDF |
| **Builder** | Prompt Builder utility assembles source‑code snippets + feature JSON into final prompt text |

---  

## 3. Functional Requirement to Technical Design Mapping  

Below each FR (FR‑01 – FR‑08) we list the linked US, provide an overview, component breakdown, API contracts, data model, business flow, integration points, NFR implementation, error handling, and testing.  

---  

### 3.1 FR‑01: **Spec Generation**  

**Business Requirement:**  
*The system shall automatically generate technical specifications (SRS/Functional Spec) from a NopCommerce source‑code package and a JSON feature descriptor.* → **BR‑001**  

**Linked User Stories:**  
- **US‑001** – “Generate spec via POST /generate‑spec”.  

#### 3.1.1 Technical Design Overview  
| Item | Detail |
|------|--------|
| **Purpose** | Transform source‑code + feature JSON into a high‑quality spec using Claude‑Instant. |
| **Architecture Layer** | *Application Layer* (Lambda SpecGenerator) & *AI Layer* (Bedrock). |
| **SA Components Used** | Step Functions (Standard), Lambda (SpecGenerator), Bedrock (Claude‑Instant), S3 Input/Output Buckets, DynamoDB Job Table, IAM Role `SpecGeneratorRole` (SA 5.2). |
| **Trigger** | Step Functions state “GenerateSpec”. |

#### 3.1.2 Component Design  

| Frontend Components | Not required for PoC (API‑first).  Future UI may use React component *SpecUploader*. |
|----------------------|--------------------------------------------------------------|

| Backend Components | Type | Responsibility | Technology | SA Reference |
|-------------------|------|----------------|------------|--------------|
| **SpecGenerator Lambda** | Compute | Load source & descriptor, build prompt, invoke Bedrock, format Markdown & PDF, store output | Python 3.11, `boto3` Bedrock client, `markdown2` + `pdfkit` | SA 5.2 (Lambda) |
| **PromptBuilder (library)** | Helper | Assemble prompt from templates, inject code snippets (≤ 200 lines) | Python module, Jinja2 | SA 4 (Tech Standards) |
| **Bedrock Client Wrapper** | Integration | Call `invoke_model`, enforce token limits, retry logic | `boto3` `bedrock-runtime` | SA 3 (Key Decision – Claude‑Instant) |

| Data Components | Type | Responsibility | Technology | SA Reference |
|----------------|------|----------------|------------|--------------|
| **Job Table (DynamoDB)** | Entity | Stores `JobId`, status, S3 keys, timestamps | On‑Demand, PK=`JobId` | SA 5.1 (DynamoDB) |
| **Input Bucket (`digital-worker-input`)** | Object Store | Holds ZIP & JSON, SSE‑KMS | S3 Standard‑IA, lifecycle 1 day | SA 5.1 (S3) |
| **Output Bucket (`digital-worker-output`)** | Object Store | Holds generated Markdown & PDF, SSE‑KMS | S3 Standard‑IA, lifecycle 1 day | SA 5.1 (S3) |

#### 3.1.3 Detailed Technical Specification  

**API Design** – The API contract is defined in **US‑001** (see section 3.5) and does **not** directly invoke this Lambda; Step Functions does.  

**Data Model (DynamoDB Job Item)**  

```
Table: DigitalWorkerJobs
PK: jobId (UUID)
Attributes:
  - status (String)                // Pending|Running|Succeeded|Failed
  - submitTime (Number)            // epoch ms
  - startTime (Number)             // epoch ms (when SpecGenerator starts)
  - endTime (Number)               // epoch ms (when done)
  - inputKey (String)              // s3://digital-worker-input/<jobId>/archive.zip
  - descriptorKey (String)          // s3://digital-worker-input/<jobId>/descriptor.json
  - outputKey (String)              // s3://digital-worker-output/<jobId>/spec.pdf
  - latencyMs (Number)              // endTime - startTime
  - errorMessage (String, nullable)
  - expiresAt (Number)              // TTL = submitTime + 86400 000
GSI: status-index (PK = status)
```

**Business Logic Flow**  

1. **Step Functions** passes `jobId` & S3 keys to **SpecGenerator**.  
2. Lambda fetches ZIP & JSON from Input Bucket (via VPC endpoint).  
3. Extracts *up to 5* top‑level code files (≤ 200 lines each).  
4. Calls **PromptBuilder** → returns final prompt string.  
5. Invokes **Bedrock** (`anthropic.claude-v2:1`) with `max_tokens=4000`.  
6. Receives raw spec text; validates that required sections exist (regex check).  
7. Converts to Markdown, then PDF (`pdfkit` + wkhtmltopdf).  
8. Stores both artefacts in Output Bucket using SSE‑KMS.  
9. Updates DynamoDB `status = Succeeded`, records `outputKey`, `latencyMs`.  
10. Emits CloudWatch custom metric `DocsGenerated` (value = 1).  
11. Returns control to Step Functions which triggers **NotifySuccess** (SNS).  

**Integration Points**  

| Internal | From → To | Protocol |
|----------|-----------|----------|
| Step Functions → SpecGenerator Lambda | State input JSON | AWS SDK (invocation) |
| SpecGenerator → Bedrock | Prompt → `invoke_model` | HTTPS (VPC endpoint) |
| SpecGenerator → S3 (input & output) | `put_object` / `get_object` | HTTPS (VPC endpoint) |
| SpecGenerator → DynamoDB | `update_item` | AWS SDK |
| SpecGenerator → SNS (NotifySuccess) | `publish` | AWS SDK |

**Non‑Functional Requirements Implementation**  

| NFR | Implementation |
|-----|----------------|
| **Performance (≤ 2 min)** | Lambda memory tuned to 1024 MB; `boto3` client kept warm via provisioned concurrency (2 concurrent) in PoC; Bedrock prompt limited to 2000 tokens. |
| **Security (SSE‑KMS, IAM)** | IAM role `SpecGeneratorRole` includes only `s3:GetObject`, `s3:PutObject`, `dynamodb:UpdateItem`, `bedrock:InvokeModel`. KMS CMK `alias/digital-worker-key` enforces audit logging. |
| **Scalability** | Stateless Lambda; Step Functions handles concurrent executions; DynamoDB on‑demand auto‑scales. |
| **Observability** | Emits `ProcessingTimeMs`, `DocsGenerated`, `FailedJobs`; logs include `requestId`, `jobId`. |
| **Compliance** | All resources deployed in `eu-west-1`; S3 lifecycle 1 day; DynamoDB TTL 30 days. |

**Error Handling & Validation**  

| Error Type | HTTP Code (if bubbled to API) | Message | Recovery Action |
|------------|-------------------------------|---------|-----------------|
| Invalid ZIP (corrupt or > 50 MB) | 400 | “Invalid source archive – must be a valid ZIP ≤ 50 MB.” | Reject request; client resubmits. |
| JSON schema violation (feature descriptor) | 400 | “Feature descriptor does not match required schema.” | Client fixes JSON. |
| Bedrock timeout or service error | 500 (mapped in Step Functions) | “AI service unavailable – please retry later.” | Step Functions retries up to 2×, then `NotifyFailure`. |
| Missing required sections in LLM output | 500 (internal) | “Generated spec incomplete – required sections missing.” | Mark job as `Failed`, trigger cleanup. |

**Testing Strategy**  

| Test Level | Target Component | Sample Scenarios |
|------------|------------------|-----------------|
| Unit | `PromptBuilder` | Verify placeholder substitution, truncation of code snippets at 200 lines. |
| Unit | `SpecGenerator Lambda` | Mock Bedrock response → verify Markdown → PDF conversion, DynamoDB update. |
| Integration | Step Functions workflow | End‑to‑end with real Bedrock (sandbox) – generate spec for sample module, assert S3 output exists, status = `Succeeded`. |
| Acceptance | API `POST /generate-spec` + `GET /job-status/{id}` | Upload NopCommerce module A & descriptor; poll until success; verify PDF content includes all four quality criteria (checked by regex). |
| Performance | Load test (2 parallel jobs) | Ensure average latency < 120 s; CloudWatch alarm `ProcessingTimeMs`. |
| Security | IAM Access Analyzer | Ensure no broader permissions than defined in roles. |

---  

### 3.2 FR‑02: **Document Formatting**  

**Business Requirement:**  
*The system shall convert the LLM‑generated text to both Markdown and PDF formats.* → **BR‑001**  

**Linked User Stories:**  
- **US‑001** (generation & download)  
- **US‑005** (validation of required sections)  

#### 3.2.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Provide human‑readable (Markdown) and printable (PDF) artefacts. |
| **Architecture Layer** | *Application Layer* (SpecGenerator Lambda). |
| **SA Components Used** | Lambda, S3 Output Bucket, CloudWatch custom metrics, IAM role `SpecGeneratorRole`. |
| **Trigger** | Same as FR‑01 – invoked by Step Functions after prompt creation. |

#### 3.2.2 Component Design  

| Backend Component | Type | Responsibility | Technology | SA Reference |
|-------------------|------|----------------|------------|--------------|
| **Markdown Converter** | Library | Turn raw LLM text into GitHub‑flavoured Markdown, inject front‑matter (title, date, version). | `markdown2` (Python) | SA 4 (Tech Standards) |
| **PDF Renderer** | Library | Render Markdown → HTML → PDF using `wkhtmltopdf` via `pdfkit`. | `pdfkit` (Python wrapper) + `wkhtmltopdf` binary (layer). | SA 4 (Tech Standards) |
| **Validation Service** | Helper | Verify presence of required sections (Accuracy, Completeness, Clarity, Consistency) via regex pattern matching. | Python `re` module | SA 4 (Tech Standards) |

#### 3.2.3 Detailed Technical Specification  

**Data Flow**  

1. **SpecGenerator Lambda** receives LLM text.  
2. Calls **Markdown Converter** → `spec.md`.  
3. Passes `spec.md` to **PDF Renderer** → `spec.pdf`.  
4. Calls **Validation Service**: ensures that headings `## Overview`, `## Functional Requirements`, `## Non‑Functional Requirements`, `## Acceptance Criteria` exist, and that each bullet contains at least one verb (clarity). If validation fails → set job status `Failed` with error “Missing required sections”.  
5. Upload both files to Output Bucket (`s3://digital-worker-output/<jobId>/spec.md` & `.pdf`).  
6. Store S3 keys in DynamoDB `outputKey` (comma‑separated list).  

**API Impact** – The presigned URL returned by **GET /job-status/{jobId}** points to the PDF (primary) and includes a query param `format=md` for Markdown download.  

**NFR Implementation**  

| NFR | How Implemented |
|-----|-----------------|
| **Performance** | PDF generation time < 30 s (benchmark with wkhtmltopdf); Lambda memory 1024 MB. |
| **Security** | PDFs stored encrypted with the same KMS CMK; presigned URLs signed with SHA‑256 and 24 h TTL. |
| **Observability** | Emits metric `DocsFormatted` (value = 1) per successful conversion. |
| **Quality (4 criteria)** | Validation Service enforces presence of sections; missing sections cause job failure → ensures quality by construction. |

**Error Handling**  

| Error | HTTP Code (if surfaced) | Message | Recovery |
|-------|--------------------------|---------|----------|
| Markdown conversion exception | 500 | “Failed to convert spec to Markdown.” | Job marked `Failed`; cleanup invoked. |
| PDF rendering failure (wkhtmltopdf crash) | 500 | “PDF generation failed.” | Retry up to 2×; if still fails, job marked `Failed`. |
| Validation missing section | 400 (internal) | “Spec missing required section: ‘Functional Requirements’.” | Return to user for descriptor improvement. |

**Testing**  

| Test | Target | Scenario |
|------|--------|----------|
| Unit | `Validation Service` | Feed sample spec missing “Non‑Functional Requirements”; assert failure. |
| Integration | End‑to‑end job | Verify both `.md` and `.pdf` exist, content includes required headings. |
| Performance | PDF generation | Ensure total Lambda duration ≤ 120 s for largest allowed source (50 MB). |

---  

### 3.3 FR‑03: **API Service**  

**Business Requirement:**  
*Expose a REST API (`POST /generate-spec` and `GET /job-status/{jobId}`) to trigger generation and retrieve status.* → **BR‑004**  

**Linked User Stories:**  
- **US‑001** (submission)  
- **US‑002** (status query)  

#### 3.3.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Provide external, IAM‑authenticated entry point for developers and CI pipelines. |
| **Architecture Layer** | *Presentation Layer* (API Gateway) + *Application Layer* (Lambda “APIGatewayHandler”). |
| **SA Components Used** | API Gateway (REST), Lambda Proxy integration, IAM authorizer, CloudWatch logs, DynamoDB (job metadata). |
| **Trigger** | Direct HTTP request from client. |

#### 3.3.2 Component Design  

| Frontend Components | Not required – PoC is API‑only. Future UI could be a simple React page using the same endpoints. |
|---------------------|----------------------------------------------------|

| Backend Components | Type | Responsibility | Technology | SA Reference |
|------------------|------|----------------|------------|--------------|
| **APIGatewayHandler Lambda** | Compute | Validate multipart request, store ZIP & JSON to Input Bucket, create DynamoDB job entry, start Step Functions execution, return `jobId`. | Python 3.11, `boto3` S3/DynamoDB/StepFunctions | SA 5 (Lambda) |
| **JobStatus Lambda** (proxy for `GET /job-status/{id}`) | Compute | Read DynamoDB entry, if `Succeeded` generate presigned S3 URL (PDF), return JSON payload. | Python 3.11, `boto3` | SA 5 |
| **API Gateway** | Service | Front‑door, request validation, throttling, IAM auth. | OpenAPI 3.0 import, usage plan 10 RPS. | SA 2.1 (System Context) |

#### 3.3.3 Detailed Technical Specification  

**OpenAPI 3.0 Contract**  

```yaml
openapi: 3.0.3
info:
  title: Digital Worker Factory API
  version: 1.0.0
paths:
  /generate-spec:
    post:
      summary: Submit source ZIP and feature descriptor to start spec generation.
      requestBody:
        required: true
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                archive:
                  type: string
                  format: binary
                  description: NopCommerce source‑code ZIP (max 50 MB)
                descriptor:
                  type: string
                  format: json
                  description: Feature descriptor JSON matching schema `FeatureDescriptorV1`.
      responses:
        '202':
          description: Accepted – job created.
          content:
            application/json:
              schema:
                type: object
                properties:
                  jobId:
                    type: string
                    format: uuid
        '400':
          $ref: '#/components/responses/BadRequest'
        '401':
          $ref: '#/components/responses/Unauthorized'
        '413':
          $ref: '#/components/responses/RequestEntityTooLarge'
  /job-status/{jobId}:
    get:
      summary: Retrieve status and download URL (if succeeded).
      parameters:
        - name: jobId
          in: path
          required: true
          schema:
            type: string
            format: uuid
      responses:
        '200':
          description: Current job state.
          content:
            application/json:
              schema:
                type: object
                properties:
                  jobId:
                    type: string
                    format: uuid
                  status:
                    type: string
                    enum: [Pending, Running, Succeeded, Failed]
                  downloadUrl:
                    type: string
                    format: uri
                    nullable: true
                  errorMessage:
                    type: string
                    nullable: true
        '404':
          $ref: '#/components/responses/NotFound'
        '401':
          $ref: '#/components/responses/Unauthorized'
components:
  responses:
    BadRequest:
      description: Invalid input.
    Unauthorized:
      description: Authentication failed.
    RequestEntityTooLarge:
      description: Payload exceeds 50 MB.
    NotFound:
      description: Job ID not found.
```

**Business Logic – POST `/generate-spec`**  

1. **Auth** – API Gateway validates IAM signature (`aws:SecureTransport` & `aws:SourceVpce`).  
2. **Payload Validation** – Lambda checks MIME type, file size (< 50 MB) and validates descriptor JSON against schema (`FeatureDescriptorV1`).  
3. **Persist Input** – Stores `archive.zip` → `digital-worker-input/<jobId>/archive.zip`; stores descriptor → `digital-worker-input/<jobId>/descriptor.json`.  
4. **Create DynamoDB Job** – `status = Pending`, timestamps, TTL = now + 24 h.  
5. **Start Step Functions Execution** – Passes `{jobId, inputKey, descriptorKey}`.  
6. **Return** `202 Accepted` with `{jobId}`.  

**Business Logic – GET `/job-status/{jobId}`**  

1. **Auth** – Same IAM check.  
2. **Read DynamoDB** – If `status = Succeeded`, call `s3.generate_presigned_url` for the PDF (or Markdown via query param).  
3. **Return** JSON with `status`, optional `downloadUrl`, optional `errorMessage`.  

**Non‑Functional Implementation**  

| NFR | Implementation |
|-----|----------------|
| **Performance** | API Gateway integrates directly with Lambda (cold start mitigated by provisioned concurrency for APIGatewayHandler: 2). Response time ≤ 1 s for POST, ≤ 200 ms for GET. |
| **Security** | IAM authorizer; TLS 1.2 enforcement (API GW); S3 VPC endpoint; KMS CMK for both buckets. |
| **Scalability** | API Gateway auto‑scales; Lambda on‑demand; Step Functions can handle concurrent executions up to 100 RPS (well within PoC). |
| **Observability** | CloudWatch LogGroups `APIGatewayHandler`, `JobStatus`; custom metrics `APICalls`, `JobCreationRate`. |
| **Compliance** | All requests logged to CloudTrail; data never leaves `eu‑west‑1`. |

**Error Handling**  

| Scenario | HTTP Code | Body (JSON) | Remarks |
|----------|------------|-------------|---------|
| Missing `archive` or `descriptor` part | 400 | `{ "code":400, "message":"Both archive and descriptor must be provided." }` | Validation error. |
| Archive > 50 MB | 413 | `{ "code":413, "message":"Payload exceeds 50 MB limit." }` | Immediate reject. |
| Invalid JWT/IAM signature | 401 | `{ "code":401, "message":"Unauthorized." }` | API GW handles. |
| Job not found | 404 | `{ "code":404, "message":"Job <id> not found." }` | From DynamoDB lookup. |

**Testing**  

| Test | Target | Description |
|------|--------|-------------|
| Unit | APIGatewayHandler → payload validation | Test oversize file, malformed JSON, missing parts. |
| Integration | End‑to‑end POST → Step Functions → S3 → DynamoDB → GET status | Use SAM‑local to emulate whole flow. |
| Load | 10 parallel POSTs | Verify API GW throttling (10 RPS) and no 429 responses. |
| Security | IAM policy simulator | Confirm role cannot delete objects outside its prefix. |

---  

### 3.4 FR‑04: **Secure Temporary Storage**  

**Business Requirement:**  
*All source archives and generated artefacts must be stored encrypted with a 24 h TTL.* → **BR‑003**, **BR‑007**  

**Linked User Stories:**  
- US‑001 (upload)  
- US‑002 (auto‑delete)  

#### 3.4.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Ensure confidential source code is never persisted longer than necessary and meets ISO 27001. |
| **Architecture Layer** | *Data Layer* (S3, DynamoDB). |
| **SA Components Used** | S3 Buckets with **SSE‑KMS**, S3 Lifecycle policies, DynamoDB TTL, Cleanup Lambda. |
| **Trigger** | Lifecycle automatically after 1 day; explicit Lambda cleanup after 24 h or on failure. |

#### 3.4.2 Component Design  

| Data Components | Type | Responsibility | Technology | SA Reference |
|----------------|------|----------------|------------|--------------|
| **Input Bucket (`digital-worker-input`)** | Object Store | Holds uploaded ZIP & descriptor, encrypted, 24 h TTL via lifecycle rule. | S3 Standard‑IA, `sse-kms`, lifecycle rule `Expiration: 1 day`. | SA 5.1 |
| **Output Bucket (`digital-worker-output`)** | Object Store | Holds generated Markdown & PDF, encrypted, 24 h TTL. | S3 Standard‑IA, `sse-kms`, same lifecycle. | SA 5.1 |
| **Job Table (DynamoDB)** | Metadata Store | Stores `expiresAt` (TTL) = `submitTime + 86400 000`. | DynamoDB On‑Demand, TTL enabled. | SA 5.1 |
| **Cleanup Lambda** | Compute | Runs hourly (EventBridge) or after Step Functions `Wait 24h`; deletes objects whose `expiresAt` passed. | Python 3.11, `boto3` delete_object, IAM role `CleanupRole`. | SA 5.2 |

#### 3.4.3 Detailed Technical Specification  

**S3 Lifecycle Policy (both buckets)**  

```json
{
  "Rules": [
    {
      "ID": "DeleteAfterOneDay",
      "Status": "Enabled",
      "Expiration": { "Days": 1 },
      "NoncurrentVersionExpiration": { "NoncurrentDays": 1 }
    }
  ]
}
```

**Cleanup Lambda Logic**  

1. Query DynamoDB GSI `status-index` for items where `status` = *Succeeded* **and** `endTime + 86400 000 <= now`.  
2. For each job, delete `inputKey` and optionally `outputKey` (if policy dictates).  
3. Update DynamoDB `status = Cleaned` (optional) for audit.  
4. Emit CloudWatch metric `CleanupActions` (count).  

**Security**  

- Lambda role `CleanupRole` limited to `s3:DeleteObject` on the two bucket ARNs with prefix `digital-worker-*/*`.  
- VPC endpoint for S3 ensures no Internet egress.  

**Non‑Functional Implementation**  

| NFR | How Implemented |
|-----|-----------------|
| **Security** | SSE‑KMS with CMK restricted to the four Lambda roles; bucket policies block public access; ACLs disabled. |
| **Compliance** | 24 h lifecycle + explicit TTL → GDPR “right to be forgotten”. |
| **Observability** | CloudWatch metric `ObjectsDeleted`; alarm if > 0 deletions happen outside normal schedule (possible over‑retention). |
| **Scalability** | S3 unlimited; DynamoDB TTL runs serverless; Cleanup Lambda processes up to 100 objects per invocation (batch). |
| **Cost** | Lifecycle deletion prevents storage cost build‑up; Lambda runs only when needed (hourly schedule). |

**Error Handling**  

| Error | Action |
|------|--------|
| DeleteObject failure (access denied) | Log error with `requestId`, `jobId`; send SNS alert to `SecurityOps`. |
| DynamoDB TTL mis‑configuration | Emit CloudWatch alarm `TTLMisconfig`. |
| Cleanup Lambda timeout (processing > 300 s) | Use pagination, invoke itself recursively with `NextToken`. |

**Testing**  

| Test | Target | Scenario |
|------|--------|----------|
| Unit | Cleanup Lambda | Mock DynamoDB items, assert correct S3 delete calls. |
| Integration | S3 lifecycle + TTL | Upload file, wait 24 h (fast‑forward with `aws s3api put-object-retention`), verify deletion. |
| Security | IAM policy simulation | Ensure `CleanupRole` cannot delete objects outside its bucket prefix. |

---  

### 3.5 FR‑05: **Automatic Cleanup**  

**Business Requirement:**  
*The system shall automatically delete source archives (and optionally output) after successful processing or after 24 h on failure.* → **BR‑003**, **BR‑007**  

**Linked User Stories:**  
- US‑002 (delete after processing)  

*Note:* FR‑05 is realized by the **Cleanup Lambda** already described in FR‑04; the additional “immediate delete on failure” is a **Compensation Path** in the Step Functions state machine.  

#### 3.5.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Prevent any residual confidential artefacts. |
| **Architecture Layer** | *Orchestration Layer* (Step Functions) + *Data Layer* (Cleanup Lambda). |
| **SA Components Used** | Step Functions `Catch` → `NotifyFailure` → `Cleanup`; EventBridge scheduled cleanup. |
| **Trigger** | Failure path of Step Functions or periodic EventBridge rule. |

#### 3.5.2 Component Design  

| Component | Type | Responsibility | Technology | SA Reference |
|-----------|------|----------------|------------|--------------|
| **Compensation State (`CleanupOnFailure`)** | Step Functions Task | Invokes `Cleanup Lambda` immediately after any failure. | AWS SFN `Task` with `Catch` | SA 2.1 |
| **Scheduled Cleanup** | EventBridge Rule | Cron `0 * * * ? *` (hourly) → invoke `Cleanup Lambda`. | EventBridge, Lambda target | SA 5.3 |

#### 3.5.3 Detailed Technical Specification  

**Step Functions State Snippet (YAML)**  

```yaml
GenerateSpec:
  Type: Task
  Resource: arn:aws:lambda:eu-west-1:123456789012:function:SpecGenerator
  Next: NotifySuccess
  Catch:
    - ErrorEquals: [States.ALL]
      Next: CleanupOnFailure

NotifySuccess:
  Type: Task
  Resource: arn:aws:lambda:...:NotifySuccess
  Next: WaitForRetention

WaitForRetention:
  Type: Wait
  Seconds: 86400   # 24 h
  Next: CleanupAfterTTL

CleanupAfterTTL:
  Type: Task
  Resource: arn:aws:lambda:...:Cleanup
  End: true

CleanupOnFailure:
  Type: Task
  Resource: arn:aws:lambda:...:Cleanup
  End: true
```

**Cleanup Lambda (Behaviour)**  

- On **failure**: delete **inputKey** only (output likely not produced).  
- On **TTL expiry**: delete both **inputKey** and **outputKey**.  

**NFR Implementation**  

| NFR | Detail |
|-----|--------|
| **Reliability** | Ensure cleanup runs even if Step Functions fails to transition (EventBridge watchdog). |
| **Observability** | Emit CloudWatch metric `CleanupInvocations`; log jobId and action (`inputOnly` vs `full`). |
| **Security** | Same IAM constraints as FR‑04. |
| **Performance** | Deletion operation < 1 s per object; batch deletes for up to 100 objects per invocation. |

**Error Handling**  

| Error | Response |
|-------|----------|
| Deletion of non‑existent object | Log warning, continue (idempotent). |
| IAM permission denied | Fail fast, send SNS alert to ops. |
| Lambda timeout (processing > 300 s) | Invoke itself with `NextToken` (recursive pattern). |

**Testing**  

| Test | Target | Description |
|------|--------|-------------|
| Unit | Cleanup Lambda | Simulate DynamoDB items older than TTL, assert proper S3 delete calls. |
| Integration | Step Functions failure path | Force SpecGenerator to raise exception, verify Cleanup is invoked and input bucket is empty. |
| Scheduling | EventBridge rule | Trigger rule manually, verify cleanup runs. |

---  

### 3.6 FR‑06: **Notification**  

**Business Requirement:**  
*Publish success/failure events containing job metadata and download URL (if any) to Amazon SNS.* → **BR‑006**  

**Linked User Stories:**  
- US‑003 (SNS email/webhook).  

#### 3.6.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Decouple consumers (email, Slack, internal dashboards) from core workflow. |
| **Architecture Layer** | *Integration Layer* (SNS) + *Orchestration* (Step Functions). |
| **SA Components Used** | SNS Topic `DigitalWorkerEvents`, Lambda `NotifySuccess` / `NotifyFailure`. |
| **Trigger** | Step Functions state `NotifySuccess` / `NotifyFailure`. |

#### 3.6.2 Component Design  

| Backend Components | Type | Responsibility | Technology | SA Reference |
|--------------------|------|----------------|------------|--------------|
| **NotifySuccess Lambda** | Compute | Build JSON payload with `jobId`, `status=Succeeded`, `downloadUrl` (presigned), publish to SNS. | Python 3.11, `boto3` `sns.publish` | SA 5.2 |
| **NotifyFailure Lambda** | Compute | Build JSON payload with `jobId`, `status=Failed`, `errorMessage`, publish to SNS. | Python 3.11 | SA 5.2 |
| **SNS Topic** `DigitalWorkerEvents` | Messaging | Fan‑out to email, HTTP webhook, or future Slack integration. | Standard SNS, no DLQ for PoC. | SA 5.2 |

#### 3.6.3 Detailed Technical Specification  

**Message Schema (JSON)**  

```json
{
  "jobId": "string (uuid)",
  "status": "Succeeded | Failed",
  "timestamp": "epoch ms",
  "downloadUrl": "string (presigned HTTPS, optional)",
  "errorMessage": "string (optional)",
  "metadata": {
    "module": "string",
    "featureCount": "integer"
  }
}
```

**Presigned URL Generation**  

```python
s3_client.generate_presigned_url(
    ClientMethod='get_object',
    Params={'Bucket': OUTPUT_BUCKET, 'Key': output_key},
    ExpiresIn=86400,   # 24 h
    HttpMethod='GET')
```

**NFR Implementation**  

| NFR | Implementation |
|-----|----------------|
| **Reliability** | SNS retries up to 3 times; Lambda captures publish errors and writes to CloudWatch. |
| **Security** | SNS topic policy restricts publish to `Notify*` Lambdas, subscribe endpoints must use HTTPS. |
| **Observability** | CloudWatch metric `NotificationsSent` (tagged `status`). |
| **Scalability** | SNS auto‑scales; no per‑message bottleneck. |

**Error Handling**  

| Scenario | Action |
|----------|--------|
| SNS publish fails (e.g., network) | Lambda logs error, retries (exponential back‑off) up to 3 times, then sends to fallback email via SES. |
| Presigned URL generation error | Mark job as `Failed`, include errorMessage in SNS payload. |

**Testing**  

| Test | Target | Description |
|------|--------|-------------|
| Unit | NotifySuccess Lambda | Mock `s3.generate_presigned_url` → assert payload includes `downloadUrl`. |
| Integration | End‑to‑end job success | Verify SNS receives message (use `aws sns list-subscriptions` with `email` endpoint). |
| Failure Path | NotifyFailure Lambda | Inject Bedrock error, ensure SNS payload contains `errorMessage`. |

---  

### 3.7 FR‑07: **Metrics & Auditing**  

**Business Requirement:**  
*Capture processing time, success count, error count; log all API actions for audit.* → **BR‑007**  

**Linked User Stories:**  
- US‑004 (monitoring dashboard).  

#### 3.7.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Provide real‑time observability and audit compliance. |
| **Architecture Layer** | *Observability Layer* (CloudWatch, CloudTrail, X‑Ray). |
| **SA Components Used** | CloudWatch Logs & Metrics, CloudTrail, X‑Ray (optional), SNS alerts. |
| **Trigger** | All Lambdas, API Gateway, Step Functions emit metrics & logs. |

#### 3.7.2 Component Design  

| Component | Type | Responsibility | Technology | SA Reference |
|-----------|------|----------------|------------|--------------|
| **Custom CloudWatch Namespace** `DigitalWorkerFactory` | Metrics | `DocsGenerated`, `ProcessingTimeMs`, `FailedJobs`, `NotificationsSent`. | CloudWatch `put_metric_data` | SA 5.2 |
| **Log Groups** per Lambda (`/aws/lambda/<name>`) | Logs | Structured JSON with `requestId`, `jobId`, `level`. | CloudWatch Logs | SA 5.2 |
| **X‑Ray Tracing** (optional) | Tracing | End‑to‑end request trace across API GW → Lambda → Bedrock. | AWS X‑Ray SDK | SA 5.3 |
| **CloudTrail** | Audit | Capture all API calls (S3, DynamoDB, Bedrock, SNS). | CloudTrail | SA 5.4 |
| **Dashboard** | Visualization | Shows SLA metrics, error rates, job throughput. | CloudWatch Dashboard (JSON) | SA 5.5 |

#### 3.7.3 Detailed Technical Specification  

**Metric Emission (Python snippet)**  

```python
import os, time, boto3
cw = boto3.client('cloudwatch')
def emit_metric(name, value, job_id):
    cw.put_metric_data(
        Namespace='DigitalWorkerFactory',
        MetricData=[{
            'MetricName': name,
            'Dimensions':[{'Name':'JobId','Value':job_id}],
            'Timestamp': time.time(),
            'Value': value,
            'Unit':'Count'
        }]
    )
```

- `ProcessingTimeMs` emitted at end of **SpecGenerator** (`latencyMs`).  
- `DocsGenerated` emitted after successful upload in **SpecGenerator**.  
- `FailedJobs` emitted in any `Catch` branch.  

**Log Format (example)**  

```json
{
  "timestamp":"2026-01-10T14:23:45.123Z",
  "requestId":"c3f9e6b9-2b5e-4d6a-9c2e-6b1b3e6a4c9a",
  "jobId":"5d9f2c1a-8e45-4b9d-b2e8-7c1f4b6d9e3f",
  "level":"INFO",
  "message":"Spec generation completed."
}
```

**Dashboard Widgets**  

| Widget | Metric | Target |
|--------|--------|--------|
| **Docs Generated / hour** | `DocsGenerated` (sum, 1 h) | ≥ 2 per PoC day |
| **Avg Processing Time** | `ProcessingTimeMs` (avg, 5 min) | ≤ 120 000 ms |
| **Failed Jobs** | `FailedJobs` (sum, 5 min) | 0 (alert > 0) |
| **API Latency** | API GW integration latency | ≤ 1 s |

**Alerting**  

- **Alarm 1:** `ProcessingTimeMs > 150 000 ms` → SNS `OpsAlert`.  
- **Alarm 2:** `FailedJobs > 0` → SNS `OpsAlert`.  

**Security / Compliance**  

- CloudTrail logs retained 30 days (SA 5.4).  
- Logs encrypted with same KMS CMK.  

**Testing**  

| Test | Target | Description |
|------|--------|-------------|
| Unit | Metric emission function | Verify `put_metric_data` called with correct namespace & dimensions. |
| Integration | End‑to‑end job | After successful run, assert CloudWatch metric `DocsGenerated` incremented. |
| Security | CloudTrail validation | Confirm S3 PutObject, DynamoDB UpdateItem are recorded. |
| Performance | Dashboard latency | Verify dashboard refresh < 30 s. |

---  

### 3.8 FR‑08: **Automatic Cleanup Scheduling** *(Complement of FR‑05)*  

**Business Requirement:**  
*Schedule cleanup after 24 h or on failure, guarantee no residual artefacts.* → **BR‑003**, **BR‑007**  

*This FR is already covered in the design of FR‑04, FR‑05 and the Step Functions workflow; the explicit “schedule” is the **Wait** state and **EventBridge** rule.*  

#### 3.8.1 Technical Design Overview  

| Item | Detail |
|------|--------|
| **Purpose** | Ensure data lifecycle compliance without manual intervention. |
| **Architecture Layer** | Orchestration (Step Functions) + Scheduler (EventBridge). |
| **SA Components Used** | Step Functions `Wait` state (86400 s), EventBridge hourly rule, Cleanup Lambda. |
| **Trigger** | Either Step Functions `Wait` after success, or EventBridge periodic run for orphaned jobs. |

#### 3.8.2 Component Design  

| Component | Type | Responsibility | Technology | SA Reference |
|-----------|------|----------------|------------|--------------|
| **WaitForRetention** | Step Function State | Pause execution 24 h before invoking final cleanup. | SFN `Wait` | SA 2.1 |
| **ScheduledCleanup Rule** | EventBridge | Cron `0 * * * ? *` → invoke Cleanup Lambda (covers any missed TTL). | EventBridge → Lambda target | SA 5.3 |
| **Cleanup Lambda** | Compute (same as FR‑05) | Delete S3 artefacts, update DynamoDB. | Python 3.11 | SA 5.2 |

#### 3.8.3 Detailed Technical Specification  

- **Wait State** ensures that the same execution that succeeded will clean up after exactly 24 h, avoiding a separate batch run for that job.  
- **EventBridge** catches any jobs that missed the Wait (e.g., Step Functions crash) and removes leftover objects.  

**Idempotency** – Cleanup Lambda uses `delete_object` with `IfExists` semantics; missing objects are ignored.  

**NFRs** – Same as FR‑04/05 (security, compliance, scalability).  

**Testing**  

| Test | Target | Scenario |
|------|--------|----------|
| Integration | Wait + Cleanup | Run a successful job, fast‑forward time (use `aws stepfunctions start-sync-execution` with `--input '{"waitSeconds":10}'`) and verify Cleanup runs after wait. |
| Scheduler | EventBridge rule | Manually trigger rule, confirm orphaned objects removed. |

---  

## 4. Cross‑Cutting Concerns  

### 4.1 Logging & Monitoring  

| Concern | Implementation |
|---------|----------------|
| **Log Format** | JSON with fields: `timestamp`, `requestId`, `jobId`, `level`, `component`, `message`. |
| **Log Aggregation** | CloudWatch Log Groups per Lambda; subscription filter can forward to Amazon OpenSearch (future). |
| **Metrics** | Custom namespace `DigitalWorkerFactory` – metrics listed in FR‑07. |
| **Tracing** | X‑Ray enabled on API Gateway, Lambdas, and Step Functions (optional). |
| **Alarms** | `ProcessingTimeMs` > 150 s, `FailedJobs` > 0, `CleanupInvocations` > 0 unexpected. |
| **Dashboard** | Pre‑built CloudWatch dashboard (see FR‑07 dashboard table). |

### 4.2 Security Implementation  

| Layer | Control |
|-------|---------|
| **Authentication** | API Gateway IAM auth (SIGV4). For future UI, Cognito User Pool tokens. |
| **Authorization** | IAM roles: `SourceLoaderRole`, `SpecGeneratorRole`, `CleanupRole`, `APIGatewayHandlerRole`. Each role scoped to specific bucket prefixes and DynamoDB keys. |
| **Data Protection** | SSE‑KMS (`alias/digital-worker-key`) on both S3 buckets; KMS key policy permits only the four Lambda roles. |
| **Network Isolation** | All Lambdas placed in private subnets; VPC endpoints for S3 and Bedrock; no internet egress. |
| **Audit** | CloudTrail logs all S3, DynamoDB, Bedrock, SNS actions; retained 30 days. |
| **Threat Detection** | GuardDuty enabled; any anomalous S3 delete alerts forwarded to Security SNS topic. |

### 4.3 Data Management  

| Pattern | Usage |
|---------|-------|
| **Single‑Table DynamoDB** | Stores all job metadata (`DigitalWorkerJobs`). |
| **TTL** | DynamoDB `expiresAt` (30 days) + S3 lifecycle (24 h). |
| **Caching** | No runtime cache needed (stateless). Future version may cache prompt templates in DynamoDB. |
| **Backup** | DynamoDB point‑in‑time recovery enabled; S3 versioning disabled (write‑once, auto‑delete). |
| **Retention** | S3 objects auto‑deleted after 1 day; ensures GDPR “right to be forgotten”. |

### 4.4 Integration Architecture  

| Integration Pattern | Where Applied |
|---------------------|----------------|
| **Request‑Response** | API Gateway → APIGatewayHandler Lambda (FR‑03). |
| **Event‑Driven** | Step Functions orchestrates Lambdas (FR‑01‑05). |
| **Publish‑Subscribe** | SNS `DigitalWorkerEvents` (FR‑06). |
| **Compensation Transaction** | Step Functions `Catch` → Cleanup Lambda (FR‑05). |
| **Batch Processing** | EventBridge hourly cleanup (FR‑08). |

---  

## 5. Deployment Architecture  

### 5.1 Component Deployment Mapping  

| Component | Environment | Deployment Method | Resources (CPU/Memory) | SA Reference |
|-----------|-------------|-------------------|------------------------|--------------|
| **APIGatewayHandler Lambda** | `dev` / `prod` | CDK `aws_lambda.Function` | 256 MB, 128 MB provisioned concurrency (2) | SA 5.2 |
| **JobStatus Lambda** | `dev` / `prod` | CDK | 256 MB, on‑demand | SA 5.2 |
| **SpecGenerator Lambda** | `dev` / `prod` | CDK (with layer for wkhtmltopdf) | 1024 MB, provisioned concurrency 2 (PoC) | SA 5.2 |
| **Cleanup Lambda** | `dev` / `prod` | CDK | 256 MB, on‑demand | SA 5.2 |
| **NotifySuccess / NotifyFailure Lambdas** | `dev` / `prod` | CDK | 256 MB | SA 5.2 |
| **Step Functions State Machine** | `dev` / `prod` | CDK `aws_stepfunctions.StateMachine` | Standard tier | SA 2.1 |
| **API Gateway** | `dev` / `prod` | CDK `aws_apigateway.RestApi` | – | SA 2.1 |
| **S3 Input Bucket** | `dev` / `prod` | CDK `aws_s3.Bucket` (SSE‑KMS, lifecycle) | – | SA 5.1 |
| **S3 Output Bucket** | `dev` / `prod` | CDK (same) | – | SA 5.1 |
| **DynamoDB Table** | `dev` / `prod` | CDK `aws_dynamodb.Table` (On‑Demand, TTL) | – | SA 5.1 |
| **SNS Topic** | `dev` / `prod` | CDK `aws_sns.Topic` | – | SA 5.2 |
| **KMS CMK** | `dev` / `prod` | CDK `aws_kms.Key` (alias `digital-worker-key`) | – | SA 5.1 |
| **EventBridge Rule** | `dev` / `prod` | CDK `aws_events.Rule` (cron) | – | SA 5.3 |
| **CloudWatch Dashboard** | `dev` / `prod` | CDK `aws_cloudwatch.Dashboard` (JSON) | – | SA 5.5 |
| **CodePipeline** | `dev` / `prod` | CDK `aws_codepipeline.Pipeline` (Source → Build → Deploy) | – | SA 9 (Implementation Strategy) |

### 5.2 Configuration Management  

| Variable | Description | Default (Dev) | Production |
|---------|-------------|----------------|------------|
| `INPUT_BUCKET` | Name of the source bucket | `digital-worker-input-dev` | `digital-worker-input` |
| `OUTPUT_BUCKET` | Name of the output bucket | `digital-worker-output-dev` | `digital-worker-output` |
| `JOB_TABLE` | DynamoDB table name | `DigitalWorkerJobsDev` | `DigitalWorkerJobs` |
| `SNS_TOPIC_ARN` | SNS notifications ARN | `arn:aws:sns:eu-west-1:123456789012:DigitalWorkerEventsDev` | production ARN |
| `KMS_KEY_ARN` | CMK for encryption | `alias/digital-worker-key-dev` | `alias/digital-worker-key` |
| `BEDROCK_MODEL_ID` | Bedrock model identifier | `anthropic.claude-v2:1` | same |
| `MAX_TOKENS` | Max tokens for Bedrock request | `4000` | same |
| `PROVISIONED_CONCURRENCY` | SpecGenerator provisioned concurrency | `2` | `5` (future) |
| `ALERT_EMAIL` | Ops email for SNS alerts | `dev-ops@example.com` | `ops@example.com` |

All variables are injected as **encrypted environment variables** into Lambdas via the CDK `secret` construct (KMS‑encrypted).  

### 5.3 CI/CD Pipeline  

1. **Source** – GitHub `main` branch triggers CodePipeline.  
2. **Build** – CodeBuild runs `npm ci` → `cdk synth` → `cdk diff`. Unit tests (`pytest`) executed; build fails if coverage < 80 % or `cfn-nag` finds violations.  
3. **Deploy** – `cdk deploy DigitalWorkerFactory-dev` to dev account; manual approval stage before production deploy.  
4. **Post‑Deploy Tests** – Integration tests executed via `aws cloudformation test` (SAM‑local) to verify end‑to‑end flow.  
5. **Rollback** – If any stage fails, CloudFormation roll‑back automatically restores previous stack.  

---  

## 6. Technical Debt & Risks  

### 6.1 Technical Debt Items  

| Item | Impact | Mitigation | Priority |
|------|--------|------------|----------|
| **Hard‑coded prompt templates** | Limits flexibility for future modules. | Externalize prompts to DynamoDB `PromptTemplates` table; add admin UI. | Medium |
| **PDF generation binary (`wkhtmltopdf`)** | Increases Lambda package size; may hit 50 MB limit. | Use Lambda Layer with pre‑compiled binary; monitor size; consider Serverless Container Image if needed. | High (PoC already uses layer). |
| **Single‑region deployment** | Not HA across regions. | Future expansion using Route 53 latency‑based routing and global DynamoDB tables. | Low (out‑of‑scope). |
| **No DLQ for SNS** | Potential message loss on SNS publish failure. | Add DLQ (SQS) in production; for PoC rely on CloudWatch logs. | Low |

### 6.2 Technical Risks  

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Bedrock service throttling** | Medium | Jobs fail → SLA breach. | Implement exponential back‑off, request quota increase early. |
| **Large ZIP > 50 MB** | Low (validated) | API rejects; user confusion. | Front‑end validation, clear error message. |
| **Lambda cold‑start latency** | Medium | First request > 2 min. | Provisioned concurrency for critical Lambdas; keep warm via CloudWatch scheduled ping. |
| **Incorrect IAM permissions** | Low | Security breach or failure to access resources. | Run IAM Access Analyzer; automated policy unit tests. |
| **Presigned URL leakage** | Low | Unauthorized download. | URLs short‑lived (24 h), logged, revoked automatically by S3 expiration. |
| **EventBridge rule mis‑configuration** | Low | Cleanup not executed -> data retention violation. | CI test that rule exists & has correct cron expression. |

---  

## 7. Traceability Matrix  

| FR‑ID | US‑IDs | Technical Components | SA Section(s) | Test Cases |
|-------|--------|---------------------|----------------|-------------|
| **FR‑01** | US‑001 | APIGatewayHandler Lambda, SpecGenerator Lambda, Step Functions, Bedrock, Output S3, DynamoDB | 2.1, 3, 5.2 | TC‑GEN‑001 (end‑to‑end spec generation) |
| **FR‑02** | US‑001, US‑005 | SpecGenerator Lambda (Markdown & PDF converters), Validation Service | 3, 5.2 | TC‑FMT‑001 (markdown→pdf conversion) |
| **FR‑03** | US‑001, US‑002 | API Gateway, APIGatewayHandler Lambda, JobStatus Lambda, OpenAPI spec | 2.1, 5.2 | TC‑API‑001 (POST success), TC‑API‑002 (GET status) |
| **FR‑04** | US‑001, US‑002 | Input/Output S3 Buckets (SSE‑KMS), DynamoDB TTL, Cleanup Lambda (scheduled) | 5.1, 5.2 | TC‑SEC‑001 (S3 encryption), TC‑CLEAN‑001 (lifecycle) |
| **FR‑05** | US‑002 | Cleanup Lambda (immediate on failure), Step Functions Catch, EventBridge rule | 2.1, 5.3 | TC‑FAIL‑001 (forced Bedrock error → cleanup) |
| **FR‑06** | US‑003 | NotifySuccess/Failure Lambdas, SNS Topic `DigitalWorkerEvents` | 5.2 | TC‑NOTIF‑001 (SNS message receipt) |
| **FR‑07** | US‑004 | CloudWatch custom metrics, CloudTrail, X‑Ray (optional), Dashboard | 5.5, 5.4 | TC‑MON‑001 (metric emission) |
| **FR‑08** | US‑002 | Wait state (24 h), EventBridge cleanup rule | 2.1, 5.3 | TC‑SCH‑001 (wait → cleanup) |

---  

## 8. Implementation Roadmap  

### 8.1 Component Dependency Order  

1. **Base Infra** – VPC, KMS CMK, S3 buckets, DynamoDB table, SNS topic, IAM roles (CDK).  
2. **Step Functions & EventBridge** – Define state machine & scheduled rule (no Lambda code needed yet).  
3. **APIGatewayHandler & JobStatus Lambdas** – Deploy, attach to API GW.  
4. **Source Loader & SpecGenerator Lambdas** – Implement core business logic, attach to Step Functions.  
5. **Notify & Cleanup Lambdas** – Deploy, integrate with Step Functions.  
6. **Observability** – CloudWatch dashboards, alarms, X‑Ray (optional).  
7. **Testing & Validation** – Unit, integration, load, security.  
8. **Demo Packaging** – Postman collection, README, CI pipeline badge.  

### 8.2 Implementation Phases  

| Phase | Duration | Activities |
|-------|----------|------------|
| **Phase 1 – Foundations** | 6 h | CDK stack (VPC, KMS, buckets, DynamoDB, IAM), CI pipeline scaffolding. |
| **Phase 2 – Core API & Orchestration** | 8 h | API GW, APIGatewayHandler, JobStatus Lambda, Step Functions definition, EventBridge rule. |
| **Phase 3 – Business Logic** | 12 h | Implement Source Loader (validation), SpecGenerator (prompt, Bedrock call, formatting), Validation Service, PromptBuilder. |
| **Phase 4 – Notifications & Cleanup** | 6 h | NotifySuccess/Failure Lambdas, SNS topic, Cleanup Lambda (immediate & scheduled). |
| **Phase 5 – Observability & Security** | 4 h | CloudWatch metrics, dashboard, alarms; enable GuardDuty, CloudTrail; run IAM Access Analyzer. |
| **Phase 6 – Testing & QA** | 4 h | Unit tests (> 80 %); integration tests with SAM‑local; load test (2 concurrent jobs); security scan (`cfn‑nag`, `bandit`). |
| **Phase 7 – Demo & Documentation** | 2 h | Create Postman collection, update Confluence wiki, record demo video, hand‑off run‑book. |
| **Total** | **48 h** (2 days) | Aligns with hackathon schedule. |

---  

## 9. Appendices  

### 9.1 Technology Stack Details  

| Layer | Service | Version / Runtime | Notes |
|-------|---------|-------------------|-------|
| **Compute** | AWS Lambda | Python 3.11 (runtime) | Layers: `pdfkit` + `wkhtmltopdf` binary (Amazon Linux 2). |
| **Orchestration** | AWS Step Functions (Standard) | – | Visual workflow, retries, compensation. |
| **AI** | Amazon Bedrock – Claude‑Instant | Model ID `anthropic.claude-v2:1` | Token limit 4000, latency < 1 s. |
| **Storage** | Amazon S3 (Standard‑IA) | – | SSE‑KMS, lifecycle 1 day. |
| **Metadata** | Amazon DynamoDB (On‑Demand) | – | Single‑table, TTL enabled. |
| **Messaging** | Amazon SNS (Standard) | – | JSON payload, email subscription for judges. |
| **Observability** | Amazon CloudWatch (Metrics, Logs, Dashboard) | – | Custom namespace `DigitalWorkerFactory`. |
| **IaC** | AWS CDK (TypeScript) v2 | – | `npm` packages: `aws-cdk-lib`, `constructs`. |
| **CI/CD** | AWS CodePipeline + CodeBuild (Docker `aws/codebuild/standard:6.0`) | – | Build runs `npm ci`, `cdk synth`, `pytest`. |
| **Testing** | PyTest ≥ 7, SAM‑local, Postman | – | Coverage target 80 %. |

### 9.2 Code Standards  

| Area | Standard |
|------|----------|
| **Python** | PEP 8, type hints (`mypy`), flake8 linting, `black` formatting. |
| **CDK** | Type‑safe constructs, unit tests with `assertions` library, `cdk-nag` for security checks. |
| **APIs** | OpenAPI 3.0, JSON‑Schema validation via API GW models. |
| **Logging** | Structured JSON, `requestId` from Lambda context, `jobId` correlation. |
| **Error Handling** | Raise custom `DigitalWorkerError` with `http_status` attribute; Lambda wrapper converts to proper response. |
| **Testing** | 80 % line coverage; mocks for `boto3` via `moto`. |
| **Versioning** | Lambda functions versioned (`$LATEST` + published version) for safe rollbacks. |

### 9.3 Glossary  

| Acronym / Term | Definition |
|-----------------|------------|
| **AI** | Artificial Intelligence (LLM‑driven text generation). |
| **Bedrock** | AWS managed service exposing foundation models (Claude‑Instant). |
| **PDF** | Portable Document Format, generated from Markdown. |
| **S3** | Amazon Simple Storage Service. |
| **SSE‑KMS** | Server‑Side Encryption with AWS KMS‑managed keys. |
| **Step Functions** | Serverless orchestration service. |
| **TTL** | Time‑to‑Live – automatic expiration in DynamoDB/S3. |
| **VPC** | Virtual Private Cloud – network isolation. |
| **Wkhtmltopdf** | Open‑source command‑line tool converting HTML to PDF. |
| **X‑Ray** | Distributed tracing service (optional). |

---  

**End of Technical Architecture Design Document**.  