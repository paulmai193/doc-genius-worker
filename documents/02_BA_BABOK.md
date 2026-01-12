# Business Requirements Document (BRD)  
**Project:** FHM Hackathon Q4 – “Digital Worker Factory” – AI‑Driven Technical Documentation Generator  
**Version:** 1.0 (PoC) – 10 January 2026  

---  

## 1. Introduction  

### 1.1 Purpose and Scope  
The purpose of this BRD is to define, in detail, the business‑level and solution‑level requirements for an **AI Digital Worker** that automatically generates high‑quality technical specifications (e.g., SRS, Functional Specification) from NopCommerce source code and feature descriptors. The document is aligned with the **BABOK** knowledge areas and references the Enterprise Architecture Document (TOGAF 10) that describes the target AWS‑native solution.  

**Scope** – Phase 1 (PoC) includes:  

- Definition of business capabilities and value streams.  
- Specification of functional, non‑functional, and regulatory requirements.  
- Design of the API, orchestration workflow, and secure temporary storage.  
- Governance, risk, and compliance artefacts needed for the PoC.  

### 1.2 Document Conventions  
| Symbol | Meaning |
|--------|---------|
| **→** | Traceability link (e.g., → Addresses: BR‑001) |
| **[ ]** | Check‑list item |
| **#** | Section heading |
| **Bold** | Key term or artefact |
| *Italic* | Note or optional text |

### 1.3 Definitions, Acronyms, and Abbreviations  

| Term | Definition |
|------|------------|
| **Digital Worker** | An AI‑powered serverless service that performs a repeatable business task without human intervention. |
| **PoC** | Proof of Concept – a time‑boxed demonstration of core functionality. |
| **LLM** | Large Language Model (e.g., Amazon Bedrock Claude‑Instant). |
| **API** | Application Programming Interface – REST endpoint exposed via Amazon API Gateway. |
| **SRS** | Software Requirements Specification. |
| **ISO 27001** | International standard for information security management. |
| **BABOK** | Business Analysis Body of Knowledge (IIBA). |
| **TOGAF** | The Open Group Architecture Framework. |

### 1.4 References  

| # | Reference |
|---|-----------|
| 1 | Enterprise Architecture Document (TOGAF 10) – Section 2‑5, 6‑8. |
| 2 | IIBA BABOK Guide v3 – Knowledge Areas. |
| 3 | AWS Well‑Architected Framework – Security & Cost Pillars. |
| 4 | ISO/IEC 27001 – Annex A.8 (Data Encryption). |
| 5 | OpenAPI 3.0 Specification (API contract). |

### 1.5 Document Overview  
| Section | Content |
|---------|---------|
| 1 | Introduction |
| 2 | Business Analysis Approach (Planning & Monitoring) |
| 3 | Strategic Context (Strategy Analysis) |
| 4 | Stakeholder Analysis (Elicitation & Collaboration) |
| 5 | Business Context & Objectives |
| 6 | Business Process Analysis (Requirements Analysis) |
| 7 | Requirements Specification (Requirements Analysis & Design) |
| 8 | Requirements Analysis & Design Definition (User Stories, Use Cases, UI) |
| 9 | Solution Design Definition (Design Definition) |
| 10 | Data Requirements |
| 11 | Integration & Interface Requirements |
| 12 | Requirements Traceability Matrix |
| 13 | Assumptions, Dependencies & Constraints |
| 14 | Acceptance Criteria & Definition of Done |
| 15 | Solution Evaluation (Solution Evaluation) |
| 16 | Appendices |

---  

## 2. Business Analysis Approach (BABOK – Planning & Monitoring)  

### 2.1 BA Planning Approach  
| Activity | Description | Owner | Artefact |
|----------|-------------|-------|----------|
| **Stakeholder Identification** | Populate stakeholder matrix (Section 4). | Business Analyst | Stakeholder Matrix |
| **Requirements Elicitation Strategy** | Combine workshops, prototype walkthrough, and API‑first interviews. | BA Lead | Elicitation Plan |
| **Requirements Management Process** | Use a centralized JIRA / Confluence backlog; enforce traceability links defined in this BRD. | BA Lead | Requirements Register |
| **Change Control Process** | Any change to a requirement must pass the **Change Advisory Board (CAB)** and be logged in the **Change Log** (Appendix 16). | Change Manager | Change Request Form |

### 2.2 Stakeholder Engagement Strategy  
| Stakeholder | Interaction Mode | Frequency | Primary Deliverable |
|------------|------------------|----------|--------------------|
| **Developers (ASM Squad)** | Demo sessions, Slack Q&A | Daily (PoC) | API usage guide |
| **Product Manager** | Review meetings, walkthroughs | Every 2 days | Generated spec samples |
| **Security Officer** | Compliance audit, log review | End‑of‑day | Audit log report |
| **Hackathon Judges** | Live demo, Q&A | Final presentation | Demo video & score sheet |
| **Ops / Platform Owner** | Operations hand‑off, run‑book review | Post‑PoC | Run‑book & monitoring dashboard |

### 2.3 Requirements Management Process  
1. **Capture** – All elicited statements are entered as Business/Functional/Non‑functional Requirements in the Requirements Register.  
2. **Validate** – Each requirement is reviewed against the **Business Objectives** and the **Traceability Matrix**.  
3. **Prioritize** – MoSCoW method (Must, Should, Could, Won’t).  
4. **Maintain** – Versioned in the repository; changes tracked via the **Change Log**.  

