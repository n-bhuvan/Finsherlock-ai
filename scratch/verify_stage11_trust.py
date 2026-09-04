import urllib.request
import json

base_url = "http://localhost:8000"

def get_json(path):
    req = urllib.request.urlopen(f"{base_url}{path}")
    return json.loads(req.read().decode())

print("=" * 60)
print("VERIFYING LIVE API GROUND TRUTH FOR TXN_00000203")
print("=" * 60)

# 1. Fund flow
flow = get_json("/api/investigation/transaction/TXN_00000203/fund-flow")
hops = flow.get("result", [])
target = next((h for h in hops if h.get("transaction_id") == "TXN_00000203"), None)
adjacent = next((h for h in hops if h.get("transaction_id") == "TXN_00000202"), None)

print("\n--- Target Transaction (TXN_00000203) ---")
if target:
    print(f"Transaction ID: {target['transaction_id']}")
    print(f"Account ID:     {target['source_account_id']}")
    print(f"Amount:         INR {target['amount']:,.2f}")
    print(f"Timestamp:      {target['timestamp']}")
    print(f"Channel:        {target['channel']}")
    print(f"Status:         {target['status']}")
else:
    print("ERROR: Target transaction not found in fund flow!")

print("\n--- Adjacent Transaction (TXN_00000202) ---")
if adjacent:
    print(f"Transaction ID: {adjacent['transaction_id']}")
    print(f"Amount:         INR {adjacent['amount']:,.2f} (PROVING DISTINCT FROM 203)")
    print(f"Timestamp:      {adjacent['timestamp']}")

# 2. Risk Predictions
risk = get_json("/api/risk/transaction/TXN_00000203")
baseline = get_json("/api/risk/transaction/TXN_00000203/baseline")

p_model_b = risk.get("predicted_ring_probability")
p_model_a = baseline.get("predicted_ring_probability")

print("\n--- Model Predictions & Precision ---")
print(f"Model A (Baseline): Raw = {p_model_a:.8f} -> Formatted = {p_model_a*100:.2f}% (Risk Band: {baseline.get('risk_band')})")
print(f"Model B (Network):  Raw = {p_model_b:.8f} -> Formatted = {p_model_b*100:.2f}% (Risk Band: {risk.get('risk_band')})")

print("\n=" * 60)
print("VERIFYING OTHER CURATED CASES")
print("=" * 60)

for tx in ["TXN_00000001", "TXN_00000646", "TXN_00000679", "TXN_00000500"]:
    flow_tx = get_json(f"/api/investigation/transaction/{tx}/fund-flow")
    hops_tx = flow_tx.get("result", [])
    t_match = next((h for h in hops_tx if h.get("transaction_id") == tx), None)
    r_tx = get_json(f"/api/risk/transaction/{tx}")
    p_b = r_tx.get("predicted_ring_probability")
    
    acc = t_match["source_account_id"] if t_match else "N/A"
    amt = f"INR {t_match['amount']:,.2f}" if t_match else "N/A"
    print(f"{tx}: Account={acc}, Amount={amt}, Model B={p_b*100:.2f}%, Band={r_tx.get('risk_band')}")

print("\nALL VERIFICATIONS COMPLETE.")
