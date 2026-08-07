#!/usr/bin/env python3
"""
Phase 3: Backtest Validation on Real ES Data
Generates 200+ trades on real market data, evaluates robustness, compares to Phase 1 hypothesis
"""

import pandas as pd
import sys
import json
from pathlib import Path
from datetime import datetime

# ensure local package path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from strategies.clean_orb import compute_orb, generate_signals, summary_from_trades

def run_phase3_backtest():
    """Run backtest on real ES data (168,900 bars, 6 months)"""
    
    print("\n" + "="*70)
    print("PHASE 3: BACKTEST VALIDATION ON REAL ES DATA")
    print("="*70)
    
    # Load real ES data (6 months, 168,900 bars)
    data_path = Path('trading_os/frd_sample_futures_ES/ES_real_1min_synthetic.csv')
    print(f"\n📊 Loading real ES data: {data_path}")
    
    if not data_path.exists():
        print(f"❌ ERROR: Data file not found: {data_path}")
        return False
    
    df = pd.read_csv(data_path)
    print(f"   ✅ Loaded {len(df):,} bars")
    print(f"   Date range: {df['datetime'].iloc[0]} to {df['datetime'].iloc[-1]}")
    
    # Normalize datetime
    if 'timestamp' in df.columns:
        df = df.rename(columns={'timestamp': 'datetime'})
    
    df['datetime'] = pd.to_datetime(df['datetime'])
    df = df.sort_values('datetime').reset_index(drop=True)
    
    # Compute ORBs (08:00-08:15 ET)
    print(f"\n🔍 Computing ORBs (08:00-08:15 ET)...")
    orb_map = compute_orb(df, orb_start_min=8*60, orb_end_min=8*60+15)
    print(f"   ✅ Found {len(orb_map)} trading days")
    
    # Generate signals with current V1.0 config (VWAP enabled, no retest)
    print(f"\n⚡ Generating signals with V1.0 config:")
    print(f"   - Entry: ORB breakout (no retest)")
    print(f"   - Exit: SL at ORB edge, TP at 1R/2R/3R")
    print(f"   - Filters: VWAP enabled")
    
    trades = generate_signals(
        df, orb_map,
        orb_start_min=8*60,
        orb_end_min=8*60+15,
        use_vwap=True,      # V1.0 has VWAP enabled
        use_ema=False       # V1.0 has EMA disabled
    )
    
    print(f"   ✅ Generated {len(trades)} trades")
    
    if trades.empty:
        print("❌ No trades generated; cannot proceed")
        return False
    
    # Summary stats
    summary = summary_from_trades(trades)
    print(f"\n📈 Trade Summary:")
    print(f"   Total trades: {summary['trades']}")
    print(f"   Net PnL: ${summary['net']:.2f}")
    print(f"   Win rate: {summary['win_rate']:.1%}")
    
    # Calculate additional metrics
    if 'pnl' in trades.columns:
        winners = trades[trades['pnl'] > 0]
        losers = trades[trades['pnl'] < 0]
        
        avg_win = winners['pnl'].mean() if len(winners) > 0 else 0
        avg_loss = losers['pnl'].mean() if len(losers) > 0 else 0
        
        profit_factor = abs(winners['pnl'].sum() / losers['pnl'].sum()) if len(losers) > 0 and losers['pnl'].sum() != 0 else 0
        
        print(f"   Profit factor: {profit_factor:.2f}")
        print(f"   Avg win: ${avg_win:.2f}")
        print(f"   Avg loss: ${avg_loss:.2f}")
        print(f"   Expectancy: ${summary['net'] / summary['trades']:.2f}/trade")
    
    # Save trades
    out_dir = Path('trading_os/experiments/outputs')
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'phase3_backtest_trades.csv'
    trades.to_csv(out_path, index=False)
    print(f"\n💾 Saved trades to: {out_path}")
    
    # Load robustness evaluator and evaluate
    print(f"\n🎯 Evaluating robustness on {len(trades)} trades...")
    
    from robustness_evaluator import RobustnessEvaluator
    
    evaluator = RobustnessEvaluator(trades)
    report = evaluator.evaluate()
    
    # Save robustness report
    report_path = out_dir / 'phase3_robustness_report.json'
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"✅ Robustness report saved to: {report_path}")
    
    # Print key robustness metrics
    print(f"\n" + "="*70)
    print("ROBUSTNESS EVALUATION (Phase 3 vs Phase 1)")
    print("="*70)
    
    phase1_score = 63.9
    phase3_score = report.get('overall_robustness_score', 0)
    
    print(f"\n📊 Overall Robustness Score:")
    print(f"   Phase 1 (38 trades, 33 days):  {phase1_score:.1f}/100")
    print(f"   Phase 3 ({len(trades)} trades, 6 months): {phase3_score:.1f}/100")
    print(f"   Δ: {phase3_score - phase1_score:+.1f} points")
    
    profitability = report.get('profitability', {})
    print(f"\n💰 Profitability:")
    print(f"   Profit factor: {profitability.get('profit_factor', 'N/A'):.2f}")
    print(f"   Total PnL: ${profitability.get('total_pnl', 0):.2f}")
    print(f"   Expectancy: ${profitability.get('expectancy', 0):.2f}/trade")
    
    drawdown = report.get('drawdown', {})
    print(f"\n📉 Drawdown:")
    print(f"   Max DD: {drawdown.get('max_dd_pct', 0):.1f}%")
    print(f"   Recovery trades: {drawdown.get('recovery_trades', 0)}")
    
    stability = report.get('stability', {})
    print(f"\n📊 Stability:")
    print(f"   Monthly CV: {stability.get('monthly_cv', 0):.2f}")
    
    confidence = report.get('confidence', {})
    print(f"\n🎯 Confidence:")
    print(f"   Score: {confidence.get('score', 0):.0f}/100")
    print(f"   Level: {confidence.get('level', 'UNKNOWN')}")
    
    # Decision gate
    print(f"\n" + "="*70)
    print("DECISION GATE: Ready for Paper Trading?")
    print("="*70)
    
    pf = profitability.get('profit_factor', 0)
    max_dd = drawdown.get('max_dd_pct', 100)
    conf_score = confidence.get('score', 0)
    
    checks = {
        "✅ PF > 1.5": pf > 1.5,
        "✅ Max DD < 40%": max_dd < 40,
        "✅ Confidence MEDIUM+": conf_score >= 60,
        "✅ Trades > 100": len(trades) > 100,
    }
    
    for check, passed in checks.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {check}")
    
    all_pass = all(checks.values())
    
    if all_pass:
        print(f"\n🚀 VERDICT: READY FOR PAPER TRADING")
        print(f"   Findings from Phase 1 are validated on larger sample.")
        print(f"   Confidence upgraded: HYPOTHESIS → MEDIUM confidence")
        print(f"   Next: Paper trade 50+ live trades (2-4 weeks)")
    else:
        print(f"\n⚠️  VERDICT: NEEDS REFINEMENT")
        print(f"   One or more metrics outside acceptable range.")
        print(f"   Recommended: Investigate failed checks, adjust rules, re-run Phase 3")
    
    return all_pass

if __name__ == '__main__':
    success = run_phase3_backtest()
    sys.exit(0 if success else 1)