### 2.4 Change Control Process  
| Step | Description |
|------|-------------|
| **1 – Request** | Submit Change Request (CR) with impact analysis. |
| **2 – Review** | CAB evaluates security, cost, and schedule impact. |
| **3 – Decision** | Approve, defer, or reject. |
| **4 – Implementation** | Updated requirement is versioned; downstream artefacts (design, test cases) are refreshed. |
| **5 – Verification** | Acceptance test verifies the change meets the updated requirement. |

---  

## 3. Strategic Context (BABOK – Strategy Analysis)  

### 3.1 Business Need and Opportunity  
| Need | Opportunity |
|------|-------------|
| **Manual creation of technical docs is time‑consuming (≈ 8 hrs per module).** | **AI automation can reduce effort by ~80 %**, freeing engineers for higher‑value work. |
| **Inconsistent documentation leads to mis‑aligned expectations.** | **Standardised AI‑generated templates** enforce uniform style and completeness. |
| **Source code is highly confidential; current ad‑hoc sharing risks leakage.** | **Serverless, encrypted, temporary storage** meets ISO 27001 and eliminates persistent copies. |
| **Hackathon requires a demonstrable AI‑driven solution using AWS.** | **Amazon Bedrock + Lambda** provide a native, cost‑effective AI pipeline. |

### 3.2 Current State Assessment  
- **Process:** Engineers manually write SRS/Functional Specs in Word/Confluence.  
- **Pain Points:** High effort, variable quality, risk of missed functional flows, no audit trail.  
- **Technology:** On‑prem IDEs, local document stores, no automation.  

### 3.3 Future State Vision  
> *A serverless AI Digital Worker that on‑demand receives a source‑code package and feature descriptor, generates accurate, complete, clear, and consistent technical documents within 2 minutes, stores them securely for ≤ 24 h, and provides a downloadable link plus audit logs.*  

### 3.4 Gap Analysis  

| Gap | Current | Target | Remedy |
|-----|---------|--------|--------|
| **Automation** | Manual authoring | AI generation | Implement Bedrock‑driven Lambda workflow. |
| **Consistency** | Varying templates | Single template engine | Embed Markdown template in Lambda; enforce via validation. |
| **Security** | Unencrypted local copies | Encrypted S3 + auto‑delete | Apply SSE‑KMS, lifecycle policies, and cleanup Lambda. |
| **Observability** | No metrics | CloudWatch dashboards | Emit custom metrics (DocsGenerated, Latency). |
| **Scalability** | Limited to one engineer | 5+ docs/day (future) | Design stateless Lambdas, enable concurrency limits. |

### 3.5 Solution Approach  
- **Architecture Style:** Serverless, event‑driven (Step Functions).  
- **Core Services:** API Gateway ➜ Step Functions ➜ Lambda (Orchestrator, Generator, Cleaner) ➜ Amazon Bedrock ➜ S3 (Input/Output) ➜ DynamoDB (Job metadata) ➜ SNS (notification).  
- **Compliance:** ISO 27001‑aligned encryption, audit logs, data residency in `eu‑west‑1`.  
- **Cost Management:** Use Bedrock *Claude‑Instant* (lowest cost), free‑tier Lambda and S3, and budget alerts.  

---  

## 4. Stakeholder Analysis (BABOK – Elicitation & Collaboration)  

### 4.1 Stakeholder Identification Matrix  

| Stakeholder | Role | Interest | Influence | Engagement Strategy |
|-------------|------|----------|-----------|----------------------|
| **ASM Development Squad** | Primary users / builders | High – need fast docs | High – direct contributors | Daily stand‑ups, demo sessions |
| **Product Manager** | Consumer of docs for planning | High – needs uniform spec | Medium | Bi‑daily review of generated docs |
| **QA Lead** | Verifies completeness of specs | High – wants full functional coverage | Medium | Acceptance test walkthroughs |
| **Security Officer** | Oversees data protection | High – compliance & leakage risk | High | Audit log inspection, compliance checklist |
| **Hackathon Judges** | Evaluate solution | High – judging criteria | Low | Live demo, score‑sheet submission |
| **Ops / Platform Owner** | Operates AWS environment | Medium – reliability & cost | Medium | Monitoring dashboard hand‑off |
| **Compliance Auditor (future)** | Periodic audit | Medium – ISO 27001 | Low | Provide audit artefacts (logs, policies) |

### 4.2 Stakeholder Needs and Expectations  

| Stakeholder | Need | Expected Outcome |
|-------------|------|------------------|
| ASM Squad | One‑click generation of SRS/Functional Spec | Docs delivered within 2 min, downloadable via API |
| Product Manager | Consistent template, traceable version | Uniform headings, version number, change log |
| QA Lead | Complete functional coverage | No missing user flows; validation rules pass |
| Security Officer | No persistent source code, encrypted transit | Auto‑delete after 24 h, KMS‑encrypted S3 |
| Hackathon Judges | Demonstrable AI pipeline, quality metrics | Live run showing ≥ 2 docs, quality checklist score |
| Ops Owner | Observability & cost control | CloudWatch dashboards, budget alerts |

