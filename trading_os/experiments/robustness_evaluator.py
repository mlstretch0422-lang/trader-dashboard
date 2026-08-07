#!/usr/bin/env python3
"""
Robustness Evaluation Framework

Evaluates trading systems by:
1. Profit Factor (but not profit alone)
2. Drawdown (recovery ability)
3. Expectancy (per-trade consistency)
4. Stability (month-to-month variance)
5. Simplicity (fewer rules = more robust)
6. Trade frequency (higher = more data, but riskier)
7. Win rate (psychological tolerance)
8. Confidence score (sample size, data coverage)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import json

sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'strat' / 'src'))
from strat.metrics import compute_metrics


class RobustnessEvaluator:
    """Evaluate trading system robustness across multiple dimensions."""
    
    def __init__(self, trades_df: pd.DataFrame):
        """
        Args:
            trades_df: DataFrame with columns: entry_time, exit_time, realized_pnl_usd, qty, etc.
        """
        self.trades = trades_df.copy()
        self.trades['entry_time'] = pd.to_datetime(self.trades['entry_time'])
        self.trades['exit_time'] = pd.to_datetime(self.trades['exit_time'])
        self.trades['pnl'] = pd.to_numeric(self.trades['realized_pnl_usd'], errors='coerce')
    
    def compute_drawdown(self) -> Tuple[float, float, float]:
        """Compute max drawdown and recovery time.
        
        Returns:
            (max_dd_pct, max_dd_dollars, time_to_recovery_days)
        """
        cumpl = self.trades['pnl'].cumsum()
        running_max = cumpl.expanding().max()
        drawdown = cumpl - running_max
        max_dd_dollars = drawdown.min()
        max_dd_pct = (max_dd_dollars / running_max.max()) * 100 if running_max.max() > 0 else 0
        
        # Recovery time (simplified)
        if len(drawdown[drawdown == drawdown.min()]) > 0:
            dd_idx = drawdown.idxmin()
            recovery_trades = (drawdown[dd_idx:] >= 0).sum()
        else:
            recovery_trades = 0
        
        return abs(max_dd_pct), abs(max_dd_dollars), recovery_trades
    
    def compute_stability(self) -> Dict[str, float]:
        """Measure month-to-month consistency.
        
        Returns:
            Dict with monthly metrics and variance scores.
        """
        self.trades['month'] = self.trades['entry_time'].dt.to_period('M')
        monthly = self.trades.groupby('month')['pnl'].agg(['sum', 'count', 'mean'])
        
        if len(monthly) < 2:
            return {'variance': 0, 'months': len(monthly)}
        
        monthly_returns = monthly['sum'].values
        monthly_variance = np.var(monthly_returns)
        monthly_cv = np.std(monthly_returns) / (np.mean(monthly_returns) + 1e-6)
        
        return {
            'monthly_variance': float(monthly_variance),
            'monthly_cv': float(monthly_cv),  # Coefficient of variation
            'months': int(len(monthly)),
            'best_month': float(monthly['sum'].max()),
            'worst_month': float(monthly['sum'].min()),
            'avg_month': float(monthly['sum'].mean()),
        }
    
    def compute_confidence_score(self) -> Dict[str, float]:
        """Score confidence in results based on sample size and data coverage.
        
        Returns:
            Confidence score 0–100 with breakdown.
        """
        n_trades = len(self.trades)
        date_range_days = (self.trades['entry_time'].max() - self.trades['entry_time'].min()).days
        days_with_trades = self.trades['entry_time'].dt.date.nunique()
        
        # Scoring:
        # N >= 100 = 50 pts (statistically significant)
        # N >= 200 = 100 pts
        sample_score = min(100, (n_trades / 200) * 100)
        
        # Date coverage >= 180 days = 50 pts
        date_score = min(50, (date_range_days / 180) * 50)
        
        # Trade frequency >= 5 trades/week = 50 pts
        trades_per_week = (n_trades / (date_range_days + 1)) * 7
        freq_score = min(50, (trades_per_week / 5) * 50)
        
        total = sample_score + date_score + freq_score
        
        return {
            'confidence_score': float(min(100, total)),
            'sample_size': int(n_trades),
            'date_range_days': int(date_range_days),
            'days_with_trades': int(days_with_trades),
            'trades_per_week': float(trades_per_week),
            'notes': self._confidence_level(total),
        }
    
    def _confidence_level(self, score: float) -> str:
        if score >= 80:
            return "HIGH — Robust findings supported by substantial data"
        elif score >= 50:
            return "MEDIUM — Findings warrant attention but need larger sample"
        else:
            return "LOW — Preliminary observation only; high variance expected"
    
    def evaluate(self) -> Dict:
        """Comprehensive robustness evaluation.
        
        Returns:
            Dict with all metrics and confidence levels.
        """
        # Base metrics
        basic = compute_metrics(self.trades)
        
        # Robustness metrics
        dd_pct, dd_usd, recovery = self.compute_drawdown()
        stability = self.compute_stability()
        confidence = self.compute_confidence_score()
        
        # Simplicity score (count filters/conditions)
        # Lower = simpler = more robust
        simplicity_score = self._estimate_simplicity()
        
        # Win rate
        wins = (self.trades['pnl'] > 0).sum()
        win_rate = wins / len(self.trades) if len(self.trades) > 0 else 0
        
        # Trade frequency
        days = (self.trades['entry_time'].max() - self.trades['entry_time'].min()).days + 1
        trades_per_day = len(self.trades) / days if days > 0 else 0
        
        # Overall robustness score (0-100)
        robustness_score = self._compute_overall_score(
            basic, dd_pct, stability, confidence, simplicity_score, win_rate
        )
        
        return {
            'profitability': {
                'total_pnl': float(basic.get('total_pnl', 0)),
                'profit_factor': float(basic.get('profit_factor', 0)),
                'expectancy': float(basic.get('expectancy', 0)),
                'win_rate': float(win_rate),
                'avg_win': float(basic.get('avg_win', 0)),
                'avg_loss': float(basic.get('avg_loss', 0)),
            },
            'drawdown': {
                'max_drawdown_pct': float(dd_pct),
                'max_drawdown_usd': float(dd_usd),
                'recovery_trades': int(recovery),
            },
            'stability': stability,
            'confidence': confidence,
            'simplicity': {
                'score': simplicity_score,
                'note': 'Lower is simpler/more robust (1=minimal rules, 10=complex)',
            },
            'execution': {
                'trades_per_day': float(trades_per_day),
                'total_trades': int(len(self.trades)),
                'trades_per_week': float(confidence['trades_per_week']),
            },
            'overall_robustness_score': robustness_score,
            'assessment': self._robustness_assessment(robustness_score),
        }
    
    def _estimate_simplicity(self) -> float:
        """Estimate simplicity (lower = simpler).
        
        This is a heuristic based on the strategy structure.
        Baseline = 1 (ORB only) to 10 (complex multi-filter).
        """
        # If we added filter columns, count them
        filter_count = 0
        for col in self.trades.columns:
            if 'filter' in col.lower() or 'vwap' in col.lower() or 'ema' in col.lower():
                filter_count += 1
        
        # Base score: 1 (core ORB)
        # +1 per major filter
        # +0.5 per minor parameter
        simplicity = 1.0 + (filter_count * 1.0)
        return min(10.0, simplicity)
    
    def _compute_overall_score(self, basic: Dict, dd_pct: float, 
                              stability: Dict, confidence: Dict, 
                              simplicity: float, win_rate: float) -> float:
        """Compute overall robustness score (0-100).
        
        Weights:
        - Profit Factor: 20%
        - Drawdown: 25% (lower is better)
        - Stability: 20% (consistency)
        - Confidence: 20%
        - Simplicity: 10%
        - Win rate: 5%
        """
        
        # Profit Factor score (max 100 at PF >= 2.0)
        pf = basic.get('profit_factor', 0)
        pf_score = min(100, (pf / 2.0) * 100) if pf > 0 else 0
        
        # Drawdown score (100 at 0%, 0 at 50%+ DD)
        dd_score = max(0, 100 - (dd_pct * 2))  # 50% DD = 0 score
        
        # Stability score (100 at CV < 0.5, 0 at CV > 2.0)
        cv = stability.get('monthly_cv', 0)
        stability_score = max(0, 100 - (cv * 50))
        
        # Confidence score (already 0-100)
        conf_score = confidence.get('confidence_score', 0)
        
        # Simplicity score (100 at 1, 0 at 10)
        simp_score = max(0, 100 - (simplicity * 11))
        
        # Win rate score (50 at 30%, 100 at 50%+)
        wr_score = min(100, max(0, (win_rate - 0.25) / 0.25 * 100))
        
        # Weighted average
        overall = (
            pf_score * 0.20 +
            dd_score * 0.25 +
            stability_score * 0.20 +
            conf_score * 0.20 +
            simp_score * 0.10 +
            wr_score * 0.05
        )
        
        return float(overall)
    
    def _robustness_assessment(self, score: float) -> str:
        if score >= 75:
            return "HIGHLY ROBUST — Production-ready"
        elif score >= 60:
            return "ROBUST — Good for forward testing"
        elif score >= 45:
            return "ACCEPTABLE — Needs refinement"
        elif score >= 30:
            return "WEAK — Risky for real trading"
        else:
            return "UNRELIABLE — Do not trade"


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate system robustness')
    parser.add_argument('--trades', type=Path, required=True, help='Trades CSV')
    parser.add_argument('--output', type=Path, default=Path('outputs/robustness.json'))
    
    args = parser.parse_args()
    
    trades = pd.read_csv(args.trades)
    evaluator = RobustnessEvaluator(trades)
    results = evaluator.evaluate()
    
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2))
    
    print("Robustness Evaluation Results:")
    print(f"Overall Score: {results['overall_robustness_score']:.1f}/100")
    print(f"Assessment: {results['assessment']}")
    print(f"\nKey Metrics:")
    print(f"  Profit Factor: {results['profitability']['profit_factor']:.2f}")
    print(f"  Max Drawdown: {results['drawdown']['max_drawdown_pct']:.1f}%")
    print(f"  Expectancy: ${results['profitability']['expectancy']:.2f}/trade")
    print(f"  Win Rate: {results['profitability']['win_rate']*100:.1f}%")
    print(f"  Confidence: {results['confidence']['notes']}")
