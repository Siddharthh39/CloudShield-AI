# Software Requirements Specification

## CloudShield AI

**Document version:** 1.0  
**Date:** 12 November 2026  
**Repository:** `Siddharthh39/CloudShield-AI`

## 1. Introduction

### 1.1 Purpose

This Software Requirements Specification (SRS) defines the requirements for CloudShield AI, a defensive website security intelligence platform. The system allows authorized users to register websites, obtain approval for diagnostics, review security posture and findings, and request evidence-grounded explanations and remediation guidance from an AI security analyst.

This document describes the current repository implementation and identifies planned capabilities separately. It is intended for developers, testers, project evaluators, system administrators, and future maintainers.

### 1.2 Product scope

CloudShield AI provides:

- Authenticated user workspaces for monitored websites.
- Administrator approval before a registered website can be scanned.
- Passive analysis of publicly reachable HTTP/HTTPS targets.
- Detection of selected missing HTTP security headers and response status conditions.
- Risk scores, letter grades, findings, recommendations, and representative log events.
- Gemini-powered explanations constrained to supplied evidence.
- Seeded demonstration data for local and evaluator environments.
- Local Docker Compose and AWS SAM deployment paths.

The current release does **not** claim to provide a full penetration test, malware detector, spyware detector, exploit engine, or arbitrary active security scan.

### 1.3 Definitions and abbreviations

| Term | Definition |
|---|---|
| **Site** | A website registered for monitoring. |
| **Scan** | A completed passive diagnostic of an approved site. |
| **Finding** | A security observation, weakness, or hardening opportunity supported by evidence. |
| **Owner** | The Cognito user identified by the `sub` claim who registered a site. |
| **Admin** | A Cognito user in the `Admin` group or configured administrator email list. |
| **SSRF** | Server-side request forgery, including attempts to reach private or internal network targets. |
| **Risk score** | A numeric score from 0 to 100 generated from observed diagnostic conditions. |

## 2. Overall description

### 2.1 Product perspective

The product is a web dashboard backed by a FastAPI service. The service uses PostgreSQL for application data, Amazon Cognito for production authentication, AWS Secrets Manager for protected credentials, and Google Gemini for optional AI explanations. The service can run locally in Docker Compose or serverlessly through AWS Lambda and API Gateway.

```text
Browser dashboard
        |
        | HTTPS/JSON
        v
FastAPI API on local Docker or AWS Lambda
        |
        +--> PostgreSQL / Amazon RDS
        +--> Amazon Cognito token validation
        +--> Secrets Manager
        +--> Google Gemini (finding explanations)
```

### 2.2 User classes

| User class | Responsibilities |
|---|---|
| **Website owner / Client** | Sign in, register owned websites, view owned sites and scans, and request AI explanations. |
| **Administrator** | Review pending registrations and approve sites before diagnostics. Administrators can view all sites. |
| **Local demo user** | Use the unauthenticated local demonstration mode when Cognito is not configured. |
| **Operator / Developer** | Configure environments, run migrations and seed data, deploy services, and monitor failures. |

### 2.3 Operating environment

- Python 3.11+ runtime for the AWS deployment.
- FastAPI, SQLAlchemy, Alembic, and PostgreSQL.
- Modern browser with JavaScript enabled.
- Docker and Docker Compose for local execution.
- AWS Lambda, API Gateway HTTP API, Cognito, RDS PostgreSQL, S3, and Secrets Manager for the cloud deployment.
- Internet access from the API runtime for authorized passive target requests and Gemini requests.

### 2.4 Constraints

1. Diagnostics must be defensive and authorization-first.
2. A site must be approved by an administrator before a passive scan.
3. Private, loopback, and internal network targets must be rejected.
4. AI output must be based on supplied evidence and must distinguish observed facts from possible threat scenarios.
5. Secrets and API keys must not be committed to source control.
6. Tenant data must be isolated by Cognito subject for non-administrator users.
7. Seeded sites and findings must be clearly treated as demonstration data.

