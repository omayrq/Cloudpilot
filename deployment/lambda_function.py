"""
AWS Lambda backend handler for CloudPilot deployment.
Supports API Gateway proxy requests and direct AWS Lambda invocations.
Hardened with safe logging, payload size limits, input validation, and correlation IDs.
"""

import json
import os
import uuid

from agent import ask_bedrock
from safety import create_change_proposal, validate_approval
from tools import plan_architecture, troubleshoot_pipeline, explain_costs

# Input limits for API security
MAX_PAYLOAD_BYTES = 100 * 1024  # 100 KB
MAX_PROMPT_CHARS = 20000        # 20,000 chars

ALLOWED_MODES = {"architecture", "troubleshooter", "change_review"}
ALLOWED_ACTIONS = {"approve", "reject", "approved", "rejected", "health"}

def lambda_handler(event, context):
    """
    AWS Lambda entry point for CloudPilot API requests.
    Handles health checks, input validation, prompt routing, and proposal decision logging.
    """
    request_id = getattr(context, "aws_request_id", uuid.uuid4().hex[:12])
    http_method = event.get("httpMethod", "POST")
    path = event.get("path", "")
    
    # Safe metadata logging (avoids logging full user prompts or pasted log payloads)
    print(f"[CloudPilot Lambda Log] RequestID={request_id} Method={http_method} Path={path}")
    
    # Handle CORS preflight HTTP OPTIONS request
    if http_method == "OPTIONS":
        return _build_response(200, {"message": "CORS preflight OK"})

    # Validate raw payload size
    raw_body = event.get("body", "")
    if isinstance(raw_body, str) and len(raw_body.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        return _build_response(413, {"error": "Request payload exceeds maximum allowed size of 100 KB."})

    # Extract request payload body
    body = {}
    if raw_body:
        try:
            if isinstance(raw_body, str):
                body = json.loads(raw_body)
            else:
                body = raw_body
        except Exception:
            return _build_response(400, {"error": "Invalid JSON payload format."})
    else:
        body = event

    action = body.get("action", "")

    # Health check path/action
    if path == "/health" or action == "health":
        return _build_response(200, {
            "status": "healthy",
            "service": "CloudPilot Backend API",
            "region": os.getenv("AWS_DEFAULT_REGION", "us-east-1"),
            "model": os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0"),
            "requestId": request_id
        })

    # Route decision actions (approve / reject proposal)
    if action:
        if action not in ALLOWED_ACTIONS:
            return _build_response(400, {"error": f"Invalid action parameter: '{action}'"})
            
        proposal = body.get("proposal", {})
        if not isinstance(proposal, dict):
            return _build_response(400, {"error": "Invalid proposal format."})
            
        result = validate_approval(proposal, action)
        return _build_response(200, result)

    # Core AI / Tool processing
    prompt = body.get("prompt", "")
    mode = body.get("mode", "architecture")

    if not prompt:
        return _build_response(400, {"error": "Missing required 'prompt' field in payload."})

    if len(prompt) > MAX_PROMPT_CHARS:
        return _build_response(400, {"error": f"Prompt length exceeds maximum limit of {MAX_PROMPT_CHARS} characters."})

    if mode not in ALLOWED_MODES:
        mode = "architecture"

    try:
        if mode == "troubleshooter":
            result = troubleshoot_pipeline(prompt)
        elif mode == "change_review":
            result = create_change_proposal(prompt)
        else:
            result = ask_bedrock(prompt, mode=mode)
            
        return _build_response(200, result)
    except Exception as e:
        print(f"[CloudPilot Error Log] RequestID={request_id} Exception={type(e).__name__}")
        # Return generic error to client without leaking internal stack traces
        return _build_response(500, {
            "error": "Internal execution error occurred. Diagnostic details logged securely.",
            "correlationId": request_id
        })

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
