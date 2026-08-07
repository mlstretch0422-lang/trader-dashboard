# Trader Dashboard Strategy Project

A lightweight Python project scaffold for analyzing paper trading order history and journal data.

## What’s included

- `src/strat/` — core data loading and performance summary modules
- `data/` — place your CSV trading data files here
- `notebooks/` — exploratory notebook starter
- `.vscode/` — editor settings and run task

## Setup

1. Create and activate a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy your CSV files into `data/`.

## Run

Load all CSVs and print a summary:

```bash
python -m strat.main
```

Load and analyze paper trading order history exports:

```bash
PYTHONPATH=src python -m strat.main --paper-trading
```

If your paper trading exports are stored elsewhere, pass the directory explicitly:

```bash
PYTHONPATH=src python -m strat.main --paper-trading --paper-trading-dir "Trade Stratagey"
```

## Next steps

- add custom strategy metrics in `src/strat/metrics.py`
- extend the notebook in `notebooks/strategy-exploration.ipynb`
- plug in order-level performance from your paper trading exports
