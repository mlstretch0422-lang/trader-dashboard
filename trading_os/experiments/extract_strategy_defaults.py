import re
import json
from pathlib import Path

p = Path('ES_ORB_Strategy_v1_1_FIXED.txt')
if not p.exists():
    p = Path('strat/ES_ORB_Strategy_v1_1_FIXED.txt')
if not p.exists():
    p = Path('ES_ORB_Strategy_v1.0.txt')

text = p.read_text()
params = {}

m = re.search(r'i_orbStart\s*=\s*input.string\("(\d{4})"', text)
if m: params['orb_start'] = m.group(1)
m = re.search(r'i_orbEnd\s*=\s*input.string\("(\d{4})"', text)
if m: params['orb_end'] = m.group(1)
m = re.search(r'i_retestMode\s*=\s*input.string\("(\w+)"', text)
if m: params['retest_mode'] = m.group(1)
m = re.search(r'i_useVWAP\s*=\s*input.bool\((true|false)', text, re.IGNORECASE)
if m: params['use_vwap'] = m.group(1).lower()=='true'
m = re.search(r'i_useEMA\s*=\s*input.bool\((true|false)', text, re.IGNORECASE)
if m: params['use_ema'] = m.group(1).lower()=='true'
m = re.search(r'i_emaLen\s*=\s*input.int\((\d+)', text)
if m: params['ema_len'] = int(m.group(1))
m = re.search(r'i_atrLen\s*=\s*input.int\((\d+)', text)
if m: params['atr_len'] = int(m.group(1))

out = Path('trading_os/experiments/outputs/strategy_defaults.json')
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(params, indent=2))
print('Wrote defaults to', out)
print(params)
