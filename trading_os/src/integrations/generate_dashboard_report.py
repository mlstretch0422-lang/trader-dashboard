import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from src.integrations.data_provider import get_data_provider
from src.strategies.clean_orb import compute_orb, generate_signals, summary_from_trades


REPLAY_ARCHIVE_PATH = Path(__file__).resolve().parent / "session_replay_archive.json"
TV_ALERTS_PATH = Path(__file__).resolve().parent / "tv_alerts.jsonl"
MAX_LIBRARY_PREVIEW_BYTES = 140_000
MAX_LIBRARY_FILE_BYTES = 1_500_000
MODULE_FILE_RULES = {
    "strategy-center": [
        {"base": "trading_os", "glob": "*.md", "limit": 30},
        {"base": "strat", "glob": "*.md", "limit": 20},
        {"base": "trading_os/pine", "glob": "*.pine", "limit": 10},
    ],
    "backtests": [
        {"base": "strat", "glob": "*BACKTEST*.csv", "limit": 20},
        {"base": "trading_os/experiments", "glob": "*.csv", "limit": 20},
        {"base": "trading_os/experiments", "glob": "*.json", "limit": 20},
    ],
    "research-vault": [
        {"base": "trading_os/docs", "glob": "*.md", "limit": 50},
        {"base": "strat/research_texts", "glob": "*.md", "limit": 30},
        {"base": "strat", "glob": "*RESEARCH*.md", "limit": 30},
    ],
    "downloads": [
        {"base": "share", "glob": "*.html", "limit": 20},
        {"base": "share", "glob": "*.json", "limit": 20},
        {"base": "assets", "glob": "*.md", "limit": 20},
        {"base": "trading_os", "glob": "*CHECKLIST*.md", "limit": 20},
    ],
}


def _safe_float(value: Optional[float]) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_relpath(path: Path) -> str:
    return path.resolve().relative_to(Path(__file__).resolve().parents[3]).as_posix()


def _format_filesize(bytes_count: int) -> str:
    if bytes_count < 1024:
        return f"{bytes_count} B"
    if bytes_count < 1024 * 1024:
        return f"{bytes_count / 1024:.1f} KB"
    return f"{bytes_count / (1024 * 1024):.2f} MB"


def _scan_library_files() -> Dict[str, List[Dict]]:
    workspace_root = Path(__file__).resolve().parents[3]
    allowed_exts = {".md", ".txt", ".csv", ".json", ".py", ".pine", ".html"}
    catalog: Dict[str, List[Dict]] = {}

    for module_id, rules in MODULE_FILE_RULES.items():
        items: List[Dict] = []
        seen = set()
        for rule in rules:
            base_dir = (workspace_root / rule["base"]).resolve()
            if not base_dir.exists() or not base_dir.is_dir():
                continue

            limit = int(rule.get("limit", 20))
            count = 0
            for file_path in sorted(base_dir.rglob(rule["glob"])):
                if count >= limit:
                    break
                if not file_path.is_file() or file_path.suffix.lower() not in allowed_exts:
                    continue
                size = file_path.stat().st_size
                if size > MAX_LIBRARY_FILE_BYTES:
                    continue

                rel_path = _to_relpath(file_path)
                if rel_path in seen:
                    continue
                seen.add(rel_path)

                try:
                    raw = file_path.read_bytes()
                except OSError:
                    continue
                truncated = len(raw) > MAX_LIBRARY_PREVIEW_BYTES
                preview_bytes = raw[:MAX_LIBRARY_PREVIEW_BYTES]
                content = preview_bytes.decode("utf-8", errors="replace")
                modified = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat()

                items.append(
                    {
                        "path": rel_path,
                        "name": file_path.name,
                        "size": size,
                        "size_label": _format_filesize(size),
                        "modified": modified,
                        "extension": file_path.suffix.lower(),
                        "truncated": truncated,
                        "content": content,
                    }
                )
                count += 1

        items.sort(key=lambda x: x.get("modified", ""), reverse=True)
        catalog[module_id] = items

    return catalog


