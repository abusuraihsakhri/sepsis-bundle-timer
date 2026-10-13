"""De-identified adult sepsis antibiotic timing worksheet.

Computes elapsed times against user-selected reference windows. It does not
make clinical decisions, establish SEP-1 compliance, or infer eligibility.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

WINDOW_HOURS = {"urgent": 1, "possible": 3}


def parse_instant(value: str, label: str) -> datetime:
    """Require an ISO-8601 timestamp with explicit UTC offset."""
    try:
        instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"{label} must be a valid ISO-8601 timestamp") from exc
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError(f"{label} must contain a timezone offset")
    return instant.astimezone(timezone.utc)


def evaluate_timing(
    recognition: str,
    pathway: str,
    *,
    antibiotic: Optional[str] = None,
    cultures: Optional[str] = None,
    lactate: Optional[str] = None,
    as_of: Optional[datetime] = None,
) -> dict:
    """Return a timing worksheet without patient identifiers or recommendations.

    'urgent': shock or probable/definite sepsis; 1-hour antibiotic reference.
    'possible': possible sepsis without shock; conditional 3-hour window.
    """
    if pathway not in WINDOW_HOURS:
        raise ValueError("pathway must be 'urgent' or 'possible'")
    now = as_of if as_of is not None else datetime.now(timezone.utc)
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("as_of must contain a timezone offset")
    now = now.astimezone(timezone.utc)
    start = parse_instant(recognition, "recognition")
    if start > now:
        raise ValueError("recognition cannot be in the future")
    events = {
        name: parse_instant(value, name) if value else None
        for name, value in (("antibiotic", antibiotic), ("cultures", cultures), ("lactate", lactate))
    }
    if any(moment is not None and moment > now for moment in events.values()):
        raise ValueError("recorded intervention timestamps cannot be in the future")
    deadline = start + timedelta(hours=WINDOW_HOURS[pathway])
    recorded = events["antibiotic"]
    if recorded is not None:
        status = "recorded" if recorded <= deadline else "after-target"
    elif now > deadline:
        status = "overdue"
    elif deadline - now <= timedelta(minutes=15):
        status = "due-soon"
    else:
        status = "pending"
    if events["cultures"] is not None and recorded is not None:
        culture_order = "before-or-same" if events["cultures"] <= recorded else "after-antibiotic"
    else:
        culture_order = "unknown"
    return {
        "recognition_utc": start.isoformat(),
        "reference_deadline_utc": deadline.isoformat(),
        "reference_hours": WINDOW_HOURS[pathway],
        "elapsed_minutes": int((now - start).total_seconds() // 60),
        "antibiotic_status": status,
        "antibiotic_minutes": round((recorded - start).total_seconds() / 60) if recorded else None,
        "culture_order": culture_order,
        "events_utc": {k: v.isoformat() if v else None for k, v in events.items()},
    }


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Timestamp calculations only; not a clinical decision tool")
    parser.add_argument("--recognition", required=True, help="ISO-8601 timestamp with offset")
    parser.add_argument("--pathway", choices=WINDOW_HOURS, required=True)
    for event in ("antibiotic", "cultures", "lactate"):
        parser.add_argument("--" + event)
    args = parser.parse_args(argv)
    try:
        result = evaluate_timing(args.recognition, args.pathway, antibiotic=args.antibiotic,
                                 cultures=args.cultures, lactate=args.lactate)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