## 3. Functional requirements

### 3.1 Authentication and authorization

**FR-01** The system shall support Cognito OAuth authorization-code sign-in for deployed environments.

**FR-02** The API shall accept Cognito bearer tokens and validate signature, issuer, token type, and client identity.

**FR-03** When authentication is required, requests without a valid bearer token shall receive HTTP 401.

**FR-04** The system shall identify a user by the Cognito `sub` claim.

**FR-05** A non-administrator shall only list, view, scan, and analyze sites whose `owner_sub` matches the authenticated user.

**FR-06** An administrator shall be able to view all sites and access the administrator approval queue.

**FR-07** Local development shall support a clearly limited demo identity when authentication is disabled by configuration.

### 3.2 Site registration and lifecycle

**FR-08** An authenticated user shall be able to register a site using a URL and optional display name.

**FR-09** The system shall normalize URLs to HTTP or HTTPS form and reject malformed URLs.

**FR-10** The system shall reject duplicate registered URLs.

**FR-11** The system shall resolve the submitted hostname and reject private, loopback, or internal addresses.

**FR-12** A new site shall have `pending_approval` status and shall not be scannable until approved.

**FR-13** An administrator shall be able to approve a pending site.

**FR-14** The system shall expose site status, score, grade, summary, technology, region, TLS metadata, ownership, approval status, and latest scan information.

### 3.3 Passive diagnostics

**FR-15** An authorized user shall be able to start diagnostics for an approved site.

**FR-16** The scanner shall make a bounded passive request using a defined user agent and timeout.

**FR-17** The scanner shall record the response status and observed response headers.

**FR-18** The scanner shall evaluate at least the following baseline headers:

- `Content-Security-Policy`
- `Strict-Transport-Security`
- `X-Content-Type-Options`
- `Referrer-Policy`

**FR-19** The system shall create a completed scan containing status, risk score, grade, summary, timestamps, duration, request counts, blocked counts, findings, and log events.

**FR-20** The system shall classify the site posture as healthy, watch, or critical using the calculated risk score.

**FR-21** If the target cannot be reached, the API shall return an explicit failure response rather than a successful scan result.

**FR-22** The system shall not imply that passive diagnostics tested malware, spyware, exploitation, or complete infrastructure exposure.

### 3.4 Findings and evidence

**FR-23** Each finding shall include severity, category, title, description, recommendation, status, and structured evidence where available.

**FR-24** Findings shall be associated with a specific scan and site.

**FR-25** Findings shall distinguish open findings from findings with another lifecycle status.

**FR-26** Evidence shall identify the observed condition, such as missing headers, response status, path, or sample count.

### 3.5 AI security analyst

**FR-27** An authenticated user shall be able to submit a finding and its evidence for explanation.

**FR-28** The system shall retrieve the Gemini API key from protected configuration, not from source code or client-side code.

**FR-29** The AI prompt shall instruct the model to use only supplied evidence and avoid claiming unobserved compromise, malware, spyware, exploitation, or a specific CVE.

**FR-30** The AI response shall provide an explanation and prioritized recommendation and identify what the passive check did not test.

**FR-31** If Gemini is unavailable or unconfigured, the API shall return an explicit service error.

### 3.6 Dashboard and user interface

**FR-32** The dashboard shall display total targets, open findings, pending approvals, and the current analysis mode.

**FR-33** The dashboard shall list monitored sites with status and risk score.

**FR-34** A user shall be able to select a site and view its grade, score, summary, findings, representative logs, and scan metrics.

**FR-35** The interface shall provide a control to register a site and a control to run passive diagnostics when approval permits.

**FR-36** Administrators shall see a pending-site queue with approval controls.

**FR-37** The interface shall escape displayed user- or target-derived values before inserting them into HTML.

### 3.7 Legacy profile compatibility

**FR-38** The API shall retain the existing profile, project, skills, search, and work-experience endpoints for compatibility with the original portfolio API.

