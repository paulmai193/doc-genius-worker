# Enterprise Architecture Document (TOGAF 10)  
**Project:** FHM Hackathon Q4 – “Digital Worker Factory” – AI‑Driven Technical Documentation Generator  
**Version:** 1.0 (PoC) – 10 January 2026  

---  

## 1. Introduction
| Item | Description |
|------|-------------|
| **Purpose** | Define a complete, TOGAF‑aligned architecture for an **AI Digital Worker** that automatically generates high‑quality technical documents (e.g., SRS, Functional Specification) from NopCommerce source code and feature descriptors. |
| **Scope** | • Specification of the Digital Worker (Phase 1 – Spec‑Driven Development). <br>• Design of the AWS‑based platform that hosts the worker, processes source code, and stores artifacts temporarily. <br>• Supporting governance, risk, and compliance artefacts needed for a PoC that can be scaled to a production environment. |
| **Audience** | Architecture team, hackathon judges, development squad (ASM), security & compliance officers, AWS Ops, future product owners. |
| **Reference Architecture** | TOGAF 10 Architecture Development Method (ADM) – Phases A–F, Architecture Repository, Architecture Governance. |
| **Document Status** | Draft – Review by stakeholders scheduled 12 Jan 2026. |

---

## 2. Requirements Management
### 2.1 Architecture Requirements
| # | Requirement | Category | Priority | Source |
|---|--------------|----------|----------|--------|
| R‑01 | Generate **≥ 2 technical documents** for distinct NopCommerce modules per execution. | Functional | High | Hackathon spec |
| R‑02 | Documents must satisfy **Accuracy, Completeness, Clarity, Consistency**. | Quality | High | Hackathon spec |
| R‑03 | Use **AWS services** (Bedrock, Lambda, Step Functions, S3) exclusively. | Technical | High | Hackathon spec |
| R‑04 | Process **source code** securely: temporary storage ≤ 24 h, auto‑delete on success/failure. | Security | High | Clarification 5 |
| R‑05 | Support **up to 5 documents per day** after PoC. | Capacity | Medium | Clarification 3 |
| R‑06 | No external integration required (stand‑alone PoC). | Boundary | Medium | Clarification 4 |
| R‑07 | Provide **API endpoint** to trigger worker and retrieve generated PDFs/Markdown. | Functional | Medium | Derived |
| R‑08 | Execution latency ≤ 2 min per document (including LLM inference). | Performance | Medium | Derived |
| R‑09 | System must be **highly available** (≥ 99 % during business hours) and **audit‑able**. | Non‑functional | Medium | Derived |
| R‑10 | Follow **ISO 27001‑aligned** data handling (temporary storage, encryption at rest/in‑transit). | Compliance | High | Clarification 5 |

### 2.2 Constraints & Assumptions
| Constraint | Detail |
|------------|--------|
| **AWS‑only** | Only AWS native services can be used; no third‑party SaaS. |
| **Statelessness** | Lambdas must be stateless; all state persisted in S3 or Step Functions. |
| **Cost** | PoC budget limited to the free tier + modest usage; design for cost‑efficiency. |
| **Skill set** | Team proficient in Python, AWS CDK, and Prompt Engineering for Bedrock. |
| **Data privacy** | Source code never leaves AWS region (choose `eu‑west‑1`). |
| **Timebox** | PoC to be delivered within **2 days** from now. |
| **No legacy integration** | Fresh repository, no need to connect to existing CI/CD or Docs portals. |

---

## 3. Architecture Vision (Phase A)
### 3.1 Business Drivers & Objectives
| Driver | Objective |
|--------|------------|
| **Speed to market** | Automate creation of technical specs to reduce manual effort by ~80 %. |
| **Consistency** | Ensure all generated docs follow a single template and style guide. |
| **Scalability** | Architecture must allow scaling from 2 → 5+ docs/day without redesign. |
| **Security & compliance** | Protect proprietary source code and meet ISO 27001 data‑handling controls. |
| **Innovation** | Showcase AI‑augmented engineering using AWS Bedrock LLM. |

### 3.2 Stakeholder Concerns
| Stakeholder | Concern | Desired Outcome |
|-------------|---------|-----------------|
| **Developers (ASM)** | Accuracy of generated specs; ease of triggering worker. | Docs match code behavior, simple CLI/API. |
| **QA / Test Leads** | Completeness – all functional flows captured. | No missing requirements. |
| **Product Managers** | Clear, consistent format for downstream planning. | Uniform templates, versioned artifacts. |
| **Security Officer** | No leakage of source code; secure deletion. | Automated purge, encrypted storage. |
| **Hackathon Judges** | Demonstrable end‑to‑end flow, measurable quality. | Live demo with two modules, score sheet. |

