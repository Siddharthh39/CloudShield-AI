# CloudShield AI --- Complete Project Summary

## 1. What is CloudShield AI?

**CloudShield AI is an AI-powered website security assessment and
monitoring platform** that helps website owners understand how secure
their websites are, identify security weaknesses, and receive actionable
recommendations to fix them.

The goal is to make cybersecurity assessments accessible through a
professional, cloud-based dashboard rather than requiring users to
understand complicated security tools or manually interpret technical
logs.

Think of it as a combination of a **website security scanner,
vulnerability assessment platform, AI security analyst, and cloud-based
reporting dashboard**.

The project is intended to be showcased as a professional final-year
engineering project, with a realistic SaaS-style interface and a working
AWS-backed architecture.

## 2. The problem we are trying to solve

Website owners often don't know whether their websites have security
weaknesses.

Examples of questions they may have:

-   Are HTTPS and SSL/TLS configured correctly?
-   Are there missing or incorrectly configured security headers?
-   Are unnecessary ports or services exposed?
-   Are there outdated technologies or potentially vulnerable
    components?
-   Are there publicly exposed files or sensitive information?
-   Are there configuration mistakes that could expose the website to
    attacks?
-   Which security issues should be fixed first?

Existing security tools can generate technical output, but interpreting
that output requires cybersecurity knowledge.

**CloudShield AI aims to simplify this process.**

## 3. The expected user experience

The most important part of the project is how a user interacts with the
platform. The experience should look and feel like a commercial
cybersecurity SaaS product.

### Step 1 --- User logs in

The user signs into CloudShield AI using their account. Their dashboard
displays their websites, assessment history, security scores, and
findings.

### Step 2 --- User adds a website

The user enters a website URL, such as `example.com`, and adds it to
their website inventory.

### Step 3 --- Platform collects assessment data

CloudShield AI collects relevant website and infrastructure security
information through authorized assessment tools. It records assessment
logs and results.

### Step 4 --- Security analysis

The platform processes the collected information, identifies missing
security configurations and potential vulnerabilities, and classifies
issues by severity.

### Step 5 --- AI-powered analysis

AI explains what each issue means, why it matters, its potential impact,
and how the website owner can resolve it.

### Step 6 --- Results and reports

The user gets an overall security score, findings, recommendations,
assessment history, and downloadable reports through the dashboard.

The experience should feel seamless: the user enters a URL, starts an
assessment, watches its progress, and receives a clear security report.

## 4. Main features of CloudShield AI

  -----------------------------------------------------------------------
  Module                              Purpose
  ----------------------------------- -----------------------------------
  Authentication                      Secure registration and login

  Dashboard                           Overall security posture and
                                      statistics

  Website inventory                   Add and manage multiple websites

  Domain verification                 Verify ownership before assessments

  Assessment engine                   Collect website security
                                      information

  Log processing                      Process and normalize assessment
                                      output

  Vulnerability detection             Identify security gaps and
                                      potential vulnerabilities

  AI security analyst                 Explain findings and generate
                                      recommendations

  Risk scoring                        Calculate and prioritize security
                                      risks

  Reports                             Generate understandable security
                                      reports

  Assessment history                  Track previous assessments

  Role-based access                   Separate Admin, Analyst, and User
                                      permissions
  -----------------------------------------------------------------------

### Dashboard

The dashboard should display:

-   Total websites registered.
-   Number of completed assessments.
-   Overall security posture.
-   Critical, high, medium, and low findings.
-   Recent assessment activity.
-   Security score trends.
-   Websites that need immediate attention.

### Website security profile

Each website should have its own detailed profile, including:

-   Domain and ownership verification status.
-   SSL/TLS information.
-   HTTP response information.
-   Security headers.
-   Detected technologies.
-   Open services and exposed infrastructure information, where
    authorized.
-   Vulnerability findings.
-   AI-generated recommendations.
-   Previous assessment results.

## 5. Technical architecture

We planned CloudShield AI around a Python backend and AWS cloud
services.

### High-level architecture

``` text
                         CLOUDSHIELD AI
                                |
                                v
                    React + TypeScript Frontend
                  Dashboard / Inventory / Reports
                                |
                                v
                     Amazon Cognito + FastAPI
                 Authentication / Authorization / APIs
                                |
                                v
                     Assessment Orchestration
                   Jobs / Queues / Workers / Logs
                                |
                                v
                 Authorized Security Assessment Tools
              Nmap / Nuclei / OWASP ZAP / httpx / etc.
                                |
                    +-----------+-----------+
                    |                       |
                    v                       v
               Amazon S3                  MySQL
           Raw logs and reports      Users, sites, jobs,
                                     findings and history
                    |                       |
                    +-----------+-----------+
                                |
                                v
                    Processing and AI Analysis
                 Normalize / Detect / Bedrock / Score
                                |
                                v
                    Security Intelligence Layer
                 Findings / Recommendations / Reports
                                |
                                v
                      Frontend Dashboard
```

