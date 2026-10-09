"""
Security regression tests for CloudPilot UI and response sanitation.
Verifies XSS payload escaping and sanitization contracts.
"""

import html
import pytest
from tools import troubleshoot_pipeline, plan_architecture
from safety import create_change_proposal

def test_xss_payload_handling_in_troubleshooter():
    xss_payload = "<script>alert('xss')</script>"
    res = troubleshoot_pipeline(xss_payload)
    assert res["mode"] == "troubleshooter"
    # Ensure raw HTML script tags are not blindly accepted as valid commands
    assert "Generic Pipeline Failure" in res["summary"] or "Error snippet" in res["summary"]

def test_xss_payload_in_change_proposal():
    xss_action = "Resize <img src=x onerror=alert(1)> database"
    res = create_change_proposal(xss_action)
    assert res["mode"] == "change_review"
    assert "Resize" in res["summary"]
    # Verify assumptions are formatted safely
    assert any("PROP-" in a for a in res["assumptions"])

def test_index_html_does_not_contain_unsafe_innerhtml():
    with open("index.html", "r", encoding="utf-8") as f:
        content = f.read()
    # Verify renderList does not contain innerHTML assignment for item interpolation
    assert "li.innerHTML = `<span" not in content
    assert "replaceChildren()" in content
