# Local dashboard option

A lightweight local dashboard is now scaffolded at:

- [trading_os/src/integrations/streamlit_app.py](src/integrations/streamlit_app.py)

## How to run it later
Once Streamlit is available in your environment, run:

```bash
streamlit run src/integrations/streamlit_app.py
```

## What it does
- loads local OHLC data
- runs the ORB strategy logic
- shows a regime summary and strategy metrics in a browser UI