### 3.8 Data initialization and deployment

**FR-39** Local startup shall support database migration followed by idempotent demo seeding.

**FR-40** Seed data shall include clearly labelled example sites, scans, findings, and log events.

**FR-41** The deployment template shall provision the configured API, database, Cognito resources, frontend hosting, and protected secrets required by the cloud path.

## 4. External interface requirements

### 4.1 HTTP API

The API shall provide, at minimum, the following interfaces:

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Service health check. |
| GET | `/sites` | List sites visible to the caller. |
| GET | `/sites/{site_id}` | Get one visible site. |
| POST | `/sites/register` | Register an authorized site for approval. |
| POST | `/sites/{site_id}/scan` | Run passive diagnostics on an approved site. |
| POST | `/sites/analyze` | Preserve compatibility with baseline analysis behavior. |
| GET | `/admin/sites` | List pending sites for administrators. |
| POST | `/admin/sites/{site_id}/approve` | Approve a pending site. |
| POST | `/ai/explain` | Generate an evidence-grounded explanation. |
| GET/POST/PUT | `/profile` | Preserve profile CRUD behavior. |
| GET | `/projects`, `/skills/top`, `/search` | Preserve portfolio query behavior. |

Successful JSON responses shall use stable field names and ISO-compatible timestamps. Error responses shall use suitable HTTP status codes and an explicit `detail` message.

### 4.2 Database interface

The relational model shall persist:

- Profiles and portfolio compatibility data.
- Monitored sites and ownership metadata.
- Security scans.
- Security findings and JSON evidence.
- Representative log events.

Relationships shall preserve site-to-scan-to-finding/log lineage, and deleting a site shall remove dependent scan data according to the configured cascade behavior.

### 4.3 Security interface

- Production requests shall use HTTPS.
- Browser API calls shall support CORS for configured frontend origins.
- Authorization shall use `Authorization: Bearer <token>`.
- Database and Gemini credentials shall be obtained from environment configuration or AWS Secrets Manager.

## 5. Non-functional requirements

### 5.1 Security

**NFR-01** The system shall enforce tenant isolation for all site and scan queries.

**NFR-02** The system shall validate target hostnames before making server-side requests.

**NFR-03** The system shall reject private and loopback target addresses to reduce SSRF risk.

**NFR-04** The system shall not execute arbitrary shell commands from user input.

**NFR-05** Sensitive values shall be excluded from logs, seed data, frontend assets, and source control.

### 5.2 Reliability and error handling

**NFR-06** External requests shall have bounded timeouts.

**NFR-07** Dependency failures shall return explicit errors and shall not produce success-shaped scan or AI results.

**NFR-08** Database initialization shall be repeatable without duplicating seeded records.

### 5.3 Performance

**NFR-09** Health checks shall return without contacting an external target or AI provider.

**NFR-10** A normal site-list request shall return only the data required by the dashboard, including each site's latest scan summary.

**NFR-11** Passive target and Gemini requests shall use bounded execution time suitable for the API timeout.

### 5.4 Usability and accessibility

**NFR-12** The dashboard shall present findings in understandable language with severity, evidence, and remediation guidance.

**NFR-13** Interactive site cards and controls shall be keyboard reachable.

**NFR-14** Authentication, approval, scan, and error states shall be visible to the user.

### 5.5 Maintainability and portability

**NFR-15** The service shall run through Docker Compose without requiring AWS services for the local demo path.

**NFR-16** Database schema changes shall be managed through Alembic migrations.

**NFR-17** The same API codebase shall support local ASGI execution and AWS Lambda through the configured adapter.

## 6. Data requirements

### 6.1 Site states

The following states shall be supported:

- `pending_approval`: registered but not approved.
- `approved`: permitted to run diagnostics.
- `healthy`, `watch`, `critical`: posture classifications after analysis.

### 6.2 Risk grading

The passive baseline shall use the repository's current score-to-grade mapping:

