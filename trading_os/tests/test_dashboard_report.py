import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from trading_os.src.integrations.generate_dashboard_report import build_dashboard_payload


def test_build_dashboard_payload_includes_premium_sections():
    summary = {
        "trades": 3,
        "net": 12.5,
        "win_rate": 0.67,
        "regime_summary": {
            "dominant_phase": "strong_trend_up",
            "phase_counts": {"strong_trend_up": 2},
        },
    }

    payload = build_dashboard_payload(summary)

    assert payload["status"]["overall"] == "Local research stack active"
    assert payload["stack"]["strategy"]["status"] == "implemented"
    assert payload["stack"]["indicators"]["items"][0]["name"] == "ORB"
    assert payload["stack"]["tools_data"]["items"][0]["name"] == "Local ES history"
    assert payload["research_output"]["trades"] == 3
    assert "beginner_guide" in payload
    assert payload["beginner_guide"]["overview"]["what_it_is"]
    assert isinstance(payload["beginner_guide"]["checklist"], list)
    assert isinstance(payload["beginner_guide"]["lessons"], list)
    assert isinstance(payload["beginner_guide"]["readiness_checks"], list)
    assert isinstance(payload["beginner_guide"]["routine"], list)
    assert payload["beginner_guide"]["continue_next"]["title"] == "Continue where you left off"
    assert payload["beginner_guide"]["risk_example"]["contract_value_per_point"] == 5
    assert payload["beginner_guide"]["risk_example"]["estimated_fees_per_contract"] == 3.5


def test_build_dashboard_payload_enforces_mission_chart_watchlist_schema():
    summary = {
        "trades": 2,
        "net": 4.2,
        "win_rate": 0.5,
        "regime_summary": {
            "dominant_phase": "range_expansion",
            "phase_counts": {"range_expansion": 1},
        },
    }

    mission = {
        "identity": {
            "mission_id": "mission-2026-07-01-MES",
            "trading_date": "2026-07-01",
            "instrument": "MES",
            "strategy_version": "ORB-edge-v1.0",
            "last_updated_time": "2026-07-01T14:45:00+00:00",
        },
        "directional_plan": {
            "action": "WAIT",
            "primary_bias": "Neutral",
            "htf_bias": "Neutral",
            "market_phase": "range_expansion",
            "confidence_pct": 55,
            "setup_state": "Awaiting reclaim",
        },
        "execution_plan": {
            "entry_zone": 6102.25,
            "invalidation": 6099.50,
            "targets": [6105.0, 6107.0],
            "expected_rr": 1.0,
            "maximum_number_of_trades": 1,
        },
        "required_conditions": [
            {"label": "Required reclaim", "status": "Pending", "evidence": "Not confirmed"}
        ],
        "no_trade_conditions": ["Late entry after cutoff"],
        "supporting_levels": {
            "orb_high": 6104.0,
            "orb_low": 6100.0,
            "prior_close": 6098.75,
            "liquidity_targets": [6105.0],
        },
        "outcome": {
            "trade_triggered": False,
            "outcome": "Pending",
            "realized_r": None,
        },
        "data_state": "Research",
        "source": "Strategy report",
        "discord_summary": "WAIT - Awaiting reclaim",
    }

    chart = {
        "data_state": "Research",
        "candles": [
            {"time": 1719835800, "open": 6100.0, "high": 6102.0, "low": 6099.5, "close": 6101.25}
        ],
        "levels": {
            "orb_high": 6104.0,
            "orb_low": 6100.0,
            "prior_close": 6098.75,
            "entry": 6102.25,
            "invalidation": 6099.5,
            "targets": [6105.0, 6107.0],
        },
    }

    watchlist = [
        {"symbol": "MES", "data_state": "Research", "price": 6101.25, "bias": "Neutral", "action": "WAIT"},
        {"symbol": "NQ", "data_state": "Unavailable", "price": None, "bias": "Unavailable", "action": "Unavailable"},
    ]

    replay_snapshots = [
        {
            "date": "2026-07-01",
            "instrument": "MES",
            "mission_id": "mission-2026-07-01-MES",
            "action": "WAIT",
            "data_state": "Research",
            "mission": mission,
            "chart": chart,
            "events": [
                {"title": "Mission Published", "body": "WAIT | Awaiting reclaim", "time": "2026-07-01T14:00:00+00:00"}
            ],
            "outcome": mission["outcome"],
        }
    ]

    payload = build_dashboard_payload(summary, mission=mission, chart=chart, watchlist=watchlist, replay_snapshots=replay_snapshots)

    assert "morning_mission" in payload
    assert "chart" in payload
    assert "watchlist" in payload
    assert "data_state" in payload

    assert payload["morning_mission"]["identity"]["mission_id"] == "mission-2026-07-01-MES"
    assert payload["morning_mission"]["directional_plan"]["action"] == "WAIT"
    assert isinstance(payload["morning_mission"]["required_conditions"], list)

    candles = payload["chart"]["candles"]
    assert isinstance(candles, list)
    assert candles and all(k in candles[0] for k in ("time", "open", "high", "low", "close"))

    levels = payload["chart"]["levels"]
    assert isinstance(levels.get("targets"), list)
    assert isinstance(levels.get("orb_high"), (int, float))
    assert isinstance(levels.get("orb_low"), (int, float))

    nq = next(item for item in payload["watchlist"] if item["symbol"] == "NQ")
    assert nq["data_state"] == "Unavailable"
    assert nq["price"] is None

    archive = payload["missions"]["archive"]
    assert isinstance(archive, list) and archive
    assert "trade_triggered" in archive[0]

    replay = payload["session_replay"]
    assert isinstance(replay["keys"], list) and replay["keys"]
    current_key = replay["keys"][0]
    assert current_key in replay["snapshots_by_key"]
    assert "events" in replay["snapshots_by_key"][current_key]