def _build_beginner_guide(mission: Dict, summary: Dict) -> Dict:
    identity = mission.get("identity", {}) or {}
    execution = mission.get("execution_plan", {}) or {}
    supporting = mission.get("supporting_levels", {}) or {}
    directional = mission.get("directional_plan", {}) or {}

    glossary = [
        {"term": "MES", "meaning": "Micro E-mini S&P 500 futures contract. Smaller size than ES."},
        {"term": "ORB", "meaning": "Opening Range Breakout. The high/low built in the opening window."},
        {"term": "HTF", "meaning": "Higher timeframe context such as 1H or 4H bias."},
        {"term": "Liquidity sweep", "meaning": "Price runs a prior high/low to trigger stops before reversing or continuing."},
        {"term": "Reclaim", "meaning": "Price trades back above/below a level and holds it to confirm direction."},
        {"term": "Invalidation", "meaning": "The price level that proves the setup idea is wrong."},
        {"term": "R", "meaning": "Risk unit. If you risk $50, then 1R = $50."},
        {"term": "Slippage", "meaning": "Difference between expected and actual fill price."},
    ]

    checklist = [
        {
            "id": "read-mission",
            "label": "Read the Morning Mission",
            "detail": "Start with the session thesis before you look for an entry.",
            "target": "dashboard",
        },
        {
            "id": "mark-levels",
            "label": "Mark ORB and prior close",
            "detail": "Plot the opening range high and low, midpoint, and prior close on your chart.",
            "target": "dashboard",
        },
        {
            "id": "wait-for-conditions",
            "label": "Wait for the checklist",
            "detail": "Do not trade until the required conditions are completed.",
            "target": "dashboard",
        },
        {
            "id": "calculate-risk",
            "label": "Calculate your risk first",
            "detail": "Use the MES calculator before any entry order is placed.",
            "target": "start-here",
        },
        {
            "id": "journal-review",
            "label": "Log the session afterward",
            "detail": "Write down what happened, even on no-trade days.",
            "target": "trade-bible",
        },
    ]

    lessons = [
        {
            "title": "Lesson 1: What MES is",
            "body": "MES is the smaller futures contract used for learning the process with less dollar risk per point.",
            "status": "Start here",
            "target": "trade-bible",
        },
        {
            "title": "Lesson 2: How ORB works",
            "body": "The ORB is the opening range. Signal Bridge watches for breaks, reclaims, and invalidation.",
            "status": "Core setup",
            "target": "trade-bible",
        },
        {
            "title": "Lesson 3: How to think about risk",
            "body": "A valid setup still needs sizing. Trade Bridge will show the setup, but you still control how much you risk.",
            "status": "Required",
            "target": "start-here",
        },
        {
            "title": "Lesson 4: Review after the close",
            "body": "Use Replay and the Journal to study winners, losers, and no-trade days.",
            "status": "Practice",
            "target": "replay",
        },
    ]

    readiness_checks = [
        "I understand WAIT means no trade.",
        "I know a bullish bias is not an automatic entry.",
        "I will size the trade before I click buy or sell.",
        "I accept that every trade can lose money.",
        "I am comfortable starting on paper first.",
    ]

    routine = [
        {"time": "Before 9:00", "step": "Read the mission, mark your chart, and set max daily risk.", "action": "Open the Morning Mission"},
        {"time": "9:00-9:30", "step": "Observe premarket structure and wait for conditions.", "action": "Review the checklist"},
        {"time": "9:30-10:30", "step": "Only act if the full setup is valid. No chase entries.", "action": "Use the risk calculator"},
        {"time": "11:00", "step": "Finish the session, save the chart, and write the review.", "action": "Open the Replay"},
    ]

    risk_example = {
        "entry": _safe_float(execution.get("entry_zone")),
        "stop": _safe_float(execution.get("invalidation")),
        "target": _safe_float((execution.get("targets") or [None])[0]),
        "contract_value_per_point": 5,
        "tick_value": 1.25,
        "estimated_fees_per_contract": 3.50,
        "symbol": identity.get("instrument") or "MES",
    }

    return {
        "overview": {
            "title": "Welcome to Signal Bridge",
            "body": "This workspace is for learning, planning, replaying, and reviewing one repeatable futures setup at a time.",
            "what_it_is": "A research-driven MES trading workspace built around one repeatable liquidity and ORB framework.",
            "what_it_is_not": "It is not automated trade execution, guaranteed income, or personalized financial advice.",
            "first_goal": "Your first goal is to identify the setup correctly and follow the risk rules consistently.",
        },
        "continue_next": {
            "title": "Continue where you left off",
            "label": "Lesson 2: How ORB works",
            "body": "If you are returning, resume with the ORB lesson and then move into the calculator.",
            "target": "trade-bible",
        },
        "checklist": checklist,
        "lessons": lessons,
        "readiness_checks": readiness_checks,
        "glossary": glossary,
        "routine": routine,
        "risk_example": risk_example,
        "support": {
            "mission_date": identity.get("trading_date"),
            "instrument": identity.get("instrument"),
            "action": directional.get("action", "WAIT"),
            "entry": risk_example["entry"],
            "stop": risk_example["stop"],
            "target": risk_example["target"],
            "prior_close": _safe_float(supporting.get("prior_close")),
            "net": summary.get("net", 0),
        },
    }


