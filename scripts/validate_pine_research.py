#!/usr/bin/env python3
"""Static governance checks for the current Pine research harness.

This does NOT compile Pine Script and must never be described as a TradingView
compiler check. It only prevents known project regressions from silently
returning before the manual TradingView compile step.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "experiments" / "phase7" / "experiment_manifest.json"


def main() -> int:
    errors: list[str] = []

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read experiment manifest: {exc}", file=sys.stderr)
        return 1

    relative_script = manifest.get("research_script")
    if not isinstance(relative_script, str) or not relative_script.strip():
        print("ERROR: manifest research_script is missing", file=sys.stderr)
        return 1

    script_path = ROOT / relative_script
    if not script_path.exists():
        print(f"ERROR: Pine research script not found: {relative_script}", file=sys.stderr)
        return 1

    pine = script_path.read_text(encoding="utf-8")

    required_snippets = {
        "Pine v6 declaration": "//@version=6",
        "research labeling": "RESEARCH",
        "10:30 entry cutoff": 'i_tradeEnd   = input.string("1030"',
        "11:00 force-flat input": 'i_flatTime   = input.string("1100"',
        "date-range lock": "i_testStart = input.time(",
        "environment lock": "i_enforceEnvironment = input.bool(true",
        "future-bar retest": "bar_index > setupBar",
        "opposite-side invalidation": "i_invalidateOnOppositeClose",
        "close-time force-flat state": "pastFlatOnClose = closeMins >= flatMins",
        "force-flat transition": "forceFlatHit = pastFlatOnClose",
        "immediate force close": "strategy.close_all(immediately=true",
        "single long bracket": 'strategy.exit("Long Exit", "Long"',
        "single short bracket": 'strategy.exit("Short Exit", "Short"',
        "fixed one-contract baseline": "default_qty_value=1",
        "close-fill assumption": "process_orders_on_close=true",
        "two-tick slippage declaration": "slippage=2",
    }

    for label, snippet in required_snippets.items():
        if snippet not in pine:
            errors.append(f"missing {label}: {snippet!r}")

    forbidden_snippets = {
        "known broken equal-start/end force-flat helper": "f_inWindow(i_flatTime, i_flatTime",
        "staircase management in entry attribution harness": "i_useStaircase",
        "partial target 1 in entry attribution harness": "TP1 Qty %",
        "partial target 2 in entry attribution harness": "TP2 Qty %",
        "partial target 3 in entry attribution harness": "TP3 Qty %",
    }

    for label, snippet in forbidden_snippets.items():
        if snippet in pine:
            errors.append(f"forbidden regression: {label}: {snippet!r}")

    baseline = manifest.get("baseline", {})
    if baseline.get("trade_end") != "1030":
        errors.append("manifest baseline trade_end must remain 1030 for current primary model")
    if baseline.get("force_flat") != "1100":
        errors.append("manifest baseline force_flat must remain 1100")
    if baseline.get("max_trades_per_day") != 1:
        errors.append("manifest baseline max_trades_per_day must remain 1")

    slippage = baseline.get("slippage", {})
    if slippage.get("pine_value_ticks") != 2:
        errors.append("manifest must record Pine slippage as 2 ticks")
    if slippage.get("interpreted_points_per_affected_fill") != 0.5:
        errors.append("manifest must record 2 ES/MES ticks as 0.50 index points")

    execution = baseline.get("execution_model", {})
    if execution.get("process_orders_on_close") is not True:
        errors.append("manifest execution model must disclose process_orders_on_close=true")

    if errors:
        print("Pine research governance validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print("\nNOTE: this is a static governance check, not a Pine compiler.", file=sys.stderr)
        return 1

    print(f"Static Pine research guard passed: {relative_script}")
    print("NOTE: TradingView compile/sanity check P7-E00 is still required.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
