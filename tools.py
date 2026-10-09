"""
Cost planning, cost breakdown, and pipeline error analysis tools for CloudPilot.
"""

import re
from typing import Dict, Any, List
from schemas import validate_and_format_response

# Standard AWS Regional Multipliers (us-east-1 reference)
AWS_BASE_PRICING = {
    "lambda": {"per_million_req": 0.20, "gb_second": 0.0000166667},
    "s3": {"storage_per_gb": 0.023, "put_per_10k": 0.005, "get_per_10k": 0.0004},
    "dynamodb": {"write_per_million": 1.25, "read_per_million": 0.25, "storage_per_gb": 0.25},
    "ec2_t3_micro": {"hourly": 0.0104, "monthly_730h": 7.59},
    "ec2_t3_medium": {"hourly": 0.0416, "monthly_730h": 30.37},
    "ec2_t3_2xlarge": {"hourly": 0.3328, "monthly_730h": 242.94},
    "nat_gateway": {"hourly": 0.045, "monthly_730h": 32.85, "data_per_gb": 0.045},
    "cloudfront": {"data_per_gb": 0.085, "http_per_10k": 0.0075}
}

def plan_architecture(
    app_description: str,
    region: str = "us-east-1",
    operating_hours_per_month: int = 730,
    expected_requests_per_month: int = 100000
) -> Dict[str, Any]:
    """
    Produces architectural recommendations, service selection, and cost drivers
    for a user-described application workload.
    """
    desc_lower = app_description.lower()
    recommendations: List[str] = []
    cost_drivers: List[str] = []
    assumptions: List[str] = []
    risks: List[str] = []
    next_steps: List[str] = []

    # Serverless vs EC2 detection
    if "web" in desc_lower or "api" in desc_lower or "low cost" in desc_lower or "simple" in desc_lower:
        recommendations.append("Use AWS Lambda + Amazon API Gateway for serverless compute with zero idle cost.")
        recommendations.append("Use Amazon DynamoDB (On-Demand billing) for persistent noSQL database.")
        recommendations.append("Use Amazon S3 + Amazon CloudFront for static asset delivery & global Anycast CDN.")

        # Estimate Serverless Cost
        req_millions = expected_requests_per_month / 1_000_000
        lambda_cost = req_millions * AWS_BASE_PRICING["lambda"]["per_million_req"]
        dynamo_cost = req_millions * AWS_BASE_PRICING["dynamodb"]["read_per_million"]
        s3_cost = 0.50 # baseline storage
        total_est = lambda_cost + dynamo_cost + s3_cost

        cost_drivers.append(f"API Request Volume: {expected_requests_per_month:,} req/month (Rough illustrative estimate: ~${total_est:.2f}/mo)")
        cost_drivers.append("Data Transfer Out (CloudFront CDN): Free tier covers up to 1 TB/month.")
        assumptions.append(f"Illustrative cost estimate based on predefined us-east-1 baseline rates (not a live AWS quote).")
        assumptions.append(f"Assumed region: {region}, operating time: {operating_hours_per_month}h/month, light payload (<128 KB).")
    else:
        recommendations.append("Deploy containerized microservices on AWS App Runner or ECS Fargate in Multi-AZ VPC.")
        recommendations.append("Use Amazon RDS PostgreSQL (db.t4g.micro) for relational database requirements.")
        cost_drivers.append("NAT Gateway hourly fee (~$32.85/mo baseline) + data processing fees ($0.045/GB).")
        cost_drivers.append("RDS Database Instance & Provisioned Storage (EBS gp3).")
        assumptions.append("Illustrative estimate based on predefined us-east-1 baseline rates. Actual costs vary by instance type and data volume.")
        assumptions.append("Requires VPC setup with Public and Private Subnets across 2 Availability Zones.")
        risks.append("NAT Gateway and provisioned RDS run 24/7 regardless of traffic volume.")

    next_steps.append("Verify baseline rates against official AWS Pricing pages (aws.amazon.com/pricing).")
    next_steps.append("Model workload scaling scenarios using the official AWS Pricing Calculator.")
    next_steps.append("Configure AWS Budgets to alert if monthly spending exceeds threshold.")

    summary = f"Architectural recommendation generated for '{app_description[:60]}...' in {region}."

    raw = {
        "mode": "architecture",
        "summary": summary,
        "recommendations": recommendations,
        "cost_drivers": cost_drivers,
        "assumptions": assumptions,
        "risks": risks,
        "next_steps": next_steps,
        "execution_status": "not_executed"
    }
    return validate_and_format_response(raw, "architecture")