def _condition(label: str, status: str, evidence: str) -> Dict:
    return {
        "label": label,
        "status": status,
        "evidence": evidence,
        "updated_time": datetime.now(timezone.utc).isoformat(),
    }


def _build_morning_mission(
    summary: Dict,
    latest_close: Optional[float],
    orb: Optional[Dict],
    prior_close: Optional[float],
    latest_date,
) -> Dict:
    regime_summary = summary.get("regime_summary", {}) or {}
    dominant_phase = regime_summary.get("dominant_phase", "n/a")
    avg_confidence = float(regime_summary.get("avg_confidence", 0.0) or 0.0)
    confidence_pct = round(max(0.0, min(1.0, avg_confidence)) * 100)

    mission_date = str(latest_date) if latest_date is not None else datetime.now(timezone.utc).date().isoformat()
    mission_id = f"mission-{mission_date}-MES"

    if not orb or latest_close is None:
        return {
            "identity": {
                "mission_id": mission_id,
                "trading_date": mission_date,
                "instrument": "MES",
                "strategy_version": "ORB-edge-v1.0",
                "created_time": datetime.now(timezone.utc).isoformat(),
                "last_updated_time": datetime.now(timezone.utc).isoformat(),
                "data_state": "Unavailable",
                "source": "Awaiting strategy output",
            },
            "session_context": {
                "premarket_status": "Unknown",
                "ny_open_time": "09:30 ET",
                "orb_start": "09:30 ET",
                "orb_end": "09:45 ET",
                "execution_window": "09:45-10:30 ET",
                "hard_cutoff_time": "10:30 ET",
                "session_status": "Awaiting data",
                "next_major_event": "Unavailable",
            },
            "directional_plan": {
                "action": "WAIT",
                "primary_bias": "Unknown",
                "htf_bias": "Unknown",
                "market_phase": "Unknown",
                "confidence_pct": None,
                "setup_state": "Mission incomplete",
                "thesis": "Awaiting strategy output",
            },
            "required_conditions": [
                _condition("Required liquidity sweep", "Pending", "Awaiting strategy output"),
                _condition("Required reclaim", "Pending", "Awaiting strategy output"),
                _condition("Required confirmation", "Pending", "Awaiting strategy output"),
                _condition("Required volume condition", "Pending", "Awaiting strategy output"),
                _condition("Required structure condition", "Pending", "Awaiting strategy output"),
                _condition("Time condition", "Pending", "Awaiting strategy output"),
                _condition("News condition", "Not applicable", "No event feed connected"),
            ],
            "execution_plan": {
                "entry_zone": None,
                "invalidation": None,
                "stop": None,
                "targets": [],
                "expected_rr": None,
                "maximum_risk": "0.5R",
                "maximum_number_of_trades": 1,
                "break_even_rule": "Move stop to break-even after T1",
                "management_rule": "Do not chase after 10:30 ET",
            },
            "no_trade_conditions": [
                "Mission incomplete",
                "Late-entry cutoff reached",
                "Invalid structure",
                "Daily-loss restriction active",
            ],
            "supporting_levels": {
                "orb_high": None,
                "orb_low": None,
                "prior_day_high": None,
                "prior_day_low": None,
                "prior_close": _safe_float(prior_close),
                "overnight_high": None,
                "overnight_low": None,
                "session_midpoint": None,
                "liquidity_targets": [],
            },
            "outcome": {
                "trade_triggered": False,
                "entry_time": None,
                "exit_time": None,
                "outcome": "Not triggered",
                "realized_r": None,
                "maximum_favorable_excursion": None,
                "maximum_adverse_excursion": None,
                "setup_validity": "Unknown",
                "rule_adherence": "Unknown",
                "screenshot": None,
                "notes": "Awaiting strategy output",
                "lesson": "Awaiting strategy output",
            },
            "data_state": "Unavailable",
            "source": "Awaiting strategy output",
            "discord_summary": "WAIT - Mission incomplete. Awaiting strategy output.",
        }

    orb_high = float(orb["orb_high"])
    orb_low = float(orb["orb_low"])
    orb_mid = float(orb["orb_mid"])
    orb_range = max(float(orb.get("orb_range", 0.0)), 0.25)

    if dominant_phase == "strong_trend_up":
        action = "LONG"
        bias = "Bullish"
        htf = "Bullish"
        entry = orb_high
        invalidation = orb_mid
        targets = [entry + orb_range * 0.5, entry + orb_range * 1.0, entry + orb_range * 1.5]
        state = "READY ON RECLAIM" if latest_close >= orb_mid else "WAIT FOR RECLAIM"
    elif dominant_phase == "strong_trend_down":
        action = "SHORT"
        bias = "Bearish"
        htf = "Bearish"
        entry = orb_low
        invalidation = orb_mid
        targets = [entry - orb_range * 0.5, entry - orb_range * 1.0, entry - orb_range * 1.5]
        state = "READY ON RECLAIM" if latest_close <= orb_mid else "WAIT FOR RECLAIM"
    else:
        action = "WAIT"
        bias = "Neutral"
        htf = "Neutral"
        entry = None
        invalidation = None
        targets = []
        state = "NO TRADE UNTIL CONDITIONS ALIGN"

    required_conditions = [
        _condition(
            "Required liquidity sweep",
            "Completed" if latest_close <= orb_low or latest_close >= orb_high else "Pending",
            f"Latest close {latest_close:.2f}; ORB range {orb_low:.2f}-{orb_high:.2f}",
        ),
        _condition("Required reclaim", "Completed" if state == "READY ON RECLAIM" else "Pending", state),
        _condition("Required confirmation", "Pending", "Awaiting trigger confirmation candle"),
        _condition("Required volume condition", "Pending", "Volume rule not wired yet"),
        _condition("Required structure condition", "Completed" if action in ("LONG", "SHORT") else "Pending", dominant_phase),
        _condition("Time condition", "Completed", "Within configured mission window"),
        _condition("News condition", "Not applicable", "Calendar feed integration pending"),
    ]

    rr = None
    if entry is not None and invalidation is not None and targets:
        risk = abs(entry - invalidation)
        reward = abs(targets[0] - entry)
        rr = round(reward / risk, 2) if risk > 0 else None

    liquidity_targets = [_safe_float(t) for t in targets]
    mission = {
        "identity": {
            "mission_id": mission_id,
            "trading_date": mission_date,
            "instrument": "MES",
            "strategy_version": "ORB-edge-v1.0",
            "created_time": datetime.now(timezone.utc).isoformat(),
            "last_updated_time": datetime.now(timezone.utc).isoformat(),
            "data_state": "Research",
            "source": "Strategy report",
        },
        "session_context": {
            "premarket_status": "Complete",
            "ny_open_time": "09:30 ET",
            "orb_start": "09:30 ET",
            "orb_end": "09:45 ET",
            "execution_window": "09:45-10:30 ET",
            "hard_cutoff_time": "10:30 ET",
            "session_status": "In session",
            "next_major_event": "Unavailable",
        },
        "directional_plan": {
            "action": action,
            "primary_bias": bias,
            "htf_bias": htf,
            "market_phase": dominant_phase,
            "confidence_pct": confidence_pct,
            "setup_state": state,
            "thesis": f"{bias} regime context with ORB retest framework. Trade only after checklist completion.",
        },
        "required_conditions": required_conditions,
        "execution_plan": {
            "entry_zone": _safe_float(entry),
            "invalidation": _safe_float(invalidation),
            "stop": _safe_float(invalidation),
            "targets": liquidity_targets,
            "expected_rr": rr,
            "maximum_risk": "0.5R",
            "maximum_number_of_trades": 1,
            "break_even_rule": "Move stop to break-even after T1",
            "management_rule": "No chase trades after 10:30 ET",
        },
        "no_trade_conditions": [
            "Confidence below 60%",
            "No reclaim confirmation",
            "Late entry after cutoff",
            "Invalid structure",
            "Daily-loss restriction active",
        ],
        "supporting_levels": {
            "orb_high": _safe_float(orb_high),
            "orb_low": _safe_float(orb_low),
            "prior_day_high": None,
            "prior_day_low": None,
            "prior_close": _safe_float(prior_close),
            "overnight_high": None,
            "overnight_low": None,
            "session_midpoint": _safe_float(orb_mid),
            "liquidity_targets": liquidity_targets,
        },
        "outcome": {
            "trade_triggered": False,
            "entry_time": None,
            "exit_time": None,
            "outcome": "Pending",
            "realized_r": None,
            "maximum_favorable_excursion": None,
            "maximum_adverse_excursion": None,
            "setup_validity": "Pending",
            "rule_adherence": "Pending",
            "screenshot": None,
            "notes": "Session still active",
            "lesson": "Collect post-market evaluation",
        },
        "data_state": "Research",
        "source": "Strategy report",
    }

    entry_text = f"{entry:.2f}" if entry is not None else "n/a"
    mission["discord_summary"] = (
        f"{mission['identity']['trading_date']} MES | {action} | {state} | "
        f"Confidence {confidence_pct}% | Entry {entry_text}"
    )
    return mission


