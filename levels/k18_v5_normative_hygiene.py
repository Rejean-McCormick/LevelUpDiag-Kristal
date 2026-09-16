from __future__ import annotations

import re
from pathlib import Path


def run(cfg, report):
    root = Path(cfg["_target_root"])
    base = root / "docs/Technical-Reference/kristal-docs-v5"
    acceptance = base / "03-reproducibility/reproducibility-acceptance-tests.md"

    if not acceptance.is_file():
        report.add(
            "kristal.v5.acceptance_doc.present",
            "FAIL",
            "normative_hygiene",
            "The v5 reproducibility acceptance-test document is missing.",
            path=str(acceptance),
        )
        return

    text = acceptance.read_text(encoding="utf-8")
    # Stale major-version normative language is dangerous inside the v5 normative tree.
    stale = []
    pattern = re.compile(r"\b(?:Kristal\s+)?v(?:3|4)\b", re.IGNORECASE)
    for lineno, line in enumerate(text.splitlines(), 1):
        if pattern.search(line):
            stale.append({"line": lineno, "text": line[:300]})

    report.add(
        "kristal.v5.acceptance_doc.no_stale_major_markers",
        "PASS" if not stale else "FAIL",
        "normative_hygiene",
        "The v5 acceptance document contains no stale v3/v4 normative markers."
        if not stale
        else "The v5 acceptance document still contains v3/v4 markers that can make normative applicability ambiguous.",
        evidence=stale or {"checked": acceptance.relative_to(root).as_posix()},
        recommendation="Replace stale major-version language with v5/current wording or explicitly label it historical/non-normative."
        if stale
        else None,
    )

    required_cases = ["EX-1", "EX-2", "EX-3", "EX-4", "RP-1", "RP-2", "RP-3", "RP-4", "RP-5", "RP-6"]
    missing = [case for case in required_cases if case not in text]
    report.add(
        "kristal.v5.acceptance_doc.required_case_ids",
        "PASS" if not missing else "FAIL",
        "normative_hygiene",
        "The v5 acceptance document names the expected EX/RP conformance cases."
        if not missing
        else "One or more expected EX/RP conformance case identifiers are absent.",
        evidence={"missing": missing, "expected": required_cases},
    )
