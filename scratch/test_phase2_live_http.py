import urllib.request
import json
import time
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
    ("GET", "/patients/P999/agent/evidence", None),
    ("GET", "/docs", None),
    ("GET", "/openapi.json", None)
]

print("=== RUNNING PHASE 2 LIVE HTTP SERVER TESTS ===")
for method, ep, data in endpoints:
    url = base_url + ep
    req = urllib.request.Request(url, data=data, method=method)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8")
        if ep == "/docs":
            print(f"\n{method} {ep:<38} -> Status: {status} (HTML {len(raw)} bytes)")
        elif ep == "/openapi.json":
            spec = json.loads(raw)
            print(f"\n{method} {ep:<38} -> Status: {status}")
            print(f"Documented routes ({len(spec['paths'])} total): {list(spec['paths'].keys())}")
        elif ep == "/patients/P001/agent/evidence":
            payload = json.loads(raw)
            print(f"\n{method} {ep:<38} -> Status: {status}")
            print(f"  Patient: {payload['patient_id']} - {payload['patient_name']}")
            print(f"  Total items: {payload['summary']['total_evidence_items']}")
            print(f"  Domains tracked: {list(payload['domain_evidence_map'].keys())}")
        else:
            payload = json.loads(raw)
            preview = json.dumps(payload)[:70] + "..." if len(json.dumps(payload)) > 70 else json.dumps(payload)
            print(f"\n{method} {ep:<38} -> Status: {status} | {preview}")

print("\n=== ALL LIVE HTTP TESTS COMPLETED SUCCESSFULLY ===")
