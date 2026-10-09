"""
AWS Lambda backend handler for CloudPilot deployment.
Supports API Gateway proxy requests and direct AWS Lambda invocations.
"""

import json
import os

from agent import ask_bedrock
from safety import create_change_proposal, validate_approval
from tools import plan_architecture, troubleshoot_pipeline, explain_costs

def lambda_handler(event, context):
    """
    AWS Lambda entry point for CloudPilot API requests.
    Handles health checks, prompt routing, and change proposal validation.
    """
    print(f"[CloudPilot Lambda Event]: {json.dumps(event)}")
    
    # Handle CORS preflight HTTP OPTIONS request
    http_method = event.get("httpMethod", "POST")
    if http_method == "OPTIONS":
        return _build_response(200, {"message": "CORS preflight OK"})
        
    # Extract request payload body
    body = {}
    if "body" in event and event["body"]:
        try:
            if isinstance(event["body"], str):
                body = json.loads(event["body"])
            else:
                body = event["body"]
        except Exception as e:
            return _build_response(400, {"error": f"Invalid JSON payload: {str(e)}"})
    else:
        body = event

    # Health check path/action
    path = event.get("path", "")
    action = body.get("action", "")
    if path == "/health" or action == "health":
        return _build_response(200, {
            "status": "healthy",
            "service": "CloudPilot Backend API",
            "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            "model": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")
        })

    # Route decision actions (approve / reject proposal)
    if action in ["approve", "reject", "approved", "rejected"]:
        proposal = body.get("proposal", {})
        result = validate_approval(proposal, action)
        return _build_response(200, result)

    # Core AI / Tool processing
    prompt = body.get("prompt", "")
    mode = body.get("mode", "architecture")

    if not prompt:
        return _build_response(400, {"error": "Missing required 'prompt' field in payload."})

    try:
        if mode == "troubleshooter":
            result = troubleshoot_pipeline(prompt)
        elif mode == "change_review":
            result = create_change_proposal(prompt)
        elif mode == "architecture":
            result = ask_bedrock(prompt, mode=mode)
        else:
            result = ask_bedrock(prompt, mode=mode)
            
        return _build_response(200, result)
    except Exception as e:
        print(f"[CloudPilot Handler Error]: {e}")
        return _build_response(500, {"error": f"Internal execution error: {str(e)}"})

def _build_response(status_code: int, body: dict) -> dict:
    """Formats standard AWS API Gateway HTTP proxy response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token",
            "Access-Control-Allow-Methods": "GET,POST,OPTIONS"
        },
        "body": json.dumps(body)
    }