| Risk score | Grade |
|---:|---|
| 0–19 | A |
| 20–44 | B |
| 45–69 | C |
| 70–100 | D |

The score and grade are indicators of observed baseline conditions, not a guarantee of overall security.

### 6.3 Demonstration data

Seeded records shall be marked or named as demo/snapshot data where appropriate. Demonstration data shall not be represented as a live customer assessment or proof of a real compromise.

## 7. Use cases

### UC-01: Register an authorized website

1. The user signs in.
2. The user enters an HTTP or HTTPS URL.
3. The API normalizes and validates the URL.
4. The API resolves the hostname and rejects private/internal targets.
5. The system creates a pending site owned by the user.
6. The dashboard displays that administrator approval is required.

### UC-02: Approve a site

1. An administrator opens the approval queue.
2. The system lists pending registrations.
3. The administrator approves a site.
4. The site becomes eligible for passive diagnostics.

### UC-03: Run passive diagnostics

1. The owner or administrator opens an approved site.
2. The user starts diagnostics.
3. The API performs a bounded passive request.
4. The system evaluates response headers and status.
5. The system stores a scan, findings, evidence, and a representative log event.
6. The dashboard displays the updated posture.

### UC-04: Explain a finding with AI

1. The user selects an open finding.
2. The dashboard sends the finding and evidence to the API.
3. The API retrieves the protected Gemini credential.
4. Gemini returns an evidence-grounded explanation.
5. The dashboard displays explanation, limitations, and remediation guidance.

### UC-05: Use the local demonstration

1. The operator copies the example environment file.
2. The operator starts Docker Compose.
3. The database is migrated and seeded.
4. The operator opens the frontend and selects a seeded site.
5. The dashboard displays clearly labelled demonstration scans and findings.

## 8. Acceptance criteria

The release shall be considered acceptable when:

1. The local Docker stack starts with a healthy PostgreSQL database, migrated schema, seeded data, API, and frontend.
2. `GET /health` returns an OK status.
3. A user can register a valid public URL and receives a pending-approval response.
4. Private, loopback, malformed, and unresolved targets are rejected.
5. A non-approved site cannot be scanned.
6. An administrator can approve a pending site.
7. An approved public site can produce a passive scan with score, grade, findings, and log event.
8. A non-administrator cannot retrieve another user's site by list or ID.
9. Missing Gemini configuration produces an explicit error rather than fabricated AI output.
10. Seeded demo sites load and are visibly distinguishable from live assessments.
11. The compatibility profile endpoints continue to respond according to their existing schemas.
12. The deployed configuration can validate Cognito tokens and access the configured database and secrets.

## 9. Future enhancements

The following are outside the current baseline and require separate design, authorization, and validation:

- DNS-based domain ownership verification.
- Asynchronous assessment jobs and progress tracking.
- Authorized integrations with Nmap, Nuclei, OWASP ZAP, httpx, or similar tools.
- Deeper infrastructure and technology discovery.
- Historical trend charts and downloadable reports.
- Analyst-specific workflows and finding status management.
- Automated alerting and scheduled rescans.
- Private-subnet deployment hardening and restricted database ingress.
- Expanded test coverage for authentication, tenant isolation, SSRF defenses, and AI failure modes.

## 10. Traceability summary

| Requirement area | Primary implementation locations |
|---|---|
| Authentication and tenant isolation | `Backend/main.py`, `Frontend/app.js` |
| Site, scan, finding, and log persistence | `Backend/models.py`, `Backend/schemas.py`, `alembic/` |
| Passive diagnostics and SSRF checks | `Backend/main.py` |
| AI explanation | `Backend/main.py`, `Backend/schemas.py` |
| Dashboard behavior | `Frontend/index.html`, `Frontend/app.js`, `Frontend/styles.css` |
| Local deployment and seed data | `docker-compose.yml`, `Dockerfile`, `seed.sql` |
| AWS deployment | `template.yaml`, `scripts/deploy.sh` |