This is the intended broader architecture, not a claim that every
component has already been implemented.

### Technology stack

  Layer                  Technology
  ---------------------- -----------------------------------
  Backend                Python 3.12, FastAPI
  Frontend               React, TypeScript, Vite
  UI                     Tailwind CSS, shadcn/ui
  Database               MySQL
  Authentication         Amazon Cognito
  Cloud infrastructure   AWS
  Object storage         Amazon S3
  AI analysis            Amazon Bedrock
  Initial AI model       Amazon Nova Lite, where available
  Containerization       Docker, Docker Compose
  Deployment targets     AWS ECR and ECS
  Testing                Pytest
  CI/CD                  Git-based CI workflow

We chose MySQL rather than PostgreSQL. Docker and Docker Compose are
intended to make the application easier for all team members to run
consistently.

## 6. AI security analysis

AI is one of the most important differentiating features. The idea is
not simply to send a website URL to an AI model and ask whether it is
secure.

Instead, the platform should follow a structured process:

1.  Security tools collect technical information.
2.  Their output is stored and normalized.
3.  The platform extracts relevant security findings.
4.  Findings are grouped and assigned severity.
5.  Relevant evidence is passed to an AI model.
6.  The model generates explanations and remediation advice.
7.  The results are displayed in the dashboard.

### Example: Missing HTTP security headers

**Illustrative demo finding --- High severity**

**Detected issue:** The website does not return the
`Content-Security-Policy` HTTP response header.

**AI explanation:** This header helps restrict the sources from which a
browser can load content. Its absence may increase exposure to certain
cross-site scripting attacks.

**Recommended action:** Configure a suitable Content Security Policy
based on the website's actual scripts, styles, and resource
requirements.

This is illustrative output only. Actual severity and recommendations
must be based on collected evidence and context.

AI should make findings easier to understand, but it should not invent
vulnerabilities or claim that a website is vulnerable without supporting
evidence.

## 7. Security and authorization requirements

CloudShield AI is intended to be a defensive security platform. We
specifically wanted to avoid building a tool that could be used to scan
random websites without permission.

The assessment process should be authorization-first:

-   A user adds a domain.
-   The platform verifies domain ownership, initially through a DNS TXT
    record.
-   Only verified domains can proceed to active assessments.
-   The platform restricts scans to approved domains and assets.
-   It validates URLs and blocks SSRF attempts.
-   It prevents arbitrary command execution.
-   It limits assessment intensity and scope.
-   It records assessment activity and logs.

Tools considered for a future assessment engine include:

-   Nmap
-   Nuclei
-   OWASP ZAP
-   httpx
-   Subfinder
-   dnsx
-   Katana
-   Naabu
-   waybackurls
-   gau

These are candidate tools for future integration, not necessarily tools
already integrated into the current application.

## 8. Authentication and user roles

We planned three user roles:

### Admin --- Platform administration

-   Manage users.
-   Manage platform configuration.
-   Review overall system activity.

### Analyst --- Security assessment

-   Review assessment results.
-   Investigate findings.
-   Analyze security reports.

### User --- Website owner

-   Register websites.
-   Verify ownership.
-   Initiate authorized assessments.
-   View reports.

Amazon Cognito was selected for authentication, with FastAPI responsible
for validating access tokens and enforcing application permissions.

One user should be able to register and manage multiple websites.

## 9. Demo data and project presentation

A major requirement is that the project should look complete and
professional when someone evaluates it.

We decided to include **2--3 seeded dummy websites** so that the
dashboard is populated immediately after setup.

Proposed demo domains:

  -----------------------------------------------------------------------
  Demo website                        Intended demonstration
  ----------------------------------- -----------------------------------
  `portal.example.com`                Missing security headers and TLS
                                      configuration findings

  `shop.example.org`                  E-commerce security configuration
                                      findings

  `api.example.net`                   API security and exposure-related
                                      findings
  -----------------------------------------------------------------------

These are reserved example domains, not real customer websites.

Each should have realistic but clearly labelled demo data, including:

-   Website details.
-   Security scores.
-   Assessment history.
-   Example assessment logs.
-   Findings with different severity levels.
-   AI explanations.
-   Remediation recommendations.
-   Reports and dashboard statistics.

**Why this matters:** During a project demonstration, you should be able
to log in and show a populated dashboard without having to perform a
live scan or wait for AWS processing.

