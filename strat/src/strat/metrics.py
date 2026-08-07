import pandas as pd

from strat.io import normalize_order_history


def describe_dataframe(df: pd.DataFrame) -> str:
    lines = ["Data summary:"]
    lines.append(f"rows={len(df)}")
    lines.append(f"columns={len(df.columns)}")
    lines.append("\nColumn types:")
    lines.extend([f"- {name}: {dtype}" for name, dtype in df.dtypes.items()])
    return "\n".join(lines)


def basic_trade_report(df: pd.DataFrame) -> pd.DataFrame:
    if "side" in df.columns and "price" in df.columns:
        summary = df.groupby("side")["price"].agg(["count", "mean", "min", "max"])
    else:
        summary = pd.DataFrame({"message": ["No 'side' and 'price' columns found"]})
    return summary


def _symbol_contract_multiplier(symbol: str) -> int:
    if "MES1!" in symbol:
        return 5
    if "ES1!" in symbol:
        return 50
    return 1


def reconstruct_trades_from_order_history(df: pd.DataFrame) -> pd.DataFrame:
    data = normalize_order_history(df)
    filled = data[data["status"].astype(str).str.lower() == "filled"].copy()
    if filled.empty:
        return pd.DataFrame()

    filled = filled.sort_values(["symbol", "closing_time", "placing_time", "order_id"], na_position="last")
    trades: list[dict] = []
    open_positions: dict[str, list[dict]] = {}

    def close_existing_position(symbol: str, qty_to_close: int, exit_row: pd.Series) -> None:
        nonlocal trades
        open_list = open_positions.setdefault(symbol, [])
        while qty_to_close > 0 and open_list:
            open_pos = open_list[0]
            matched_qty = min(qty_to_close, open_pos["qty"])
            direction = "Long" if open_pos["side"] == "Buy" else "Short"
            entry_price = open_pos["entry_price"]
            exit_price = exit_row["fill_price"]
            multiplier = _symbol_contract_multiplier(symbol)
            if direction == "Long":
                pl_points = (exit_price - entry_price) * matched_qty
            else:
                pl_points = (entry_price - exit_price) * matched_qty
            trades.append(
                {
                    "symbol": symbol,
                    "direction": direction,
                    "qty": matched_qty,
                    "entry_time": open_pos["entry_time"],
                    "exit_time": exit_row.get("closing_time"),
                    "entry_price": entry_price,
                    "exit_price": exit_price,
                    "realized_pnl_points": pl_points,
                    "realized_pnl_usd": pl_points * multiplier,
                    "contract_multiplier": multiplier,
                    "entry_order_id": open_pos["entry_order_id"],
                    "exit_order_id": exit_row.get("order_id"),
                    "entry_type": open_pos["entry_type"],
                    "exit_type": exit_row.get("order_type"),
                    "entry_level_id": open_pos["entry_level_id"],
                    "exit_level_id": exit_row.get("level_id"),
                    "entry_source_file": open_pos["entry_source_file"],
                    "exit_source_file": exit_row.get("source_file"),
                }
            )
            open_pos["qty"] -= matched_qty
            qty_to_close -= matched_qty
            if open_pos["qty"] == 0:
                open_list.pop(0)

        return

    for _, row in filled.iterrows():
        symbol = row["symbol"]
        side = row["side"]
        qty = int(row["qty"])
        if qty <= 0 or pd.isna(row["fill_price"]):
            continue

        current_positions = open_positions.setdefault(symbol, [])
        net_qty = sum(pos["qty"] if pos["side"] == "Buy" else -pos["qty"] for pos in current_positions)

        if side == "Buy":
            if net_qty < 0:
                close_qty = min(qty, -net_qty)
                close_existing_position(symbol, close_qty, row)
                remaining_qty = qty - close_qty
                if remaining_qty > 0:
                    current_positions.append(
                        {
                            "side": side,
                            "qty": remaining_qty,
                            "entry_price": row["fill_price"],
                            "entry_time": row.get("closing_time"),
                            "entry_order_id": row.get("order_id"),
                            "entry_type": row.get("order_type"),
                            "entry_level_id": row.get("level_id"),
                            "entry_source_file": row.get("source_file"),
                        }
                    )
            else:
                current_positions.append(
                    {
                        "side": side,
                        "qty": qty,
                        "entry_price": row["fill_price"],
                        "entry_time": row.get("closing_time"),
                        "entry_order_id": row.get("order_id"),
                        "entry_type": row.get("order_type"),
                        "entry_level_id": row.get("level_id"),
                        "entry_source_file": row.get("source_file"),
                    }
                )
        elif side == "Sell":
            if net_qty > 0:
                close_qty = min(qty, net_qty)
                close_existing_position(symbol, close_qty, row)
                remaining_qty = qty - close_qty
                if remaining_qty > 0:
                    current_positions.append(
                        {
                            "side": side,
                            "qty": remaining_qty,
                            "entry_price": row["fill_price"],
                            "entry_time": row.get("closing_time"),
                            "entry_order_id": row.get("order_id"),
                            "entry_type": row.get("order_type"),
                            "entry_level_id": row.get("level_id"),
                            "entry_source_file": row.get("source_file"),
                        }
                    )
            else:
                current_positions.append(
                    {
                        "side": side,
                        "qty": qty,
                        "entry_price": row["fill_price"],
                        "entry_time": row.get("closing_time"),
                        "entry_order_id": row.get("order_id"),
                        "entry_type": row.get("order_type"),
                        "entry_level_id": row.get("level_id"),
                        "entry_source_file": row.get("source_file"),
                    }
                )

    for symbol, open_list in open_positions.items():
        for open_pos in open_list:
            trades.append(
                {
                    "symbol": symbol,
                    "direction": "Long" if open_pos["side"] == "Buy" else "Short",
                    "qty": open_pos["qty"],
                    "entry_time": open_pos["entry_time"],
                    "exit_time": pd.NaT,
                    "entry_price": open_pos["entry_price"],
                    "exit_price": pd.NA,
                    "realized_pnl_points": pd.NA,
                    "realized_pnl_usd": pd.NA,
                    "contract_multiplier": _symbol_contract_multiplier(symbol),
                    "entry_order_id": open_pos["entry_order_id"],
                    "exit_order_id": pd.NA,
                    "entry_type": open_pos["entry_type"],
                    "exit_type": pd.NA,
                    "entry_level_id": open_pos["entry_level_id"],
                    "exit_level_id": pd.NA,
                    "entry_source_file": open_pos["entry_source_file"],
                    "exit_source_file": pd.NA,
                }
            )

    return pd.DataFrame(trades)


