"""
Unit tests for human-in-the-loop safety guardrails and change proposal validation.
"""

import pytest
from safety import create_change_proposal, validate_approval

def test_create_change_proposal_high_risk():
    res = create_change_proposal("Resize RDS instance to db.r5.xlarge", target_resource="Database")
    assert res["mode"] == "change_review"
    assert "PROP-" in res["summary"]
    assert "HIGH" in res["summary"]

def test_create_change_proposal_critical_risk():
    res = create_change_proposal("delete-db-instance production-db", target_resource="RDS Instance")
    assert res["mode"] == "change_review"
    assert "CRITICAL" in res["summary"]

def test_validate_approval_approved():
    proposal = create_change_proposal("Resize EC2 instance")
    res = validate_approval(proposal, "approve")
    assert res["execution_status"] == "approved"
    assert "APPROVED" in res["summary"]

def test_validate_approval_rejected():
    proposal = create_change_proposal("Delete S3 bucket")
    res = validate_approval(proposal, "reject")
    assert res["execution_status"] == "rejected"
    assert "REJECTED" in res["summary"]