def _build_chart_payload(day_frame: pd.DataFrame, mission: Dict) -> Dict:
    if day_frame.empty:
        return {
            "data_state": "Unavailable",
            "simulated": False,
            "candles": [],
            "levels": {},
        }

    candles: List[Dict] = []
    for _, row in day_frame.tail(78).iterrows():
        candles.append(
            {
                "time": int(pd.Timestamp(row["datetime"]).timestamp()),
                "open": _safe_float(row["open"]),
                "high": _safe_float(row["high"]),
                "low": _safe_float(row["low"]),
                "close": _safe_float(row["close"]),
            }
        )

    current_price = candles[-1]["close"] if candles else None
    supporting_levels = mission.get("supporting_levels", {}) or {}
    execution_plan = mission.get("execution_plan", {}) or {}

    levels = {
        "orb_high": supporting_levels.get("orb_high"),
        "orb_low": supporting_levels.get("orb_low"),
        "prior_close": supporting_levels.get("prior_close"),
        "entry": execution_plan.get("entry_zone"),
        "invalidation": execution_plan.get("invalidation"),
        "targets": execution_plan.get("targets", []),
        "current_price": _safe_float(current_price),
    }

    return {
        "data_state": "Research",
        "simulated": False,
        "candles": candles,
        "levels": levels,
    }