### 3.3 Architecture Vision Statement
> *“Deliver a secure, AWS‑native AI Digital Worker that, on demand, transforms NopCommerce source code and feature descriptions into high‑quality technical specifications, achieving a repeatable, cost‑effective proof‑of‑concept within 48 hours, and establishing a reusable blueprint for enterprise‑wide documentation automation.”*

---

## 4. Business Architecture (Phase B)

### 4.1 Business Capabilities
| Capability | Description | Owner |
|------------|-------------|-------|
| **Automated Specification Generation** | AI‑driven conversion of code & feature data → SRS/Functional Specs. | ASM – Engineering Lead |
| **Document Management & Delivery** | Store generated docs temporarily, provide download links, clean‑up. | Ops – Platform Owner |
| **Trigger & Orchestration** | API + Step Functions workflow to start generation, monitor status. | DevOps – CI/CD Lead |
| **Quality Assurance** | Validation rules (template compliance, completeness checks) before release. | QA – Lead Engineer |
| **Security & Auditing** | Encrypt data, log actions, enforce deletion policy. | Security – InfoSec Lead |

### 4.2 Value Streams
1. **Requirement Capture → AI Generation → Review → Publish**  
   - *Input*: Source code ZIP, feature description JSON.  
   - *Output*: PDF/Markdown spec stored in S3 (TTL 24 h).  

2. **Feedback Loop → Model Prompt Refinement → Re‑run**  
   - *Input*: Review comments.  
   - *Output*: Updated prompts, higher accuracy for next runs.

### 4.3 Organization Structure (simplified for PoC)
```
+-------------------+
| ASM Digital Worker|
|   Squad (5 ppl)  |
+----+------+-------+
     |      |
  Dev  QA   Ops
```
- **Product Owner** – defines modules & quality criteria.  
- **Lead Engineer** – owns Lambda code & Bedrock prompt library.  
- **Security Champion** – validates data‑privacy controls.  

---

## 5. Information Systems Architecture (Phase C)

### 5.1 Data Architecture
| Data Object | Source | Storage | Retention | Security |
|------------|--------|---------|-----------|----------|
| **Source Code Archive** | Uploaded ZIP (via API) | S3 bucket `digital-worker-input` (encrypted SSE‑KMS) | ≤ 24 h (auto‑delete) | IAM role `WorkerInputAccess` (read/write limited) |
| **Feature Descriptor** | JSON payload | Same input bucket | ≤ 24 h | Same controls |
| **Generated Spec** | LLM output (text) → PDF/Markdown | S3 bucket `digital-worker-output` (encrypted) | ≤ 24 h (auto‑delete) | IAM role `WorkerOutputAccess` |
| **Execution Log** | Step Functions & Lambda logs | CloudWatch Logs (log group `digital-worker`) | 30 days retention | KMS‑encrypted logs, audit‑enabled |
| **Metadata (Job ID, status, timestamps)** | DynamoDB table `DigitalWorkerJobs` | DynamoDB (encrypted) | Unlimited (archival) | Fine‑grained IAM |

### 5.2 Application Architecture
```
+----------------+    +----------------+    +---------------------+
| API Gateway    | →  | Step Functions | →  | Lambda – Orchestrator|
+----------------+    +----------------+    +---------------------+
                                                    |
                 +----------------+   +----------------+   +-----------------+
                 | Lambda –       |   | Lambda –       |   | Lambda –       |
                 | Source Loader  |   | Spec Generator |   | Cleanup Worker |
                 +----------------+   +----------------+   +-----------------+

* API Gateway (REST) – /generate-spec (POST) – Auth via Cognito (optional for PoC)
* Step Functions – state machine:
   1. Validate input → 2. Store to S3 → 3. Invoke Spec Generator → 4. Store output → 5. Notify (SNS) → 6. Cleanup (if success/failure)
* Spec Generator Lambda:
   - Retrieves code + features.
   - Calls **Amazon Bedrock** (Claude/Claude‑Instant) with engineered prompt.
   - Formats output (Markdown → PDF via wkhtmltopdf or AWS Lambda‑layer).
* Cleanup Worker Lambda:
   - Runs after 24 h or on success to delete source bucket objects.
```

**Technology Stack**  
- **Language**: Python 3.11 (runtime for Lambdas).  
- **Infrastructure as Code**: AWS CDK (TypeScript).  
- **LLM**: Amazon Bedrock (Claude‑Instant, cost‑effective).  
- **Orchestration**: AWS Step Functions (Standard).  
- **Storage**: Amazon S3 (Standard-IA).  
- **Metadata**: Amazon DynamoDB.  
- **Notifications**: Amazon SNS (email/webhook).  
- **Security**: AWS KMS, IAM least‑privilege, VPC‑endpoint for S3+Bedrock, GuardDuty.  

