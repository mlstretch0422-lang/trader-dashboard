#!/usr/bin/env python3
"""Validate the strategy evidence registry and Phase 7 experiment manifest.

This validates evidence hygiene and experiment structure. It does not validate
trading performance and it does not compile Pine Script.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "data" / "content-status.json"
EXPERIMENT_PATH = ROOT / "experiments" / "phase7" / "experiment_manifest.json"

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
        "id", "name", "value", "source", "sample_size", "date_range",
        "test_type", "cost_model", "decision",
    }
    missing = sorted(required - metric.keys())
    if missing:
        fail(f"metric {metric.get('id', '<missing-id>')}: missing {', '.join(missing)}", errors)
        return

    if not isinstance(metric.get("value"), dict) or not metric["value"]:
        fail(f"metric {metric.get('id', '<missing-id>')}: 'value' must be a non-empty object", errors)

    sample_size = metric.get("sample_size")
    if not isinstance(sample_size, (int, float)) or sample_size <= 0:
        fail(f"metric {metric.get('id', '<missing-id>')}: sample_size must be positive", errors)

    source = metric.get("source")
    if not isinstance(source, str) or not source.strip():
        fail(f"metric {metric.get('id', '<missing-id>')}: source must be a repository path", errors)


def validate_experiment_manifest(errors: list[str]) -> int:
    if not EXPERIMENT_PATH.exists():
        fail(f"experiment manifest not found: {EXPERIMENT_PATH}", errors)
        return 0

    try:
        manifest = json.loads(EXPERIMENT_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"invalid experiment manifest JSON: {exc}", errors)
        return 0

    research_script = manifest.get("research_script")
    if not isinstance(research_script, str) or not research_script.strip():
        fail("experiment manifest must name a research_script", errors)
    elif not (ROOT / research_script).exists():
        fail(f"research_script does not exist: {research_script}", errors)

    experiments = manifest.get("experiments")
    if not isinstance(experiments, list) or not experiments:
        fail("experiment manifest must contain a non-empty 'experiments' list", errors)
        return 0

    experiment_ids: list[str] = []
    for experiment in experiments:
        if not isinstance(experiment, dict):
            fail("every experiment must be an object", errors)
            continue

        experiment_id = experiment.get("id")
        for field in ("id", "question", "decision_rule"):
            value = experiment.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"experiment {experiment_id or '<missing-id>'}: missing/non-empty '{field}'", errors)

        if isinstance(experiment_id, str) and experiment_id.strip():
            experiment_ids.append(experiment_id)

        variants = experiment.get("variants")
        manual_checks = experiment.get("manual_checks")

        has_variants = isinstance(variants, list) and len(variants) >= 2
        has_manual_checks = (
            isinstance(manual_checks, list)
            and len(manual_checks) >= 1
            and all(isinstance(check, str) and check.strip() for check in manual_checks)
        )

        if not has_variants and not has_manual_checks:
            fail(
                f"experiment {experiment_id}: must contain either at least two variants "
                "or at least one manual sanity check",
                errors,
            )

        if isinstance(variants, list):
            variant_names: list[str] = []
            for variant in variants:
                if not isinstance(variant, dict):
                    fail(f"experiment {experiment_id}: every variant must be an object", errors)
                    continue
                name = variant.get("name")
                if not isinstance(name, str) or not name.strip():
                    fail(f"experiment {experiment_id}: every variant needs a non-empty name", errors)
                else:
                    variant_names.append(name)
            duplicate_variants = [name for name, count in Counter(variant_names).items() if count > 1]
            if duplicate_variants:
                fail(
                    f"experiment {experiment_id}: duplicate variant names: {', '.join(sorted(duplicate_variants))}",
                    errors,
                )

    duplicates = [item_id for item_id, count in Counter(experiment_ids).items() if count > 1]
    if duplicates:
        fail(f"duplicate experiment ids: {', '.join(sorted(duplicates))}", errors)

    run_order = manifest.get("run_order", [])
    if run_order:
        if not isinstance(run_order, list) or not all(isinstance(item, str) for item in run_order):
            fail("run_order must be a list of experiment IDs", errors)
        else:
            missing_from_manifest = [item for item in run_order if item not in experiment_ids]
            if missing_from_manifest:
                fail(f"run_order references missing experiments: {', '.join(missing_from_manifest)}", errors)

    return len(experiments)


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
        metrics = []
    else:
        metric_ids: list[str] = []
        for metric in metrics:
            if not isinstance(metric, dict):
                fail("every metric must be an object", errors)
                continue
            validate_metric(metric, errors)
            metric_id = metric.get("id")
            if isinstance(metric_id, str):
                metric_ids.append(metric_id)
        duplicate_metrics = [metric_id for metric_id, count in Counter(metric_ids).items() if count > 1]
        if duplicate_metrics:
            fail(f"duplicate metric ids: {', '.join(sorted(duplicate_metrics))}", errors)

    experiment_count = validate_experiment_manifest(errors)

    if errors:
        print("Content status validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    counts = Counter(item["status"] for item in items)
    print(f"Registry valid: {len(items)} claims, {len(metrics)} metrics, {experiment_count} experiments")
    print("Status counts: " + ", ".join(f"{status}={counts.get(status, 0)}" for status in sorted(VALID_STATUSES)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
