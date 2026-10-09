"""
Structured response contract and schema validation for CloudPilot.
"""

from typing import Dict, Any, List

REQUIRED_KEYS = [
    "mode",
    "summary",
    "recommendations",
    "cost_drivers",
    "assumptions",
    "risks",
    "next_steps",
    "execution_status"
]

VALID_MODES = ["architecture", "troubleshooter", "change_review"]
VALID_EXECUTION_STATUSES = ["not_executed", "approved", "rejected"]

def validate_and_format_response(raw_data: Any, default_mode: str = "architecture") -> Dict[str, Any]:
    """
    Validates and normalizes raw dict/JSON output from Bedrock or tools
    to ensure it strictly conforms to the CloudPilot response contract.
    """
    if not isinstance(raw_data, dict):
        raw_data = {"summary": str(raw_data)}

    mode = str(raw_data.get("mode", default_mode)).lower()
    if mode not in VALID_MODES:
        mode = default_mode

    summary = str(raw_data.get("summary", "No summary provided."))

    def ensure_list(val: Any) -> List[str]:
        if isinstance(val, list):
            return [str(item) for item in val if item]
        elif isinstance(val, str) and val.strip():
            return [val.strip()]
        return []

    recommendations = ensure_list(raw_data.get("recommendations"))
    cost_drivers = ensure_list(raw_data.get("cost_drivers"))
    assumptions = ensure_list(raw_data.get("assumptions"))
    risks = ensure_list(raw_data.get("risks"))
    next_steps = ensure_list(raw_data.get("next_steps"))

    execution_status = str(raw_data.get("execution_status", "not_executed")).lower()
    if execution_status not in VALID_EXECUTION_STATUSES:
        execution_status = "not_executed"

    return {
        "mode": mode,
        "summary": summary,
        "recommendations": recommendations,
        "cost_drivers": cost_drivers,
        "assumptions": assumptions,
        "risks": risks,
        "next_steps": next_steps,
        "execution_status": execution_status
    }
