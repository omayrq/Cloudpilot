"""
Unit tests for CloudPilot Agent & Response Contract Validator.
"""

from schemas import validate_and_format_response
from agent import ask_bedrock

def test_validate_and_format_response_contract():
    raw = {
        "mode": "architecture",
        "summary": "Sample summary",
        "recommendations": ["Use Lambda"],
        "invalid_extra_field": "test"
    }

    formatted = validate_and_format_response(raw)

    assert formatted["mode"] == "architecture"
    assert formatted["summary"] == "Sample summary"
    assert isinstance(formatted["recommendations"], list)
    assert isinstance(formatted["cost_drivers"], list)
    assert isinstance(formatted["assumptions"], list)
    assert isinstance(formatted["risks"], list)
    assert isinstance(formatted["next_steps"], list)
    assert formatted["execution_status"] == "not_executed"

def test_ask_bedrock_architecture_mode():
    result = ask_bedrock("Plan a low-cost web application on AWS", mode="architecture")

    assert result["mode"] in ["architecture", "change_review", "troubleshooter"]
    assert "summary" in result
    assert isinstance(result["recommendations"], list)
