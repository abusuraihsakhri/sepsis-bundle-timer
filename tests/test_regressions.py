"""Regression tests for CSV boolean parsing and auxiliary attribute screening."""
import csv
import pytest
from cli import main
from agents.base import SecurityException
from agents.models import SystemTaskPayload
from agents.supervisor import SystemSupervisor


@pytest.mark.parametrize("flag, expected", [("false", "ROUTINE"), ("no", "ROUTINE"), ("true", "CRITICAL_STAT_PANIC"), ("1", "CRITICAL_STAT_PANIC")])
def test_cli_batch_critical_flag(tmp_path, flag, expected):
    source = tmp_path / "inputs.csv"
    output = tmp_path / "output.csv"
    with source.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["task_id", "target_identifier", "primary_metric", "secondary_metric", "is_critical_flag"])
        writer.writeheader()
        writer.writerow({"task_id": "TEST-001", "target_identifier": "KEY-001", "primary_metric": "10", "secondary_metric": "4", "is_critical_flag": flag})
    assert main(["batch", "-i", str(source), "-o", str(output)]) == 0
    with output.open(newline="", encoding="utf-8") as f:
        row = next(csv.DictReader(f))
    assert row["overall_urgency"] == expected


def test_supervisor_rejects_phi_in_attributes():
    payload = SystemTaskPayload(task_id="T-1", target_identifier="KEY-1", primary_metric=10.0,
                                attributes={"comment": "MRN-12345678"})
    with pytest.raises(SecurityException):
        SystemSupervisor().process_task(payload)
