"""
Unit tests for CloudPilot Architecture, Cost Planning, and Troubleshooter Tools.
"""

from tools import plan_architecture, explain_costs, troubleshoot_pipeline

def test_plan_architecture_serverless():
    result = plan_architecture("Plan a low-cost web application on AWS", region="us-east-1", expected_requests_per_month=500000)
    
    assert result["mode"] == "architecture"
    assert len(result["recommendations"]) > 0
    assert any("Lambda" in r for r in result["recommendations"])
    assert len(result["cost_drivers"]) > 0
    assert result["execution_status"] == "not_executed"

def test_explain_costs():
    result = explain_costs(["ec2", "lambda", "nat_gateway"], region="us-east-1")
    
    assert result["mode"] == "architecture"
    assert len(result["cost_drivers"]) >= 3
    assert any("EC2" in c for c in result["cost_drivers"])

def test_troubleshoot_pipeline_docker_rate_limit():
    log = "ERROR: 429 Too Many Requests - Server message: toomanyrequests: You have reached your pull rate limit."
    result = troubleshoot_pipeline(log)
    
    assert result["mode"] == "troubleshooter"
    assert "Docker Hub Rate Limit" in result["summary"]
    assert any("ecr.aws" in r for r in result["recommendations"])

def test_troubleshoot_pipeline_access_denied():
    log = "An error occurred (AccessDenied) when calling the CreateFunction operation: User is not authorized to perform: lambda:CreateFunction"
    result = troubleshoot_pipeline(log)
    
    assert result["mode"] == "troubleshooter"
    assert "IAM Permission Denied" in result["summary"]