---

## 6. Technology Architecture (Phase D)

### 6.1 Core Technology Components
| Component | Role | AWS Service | Key Config |
|-----------|------|--------------|------------|
| **Compute** | Serverless processing | AWS Lambda (x3) | 128 MB‑512 MB memory; timeout 300 s |
| **Orchestration** | Workflow coordination | AWS Step Functions | Standard, error‑catchers, retries |
| **LLM** | AI generation | Amazon Bedrock (Claude‑Instant) | Model version `anthropic.claude-v2:1` |
| **Storage** | Input/Output artifacts | Amazon S3 (two buckets) | SSE‑KMS, lifecycle policy (expire 1 day) |
| **Metadata** | Job tracking | Amazon DynamoDB (PK=JobId) | PITR enabled |
| **Notification** | User feedback | Amazon SNS (topic `DigitalWorkerEvents`) | Email subscription for PoC review |
| **Security** | Encryption, access control | AWS KMS, IAM, CloudTrail, GuardDuty | IAM roles per Lambda, audit logs |
| **Observability** | Metrics & logs | Amazon CloudWatch (Metrics, Logs) | Custom metrics: `DocsGenerated`, `ProcessingTime` |
| **CI/CD (optional)** | Deploy IaC | AWS CodePipeline + CodeBuild | Deploy CDK stack from GitHub repo |

### 6.2 Platform Services – “Digital Worker Factory” Blueprint
| Layer | Service | Responsibility |
|-------|---------|-----------------|
| **Presentation** | API Gateway (REST) | Expose `/generate-spec` endpoint, request validation. |
| **Application** | Lambda (Orchestrator, Generator, Cleaner) | Business logic, LLM calls, format conversion. |
| **Integration** | Step Functions | Sequence, retries, compensation. |
| **Data** | S3, DynamoDB | Durable storage, TTL management. |
| **Security** | IAM, KMS, VPC Endpoints | Isolation, encryption, least‑privilege. |
| **Management** | CloudWatch, SNS, CloudTrail | Monitoring, alerting, audit. |

### 6.3 Infrastructure Diagram (simplified)
```
[Client] → API GW → Step Functions → Lambda (Orchestrator)
                                 ├─> Lambda (Source Loader) → S3 (input)
                                 ├─> Lambda (Spec Generator) → Bedrock → S3 (output)
                                 ├─> Lambda (Cleaner) → S3 (delete) 
                                 └─> DynamoDB (Job Metadata) & SNS (status)
```

---

## 7. Opportunities & Solutions (Phase E)

### 7.1 Implementation & Migration Planning
| Phase | Milestone | Activities | Owner | Duration |
|-------|-----------|------------|-------|----------|
| **E‑1** | **Foundational Setup** | Create AWS account, define IAM baseline, enable GuardDuty & CloudTrail. | Ops | 0.5 day |
| **E‑2** | **Infrastructure as Code** | Develop CDK stack (API GW, Lambdas, Step Functions, S3, DynamoDB, SNS). | Dev | 0.5 day |
| **E‑3** | **Prompt Engineering** | Design Bedrock prompts for SRS & Functional Spec; test with sample code. | Lead Engineer | 0.5 day |
| **E‑4** | **Lambda Development** | Implement source loader, spec generator (Bedrock call + formatting), cleanup worker. | Dev | 0.5 day |
| **E‑5** | **Security Hardening** | Apply KMS keys, S3 lifecycle rules, IAM policies, automated delete logic. | Security Champion | 0.25 day |
| **E‑6** | **Testing & Validation** | Unit tests, integration test (end‑to‑end) for 2 NopCommerce modules, quality checklist. | QA | 0.5 day |
| **E‑7** | **Demo & Documentation** | Prepare demo script, generate PoC documents, capture metrics. | Product Owner | 0.25 day |
| **E‑8** | **Transition to Production (Future)** | Define scaling plan (increase Lambda concurrency, use SQS buffer), cost monitoring. | Ops | – (future) |

_Total PoC effort ≈ 2 days (as required)._

