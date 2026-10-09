"""
Unit tests for CloudPilot Safety & Change Proposal Engine.
"""

from safety import create_change_proposal, validate_approval

def test_create_change_proposal_high_risk():
    proposal = create_change_proposal("Resize EC2 instance from t3.micro to t3.2xlarge", "i-0123456789abcdef0")
    
    assert proposal["mode"] == "change_review"
    assert "HIGH" in proposal["summary"] or "HIGH" in str(proposal["assumptions"])
    assert len(proposal["risks"]) > 0
    assert proposal["execution_status"] == "not_executed"

def test_create_change_proposal_critical_risk():
    proposal = create_change_proposal("delete-db-instance prod-rds-database", "rds:prod-db")
    
    assert proposal["mode"] == "change_review"
    assert "CRITICAL" in str(proposal["risks"]) or "CRITICAL" in proposal["summary"]
    assert proposal["execution_status"] == "not_executed"

def test_validate_approval_accept():
    proposal = create_change_proposal("Resize EC2 instance from t3.micro to t3.medium", "i-12345678")
    result = validate_approval(proposal, "approved")
    
    assert result["execution_status"] == "approved"
    assert "APPROVED" in result["summary"]

def test_validate_approval_reject():
    proposal = create_change_proposal("Delete S3 bucket production-logs", "s3://production-logs")
    result = validate_approval(proposal, "rejected")
    
    assert result["execution_status"] == "rejected"
    assert "REJECTED" in result["summary"]