### 4.3 Communication Plan  

| Audience | Channel | Frequency | Owner |
|----------|--------|-----------|-------|
| All Stakeholders | Slack channel `#docgenius-worker` | Real‑time updates | BA Lead |
| Product Manager & QA | Email summary + Confluence page | Every 2 days | Product Owner |
| Security Officer | Secure log export (CSV) | End‑of‑day | Security Champion |
| Hackathon Judges | Live Zoom demo | Final day | Team Lead |
| Ops Owner | CloudWatch dashboard link | Continuous | Ops Lead |

---  

## 5. Business Context and Objectives  

### 5.1 Business Goals and Objectives  

| ID | Objective | Description |
|----|-----------|-------------|
| **BO‑001** | **Accelerate documentation creation** | Reduce manual effort for SRS/Functional Spec creation by ≥ 80 % (target 8 hrs → ≤ 1.5 hrs). |
| **BO‑002** | **Ensure documentation consistency** | All generated docs must follow a single, approved template and meet the four quality criteria (Accuracy, Completeness, Clarity, Consistency). |
| **BO‑003** | **Protect source‑code confidentiality** | Process source code in encrypted storage, auto‑delete within 24 h, complying with ISO 27001. |
| **BO‑004** | **Demonstrate AI‑driven automation** | Deliver a functioning PoC that showcases end‑to‑end generation of ≥ 2 technical documents for distinct NopCommerce modules within the hackathon timeframe. |
| **BO‑005** | **Establish reusable blueprint** | Produce Architecture Repository artefacts (CDK, prompts, SBBs) reusable for future enterprise‑wide documentation automation. |

### 5.2 Success Criteria and KPIs  

| KPI | Target | Measurement Method |
|-----|--------|--------------------|
| **Docs per execution** | ≥ 2 distinct modules | Count of completed jobs in DynamoDB. |
| **Quality Score** (accuracy, completeness, clarity, consistency) | ≥ 4/5 average (peer review) | Review checklist completed by QA. |
| **Processing latency** | ≤ 2 min per document | CloudWatch metric `ProcessingTime`. |
| **Availability** | ≥ 99 % during business hours (08:00‑18:00 UTC) | CloudWatch `Availability` alarm. |
| **Data retention compliance** | 100 % of source archives deleted ≤ 24 h | S3 lifecycle + Lambda audit log. |
| **Cost** | ≤ $150 total AWS spend for PoC | AWS Cost Explorer report. |

### 5.3 Critical Success Factors  

- Accurate prompt engineering for Bedrock.  
- Strict IAM and KMS policies to avoid data leakage.  
- Effective orchestration (Step Functions) to guarantee cleanup on success/failure.  
- Clear acceptance criteria and sign‑off from QA & Security.  

### 5.4 Business Constraints  

| Constraint | Impact |
|------------|--------|
| **AWS‑only services** | Limits use to Bedrock, Lambda, S3, Step Functions, DynamoDB, SNS. |
| **Free‑tier budget** | Requires cost‑efficient model (Claude‑Instant) and tight monitoring. |
| **24 h data retention** | Must implement lifecycle policies and cleanup Lambda. |
| **Timebox 48 h** | All design, implementation, and testing must fit within 2 days. |
| **No external integrations** | No CI/CD or Confluence connectors for PoC. |

---  

## 6. Business Process Analysis (BABOK – Requirements Analysis)  

### 6.1 Current State (As‑Is) Process  

1. **Requirement Capture** – Business analyst writes functional requirements in Word.  
2. **Manual Spec Authoring** – Engineer reads source code, writes SRS/Functional Spec manually.  
3. **Review & Approval** – QA and PM review the document, iterate.  
4. **Storage** – Docs stored in shared drive (unstructured).  

**Pain Points**  

- High manual effort & cycle time.  
- Inconsistent style and missing functional flows.  
- No audit trail of who generated/edited the document.  
- Source code may be shared in unsecured email attachments during review.  

### 6.2 Future State (To‑Be) Process  

1. **Upload Package** – Developer/CI uploads a ZIP of source code + JSON feature descriptor to the API endpoint.  
2. **Orchestration** – Step Functions invoke Lambdas: store package, call Bedrock, format output, store result, send notification.  
3. **Automatic Cleanup** – After 24 h, cleanup Lambda deletes the input archive and any residual artefacts.  
4. **Delivery** – User receives a presigned S3 URL (PDF/Markdown) and an audit log entry.  

**Improvements**  

- **Speed:** ≤ 2 min per document vs. hours.  
- **Quality:** Template‑driven, validated against business rules.  
- **Security:** Encrypted, temporary storage, immutable audit logs.  
- **Scalability:** Stateless Lambdas support parallel runs.  

### 6.3 Process Gap Analysis  

| Gap | As‑Is | To‑Be | Required Change |
|-----|-------|-------|-----------------|
| **Automation** | Manual authoring | AI generation via Bedrock | Implement Lambda workflow. |
| **Consistency** | Free‑form Word | Fixed Markdown template + validation | Embed template in code, add QA rules. |
| **Security** | Unencrypted zip files on local drives | SSE‑KMS encrypted S3 + auto‑delete | IAM, KMS, lifecycle policies. |
| **Visibility** | No metrics | CloudWatch dashboards & SNS alerts | Emit custom metrics & notifications. |
| **Traceability** | Email threads | Structured audit logs in CloudTrail/DynamoDB | Log every state transition. |