def summarize_trade_dataset(df: pd.DataFrame) -> str:
    if df.empty:
        return "No reconstructed trades found."

    closed = df[df["exit_price"].notna()].copy()
    total_trades = len(closed)
    if total_trades == 0:
        return "No closed trades available in reconstructed dataset."

    total_pnl = closed["realized_pnl_usd"].sum()
    wins = closed[closed["realized_pnl_usd"] > 0]
    losses = closed[closed["realized_pnl_usd"] <= 0]
    win_rate = len(wins) / total_trades * 100
    avg_pnl = closed["realized_pnl_usd"].mean()
    avg_win = wins["realized_pnl_usd"].mean() if not wins.empty else 0
    avg_loss = losses["realized_pnl_usd"].mean() if not losses.empty else 0

    lines = [
        f"Reconstructed trades: {total_trades}",
        f"Total P&L (USD): {total_pnl:.2f}",
        f"Win rate: {win_rate:.1f}%",
        f"Avg P&L per trade: {avg_pnl:.2f}",
        f"Avg win: {avg_win:.2f}",
        f"Avg loss: {avg_loss:.2f}",
    ]
    return "\n".join(lines)


def compute_metrics(df: pd.DataFrame) -> dict:
    """Compute basic performance metrics from a reconstructed trades DataFrame.

    Expects `realized_pnl_usd` and `exit_price` columns. Returns a dict
    compatible with the A/B harness consumer.
    """
    closed = df[df["exit_price"].notna()].copy()
    if closed.empty:
        return {"total_trades": 0}
    total_trades = len(closed)
    pnl = closed["realized_pnl_usd"].astype(float)
    gross_win = pnl[pnl > 0].sum()
    gross_loss = -pnl[pnl <= 0].sum()
    profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf")
    expectancy = pnl.mean()
    win_rate = (pnl > 0).sum() / total_trades
    return {
        "total_trades": int(total_trades),
        "total_pnl": float(pnl.sum()),
        "profit_factor": float(profit_factor),
        "expectancy": float(expectancy),
        "win_rate": float(win_rate),
        "avg_win": float(pnl[pnl > 0].mean()) if (pnl > 0).any() else 0.0,
        "avg_loss": float(pnl[pnl <= 0].mean()) if (pnl <= 0).any() else 0.0,
    }