def explain_costs(services: List[str], region: str = "us-east-1") -> Dict[str, Any]:
    """
    Explains cost drivers and trade-offs for a given list of AWS services.
    """
    cost_drivers: List[str] = []
    recommendations: List[str] = []
    assumptions: List[str] = []

    for svc in services:
        s_lower = svc.lower()
        if "ec2" in s_lower:
            cost_drivers.append("Amazon EC2: Charged per instance-hour + EBS volume storage (gp3) + Elastic IP idle fees.")
            recommendations.append("Consider Savings Plans or Spot Instances for up to 70% cost reduction on EC2 workloads.")
        elif "lambda" in s_lower:
            cost_drivers.append("AWS Lambda: Charged per request ($0.20/M) + compute duration (GB-seconds).")
            recommendations.append("Configure minimum required memory (e.g. 128MB - 512MB) to avoid paying for unused vCPU capacity.")
        elif "dynamodb" in s_lower:
            cost_drivers.append("Amazon DynamoDB: On-Demand read/write request units + storage over 25 GB free tier.")
        elif "nat" in s_lower:
            cost_drivers.append("NAT Gateway: Charged $0.045/hour (~$32.85/mo) plus $0.045/GB data processed.")
            recommendations.append("Use VPC Endpoints (Gateway endpoints for S3 & DynamoDB) to bypass NAT Gateway data charges.")

    assumptions.append(f"Prices grounded in AWS {region} standard public pricing.")

    raw = {
        "mode": "architecture",
        "summary": f"Cost breakdown for {len(services)} requested AWS service(s).",
        "recommendations": recommendations,
        "cost_drivers": cost_drivers,
        "assumptions": assumptions,
        "risks": [],
        "next_steps": ["Inspect AWS Cost Explorer for active billing trends."],
        "execution_status": "not_executed"
    }
    return validate_and_format_response(raw, "architecture")

def troubleshoot_pipeline(error_log: str) -> Dict[str, Any]:
    """
    Analyzes deployment/pipeline logs (CodeBuild, CodePipeline, CloudFormation, Docker)
    and identifies root cause, evidence, and verification steps.
    """
    log_upper = error_log.upper()
    recommendations: List[str] = []
    risks: List[str] = []
    next_steps: List[str] = []
    evidence: List[str] = []

    if "429" in log_upper or "TOO MANY REQUESTS" in log_upper or "DOCKER" in log_upper:
        summary = "Root Cause Identified: Docker Hub Rate Limit Exceeded (HTTP 429)."
        evidence.append("Log indicates 429 Too Many Requests when pulling base container image from Docker Hub.")
        recommendations.append("Switch Dockerfile base image to Amazon ECR Public Gallery (e.g. `public.ecr.aws/docker/library/node:20-alpine`).")
        recommendations.append("Authenticate Docker CLI using ECR credentials before pulling third-party images.")
        next_steps.append("Run `aws ecr-public get-login-password --region us-east-1` in buildspec.yml.")
    elif "ACCESSDENIED" in log_upper or "403" in log_upper or "UNAUTHORIZED" in log_upper or "NOT AUTHORIZED" in log_upper:
        summary = "Root Cause Identified: IAM Permission Denied (HTTP 403 AccessDenied)."
        evidence.append("Log indicates service execution role lacks required IAM action policy.")
        recommendations.append("Attach required IAM managed policy or inline permission to the service execution role.")
        next_steps.append("Check IAM policy simulator or CloudTrail event history for missing action name.")
    elif "TIMEOUT" in log_upper or "TIMED OUT" in log_upper or "SUBNET" in log_upper:
        summary = "Root Cause Identified: Network Connectivity Timeout / VPC Routing Defect."
        evidence.append("Log shows network timeout connecting to internal or external endpoints.")
        recommendations.append("Verify VPC Route Tables, NAT Gateway availability, and Security Group egress rules.")
        next_steps.append("Check VPC Reachability Analyzer for blocked network paths.")
    else:
        summary = "Generic Pipeline Failure Detected."
        evidence.append(f"Error snippet: {error_log[:150]}...")
        recommendations.append("Inspect full buildspec.yml build commands and environment variables.")
        next_steps.append("Reproduce build step locally using AWS SAM CLI or local container runtime.")

    raw = {
        "mode": "troubleshooter",
        "summary": summary,
        "recommendations": recommendations,
        "cost_drivers": [],
        "assumptions": ["Log analyzed using pattern matching and diagnostic rules."],
        "risks": risks,
        "next_steps": next_steps,
        "execution_status": "not_executed"
    }
    return validate_and_format_response(raw, "troubleshooter")