The demo data must be internally consistent and clearly marked as demo
data. It should never be presented as the result of a real scan.

## 10. What has been completed so far

It is important to separate actual progress from the intended final
product.

### Completed or previously reported as completed

  -----------------------------------------------------------------------
  Component                           Status
  ----------------------------------- -----------------------------------
  Project concept and architecture    Defined

  Python/FastAPI backend foundation   Phase 1 reported complete

  MySQL integration foundation        Implemented in initial backend

  Docker and Docker Compose           Configured
  foundation                          

  Environment configuration           `.env` and `.env.example`

  Logging and health endpoints        Implemented

  Backend tests                       Five health tests were present in
                                      the latest inspected checkout

  AWS foundation                      Configured

  Amazon Cognito User Pool            Created

  Cognito Admin, Analyst, User groups Configured previously

  Cognito test users                  Created previously

  AWS region                          `ap-south-1`

  Amazon Bedrock                      Nova Lite availability confirmed
                                      previously
  -----------------------------------------------------------------------

### Important repository-status qualification

A previous Phase 2.1 report described Cognito-to-FastAPI authentication
as implemented. However, the latest repository inspection showed only
`tests/test_health.py` in the test directory. Therefore, the
authentication implementation needs to be verified against the actual
current repository before that phase is considered complete.

The latest checkout also had local uncommitted changes in `.env.example`
and `docker-compose.yml`, and a local Python 3.12.14 setup. These should
be preserved while continuing development.

## 11. Planned development phases

The project should be developed incrementally rather than trying to
implement everything at once.

### Phase 1 --- Backend foundation

-   FastAPI.
-   MySQL.
-   Docker and Docker Compose.
-   Environment configuration.
-   Logging.
-   Health endpoints.
-   Tests and CI.

**Status:** Previously reported complete.

### Phase 2 --- Authentication and user management

-   Cognito integration.
-   JWT validation.
-   Roles and permissions.
-   User management.
-   Protected APIs.

**Status:** Verify current repository.

### Phase 3 --- Frontend and dashboard

-   Professional SaaS interface.
-   Authentication screens.
-   Website inventory.
-   Overview dashboard.
-   Findings.
-   Reports.

### Phase 4 --- Website and assessment management

-   Multiple websites per user.
-   Domain verification.
-   Assessment job management.
-   Status tracking.

### Phase 5 --- Assessment engine

-   Integrate authorized security tools.
-   Collect assessment logs.
-   Normalize results.
-   Store evidence.

### Phase 6 --- AI security analysis

-   Bedrock integration.
-   Finding explanations.
-   Remediation suggestions.
-   Risk prioritization.

### Phase 7 --- Reports and analytics

-   Security scores.
-   Historical trends.
-   Downloadable reports.
-   Dashboard analytics.

### Phase 8 --- AWS deployment and final demonstration

-   Container image publishing.
-   Deployment.
-   Monitoring.
-   Cost controls.
-   Testing.
-   Documentation.
-   Presentation.

## 12. What the final project should demonstrate

When the project is finished, an evaluator should be able to:

1.  Open the CloudShield AI web application.
2.  Log in as a user.
3.  View a professional security dashboard.
4.  See the 2--3 preloaded demo websites.
5.  Open a website's security profile.
6.  Start or view an assessment.
7.  See assessment progress and collected logs.
8.  View identified security gaps and vulnerabilities.
9.  Open an individual finding and understand its impact.
10. View AI-generated remediation recommendations.
11. Review the website's overall security score.
12. Generate or view a security report.
13. Log in with different roles and see the appropriate permissions.

The project should look like a genuine commercial cybersecurity product,
not just a collection of API endpoints or a basic college CRUD
application.

## 13. Overall vision

### CloudShield AI

**AI-Powered Website Security Intelligence Platform**

**Our mission:** To help website owners understand, monitor, and improve
their website security through automated assessments, intelligent
vulnerability analysis, and actionable AI-powered recommendations.

**The core value proposition:** Instead of giving users raw
security-tool output, CloudShield AI turns technical assessment data
into understandable security intelligence.

### Project summary in one sentence

CloudShield AI is a cloud-based, AI-powered website security assessment
platform where users register and verify their websites, initiate
authorized security assessments, collect and process technical logs,
identify vulnerabilities and security misconfigurations, and receive
AI-generated explanations, risk prioritization, and remediation
recommendations through a professional dashboard.

### Key implementation principle

The most important thing going forward is to make the complete user
journey work convincingly, even if some advanced scanning and AI
capabilities initially use realistic demo data. Then progressively
replace those demo components with actual AWS-backed assessment and
analysis workflows.

The project should clearly distinguish between demo results, actual
assessment evidence, and AI-generated interpretation at every stage.