### 7.2 Solution Building Blocks (SBBs)
| SBB ID | Name | Description | Reuse Potential |
|--------|------|-------------|-----------------|
| SBB‑01 | **Serverless Orchestration** | Step Functions state machine coordinating AI generation. | High – can be reused for other AI‑driven pipelines. |
| SBB‑02 | **AI Spec Generator** | Lambda + Bedrock prompt library for documentation synthesis. | High – prompt set can be extended to other languages/frameworks. |
| SBB‑03 | **Secure Temporary Storage** | S3 bucket with 24 h lifecycle + deletion Lambda. | Medium – generic for any transient file processing. |
| SBB‑04 | **Job Metadata Service** | DynamoDB table + analytics CloudWatch metrics. | High – reusable job‑tracking backbone. |
| SBB‑05 | **Notification Layer** | SNS topic for status updates. | Medium – can plug into Slack/Teams later. |

### 7.3 Architecture Roadmap (high‑level)
| Quarter | Target | Key Deliverables |
|---------|--------|------------------|
| **Q1 2026** | PoC (completed) | Working Digital Worker, 2 docs generated, demo video, governance package. |
| **Q2 2026** | Pilot (5 docs/day) | Auto‑scale Lambdas, CI/CD pipeline, basic UI (static site) for request submission. |
| **Q3 2026** | Enterprise Roll‑out | Integration with Confluence via API, RBAC, multi‑region deployment, cost‑optimization. |
| **Q4 2026** | Continuous Improvement | Prompt refinement loop, support for additional languages, SLA reporting dashboard. |

---

## 8. Migration Planning (Phase F)

### 8.1 Implementation & Migration Strategy
1. **Parallel Run** – Keep existing manual documentation process while PoC runs; compare quality metrics.  
2. **Incremental Adoption** – Start with one module (e.g., `ShoppingCart`), then expand to `CustomerManagement`.  
3. **Data Migration** – No historic data migration required (documents are generated on‑demand).  

### 8.2 Transition Architecture
| Component | Current (None) | Target (PoC) | Target (Full) |
|-----------|----------------|-------------|---------------|
| **Documentation Process** | Manual authoring (Word/Confluence) | AI‑generated PDFs via API | Integrated docs portal with auto‑publish & versioning. |
| **Storage** | Local drives | S3 (temp) | S3 with lifecycle + backup to Glacier/Enterprise archive. |
| **Compute** | Human effort | Serverless Lambdas | Possibly containerised Fargate for heavy‑load bursts. |
| **Governance** | Ad‑hoc reviews | Defined WA (Workflow Automation) via Step Functions | Full governance with Change Management (ITSM). |

### 8.3 Implementation Governance
| Governance Item | Description | Frequency |
|-----------------|-------------|-----------|
| **Architecture Review Board (ARB)** | Approve CDK changes, security posture, cost estimates. | Weekly (PoC) → Bi‑weekly (production) |
| **Change Advisory Board (CAB)** | Review any changes to prompts, model versions. | As needed |
| **Operational Run‑books** | Incident response for failed document generation, data leakage. | Reviewed monthly |
| **Compliance Audits** | Verify encryption, data‑retention, audit logs. | Quarterly |

---

## 9. Architecture Principles
| # | Principle | Statement | Rationale |
|---|------------|-----------|-----------|
| P‑01 | **Secure‑by‑Design** | All data (source code, generated docs) must be encrypted at rest and in transit, and retained no longer than 24 h. | Protect IP, meet ISO 27001. |
| P‑02 | **Serverless First** | Prefer AWS serverless services over managed servers to reduce ops overhead and improve scalability. | Align with cost‑effective PoC and rapid iteration. |
| P‑03 | **AI‑Driven Automation** | Use AI services (Bedrock) as the core engine for knowledge extraction and document generation. | Achieve the hackathon’s primary goal of AI automation. |
| P‑04 | **Modular & Reusable** | Build the solution as composable building blocks (SBBs) that can be reused for other domains. | Future‑proofing, reduces duplication. |
| P‑05 | **Observability** | Emit metrics, logs, and traces for every execution step; integrate with CloudWatch dashboards. | Enable rapid debugging and SLA monitoring. |
| P‑06 | **Cost Conscious** | Design for minimal resource consumption; use auto‑scaling and lifecycle policies to avoid waste. | Stay within hackathon budget and AWS free‑tier limits. |
| P‑07 | **Stakeholder‑Centric** | Provide simple, documented API and clear status notifications to meet user expectations. | Improves adoption and satisfaction. |

---

