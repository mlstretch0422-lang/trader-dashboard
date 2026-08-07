import argparse
from pathlib import Path

from strat.io import load_data, load_paper_trading_order_history
from strat.metrics import (
    basic_trade_report,
    compute_metrics,
    describe_dataframe,
    reconstruct_trades_from_order_history,
    summarize_trade_dataset,
)
from strat.tag_trades import tag_trades


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Trader Dashboard strategy analysis tools"
    )
    parser.add_argument(
        "--paper-trading",
        action="store_true",
        help="Load and analyze paper trading order history exports",
    )
    root_dir = Path(__file__).resolve().parents[2]
    parser.add_argument(
        "--paper-trading-dir",
        type=Path,
        default=root_dir / "Trade Stratagey",
        help="Directory containing paper trading order history CSV exports",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=root_dir / "data",
        help="Directory containing generic CSV data files",
    )
    parser.add_argument(
        "--export-tagged",
        action="store_true",
        help="Export reconstructed trades with heuristic tags",
    )
    parser.add_argument(
        "--tagged-out",
        type=Path,
        default=root_dir / "data" / "reconstructed_trades_tagged.csv",
        help="Output path for tagged reconstructed trade export",
    )
    parser.add_argument(
        "--group-by",
        type=str,
        default=None,
        help="Optional column name to group metrics by after export",
    )
    args = parser.parse_args()

    if args.paper_trading:
        data_dir = args.paper_trading_dir.expanduser().resolve()
        print(f"Loading paper trading exports from: {data_dir}")
        df = load_paper_trading_order_history(data_dir)
        print(describe_dataframe(df))
        trades = reconstruct_trades_from_order_history(df)
        print("\nPaper trading reconstructed trade summary:")
        print(summarize_trade_dataset(trades))

        if args.export_tagged:
            tagged_output = args.tagged_out.expanduser().resolve()
            tagged = tag_trades(trades, tagged_output)
            print(f"\nTagged trades exported to: {tagged_output}")
            print(f"Rows written: {len(tagged)}")
            if args.group_by and args.group_by in tagged.columns:
                print(f"\nMetrics by {args.group_by}:")
                for name, group in tagged.groupby(args.group_by):
                    m = compute_metrics(group)
                    print(
                        f"  {args.group_by}={name}: trades={m['total_trades']} pf={m['profit_factor']:.3f} "
                        f"exp={m['expectancy']:.2f} win={m['win_rate']*100:.1f}%"
                    )
            else:
                print("\nOverall metrics:")
                m = compute_metrics(tagged)
                print(
                    f"  trades={m['total_trades']} pf={m['profit_factor']:.3f} exp={m['expectancy']:.2f} "
                    f"win={m['win_rate']*100:.1f}%"
                )
    else:
        data_dir = args.data_dir.expanduser().resolve()
        print(f"Loading CSVs from: {data_dir}")
        df = load_data(data_dir)
        print(describe_dataframe(df))
        print("\nBasic trade report:")
        print(basic_trade_report(df))


if __name__ == "__main__":
    main()
