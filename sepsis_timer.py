#!/usr/bin/env python3
"""
Sepsis Bundle Compliance Timer
Surviving Sepsis 1h/3h bundle compliance timer from triage, lactate and antibiotic timestamps.
Stdlib parser / mapper with batch CSV and single lookup.
"""
import argparse
import csv
import os
import pathlib
import re
import sys
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Built-in reference dictionary for sepsis-bundle-timer lookups
# ---------------------------------------------------------------------------
_SEPSIS_BANK: List[tuple] = [
    ("Lactate", "lactate"),
    ("Blood Culture", "blood culture"),
    ("Antibiotic", "antibiotic"),
    ("IV Fluid", "fluid"),
    ("Vasopressor", "vasopressor"),
    ("Creatinine", "creatinine"),
    ("WBC", "wbc"),
    ("Hemoglobin", "hemoglobin"),
    ("Platelets", "platelets"),
    ("Bilirubin", "bilirubin"),
    ("MAP", "map"),
    ("Urine Output", "urine output"),
    ("qSOFA", "qsofa"),
    ("SOFA", "sofa"),
    ("Procalcitonin", "procalcitonin"),
    ("C-Reactive Protein", "crp"),
]


def lookup(query: str) -> Dict[str, Any]:
    """Single lookup: token overlap + substring scoring (no deps). Returns top hits."""
    if query is None:
        raise ValueError("query must not be None")
    q = str(query).lower().strip()
    if not q:
        raise ValueError("query must not be empty")

    scored: List[tuple] = []
    for label, key in _SEPSIS_BANK:
        score = 0
        if key in q:
            score += 10
        # token overlap
        qt = set(q.split())
        lt = set(label.lower().split())
        overlap = len(qt & lt)
        score += overlap * 2
        scored.append((score, label))
    scored.sort(reverse=True)
    top = scored[0] if scored else (0, "no match")
    return {"query": query, "top_hit": top[1], "score": top[0], "all": scored[:3]}


def _validate_path(path_str: str, must_exist: bool = False) -> pathlib.Path:
    """Resolve and validate a file path, preventing directory traversal."""
    p = pathlib.Path(path_str).resolve()
    if must_exist and not p.is_file():
        raise FileNotFoundError(f"Input file not found: {path_str}")
    # Ensure parent directory exists for output
    if not must_exist:
        p.parent.mkdir(parents=True, exist_ok=True)
    return p


def process_csv(inp: str, out: str) -> List[Dict[str, Any]]:
    """Process a CSV file: look up each row's query column and append results."""
    inp_path = _validate_path(inp, must_exist=True)
    out_path = _validate_path(out, must_exist=False)

    with open(inp_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        rows = list(r)
        fn = r.fieldnames
        if not fn:
            raise ValueError("CSV file has no header row")

        # guess query column
        qcol = fn[0]
        for cand in ["query", "test", "drug", "code", "variant", "hla", "lab", "name"]:
            if cand in [c.lower() for c in fn]:
                qcol = [c for c in fn if c.lower() == cand][0]
                break

        results: List[Dict[str, Any]] = []
        for row in rows:
            res = lookup(row.get(qcol, ""))
            merged = {**row, "top_hit": res["top_hit"], "lookup_score": res["score"]}
            results.append(merged)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(fn) + ["top_hit", "lookup_score"])
        w.writeheader()
        w.writerows(results)
    return results


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="sepsis_timer", description="Sepsis Bundle Compliance Timer")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("single")
    s.add_argument("query", nargs="?", default="creatinine")
    s.add_argument("--query", dest="q2")
    b = sub.add_parser("batch")
    b.add_argument("--input", required=True)
    b.add_argument("--output", required=True)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    p = build_parser()
    a = p.parse_args(argv)
    if a.cmd == "single":
        q = getattr(a, "q2", None) or getattr(a, "query")
        print(lookup(q))
        return 0
    if a.cmd == "batch":
        res = process_csv(a.input, a.output)
        print(f"Processed {len(res)} -> {a.output}")
        return 0
    p.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
