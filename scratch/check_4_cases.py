import urllib.request
import json

cases = ['TXN_00000646', 'TXN_00000679', 'TXN_00000001', 'TXN_00000500']

for tx in cases:
    print(f"\n--- Checking {tx} ---")
    try:
        url_flow = f"http://localhost:8000/api/investigation/transaction/{tx}/fund-flow"
        req = urllib.request.urlopen(url_flow)
        flow_data = json.loads(req.read())
        print(f"Fund flow result: {flow_data.get('result')}")
    except Exception as e:
        print(f"Fund flow error: {e}")

    try:
        url_risk = f"http://localhost:8000/api/risk/transaction/{tx}"
        req = urllib.request.urlopen(url_risk)
        risk_data = json.loads(req.read())
        print(f"Risk prob: {risk_data.get('predicted_ring_probability')}, band: {risk_data.get('risk_band')}")
    except Exception as e:
        print(f"Risk error: {e}")
