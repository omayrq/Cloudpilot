# CloudPilot: Your AWS Cost & Deployment Copilot 🚀

**Article Tag**: `agent`  
**Submission Date**: October 9, 2026  
**Live Application URL**: [http://cloudpilot-app-528582359305.s3-website-us-east-1.amazonaws.com](http://cloudpilot-app-528582359305.s3-website-us-east-1.amazonaws.com)  
**GitHub Repository**: [https://github.com/omayrq/Cloudpilot.git](https://github.com/omayrq/Cloudpilot.git)  
**Live API Endpoint**: `https://l4jxfpbef1.execute-api.us-east-1.amazonaws.com/prod/health`  

---

## 1. What Your Agent Does

**CloudPilot** is an intelligent, specialized AI copilot designed for developers, DevOps engineers, and startup builders working on Amazon Web Services (AWS). Building and scaling cloud applications often introduces two common pain points: unexpected infrastructure cost overruns and cryptic deployment pipeline errors (such as Docker Hub HTTP 429 rate limits, IAM AccessDenied HTTP 403 errors, or VPC network timeouts).

CloudPilot addresses these challenges by combining architectural pattern recommendations, illustrative cost breakdowns, and log diagnostics into a unified assistant.

### Core Capabilities:
- **Architecture & Cost Planner**: Analyzes application workload descriptions (e.g., "Build a serverless REST API with DynamoDB") and recommends serverless or containerized AWS service patterns. It generates a **rough illustrative cost estimate based on predefined us-east-1 baseline pricing assumptions. This is not a live AWS quote, and actual charges may vary.**
- **Deployment Pipeline Troubleshooter**: Parses raw deployment logs from AWS CodeBuild, CodePipeline, CloudFormation, or Docker buildspec files. It pattern-matches diagnostic signatures, identifies likely root causes, and recommends step-by-step verification commands (e.g., switching base container images to Amazon ECR Public Gallery or inspecting IAM policy simulators).
- **Human-in-the-Loop Review Prototype**: Evaluates proposed infrastructure updates (e.g., instance resizes, scaling actions, or resource deletions) and assigns a **preliminary rule-based risk indicator (not a security guarantee)**. Most importantly, CloudPilot operates as a governance prototype: it logs review decisions (`[Approve Proposal]` or `[Reject Proposal]`) **without executing live modifications on AWS or making unauthorized identity claims**.

---

## 2. How You Built It

CloudPilot is structured around a modular Python and AWS architecture. The repository includes two complementary interfaces: a **Streamlit application (`app.py`) for rich local development**, and a **lightweight static web UI (`index.html`) deployed on Amazon S3** for public web access.

### AWS Services & Architecture Breakdown:

| AWS Service | Deployment & Implementation Role | Operational Details & Security Notes |
| :--- | :--- | :--- |
| **Amazon Bedrock** | Core AI Reasoning Engine | Invokes the Converse API (`amazon.nova-lite-v1:0`) to understand prompt intent and format structured JSON responses. Model availability depends on account quotas and regional access. |
| **AWS Lambda** | Backend Logic Handler | Executes `CloudPilotBackendLambda` (Python 3.11). Uses a narrowly scoped IAM execution role (`AWSLambdaBasicExecutionRole` and `bedrock:InvokeModel`). |
| **Amazon API Gateway** | Public REST API Endpoint | Exposes `/prod` proxy routes to Lambda (`l4jxfpbef1`). Configured with CORS for web access; production environments recommend adding throttling, input validation, and AWS WAF. |
| **Amazon S3** | Deployed Live Frontend Host | Hosts the static web UI (`cloudpilot-app-528582359305`). S3 website endpoints serve over HTTP; AWS recommends pairing S3 with CloudFront for HTTPS distribution. |
| **Amazon ECR** | Container Image Registry | Stores the containerized Docker image (`528582359305.dkr.ecr.us-east-1.amazonaws.com/cloudpilot-ui`). Note: ECR stores images; a container runtime like ECS or AWS App Runner executes them. |

```mermaid
flowchart TD
    subgraph Deployed Public Production Path
        User["👨‍💻 Developer / Browser"] -->|HTTP Static Frontend| S3["Amazon S3 Website Host (cloudpilot-app-528582359305)"]
        User -->|HTTPS API Request| APIGW["Amazon API Gateway (/prod)"]
        APIGW -->|Lambda Proxy| Lambda["AWS Lambda Backend (CloudPilotBackendLambda)"]
        Lambda -->|Converse API| Bedrock["Amazon Bedrock (amazon.nova-lite-v1:0)"]
    end

    subgraph Local Development Path
        DevUser["👨‍💻 Developer (Local)"] -->|Streamlit App| LocalApp["Streamlit Frontend (app.py)"]
        LocalApp -->|Boto3 SDK| Bedrock
    end

    subgraph Agent Core Processing
        Bedrock --> Agent["Routing Agent (agent.py)"]
        Agent --> Schema["Contract Validator (schemas.py)"]
        Agent --> Safety["Safety Policy Engine (safety.py)"]
        Agent --> Tools["Cost & Diagnostics Tools (tools.py)"]
    end
    
    Safety -->|Decision Gate| ActionCard["Review Action Card (Approve / Reject)"]
```

### Key Decisions & Challenges Overcome:
- **Illustrative Pricing Grounding**: Cost estimates are presented as illustrative baseline estimates based on predefined `us-east-1` pricing models rather than live AWS Pricing API quotes. The agent explicitly displays baseline assumptions and prompts users to verify final rates on official AWS pricing pages.
- **Rule-Based Risk Scoring**: Risk ratings serve as preliminary indicators rather than security guarantees. For example, impact of resize operations depends on the specific service, instance type, and configuration (e.g. standard EC2 restarts vs. Aurora Serverless dynamic scaling). The system prompts users to verify service-specific backup, snapshot, and rollback policies.
- **Credential Security Policy**: No hard-coded AWS credentials are committed to the repository; runtime credentials should be managed securely using IAM roles or another approved credential mechanism.

---

## 3. The Experience (Making it Enjoyable to Use)

The **one key thing** we prioritized to make CloudPilot enjoyable to use is **Zero-Friction Transparency and Predictable Governance Controls**.

Many AI assistants operate as black boxes: developers worry that an autonomous agent might make unvetted changes or output misleading numbers.

To address this, **the interface is designed to improve user confidence by making cost assumptions, risks, and review decisions visible**:
1. **Clear Visual Risk Indicators**: Proposed actions display preliminary risk badges (`HIGH` or `CRITICAL`) alongside explicit downtime and backup recommendations.
2. **Instant Quick-Start Prompts**: First-time users can click pre-configured prompts ("Build a serverless REST API", "Fix Docker 429 error", "Resize EC2 instance") for immediate interactive feedback.
3. **Transparent Decision Audit**: Users test human-in-the-loop review by clicking **[Approve Proposal]** or **[Reject Proposal]**. The output records: *"Approval decision recorded by the prototype,"* demonstrating governance controls without unvetted cloud mutation.

---

## 4. Proof It Works

CloudPilot is functional, tested, and accessible via the following live resources:

- **Live Deployed Web App**: [http://cloudpilot-app-528582359305.s3-website-us-east-1.amazonaws.com](http://cloudpilot-app-528582359305.s3-website-us-east-1.amazonaws.com)
- **Live AWS REST API Endpoint**: `https://l4jxfpbef1.execute-api.us-east-1.amazonaws.com/prod`
- **Live AWS Lambda Health Check**: [https://l4jxfpbef1.execute-api.us-east-1.amazonaws.com/prod/health](https://l4jxfpbef1.execute-api.us-east-1.amazonaws.com/prod/health)
- **Public GitHub Source Code**: [https://github.com/omayrq/Cloudpilot.git](https://github.com/omayrq/Cloudpilot.git)

### Empirical Verification Output:

Executing a live health check query against the AWS API Gateway endpoint:
```json
{
  "status": "healthy",
  "service": "CloudPilot Backend API",
  "region": "us-east-1",
  "model": "amazon.nova-lite-v1:0"
}
```

Running the Pytest suite across all agent, tools, safety, and Lambda test files:
```
============================= 13 passed in 19.38s =============================
```