### 6.4 Business Rules  

| Rule ID | Description |
|---------|-------------|
| **BR‑A1** | All source‑code archives must be encrypted using KMS key `alias/docgenius-worker-key`. |
| **BR‑A2** | Generated documents must contain a header with: Project name, Module, Generation timestamp, Version. |
| **BR‑A3** | If Bedrock returns an error, the job status must be marked **Failed** and the source archive deleted. |
| **BR‑A4** | No more than **5** documents may be generated per day in the PoC phase. |
| **BR‑A5** | All API calls must be authenticated via AWS IAM (or Cognito for PoC). |

---  

## 7. Requirements Specification (BABOK – Requirements Analysis & Design Definition)  

### 7.1 Business Requirements (BR)  

| ID | Requirement | Rationale | Supports |
|----|-------------|----------|----------|
| **BR‑001** | The system shall automatically generate technical specifications (SRS and Functional Spec) from a NopCommerce source‑code package and a corresponding feature‑descriptor JSON. → Addresses: **BO‑001**, **BO‑002** |
| **BR‑002** | Generated documents shall satisfy the four quality criteria: **Accuracy, Completeness, Clarity, Consistency**. → Addresses: **BO‑002** |
| **BR‑003** | All source‑code artefacts shall be stored encrypted at rest and in transit, and automatically deleted no later than 24 h after successful or failed processing. → Addresses: **BO‑003** |
| **BR‑004** | An API endpoint shall be provided to trigger a generation job and to retrieve the resulting PDF/Markdown artefacts. → Addresses: **BO‑001**, **BO‑004** |
| **BR‑005** | The solution shall achieve an end‑to‑end processing latency of ≤ 2 minutes per document and an availability of ≥ 99 % during business hours. → Addresses: **BO‑001**, **BO‑005** |
| **BR‑006** | All operations shall be performed using **AWS‑native services only**. → Addresses: **BO‑005**, **Constraint** |
| **BR‑007** | The solution shall produce audit logs (job‑ID, timestamps, status, user) that are immutable and retained for 30 days. → Addresses: **BO‑003**, **BO‑005** |

### 7.2 Functional Requirements (FR)  

| ID | Requirement | Addresses |
|----|-------------|-----------|
| **FR‑01** | **Spec Generation** – Lambda **Generator** shall retrieve the source archive and feature descriptor, construct a Bedrock prompt, invoke the LLM, and receive the spec text. → Addresses: **BR‑001** |
| **FR‑02** | **Document Formatting** – Generator shall convert LLM text to Markdown, then to PDF (using wkhtmltopdf library). → Addresses: **BR‑001**, **BR‑002** |
| **FR‑03** | **Secure Storage** – Input archive stored in S3 bucket `docgenius-worker-input` with SSE‑KMS; output stored in `docgenius-worker-output` with same encryption. → Addresses: **BR‑003** |
| **FR‑04** | **API Service** – API Gateway endpoint **POST /generate‑spec** shall accept multipart/form‑data (ZIP + JSON) and return a job‑ID. → Addresses: **BR‑004** |
| **FR‑05** | **Orchestration & Cleanup** – Step Functions workflow shall invoke Lambdas in order, handle retries, and trigger **Cleanup** Lambda to delete objects after 24 h or on failure. → Addresses: **BR‑003**, **BR‑005** |
| **FR‑06** | **Notification** – On completion (success or failure) the system shall publish a message to SNS topic `DocGeniusWorkerEvents` with a presigned URL (if success) or error details. → Addresses: **BR‑004**, **BR‑007** |
| **FR‑07** | **Metadata Persistence** – DynamoDB table `DocGeniusWorkerJobs` shall store job‑ID, status, timestamps, user, and S3 object keys. → Addresses: **BR‑007** |
| **FR‑08** | **Observability** – Lambdas shall emit custom CloudWatch metrics: `DocsGenerated`, `ProcessingTimeMs`, `FailedJobs`. → Addresses: **BR‑005**, **BR‑007** |

### 7.3 Non‑Functional Requirements (NFR)  

| ID | Requirement | Supports |
|----|-------------|----------|
| **NFR‑PERF‑001** | Average processing latency ≤ 2 minutes per document (including LLM inference). → Supports: **FR‑01**, **FR‑02**, **FR‑05** |
| **NFR‑SEC‑001** | All data at rest encrypted with AWS KMS; in‑transit encrypted with TLS 1.2. → Supports: **FR‑03**, **BR‑003** |
| **NFR‑SCAL‑001** | System shall handle up to **5 documents per day** (PoC) and scale horizontally to 10 docs/day with no code changes. → Supports: **FR‑01**, **FR‑05**, **BR‑005** |
| **NFR‑REL‑001** | Availability ≥ 99 % during business hours (08:00‑18:00 UTC). → Supports: **FR‑04**, **FR‑05**, **BR‑005** |
| **NFR‑COST‑001** | Total AWS cost for PoC shall not exceed **$150**; budget alerts set at 80 % of limit. → Supports: **BR‑006**, **BR‑005** |
| **NFR‑COMP‑001** | System shall be **serverless**; no persistent VMs or containers. → Supports: **BR‑006**, **BR‑001** |
| **NFR‑MAINT‑001** | All IaC assets (CDK) shall be version‑controlled; changes must pass automated lint and security scans. → Supports: **BR‑007**, **BR‑005** |

