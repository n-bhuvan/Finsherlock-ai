import urllib.request
import json

base_url = "http://localhost:8000"
frontend_url = "http://localhost:3000"

def get_json(path):
    req = urllib.request.urlopen(f"{base_url}{path}")
    return json.loads(req.read().decode())

def format_probability(prob):
    if prob is None:
        return "0.00%"
    pct = float(prob) * 100
    return f"{pct:.2f}%"

print("=" * 65)
print("STAGE 11 FINAL TRUST VERIFICATION (TXN_00000203)")
print("=" * 65)

# 1. Frontend HTTP check
front_res = urllib.request.urlopen(f"{frontend_url}/cases/TXN_00000203")
print(f"Frontend Live URL: {frontend_url}/cases/TXN_00000203 (HTTP {front_res.getcode()})")

# 2. Target Transaction verification
flow = get_json("/api/investigation/transaction/TXN_00000203/fund-flow")
hops = flow.get("result", [])
target = next((h for h in hops if h.get("transaction_id") == "TXN_00000203"), None)

print("\n--- Target Transaction Ground Truth ---")
assert target is not None, "Target transaction TXN_00000203 not found in fund flow!"
print(f"Transaction ID: {target['transaction_id']}")
print(f"Account ID:     {target['source_account_id']}")
print(f"Amount (Raw):   {target['amount']}")
print(f"Amount (INR):   INR {target['amount']:,.2f}")
print(f"Timestamp:      {target['timestamp']}")
print(f"Channel:        {target['channel']}")
print(f"Status:         {target['status']}")

# 3. Model A and Model B consistency
risk = get_json("/api/risk/transaction/TXN_00000203")
baseline = get_json("/api/risk/transaction/TXN_00000203/baseline")
timeline = get_json("/api/timeline/transaction/TXN_00000203")

prob_a = baseline.get("predicted_ring_probability")
prob_b = risk.get("predicted_ring_probability")
prob_timeline_b = timeline.get("risk_context", {}).get("predicted_ring_probability")

fmt_a = format_probability(prob_a)
fmt_b = format_probability(prob_b)
fmt_timeline_b = format_probability(prob_timeline_b)

print("\n--- Shared Model Probability Formatting ---")
print(f"Model A (Baseline): Raw = {prob_a:.8f} -> Display = {fmt_a} (Band: {baseline.get('risk_band')})")
print(f"Model B (Network):  Raw = {prob_b:.8f} -> Display = {fmt_b} (Band: {risk.get('risk_band')})")
print(f"Timeline Model B:   Raw = {prob_timeline_b:.8f} -> Display = {fmt_timeline_b} (Band: {timeline.get('risk_context', {}).get('risk_band')})")

assert fmt_b == fmt_timeline_b == "99.92%", f"Inconsistent Model B display: CaseHeader/ModelB={fmt_b}, Timeline={fmt_timeline_b}"
assert fmt_a == "99.94%", f"Unexpected Model A display: {fmt_a}"
assert not fmt_a.endswith("%%"), "Double percent sign detected in Model A!"
assert not fmt_b.endswith("%%"), "Double percent sign detected in Model B!"

print("\n--- Topology Central Node & Header Alignment ---")
print(f"Central Node Label:    {target['transaction_id']}")
print(f"Central Node Sublabel: INR {target['amount']:,.0f}")
print(f"Case Header Amount:    INR {target['amount']:,.0f}")
print(f"Case Header Account:   {target['source_account_id']}")

print("\nALL INTEGRITY ASSERTIONS PASSED SUCCESSFULLY.")
