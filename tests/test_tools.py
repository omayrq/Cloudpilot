"""
Unit tests for CloudPilot architecture planner, cost estimator, and log troubleshooter.
"""

import pytest
from tools import plan_architecture, explain_costs, troubleshoot_pipeline

def test_plan_architecture_serverless():
    res = plan_architecture("Serverless API with DynamoDB")
    assert res["mode"] == "architecture"
    assert len(res["recommendations"]) > 0
    assert any("Lambda" in r for r in res["recommendations"])

def test_explain_costs():
    res = explain_costs(["EC2", "NAT Gateway"])
    assert res["mode"] == "architecture"
    assert len(res["cost_drivers"]) >= 2

def test_troubleshoot_docker_429():
    log = "Error: 429 Too Many Requests - Hitting Docker Hub rate limit"
    res = troubleshoot_pipeline(log)
    assert res["mode"] == "troubleshooter"
    assert "Docker Hub Rate Limit Exceeded" in res["summary"]

def test_troubleshoot_iam_access_denied():
    log = "User is not authorized to perform: bedrock:InvokeModel (403 AccessDenied)"
    res = troubleshoot_pipeline(log)
    assert res["mode"] == "troubleshooter"
    assert "IAM Permission Denied" in res["summary"]