---  

## 8. Requirements Analysis & Design Definition (BABOK – Requirements Analysis & Design Definition)  

### 8.1 User Stories and Acceptance Criteria  

| ID | User Story | Implements | Priority | Story Points |
|----|------------|-----------|----------|--------------|
| **US‑001** | *As a **developer**, I want to POST a ZIP of source code and a JSON feature descriptor to `/generate-spec` so that I receive a presigned download link for the generated SRS within minutes.* → Implements: **FR‑04**, **FR‑01**, **FR‑02** | **FR‑04**, **FR‑01**, **FR‑02** | Must | 8 |
| **US‑002** | *As a **security officer**, I want the system to automatically delete the source‑code archive after processing so that no proprietary code remains in storage.* → Implements: **FR‑05**, **FR‑03** | **FR‑05**, **FR‑03** | Must | 5 |
| **US‑003** | *As a **product manager**, I want to receive an email (via SNS) containing a presigned URL to the PDF/Markdown spec so that I can review it without logging into AWS.* → Implements: **FR‑06**, **FR‑02** | **FR‑06**, **FR‑02** | Should | 3 |
| **US‑004** | *As an **operations engineer**, I want to view a CloudWatch dashboard showing `DocsGenerated`, `ProcessingTimeMs`, and error counts so that I can ensure SLA compliance.* → Implements: **FR‑08**, **FR‑05** | **FR‑08**, **FR‑05** | Should | 4 |
| **US‑005** | *As a **QA lead**, I want a validation step that checks the generated spec for mandatory sections (e.g., Functional Overview, Non‑functional Requirements) and flags missing items.* → Implements: **FR‑02**, **FR‑01** | **FR‑02**, **FR‑01** | Could | 3 |

#### Acceptance Criteria (Given‑When‑Then)  

**US‑001**  

- **AC‑001:** *Given* a valid authenticated request with a ZIP ≤ 50 MB and a well‑formed JSON, *when* the POST is sent, *then* the API returns `202 Accepted` with a `jobId`.  
- **AC‑002:** *Given* the job is completed successfully, *when* the user queries `/job-status/{jobId}`, *then* the response contains a presigned URL valid for 24 h.  
- **AC‑003:** *Given* the processing exceeds 2 minutes, *then* the status is still `Succeeded` but a warning flag is set in the response.  

**US‑002**  

- **AC‑001:** *Given* a job finishes (success or failure), *when* 24 h elapse, *then* the source archive is no longer present in `docgenius-worker-input`.  
- **AC‑002:** *Given* the cleanup Lambda runs, *when* it attempts to delete the object, *then* an audit log record is written with `DeleteAction=Success`.  

**US‑003**  

- **AC‑001:** *Given* a job succeeds, *when* the SNS message is published, *then* the email body contains the presigned URL and job metadata.  

(Additional ACs for US‑004 and US‑005 follow the same G‑W‑T pattern.)

### 8.2 Use Case Specifications  

#### UC‑001: Trigger Documentation Generation  

- **Primary Actor:** Developer (or CI system)  
- **Secondary Actors:** API Gateway, Step Functions, Lambda, Bedrock, S3, SNS  
- **Preconditions:** Developer has valid IAM credentials; source ZIP and feature JSON are prepared.  
- **Postconditions:** Job entry created in DynamoDB; output document stored; notification sent; source archive marked for deletion.  
- **Main Success Scenario:**  

  1. Developer calls POST `/generate-spec` with payload.  
  2. API Gateway validates request and writes payload to `docgenius-worker-input` bucket.  
  3. Step Functions start, invoking **Source Loader** Lambda.  
  4. **Spec Generator** Lambda builds Bedrock prompt and receives spec text.  
  5. Formatter converts text to Markdown → PDF.  
  6. Output stored in `docgenius-worker-output`.  
  7. DynamoDB job record updated to **Succeeded**.  
  8. SNS sends notification with presigned URL.  
  9. Cleanup Lambda scheduled for 24 h later.  

- **Alternative Flows:**  

  - **A1 – Validation Failure:** Input fails schema check → Step Functions transition to **Failed**; user receives error response.  
  - **A2 – LLM Error:** Bedrock returns error → job marked **Failed**, source archive deleted, SNS error notification sent.  

- **Business Rules Applied:** BR‑A1, BR‑A3, BR‑A4.  

#### UC‑002: Retrieve Generated Document  

- **Primary Actor:** Developer / Product Manager  
- **Preconditions:** Job status is **Succeeded**, presigned URL not expired.  
- **Main Success Scenario:** Developer clicks URL → downloads PDF/Markdown.  
- **Alternative Flow:** URL expired → system returns 410 Gone; user must re‑trigger job.  

### 8.3 User Interface Design Requirements (BABOK – Design Definition)  

#### 8.3.1 UI/UX Design Principles  

- **Usability:** Simple one‑page web form (optional PoC UI) with clear field labels (ZIP, JSON, Submit).  
- **Consistency:** Same visual style as other FHM hackathon tools (Figma assets).  
- **Accessibility:** WCAG 2.1 AA – keyboard navigation, ARIA labels for file inputs.  
- **Responsiveness:** Works on desktop browsers (Chrome/Firefox) and tablets.  

