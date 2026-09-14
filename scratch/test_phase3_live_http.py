import urllib.request
import json
import sys

base_url = "http://127.0.0.1:8000"

endpoints = [
    ("GET", "/", None),
    ("GET", "/patients/P001", None),
    ("GET", "/patients/P001/notes", None),
    ("GET", "/patients/P001/medications", None),
    ("GET", "/patients/P001/allergies", None),
    ("GET", "/patients/P001/labs", None),
    ("GET", "/patients/P001/consultation", None),
    ("GET", "/patients/P001/evidence", None),
    ("GET", "/patients/P001/agent/evidence", None),
    ("POST", "/patients/P001/agent/gather-evidence", b""),
    ("POST", "/patients/P001/reconcile", b""),
    ("GET", "/patients/P001/reconcile", None),
    ("POST", "/patients/P999/reconcile", b""),
    ("GET", "/docs", None),
    ("GET", "/openapi.json", None)
]

print("=== RUNNING PHASE 3 LIVE HTTP SERVER TESTS ===")
for method, ep, data in endpoints:
    url = base_url + ep
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8")
        if ep == "/docs":
            print(f"\n{method} {ep:<36} -> Status: {status} (HTML {len(raw)} bytes)")
        elif ep == "/openapi.json":
            spec = json.loads(raw)
            print(f"\n{method} {ep:<36} -> Status: {status}")
            print(f"Documented routes ({len(spec['paths'])} total): {list(spec['paths'].keys())}")
        elif "/reconcile" in ep and "P001" in ep:
            payload = json.loads(raw)
            print(f"\n{method} {ep:<36} -> Status: {status}")
            print(f"  Patient ID: {payload['patient_id']}")
            print(f"  Total Entities: {payload['total_entities']}")
            print(f"  Human Review Needed: {payload['requires_human_review_count']}")
            for item in payload['results']:
                hr = " [REVIEW]" if item['requires_human_review'] else ""
                print(f"    * {item['entity']} ({item['category']}): {item['status']} | state: {item['current_state']}{hr}")
        else:
            payload = json.loads(raw)
            preview = json.dumps(payload)[:65] + "..." if len(json.dumps(payload)) > 65 else json.dumps(payload)
            print(f"\n{method} {ep:<36} -> Status: {status} | {preview}")

print("\n=== ALL PHASE 3 LIVE HTTP TESTS COMPLETED SUCCESSFULLY ===")
