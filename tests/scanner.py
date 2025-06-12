"""Tests for the Dream.OS Beta Verification System."""

import pytest
import json
from pathlib import Path
from datetime import datetime
from dreamos.core.verification.verify_beta import BetaVerifier, CheckResult

@pytest.fixture(scope="session")
def test_env() -> Path:
    """Create a test environment for verification tests."""
    test_dir = Path("tests/temp/verification_test")
    test_dir.mkdir(parents=True, exist_ok=True)
    yield test_dir
    # Cleanup handled by test environment

@pytest.fixture
def verifier(test_env: Path) -> BetaVerifier:
    """Create a verifier instance for testing."""
    return BetaVerifier(base_path=test_env)

def test_verifier_initialization(test_env: Path, verifier: BetaVerifier):
    """Test verifier initialization."""
    assert verifier.base_path == test_env
    assert isinstance(verifier.results, list)
    assert isinstance(verifier.start_time, datetime)

def test_check_result_creation():
    """Test CheckResult dataclass creation and conversion."""
    result = CheckResult(
        name="Test Check",
        status=True,
        details="Test details",
        category="test",
        severity="low"
    )
    
    assert result.name == "Test Check"
    assert result.status is True
    assert result.details == "Test details"
    assert result.category == "test"
    assert result.severity == "low"
    assert isinstance(result.timestamp, str)
    assert isinstance(result.recommendations, list)
    
    # Test dictionary conversion
    result_dict = result.to_dict()
    assert isinstance(result_dict, dict)
    assert result_dict["name"] == "Test Check"
    assert result_dict["status"] is True

def test_check_mailboxes(verifier: BetaVerifier):
    """Test mailbox verification."""
    # Create test mailbox structure
    mailboxes = verifier.base_path / "runtime/agent_memory"
    mailboxes.mkdir(parents=True, exist_ok=True)
    
    # Test with missing mailboxes
    result = verifier.check_mailboxes()
    assert result.status is False
    assert "Missing or empty mailboxes" in result.details
    
    # Create valid mailbox
    agent_dir = mailboxes / "agent-1"
    agent_dir.mkdir(exist_ok=True)
    (agent_dir / "inbox.json").write_text("{}")
    
    # Test with valid mailbox
    result = verifier.check_mailboxes()
    assert result.status is True
    assert "All" in result.details

def test_check_required_docs(verifier: BetaVerifier):
    """Test documentation verification."""
    # Test with missing docs
    result = verifier.check_required_docs()
    assert result.status is False
    assert "Missing docs" in result.details
    
    # Create required docs
    docs_dir = verifier.base_path / "docs/onboarding"
    docs_dir.mkdir(parents=True, exist_ok=True)
    for doc in ["CORE_AGENT_IDENTITY_PROTOCOL.md", 
                "AGENT_OPERATIONAL_LOOP_PROTOCOL.md",
                "AGENT_ONBOARDING_CHECKLIST.md"]:
        (docs_dir / doc).write_text("# Test Doc")
    
    # Test with all docs present
    result = verifier.check_required_docs()
    assert result.status is True
    assert "All" in result.details

def test_check_unit_tests(verifier: BetaVerifier):
    """Test unit test verification."""
    # Create a simple test file
    test_file = verifier.base_path / "tests/test_verify.py"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    test_file.write_text("""
def test_simple():
    assert True
""")
    
    result = verifier.check_unit_tests()
    assert result.status is True
    assert "All tests passed" in result.details

def test_check_orphans_and_dupes(verifier: BetaVerifier):
    """Test orphaned files verification."""
    # Test with no report
    result = verifier.check_orphans_and_dupes()
    assert result.status is True
    assert "No orphaned files report found" in result.details
    
    # Create orphaned files report
    reports_dir = verifier.base_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / "orphaned_files.json").write_text('{"orphaned": ["test.py"]}')
    
    result = verifier.check_orphans_and_dupes()
    assert result.status is False
    assert "orphaned files found" in result.details

def test_verification_report_generation(verifier: BetaVerifier):
    """Test verification report generation."""
    # Run some checks
    verifier.check_mailboxes()
    verifier.check_required_docs()
    
    # Generate report
    report = verifier.generate_report()
    assert isinstance(report, str)
    assert "Verification Report" in report
    
    # Test JSON output
    report_dict = json.loads(report)
    assert isinstance(report_dict, dict)
    assert "checks" in report_dict
    assert "summary" in report_dict

def test_verification_categories_and_severity(verifier: BetaVerifier):
    """Test check categorization and severity determination."""
    # Test category determination
    assert verifier._categorize_check("check_mailboxes") == "system"
    assert verifier._categorize_check("check_unit_tests") == "testing"
    
    # Test severity determination
    assert verifier._determine_severity("check_mailboxes", False) == "high"
    assert verifier._determine_severity("check_unit_tests", True) == "medium"

def test_recommendation_generation(verifier: BetaVerifier):
    """Test recommendation generation for failed checks."""
    recommendations = verifier._generate_recommendations(
        "check_mailboxes",
        False,
        "Missing mailboxes"
    )
    assert isinstance(recommendations, list)
    assert len(recommendations) > 0
    assert any("mailbox" in rec.lower() for rec in recommendations) 