#### 8.3.2 Mockups & Prototypes  

- **Low‑Fidelity Wireframe:** Single section with two file‑upload controls and a “Generate” button.  
- **High‑Fidelity Prototype (future):** Dashboard showing recent jobs, status colors (green = Success, red = Failed), and a “Download” link per row.  

#### 8.3.3 Interaction Flows  

| Flow | Steps |
|------|-------|
| **Generate Spec** | 1. User selects ZIP → 2. User selects JSON → 3. Click *Generate* → 4. UI shows “Job submitted, ID = …” → 5. Polls `/job-status/{id}` → 6. On success, displays download button. |
| **Error Handling** | 1. API returns validation error → UI shows inline message next to offending field. |
| **Help** | Tooltip on each field explaining size limits, required format. |

#### 8.3.4 Accessibility (WCAG)  

- **Keyboard Navigation:** Tab order defined; Enter key triggers submit.  
- **Screen Reader:** `aria-label` attributes on file inputs.  
- **Contrast Ratio:** Minimum 4.5:1 for text against background.  
- **Alt Text:** All icons have descriptive `alt` text.  

---  

## 9. Solution Design Definition (BABOK – Design Definition)  

### 9.1 Solution Components Design  

| Component | Description | Reuse Potential |
|-----------|-------------|-----------------|
| **API Gateway** | Exposes `POST /generate-spec` and `GET /job-status/{id}`. | Reusable for any AI‑driven service. |
| **Step Functions State Machine** | Orchestrates Lambdas, implements retries & compensation. | Generic workflow pattern. |
| **Lambda – Source Loader** | Persists incoming ZIP/JSON to S3, validates schema. | Can be reused for other file‑ingestion pipelines. |
| **Lambda – Spec Generator** | Builds Bedrock prompt, calls LLM, formats output. | Core AI generation block; reusable across domains. |
| **Lambda – Cleanup Worker** | Deletes source artefacts after 24 h or on failure. | Reusable secure‑delete utility. |
| **Amazon Bedrock** | Provides Claude‑Instant LLM for text generation. | Service‑agnostic AI layer. |
| **S3 Buckets** | `docgenius-worker-input` (encrypted, lifecycle 1 day) and `docgenius-worker-output` (encrypted, TTL 1 day). | Standard for asset storage. |
| **DynamoDB Table** | Stores job metadata, status, timestamps. | Generic job‑tracking store. |
| **SNS Topic** | Publishes success/failure notifications. | Can feed Slack, Teams, email. |
| **CloudWatch** | Metrics, alarms, dashboards. | Enterprise‑wide observability. |
| **IAM Roles & KMS Keys** | Fine‑grained permissions; encryption. | Security baseline for all serverless apps. |

### 9.2 Interface Design Specifications  

| Interface | Type | Protocol | Key Attributes |
|-----------|------|----------|----------------|
| **API Endpoint** | REST | HTTPS (TLS 1.2) | `POST /generate-spec` (multipart/form‑data), `GET /job-status/{id}` (JSON) |
| **Lambda – Bedrock Call** | Service API | HTTPS (AWS SDK) | Model ID `anthropic.claude-v2:1`, max tokens 4 k |
| **S3 Object Access** | REST/SDK | HTTPS | Presigned URL TTL 24 h, SSE‑KMS `alias/docgenius-worker-key` |
| **SNS Notification** | Pub/Sub | HTTPS (HTTPS endpoint) | Message JSON: `{jobId, status, url?, error}` |
| **CloudWatch Metric** | Custom | – | `DocsGenerated`, `ProcessingTimeMs`, `FailedJobs` |

### 9.3 Solution Architecture Alignment  

- **Enterprise Architecture (TOGAF)** – Architecture Vision (Section 3) and Business Architecture (Section 4) map directly to this solution.  
- **Technology Stack** – All components are AWS‑native, complying with **Principle P‑02 (Serverless First)** and **Principle P‑03 (AI‑Driven Automation)**.  
- **Security Architecture** – Implements **Principle P‑01 (Secure‑by‑Design)** via KMS, IAM least‑privilege, VPC endpoints.  
- **Integration Pattern** – Event‑driven (Step Functions) matches TOGAF **Integration View** and aligns with the **AWS Well‑Architected** Operational Excellence pillar.  

---  

## 10. Data Requirements (BABOK – Requirements Analysis)  

### 10.1 Conceptual Data Model  

- **Job** (JobID, Status, Submitter, SubmissionTime, CompletionTime, InputObjectKey, OutputObjectKey, Metrics).  
- **SourceArchive** (S3Key, Size, UploadTime, EncryptionKeyID).  
- **GeneratedDocument** (S3Key, Format, Size, GenerationPrompt, LLMModelVersion).  

### 10.2 Data Entities and Attributes  

| Entity | Attributes |
|--------|------------|
| **Job** | JobID (PK), Status (Enum), Submitter (IAM ARN), SubmitTS, CompleteTS, InputKey, OutputKey, LatencyMs, ErrorMessage |
| **SourceArchive** | S3Key, MD5Hash, SizeBytes, KMSKeyARN, TTL |
| **GeneratedDocument** | S3Key, Format (`pdf`/`md`), SizeBytes, GenerationPrompt (text), ModelVersion, CreatedTS |

