"""
Human-in-the-loop safety, policy evaluation, and change proposal validation engine for CloudPilot.
"""

import uuid
from typing import Dict, Any, List
from schemas import validate_and_format_response

# Policy boundaries for risk evaluation
HIGH_RISK_KEYWORDS = ["delete", "terminate", "drop", "destroy", "purge", "resize", "reboot", "truncate"]
CRITICAL_RISK_KEYWORDS = ["delete-db-instance", "delete-bucket", "delete-vpc", "kms-disable"]

def create_change_proposal(
    action_description: str,
    target_resource: str = "AWS Resource"
) -> Dict[str, Any]:
    """
    Generates a structured Change Review Proposal.
    Evaluates risk rating, financial impact, and reversibility.
    Does NOT execute live modifications on AWS.
    """
    desc_lower = action_description.lower()
    proposal_id = f"PROP-{uuid.uuid4().hex[:8].upper()}"

    risk_level = "LOW"
    risks: List[str] = []
    cost_drivers: List[str] = []
    recommendations: List[str] = []

    # Risk evaluation policy rules
    if any(k in desc_lower for k in CRITICAL_RISK_KEYWORDS):
        risk_level = "CRITICAL"
        risks.append("CRITICAL: Destructive action resulting in permanent data loss or service unavailability!")
        risks.append("Action cannot be easily undone without active backups or Point-In-Time recovery.")
    elif any(k in desc_lower for k in HIGH_RISK_KEYWORDS):
        risk_level = "HIGH"
        risks.append("HIGH: Potential service disruption, instance downtime, or network state change.")
        if "resize" in desc_lower or "scale up" in desc_lower:
            cost_drivers.append("Financial Impact: Significant increase in hourly compute or database charges.")
            risks.append("Resize operations require stopping EC2/RDS instances (downtime window).")
    else:
        risk_level = "MEDIUM"
        risks.append("MEDIUM: Standard operational configuration update.")

    recommendations.append(f"Review target resource parameters ({target_resource}).")
    recommendations.append("Ensure automated snapshot or backup exists prior to approving.")

    summary = f"Change Proposal [{proposal_id}]: {action_description} on {target_resource} (Risk: {risk_level})"

    raw = {
        "mode": "change_review",
        "summary": summary,
        "recommendations": recommendations,
        "cost_drivers": cost_drivers,
        "assumptions": [
            f"Proposal ID: {proposal_id}",
            f"Risk Level: {risk_level}",
            "Reversibility: Depends on snapshot/backup policy",
            "Safety Guardrail: Requires explicit human approval"
        ],
        "risks": risks,
        "next_steps": ["Select [Approve Proposal] or [Reject Proposal] below to record decision."],
        "execution_status": "not_executed"
    }

    return validate_and_format_response(raw, "change_review")

def validate_approval(proposal: Dict[str, Any], user_decision: str) -> Dict[str, Any]:
    """
    Validates user decision (approved or rejected) for a proposal.
    Records human approval status without unvetted live execution.
    """
    decision = user_decision.lower()
    status = "approved" if decision in ["approved", "approve"] else "rejected"

    summary = proposal.get("summary", "Proposal")
    updated_summary = f"{summary} — DECISION: {status.upper()}"

    updated_assumptions = list(proposal.get("assumptions", []))
    updated_assumptions.append(f"Human Decision Recorded: {status.upper()}")
    updated_assumptions.append("Live AWS Execution: Skipped in MVP / Controlled Gate")

    updated_next_steps = []
    if status == "approved":
        updated_next_steps.append("Proposal approved by authorized human reviewer.")
        updated_next_steps.append("Proceed with manual deployment or CI/CD approval pipeline.")
    else:
        updated_next_steps.append("Proposal rejected by human reviewer. No infrastructure action taken.")

    raw = {
        "mode": "change_review",
        "summary": updated_summary,
        "recommendations": proposal.get("recommendations", []),
        "cost_drivers": proposal.get("cost_drivers", []),
        "assumptions": updated_assumptions,
        "risks": proposal.get("risks", []),
        "next_steps": updated_next_steps,
        "execution_status": status
    }

    return validate_and_format_response(raw, "change_review")
