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

    # Risk evaluation policy rules (preliminary rule-based indicator)
    if any(k in desc_lower for k in CRITICAL_RISK_KEYWORDS):
        risk_level = "CRITICAL"
        risks.append("CRITICAL: Destructive action resulting in permanent data loss or service unavailability!")
        risks.append("Action cannot be easily undone without active backups or Point-In-Time recovery.")
    elif any(k in desc_lower for k in HIGH_RISK_KEYWORDS):
        risk_level = "HIGH"
        risks.append("HIGH: Potential service disruption, state change, or instance downtime window.")
        if "resize" in desc_lower or "scale up" in desc_lower:
            cost_drivers.append("Financial Impact: Increase in hourly compute or database charges.")
            risks.append("Note: Instance resizes may require restart/downtime depending on instance type and configuration.")
    else:
        risk_level = "MEDIUM"
        risks.append("MEDIUM: Standard operational configuration update.")

    recommendations.append(f"Verify target resource parameters ({target_resource}) and backup/snapshot policies.")
    recommendations.append("Review availability requirements and rollback plans before approving.")

    summary = f"Change Proposal [{proposal_id}]: {action_description} on {target_resource} (Risk: {risk_level})"

    raw = {
        "mode": "change_review",
        "summary": summary,
        "recommendations": recommendations,
        "cost_drivers": cost_drivers,
        "assumptions": [
            f"Proposal ID: {proposal_id}",
            f"Risk Rating: {risk_level} (Preliminary rule-based indicator)",
            "Reversibility: Dependent on backup/snapshot strategy",
            "Governance Gate: Human-in-the-loop review prototype (records decision without live AWS execution)"
        ],
        "risks": risks,
        "next_steps": ["Select [Approve Proposal] or [Reject Proposal] below to record review decision."],
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
    updated_assumptions.append(f"Reviewer Decision Recorded: {status.upper()}")
    updated_assumptions.append("Prototype Notice: Decision logged; live AWS modification requires explicit IAM authorization.")

    updated_next_steps = []
    if status == "approved":
        updated_next_steps.append("Proposal marked as APPROVED in review prototype.")
        updated_next_steps.append("Pass proposal parameters to authorized CI/CD pipeline or IAM reviewer for execution.")
    else:
        updated_next_steps.append("Proposal marked as REJECTED in review prototype. No infrastructure action taken.")

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