### 10.3 Data Relationships  

- **Job → SourceArchive** (one‑to‑one, via InputKey).  
- **Job → GeneratedDocument** (zero‑or‑one to one, via OutputKey).  

### 10.4 Data Quality Requirements  

| Requirement | Metric |
|-------------|--------|
| **Completeness** | All mandatory fields (JobID, Status, timestamps) must be non‑null. |
| **Integrity** | InputKey must reference an existing object in `docgenius-worker-input`. |
| **Accuracy** | MD5 hash of uploaded archive must match stored value. |
| **Timeliness** | Job CompletionTime – SubmitTS ≤ 2 min (performance). |

### 10.5 Data Governance and Compliance  

- **Retention:** SourceArchive and GeneratedDocument objects automatically deleted after 24 h (S3 lifecycle).  
- **Encryption:** SSE‑KMS with key `alias/docgenius-worker-key`.  
- **Audit:** All read/write actions logged to CloudTrail; immutable for 30 days.  
- **Access Control:** IAM role `DocGeniusWorkerJobRole` limited to required actions; no public access.  

---  

## 11. Integration and Interface Requirements  

### 11.1 System Integration Points  

| System | Integration Type | Direction | Protocol |
|--------|------------------|-----------|----------|
| **Amazon Bedrock** | Service call (LLM) | Digital Worker → Bedrock | HTTPS (AWS SDK) |
| **AWS SNS** | Publish | Digital Worker → SNS | HTTPS (Publish API) |
| **AWS CloudWatch** | Metrics | Digital Worker → CloudWatch | CloudWatch API |
| **External UI (future)** | REST API consumption | UI → API Gateway | HTTPS (REST) |

### 11.2 API Specifications  

| Method | URI | Request | Response | Status Codes |
|--------|-----|---------|----------|--------------|
| **POST** | `/generate-spec` | `multipart/form-data` (file `archive.zip`, field `descriptor.json`) | `{jobId: string}` | 202 Accepted, 400 Bad Request, 401 Unauthorized |
| **GET** | `/job-status/{jobId}` | – | `{jobId, status, downloadUrl?, errorMessage?}` | 200 OK, 404 Not Found, 401 Unauthorized |
| **GET** | `/health` | – | `{status: "OK"}` | 200 OK |

### 11.3 Data Exchange Formats  

- **Input Archive:** ZIP (binary).  
- **Feature Descriptor:** JSON (schema defined in Appendix 16).  
- **Job Status:** JSON (snake_case).  
- **Notification Message:** JSON (camelCase).  

### 11.4 Interface Requirements  

- **Idempotency:** Re‑submitting the same `jobId` returns the existing status.  
- **Error Handling:** Detailed error payload (`errorCode`, `message`) for client debugging.  
- **Rate Limiting:** API Gateway throttling – max 10 requests/second (PoC).  

---  

## 12. Requirements Traceability Matrix  

| Business Objective | Business Requirement | Functional Requirement | User Story | Priority | Status |
|-------------------|---------------------|----------------------|------------|----------|--------|
| **BO‑001** | **BR‑001** | **FR‑01** | **US‑001** | Must | Draft |
| **BO‑001** | **BR‑004** | **FR‑04** | **US‑001** | Must | Draft |
| **BO‑001** | **BR‑005** | **FR‑08** | **US‑004** | Should | Draft |
| **BO‑002** | **BR‑002** | **FR‑02** | **US‑005** | Should | Draft |
| **BO‑003** | **BR‑003** | **FR‑03** | **US‑002** | Must | Draft |
| **BO‑003** | **BR‑007** | **FR‑07** | **US‑004** | Should | Draft |
| **BO‑004** | **BR‑006** | **FR‑06** | **US‑003** | Must | Draft |
| **BO‑005** | **BR‑005** | **FR‑05** | **US‑001** | Must | Draft |
| **BO‑005** | **BR‑007** | **FR‑07** | **US‑004** | Should | Draft |

---  

## 13. Assumptions, Dependencies, and Constraints  

### 13.1 Business Assumptions  

| # | Assumption |
|---|------------|
| A‑01 | Developers will provide well‑structured feature‑descriptor JSON following the agreed schema. |
| A‑02 | The PoC will be demonstrated only within the `eu‑west‑1` AWS region. |
| A‑03 | Hackathon judges accept a 48‑hour delivery window for the PoC. |

### 13.2 Technical Constraints  

| # | Constraint |
|---|------------|
| C‑01 | Only AWS‑native services may be used (Bedrock, Lambda, Step Functions, S3, DynamoDB, SNS). |
| C‑02 | All Lambdas must remain **stateless**; any state persisted in S3/DynamoDB. |
| C‑03 | Total AWS spend for PoC limited to **$150**. |
| C‑04 | Source code must never leave the AWS region. |
| C‑05 | No external SaaS (e.g., OpenAI, third‑party storage) allowed. |

### 13.3 External Dependencies  

| Dependency | Provider | Impact |
|------------|----------|--------|
| **Amazon Bedrock** | AWS | LLM availability and pricing affect latency & cost. |
| **AWS Free Tier** | AWS | Provides cost cushion; exceeding limits triggers charges. |
| **NopCommerce Sample Modules** | FHM team | Needed for test input data. |

