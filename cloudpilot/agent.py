"""
Amazon Bedrock Converse API integration for CloudPilot agent.
"""

import os
import json
import boto3
from typing import Dict, Any, List
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from prompts import CLOUDPILOT_SYSTEM_PROMPT
from schemas import validate_and_format_response
from tools import plan_architecture, troubleshoot_pipeline
from safety import create_change_proposal

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "amazon.nova-lite-v1:0")

def get_bedrock_client():
    """Returns a boto3 bedrock-runtime client with configured region and credentials."""
    return boto3.client("bedrock-runtime", region_name=REGION)

def ask_bedrock(user_prompt: str, mode: str = "architecture") -> Dict[str, Any]:
    """
    Sends user request to Amazon Bedrock Converse API.
    Parses minified JSON response and validates contract.
    Falls back gracefully to tool functions if Bedrock is unavailable.
    """
    prompt_lower = user_prompt.lower()

    # Route request to specific mode tools if explicit keywords match
    if mode == "troubleshooter" or "error" in prompt_lower or "failed" in prompt_lower or "buildspec" in prompt_lower:
        return troubleshoot_pipeline(user_prompt)
    elif mode == "change_review" or "resize" in prompt_lower or "delete" in prompt_lower or "terminate" in prompt_lower or "scale" in prompt_lower:
        return create_change_proposal(user_prompt)

    # Invoke Amazon Bedrock Converse API for general architecture & cost queries
    try:
        client = get_bedrock_client()
        system_rules = [{"text": CLOUDPILOT_SYSTEM_PROMPT}]
        messages = [
            {
                "role": "user",
                "content": [{"text": user_prompt}]
            }
        ]

        response = client.converse(
            modelId=MODEL_ID,
            system=system_rules,
            messages=messages,
            inferenceConfig={"temperature": 0.7, "maxTokens": 2000}
        )

        output_msg = response["output"]["message"]["content"][0]["text"]
        parsed_json = _extract_json(output_msg)

        if parsed_json and isinstance(parsed_json, dict):
            return validate_and_format_response(parsed_json, default_mode=mode)
    except Exception as e:
        print(f"[CloudPilot Bedrock Warning]: {e}. Using deterministic tool fallback.")

    # Tool Fallback
    return plan_architecture(user_prompt, region=REGION)

def _extract_json(text: str) -> Any:
    """Helper to extract JSON object from LLM response text."""
    try:
        # Try direct parse
        return json.loads(text)
    except Exception:
        # Try regex extract
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
    return None
