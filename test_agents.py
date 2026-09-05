"""
Tests for the agents module: PHI guard, audit trail, and workers.
"""
import pytest
from agents.base import (
    PHIGuard,
    SecurityException,
    AuditTrail,
    AuditLogger,
    assert_no_phi,
)
from agents.models import SystemTaskPayload, UrgencyLevel, SystemIntegrityStatus
from agents.supervisor import SystemSupervisor


class TestPHIGuard:
    """Tests for the Zero-PHI Outbound Guard."""

    def test_clean_text_passes(self):
        assert_no_phi("Routine lactate measurement 2.1 mmol/L")

    def test_mrn_blocked(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Patient MRN-12345678")

    def test_ssn_blocked(self):
        with pytest.raises(SecurityException):
            assert_no_phi("SSN: 123-45-6789")

    def test_phone_blocked(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Contact: (555) 123-4567")

    def test_email_blocked(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Email: patient@hospital.org")

    def test_doe_name_blocked(self):
        with pytest.raises(SecurityException):
            assert_no_phi("Patient Name John Doe")

    def test_none_input_ok(self):
        assert_no_phi(None)

    def test_empty_string_ok(self):
        assert_no_phi("")

    def test_redact_phi(self):
        redacted = PHIGuard.redact_phi("MRN-12345678 lactate result")
        assert "REDACTED_IDENTIFIER" in redacted
        assert "lactate result" in redacted


class TestAuditTrail:
    """Tests for the HMAC-SHA256 tamper-evident audit trail."""

    def test_log_creates_entry(self):
        trail = AuditTrail(secret_key="test-key-for-unit-tests")
        entry = trail.log("tester", "unit", "TEST_EVENT", {"key": "value"})
        assert "audit_id" in entry
        assert "current_hash" in entry
        assert "prev_hash" in entry

    def test_integrity_valid(self):
        trail = AuditTrail(secret_key="test-key-for-unit-tests")
        trail.log("tester", "unit", "EVENT_1", {"a": 1})
        trail.log("tester", "unit", "EVENT_2", {"b": 2})
        trail.log("tester", "unit", "EVENT_3", {"c": 3})
        assert trail.verify_integrity() is True

    def test_chained_hashes(self):
        trail = AuditTrail(secret_key="test-key-for-unit-tests")
        e1 = trail.log("tester", "unit", "EVENT_1", {"a": 1})
        e2 = trail.log("tester", "unit", "EVENT_2", {"b": 2})
        assert e2["prev_hash"] == e1["current_hash"]

    def test_get_trail_returns_all(self):
        trail = AuditTrail(secret_key="test-key-for-unit-tests")
        trail.log("tester", "unit", "EVENT_1", {"a": 1})
        trail.log("tester", "unit", "EVENT_2", {"b": 2})
        assert len(trail.get_trail()) == 2


class TestSupervisor:
    """Tests for the SystemSupervisor orchestrator."""

    def test_routine_task(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TEST-001",
            target_identifier="SPECIMEN-001",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
            is_critical_flag=False,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ROUTINE
        assert dossier.integrity_status == SystemIntegrityStatus.VALIDATED

    def test_elevated_task(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TEST-002",
            target_identifier="SPECIMEN-002",
            primary_metric=30.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
            is_critical_flag=False,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.ELEVATED

    def test_critical_task(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TEST-003",
            target_identifier="SPECIMEN-003",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
            is_critical_flag=True,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.overall_urgency == UrgencyLevel.CRITICAL_STAT
        assert dossier.integrity_status == SystemIntegrityStatus.RECALIBRATION_REQUIRED

    def test_discordant_descriptor(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TEST-004",
            target_identifier="SPECIMEN-004",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="DISCORDANT_ANOMALY",
            is_critical_flag=False,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.total_alerts > 0

    def test_phi_guard_blocks_task_id(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="MRN-12345678",
            target_identifier="SPECIMEN-005",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
            is_critical_flag=False,
        )
        with pytest.raises(SecurityException):
            supervisor.process_task(payload)

    def test_dossier_registered(self):
        supervisor = SystemSupervisor(model_provider="mock")
        payload = SystemTaskPayload(
            task_id="TEST-006",
            target_identifier="SPECIMEN-006",
            primary_metric=10.0,
            secondary_metric=5.0,
            status_descriptor="NOMINAL",
            is_critical_flag=False,
        )
        dossier = supervisor.process_task(payload)
        assert dossier.dossier_id in supervisor.dossier_registry
