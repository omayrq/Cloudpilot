"""
Unit tests for agent routing and fallback in CloudPilot.
"""

import pytest
from agent import ask_bedrock, _extract_json

def test_ask_bedrock_architecture():
    res = ask_bedrock("Build a serverless web app", mode="architecture")
    assert res["mode"] == "architecture"
    assert "summary" in res
    assert "recommendations" in res

def test_extract_json():
    text = 'Some response text {"mode": "architecture", "summary": "test response"} end text'
    parsed = _extract_json(text)
    assert parsed is not None
    assert parsed["mode"] == "architecture"
