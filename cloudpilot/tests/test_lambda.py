"""
Tests for AWS Lambda deployment handler in cloudpilot/deployment/lambda_function.py
"""

import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../deployment")))

from deployment.lambda_function import lambda_handler

def test_lambda_handler_health():
    event = {"path": "/health"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["status"] == "healthy"

def test_lambda_handler_architecture_query():
    event = {
        "body": json.dumps({
            "prompt": "Build a serverless REST API with DynamoDB",
            "mode": "architecture"
        })
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["mode"] == "architecture"
    assert "summary" in body

def test_lambda_handler_approval():
    proposal = {
        "summary": "Resize EC2 instance to t3.2xlarge",
        "assumptions": [],
        "recommendations": []
    }
    event = {
        "body": json.dumps({
            "action": "approve",
            "proposal": proposal
        })
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["execution_status"] == "approved"