### 13.4 Regulatory & Compliance Constraints  

- Must align with **ISO 27001** (encryption, audit logs).  
- Must respect **GDPR** – data residency in EU region, 24 h deletion.  

---  

## 14. Acceptance Criteria and Definition of Done  

### 14.1 Solution Acceptance Criteria  

| Criterion | Verification Method |
|-----------|---------------------|
| **AC‑001** – Generate ≥ 2 distinct technical docs in one run. | Execute PoC with two NopCommerce modules; count output objects. |
| **AC‑002** – All docs meet the four quality criteria (≥ 4/5 score). | Independent QA reviewer fills checklist; average score ≥ 4. |
| **AC‑003** – No source archive remains after 24 h. | Query S3 after 24 h; confirm object not present; review CloudTrail. |
| **AC‑004** – API latency ≤ 2 min (average) for successful jobs. | CloudWatch metric `ProcessingTimeMs` < 120 000 ms. |
| **AC‑005** – System availability ≥ 99 % during 08:00‑18:00 UTC. | CloudWatch uptime alarm over 7‑day period. |
| **AC‑060** – Total AWS cost ≤ $150 for PoC. | AWS Cost Explorer report. |
| **AC‑070** – All artifacts (CDK code, prompts, design docs) stored in the Architecture Repository. | Repository audit. |

### 14.2 Definition of Done (DoD)  

- **Code** – Implemented, peer‑reviewed, and passed unit tests (> 80 % coverage).  
- **IaC** – CDK stack deployed to `dev` environment without errors.  
- **Documentation** – API spec (OpenAPI), prompt library, and run‑book published in Confluence.  
- **Testing** – End‑to‑end test covering all acceptance criteria executed and passed.  
- **Security Review** – IAM policies approved; KMS key usage validated.  
- **Stakeholder Sign‑off** – Product Owner, Security Officer, and Hackathon Judges sign the acceptance matrix.  

---  

## 15. Solution Evaluation (BABOK – Solution Evaluation)  

### 15.1 Evaluation Metrics  

| Metric | Target | Measurement Tool |
|--------|--------|-----------------|
| **Doc Generation Count** | ≥ 2 per execution | DynamoDB query |
| **Quality Score** (Accuracy, Completeness, Clarity, Consistency) | ≥ 4/5 each | QA checklist |
| **Latency** | ≤ 2 min average | CloudWatch `ProcessingTimeMs` |
| **Availability** | ≥ 99 % (business hours) | CloudWatch `ServiceAvailability` alarm |
| **Cost** | ≤ $150 total | AWS Cost Explorer |
| **Security Compliance** | 100 % encrypted, 0 leakage incidents | GuardDuty, CloudTrail audit |

### 15.2 Performance Measurement  

- **Baseline** – Manual authoring: ~8 hrs per module, cost = staff time.  
- **PoC Result** – Automated: ≤ 2 min, cost = AWS usage (< $150).  
- **Benefit Realisation** – 80 % effort reduction → estimated annual savings of **≈ $30 k** (based on 200 modules/year).  

### 5‑Year Outlook (Future Evaluation)  

| Year | Expected Docs/Day | Scaling Strategy |
|------|-------------------|------------------|
| **2026** (PoC) | 2 | Serverless, single Lambda concurrency. |
| **2027** | 5 | Increase Lambda memory, enable reserved concurrency; add SQS buffer. |
| **2028** | 10+ | Introduce Amazon SageMaker fine‑tuned model for domain‑specific accuracy. |
| **2029** | Enterprise‑wide | Integrate with Confluence via API, add RBAC, multi‑region deployment. |

---  

## 16. Appendices  

### 16.1 Glossary  

| Term | Definition |
|------|------------|
| **AI Digital Worker** | Serverless AI service that performs a business task autonomously. |
| **Bedrock** | AWS managed service providing access to pretrained LLMs (e.g., Claude‑Instant). |
| **Step Functions** | AWS service for orchestrating serverless workflows. |
| **SSE‑KMS** | Server‑Side Encryption with AWS Key Management Service. |
| **Presigned URL** | Time‑limited URL granting temporary S3 object access. |
| **PoC** | Proof of Concept – limited‑scope demonstration. |
| **MoSCoW** | Prioritisation technique (Must, Should, Could, Won’t). |

### 16.2 Supporting Documentation  

- **Architecture Vision & Principles** – TOGAF 10 Phase A (Enterprise Architecture Document).  
- **CDK Infrastructure Code** – `infra/cdk/` (GitHub repo).  
- **Prompt Library** – `ai/prompts/` (Markdown files).  
- **Test Plan** – `test/plan.md`.  
- **Run‑book** – `ops/runbook.md`.  

### 16.3 Change Log  

| Version | Date | Author | Change Description |
|---------|------|--------|---------------------|
| 1.0 | 10 Jan 2026 | Lead Business Analyst | Initial BRD creation (aligned with EA doc). |
| 1.1 | 12 Jan 2026 | Architecture Lead | Updated NFR‑COST after budget review. |
| 1.2 | 14 Jan 2026 | Security Champion | Added ISO 27001 audit log details. |

---  

**Prepared by:**  
*Lead Business Analyst – IIBA Certified*  
*Enterprise Architecture Team – FHM Hackathon*  

*End of Document*