def _build_watchlist_payload(latest_close: Optional[float], mission: Dict) -> List[Dict]:
    directional_plan = mission.get("directional_plan", {}) or {}
    return [
        {
            "symbol": "MES",
            "data_state": "Research",
            "price": _safe_float(latest_close),
            "bias": directional_plan.get("primary_bias", "Unknown"),
            "action": directional_plan.get("action", "WAIT"),
        },
        {"symbol": "NQ", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
        {"symbol": "SPY", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
        {"symbol": "BTC", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
        {"symbol": "GOLD", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
        {"symbol": "OIL", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
    ]


def _build_replay_events(mission: Dict) -> List[Dict]:
    identity = mission.get("identity", {}) or {}
    directional_plan = mission.get("directional_plan", {}) or {}
    outcome = mission.get("outcome", {}) or {}
    base_time = identity.get("last_updated_time") or datetime.now(timezone.utc).isoformat()

    conditions = mission.get("required_conditions", []) or []
    events = [
        {
            "title": "Mission Published",
            "body": f"{directional_plan.get('action', 'WAIT')} | {directional_plan.get('setup_state', 'Unknown')}",
            "time": identity.get("created_time") or base_time,
        }
    ]

    for idx, condition in enumerate(conditions):
        events.append(
            {
                "title": condition.get("label") or f"Condition {idx + 1}",
                "body": f"{condition.get('status', 'Pending')} | {condition.get('evidence', 'No evidence logged')}",
                "time": condition.get("updated_time") or base_time,
            }
        )

    events.append(
        {
            "title": "Outcome Snapshot",
            "body": f"{outcome.get('outcome', 'Pending')} | Rule adherence {outcome.get('rule_adherence', 'Pending')}",
            "time": base_time,
        }
    )
    return events


def _load_recent_tv_alerts(path: Path, max_entries: int = 400) -> List[Dict]:
    if not path.exists():
        return []

    alerts: List[Dict] = []
    try:
        with path.open("r", encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(entry, dict):
                    alerts.append(entry)
    except OSError:
        return []

    return alerts[-max_entries:]


def _alerts_for_mission(alerts: List[Dict], mission: Dict) -> List[Dict]:
    identity = mission.get("identity", {}) or {}
    date = identity.get("trading_date")
    instrument = str(identity.get("instrument") or "MES").upper()
    if not date:
        return []

    matched: List[Dict] = []
    for alert in alerts:
        symbol = str(alert.get("symbol") or "").upper()
        alert_time = str(alert.get("time") or alert.get("received_at") or "")
        if symbol and symbol != instrument:
            continue
        if alert_time.startswith(date):
            matched.append(alert)
    return matched


def _alert_to_replay_event(alert: Dict) -> Dict:
    side = str(alert.get("side") or "WAIT").upper()
    event_name = str(alert.get("event") or "alert")
    price = _safe_float(alert.get("price"))
    note = str(alert.get("note") or "TradingView alert")
    price_text = f" @ {price:.2f}" if price is not None else ""

    return {
        "title": f"TV {event_name} {side}".strip(),
        "body": f"{note}{price_text}",
        "time": alert.get("time") or alert.get("received_at") or datetime.now(timezone.utc).isoformat(),
    }


def _build_replay_snapshot(mission: Dict, chart: Dict, tv_alerts: Optional[List[Dict]] = None) -> Dict:
    identity = mission.get("identity", {}) or {}
    directional_plan = mission.get("directional_plan", {}) or {}
    outcome = mission.get("outcome", {}) or {}

    mission_events = _build_replay_events(mission)
    tv_events = [_alert_to_replay_event(a) for a in (tv_alerts or [])]

    news = [
        {
            "title": "Replay news feed not connected",
            "summary": "Historical macro/news snapshots will appear here once news storage is enabled.",
            "time": identity.get("last_updated_time"),
        }
    ]

    if tv_alerts:
        latest = tv_alerts[-1]
        news.insert(
            0,
            {
                "title": "TradingView alerts connected",
                "summary": f"{len(tv_alerts)} alert(s) captured for this session. Latest: {latest.get('event', 'alert')} {str(latest.get('side', 'WAIT')).upper()}.",
                "time": latest.get("time") or latest.get("received_at"),
            },
        )

    return {
        "date": identity.get("trading_date") or datetime.now(timezone.utc).date().isoformat(),
        "instrument": identity.get("instrument") or "MES",
        "mission_id": identity.get("mission_id"),
        "strategy_version": identity.get("strategy_version"),
        "data_state": mission.get("data_state", "Unavailable"),
        "action": directional_plan.get("action", "WAIT"),
        "setup_state": directional_plan.get("setup_state"),
        "confidence_pct": directional_plan.get("confidence_pct"),
        "mission": mission,
        "chart": chart,
        "news": news,
        "events": mission_events + tv_events,
        "outcome": outcome,
        "captured_at": datetime.now(timezone.utc).isoformat(),
    }


def _load_replay_archive(path: Path) -> List[Dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text())
        if isinstance(data, dict) and isinstance(data.get("snapshots"), list):
            return data["snapshots"]
        if isinstance(data, list):
            return data
    except (json.JSONDecodeError, OSError):
        return []
    return []


def _upsert_replay_archive(archive: List[Dict], snapshot: Dict, max_entries: int = 30) -> List[Dict]:
    date = snapshot.get("date")
    instrument = snapshot.get("instrument")
    filtered = [
        item
        for item in archive
        if not (item.get("date") == date and item.get("instrument") == instrument)
    ]
    filtered.append(snapshot)
    filtered.sort(key=lambda x: (x.get("date") or "", x.get("captured_at") or ""), reverse=True)
    return filtered[:max_entries]


def _write_replay_archive(path: Path, snapshots: List[Dict]) -> None:
    path.write_text(json.dumps({"snapshots": snapshots}, indent=2))


def build_dashboard_payload(summary, mission=None, chart=None, watchlist=None, replay_snapshots=None):
    regime_summary = summary.get("regime_summary", {}) or {}
    phase_counts = regime_summary.get("phase_counts", {}) or {}
    dominant_phase = regime_summary.get("dominant_phase", "n/a")

    replay_snapshots = replay_snapshots or []
    replay_by_date = {
        f"{item.get('date')}::{item.get('instrument', 'MES')}": item
        for item in replay_snapshots
        if item.get("date")
    }

    mission_archive = [
        {
            "mission_id": item.get("mission_id"),
            "date": item.get("date"),
            "instrument": item.get("instrument"),
            "initial_action": item.get("action"),
            "final_outcome": (item.get("outcome") or {}).get("outcome"),
            "conditions_completed": sum(
                1
                for c in ((item.get("mission") or {}).get("required_conditions") or [])
                if c.get("status") == "Completed"
            ),
            "phase": ((item.get("mission") or {}).get("directional_plan") or {}).get("market_phase"),
            "trade_triggered": (item.get("outcome") or {}).get("trade_triggered"),
            "realized_r": (item.get("outcome") or {}).get("realized_r"),
            "data_state": item.get("data_state"),
            "snapshot_key": f"{item.get('date')}::{item.get('instrument', 'MES')}",
        }
        for item in replay_snapshots
    ]

    return {
        "status": {
            "overall": "Local research stack active",
            "mode": "regime-aware ORB workflow",
            "last_updated": "local analysis run",
        },
        "stack": {
            "strategy": {
                "name": "ORB edge framework",
                "status": "implemented",
                "details": [
                    "Market-phase aware execution logic",
                    "Trade generation and confidence tagging",
                    "Regime-aware summaries for research review",
                ],
            },
            "indicators": {
                "name": "Core indicators",
                "status": "active",
                "items": [
                    {"name": "ORB", "status": "implemented"},
                    {"name": "Market phase classifier", "status": "implemented"},
                    {"name": "Confidence scoring", "status": "implemented"},
                ],
            },
            "tools_data": {
                "name": "Tools and data",
                "status": "local",
                "items": [
                    {"name": "Local ES history", "status": "available"},
                    {"name": "Discord bridge", "status": "wired"},
                    {"name": "Dashboard view", "status": "running"},
                ],
            },
        },
        "research_output": {
            "trades": summary.get("trades", 0),
            "net": summary.get("net", 0),
            "win_rate": summary.get("win_rate", 0),
            "dominant_phase": dominant_phase,
            "phase_counts": phase_counts,
        },
        "data_state": {
            "overall": "Research",
            "mission": (mission or {}).get("data_state", "Unavailable"),
            "chart": (chart or {}).get("data_state", "Unavailable"),
            "watchlist": "Mixed",
        },
        "morning_mission": mission or {},
        "missions": {
            "current": mission or {},
            "archive": mission_archive,
        },
        "session_replay": {
            "current_key": f"{((mission or {}).get('identity', {}) or {}).get('trading_date')}::{((mission or {}).get('identity', {}) or {}).get('instrument', 'MES')}",
            "snapshots_by_key": replay_by_date,
            "keys": list(replay_by_date.keys()),
        },
        "discord_summary": (mission or {}).get("discord_summary"),
        "chart": chart or {},
        "watchlist": watchlist or [],
        "library_catalog": _scan_library_files(),
        "beginner_guide": _build_beginner_guide(mission or {}, summary),
        "raw_summary": summary,
    }


def main():
    provider = get_data_provider()
    df = provider.load()
    if "datetime" in df.columns:
        df = df.copy()
        df["datetime"] = pd.to_datetime(df["datetime"])
    df = df.sort_values("datetime").reset_index(drop=True)

    orb_map = compute_orb(df, 570, 585)
    trades = generate_signals(df, orb_map, 570, 585, market_phase_filter=True, market_phase_threshold=0.5, use_vwap=False, use_ema=False)
    summary = summary_from_trades(trades)

    latest_close = _safe_float(df.iloc[-1]["close"]) if not df.empty else None
    latest_date = df["datetime"].dt.date.iloc[-1] if not df.empty else None
    day_frame = df[df["datetime"].dt.date == latest_date].copy() if latest_date is not None else pd.DataFrame()
    previous_rows = df[df["datetime"].dt.date < latest_date] if latest_date is not None else pd.DataFrame()
    prior_close = _safe_float(previous_rows.iloc[-1]["close"]) if not previous_rows.empty else None
    orb = orb_map.get(latest_date) if latest_date is not None else None

    mission = _build_morning_mission(summary, latest_close=latest_close, orb=orb, prior_close=prior_close, latest_date=latest_date)
    chart = _build_chart_payload(day_frame, mission)
    watchlist = _build_watchlist_payload(latest_close, mission)

    all_tv_alerts = _load_recent_tv_alerts(TV_ALERTS_PATH)
    session_tv_alerts = _alerts_for_mission(all_tv_alerts, mission)
    replay_snapshot = _build_replay_snapshot(mission, chart, tv_alerts=session_tv_alerts)
    replay_archive = _load_replay_archive(REPLAY_ARCHIVE_PATH)
    replay_archive = _upsert_replay_archive(replay_archive, replay_snapshot)
    _write_replay_archive(REPLAY_ARCHIVE_PATH, replay_archive)

    payload = build_dashboard_payload(summary, mission=mission, chart=chart, watchlist=watchlist, replay_snapshots=replay_archive)

    output_path = Path(__file__).resolve().parent / "report.json"
    output_path.write_text(json.dumps(payload, indent=2))
    print(f"Wrote dashboard report to {output_path}")


if __name__ == "__main__":
    main()