## 10. Architecture Repository
### 10.1 Architecture Landscape
| Artifact | Location | Owner |
|----------|----------|-------|
| **Architecture Vision & Principles** | `repo-root/architecture/vision.md` | Enterprise Architect |
| **ADM Phase Deliverables** | `repo-root/adm/` (subfolders A‑F) | Architecture Team |
| **Solution Building Blocks** | `repo-root/sbbs/` | Solution Engineer |
| **CDK Code (IaC)** | `repo-root/infrastructure/` | DevOps Engineer |
| **Prompt Library** | `repo-root/ai/prompts/` | Lead Engineer |
| **Governance Docs** | `repo-root/governance/` | Architecture Governance Lead |
| **Risk Register** | `repo-root/risk/register.xlsx` | Risk Manager |

### 10.2 Standards Information Base (SIB)
| Standard | Description | Reference |
|----------|-------------|-----------|
| **TOGAF 10** | Architecture development method, content meta‑model. | TOGAF 10.0 (Open Group) |
| **AWS Well‑Architected Framework** | Operational Excellence, Security, Reliability, Performance, Cost Optimization. | AWS WA Guide |
| **ISO 27001 – Annex A.8** | Data encryption and handling. | ISO/IEC 27001 |
| **OpenAPI 3.0** | API contract for `/generate-spec`. | OAS Spec |
| **Markdown & PDF Styling Guide** | Consistent headings, tables, code blocks. | Internal Docs |

---

## 11. Risk Assessment
| ID | Risk | Impact | Likelihood | Mitigation |
|----|------|--------|------------|------------|
| RSK‑01 | **LLM hallucination → inaccurate specs** | High (incorrect docs) | Medium | Implement post‑generation validation rules (e.g., required sections, regex checks); manual reviewer in PoC. |
| RSK‑02 | **Source code leakage** | Critical | Low | Enforce IAM least‑privilege, VPC endpoints, KMS, automatic deletion, CloudTrail alerts. |
| RSK‑03 | **Cost overrun (Bedrock usage)** | Medium | Medium | Set AWS Budgets, use Claude‑Instant (lowest cost), monitor usage metrics. |
| RSK‑04 | **Step Functions state‑machine failure** | Medium | Low | Add retries, catchers, dead‑letter SQS for fallback. |
| RSK‑05 | **Performance > 2 min** | Medium | Low | Benchmark Bedrock latency; increase Lambda memory if needed; consider async pattern. |
| RSK‑06 | **Team skill gap (prompt engineering)** | Medium | Medium | Pair‑programming sessions, use AWS Bedrock examples, allocate time for prompt tuning. |
| RSK‑07 | **Regulatory non‑compliance** (data residency) | High | Low | Restrict resources to `eu-west-1`; configure S3 Block Public Access; log all access. |

---

## 12. Governance Framework
### 12.1 Architecture Governance Approach
| Governance Body | Role | Frequency | Artifacts Reviewed |
|----------------|------|-----------|--------------------|
| **Architecture Review Board (ARB)** | Approve high‑level design, ensure alignment with principles, assess cost & security. | Weekly (PoC) → Bi‑weekly (production) | Vision, Principles, System Landscape, SBBs, Risk Register |
| **Change Advisory Board (CAB)** | Review changes to prompts, model versions, Lambda code that affect output quality. | As required (per change) | Change tickets, impact analysis, test results |
| **Operations Review Committee** | Monitor runtime metrics, SLA compliance, incident handling. | Monthly | CloudWatch dashboards, incident reports |
| **Compliance Audit Team** | Verify adherence to ISO 27001, data‑privacy policies. | Quarterly | IAM policies, KMS usage, data‑retention logs |

### 12.2 Compliance Requirements
| Requirement | How It Is Satisfied |
|-------------|--------------------|
| **ISO 27001 – Data Protection** | SSE‑KMS encryption, IAM least‑privilege, audit logging in CloudTrail, 24 h data TTL. |
| **AWS Well‑Architected – Security Pillar** | VPC endpoints for S3 & Bedrock, GuardDuty alerts, automated security scans (Amazon Inspector). |
| **GDPR (if EU data)** | Data processed only within `eu-west-1`; no export, deletion within 24 h. |
| **PCI‑DSS (if applicable)** | Not in scope (no cardholder data); still follow strong access controls and encryption. |

### 12.3 Decision‑Making Process (simplified)
1. **Proposal** – Architecture team submits a change request (e.g., new prompt).  
2. **Impact Analysis** – Evaluate functional, security, cost impacts.  
3. **Review** – ARB/CAB reviews; may request pilot testing.  
4. **Approval** – Upon approval, change is merged to CDK repo and deployed via CodePipeline.  
5. **Post‑Implementation Review** – Verify metrics, update documentation, close change ticket.

---

**Prepared by:**  
*Enterprise Architecture Team – FHM Hackathon*  
*Lead Architect: [Name], TOGAF 10 Certified*  

*Document version 1.0 – 10 January 2026*  