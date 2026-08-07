#!/usr/bin/env python3
"""Validate the strategy evidence registry.

This script intentionally validates evidence hygiene rather than trading performance.
It prevents claims from silently losing provenance or being promoted without the
metadata required by the project governance rules.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "content-status.json"

VALID_STATUSES = {"VERIFIED", "TESTING", "UNTESTED", "RETIRED"}
VALID_EVIDENCE_LEVELS = {
    "PROJECT_RULE",
    "IMPLEMENTED",
    "BACKTESTED",
    "ISOLATED_ATTRIBUTION",
    "WALK_FORWARD",
    "PAPER_FORWARD",
    "LIVE",
}


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def require_nonempty_string(item: dict[str, Any], field: str, errors: list[str]) -> None:
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"{item.get('id', '<missing-id>')}: '{field}' must be a non-empty string", errors)


def validate_metric(metric: dict[str, Any], errors: list[str]) -> None:
    required = {
        "id",
        "name",
        "value",
        "source",
        "sample_size",
        "date_range",
        "test_type",
        "cost_model",
        "decision",
    }
    missing = sorted(required - metric.keys())
    if missing:
        fail(f"metric {metric.get('id', '<missing-id>')}: missing {', '.join(missing)}", errors)


def main() -> int:
    errors: list[str] = []

    if not REGISTRY_PATH.exists():
        print(f"ERROR: registry not found: {REGISTRY_PATH}", file=sys.stderr)
        return 1

    try:
        data = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON: {exc}", file=sys.stderr)
        return 1

    items = data.get("items")
    if not isinstance(items, list) or not items:
        fail("'items' must be a non-empty list", errors)
        items = []

    ids: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            fail("every registry item must be an object", errors)
            continue

        for field in ("id", "name", "status", "evidence_level", "category", "claim"):
            require_nonempty_string(item, field, errors)

        item_id = item.get("id")
        if isinstance(item_id, str):
            ids.append(item_id)

        status = item.get("status")
        if status not in VALID_STATUSES:
            fail(f"{item_id}: invalid status '{status}'", errors)

        evidence_level = item.get("evidence_level")
        if evidence_level not in VALID_EVIDENCE_LEVELS:
            fail(f"{item_id}: invalid evidence level '{evidence_level}'", errors)

        sources = item.get("sources")
        if not isinstance(sources, list) or not sources or not all(isinstance(source, str) and source.strip() for source in sources):
            fail(f"{item_id}: 'sources' must contain at least one repository path", errors)

        if status == "VERIFIED" and evidence_level == "IMPLEMENTED":
            fail(f"{item_id}: implementation alone cannot support VERIFIED status", errors)

        if status in {"TESTING", "UNTESTED"} and not item.get("note") and not item.get("test_requirements"):
            fail(f"{item_id}: testing/untested records need an evidence note or test requirements", errors)

    duplicates = [item_id for item_id, count in Counter(ids).items() if count > 1]
    if duplicates:
        fail(f"duplicate item ids: {', '.join(sorted(duplicates))}", errors)

    metrics = data.get("metrics", [])
    if not isinstance(metrics, list):
        fail("'metrics' must be a list", errors)
    else:
        for metric in metrics:
            if not isinstance(metric, dict):
                fail("every metric must be an object", errors)
                continue
            validate_metric(metric, errors)

    if errors:
        print("Content status validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    counts = Counter(item["status"] for item in items)
    print(f"Registry valid: {len(items)} claims, {len(metrics)} metrics")
    print("Status counts: " + ", ".join(f"{status}={counts.get(status, 0)}" for status in sorted(VALID_STATUSES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
