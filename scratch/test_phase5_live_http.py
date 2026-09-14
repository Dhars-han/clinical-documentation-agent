import urllib.request
import json
import sys

base_url = "http://127.0.0.1:8000"

rag_payload = json.dumps({
    "query": "Metformin renal contraindications eGFR",
    "top_k": 2,
    "score_threshold": 0.15
}).encode("utf-8")

endpoints = [
    ("GET", "/", None, None),
    ("GET", "/patients/P001", None, None),
    ("GET", "/patients/P001/notes", None, None),
    ("GET", "/patients/P001/medications", None, None),
    ("GET", "/patients/P001/allergies", None, None),
    ("GET", "/patients/P001/labs", None, None),
    ("GET", "/patients/P001/consultation", None, None),
    ("GET", "/patients/P001/evidence", None, None),
    ("GET", "/patients/P001/agent/evidence", None, None),
    ("POST", "/patients/P001/reconcile", b"", "application/json"),
    ("POST", "/rag/query", rag_payload, "application/json"),
    ("GET", "/rag/documents", None, None),
    ("GET", "/patients/P001/rag/context", None, None),
    ("POST", "/patients/P001/document", b"", "application/json"),
    ("GET", "/patients/P001/document", None, None),
    ("POST", "/patients/P999/document", b"", "application/json"),
    ("GET", "/docs", None, None),
    ("GET", "/openapi.json", None, None)
]

print("=== RUNNING PHASE 5 LIVE HTTP SERVER TESTS ===")
for method, ep, data, content_type in endpoints:
    url = base_url + ep
    headers = {"Content-Type": content_type} if content_type else {}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8")
        if ep == "/docs":
            print(f"\n{method} {ep:<34} -> Status: {status} (HTML {len(raw)} bytes)")
        elif ep == "/openapi.json":
            spec = json.loads(raw)
            print(f"\n{method} {ep:<34} -> Status: {status}")
            print(f"Documented routes ({len(spec['paths'])} total): {list(spec['paths'].keys())}")
        elif "/document" in ep and "P001" in ep:
            doc = json.loads(raw)
            print(f"\n{method} {ep:<34} -> Status: {status}")
            print(f"  Patient: {doc['patient_id']} - {doc['patient_name']} (Age: {doc['patient_age']})")
            print(f"  Human Review Needed: {doc['requires_human_review']} | Unresolved Conflicts: {doc['unresolved_conflict_count']}")
            print(f"  Medications ({len(doc['medications'])}):")
            for m in doc['medications']:
                print(f"    - {m['name']}: {m['status']} (Regimen: {m['regimen']}) | Reconciliation: {m['reconciliation_status']}")
            print(f"  Allergies ({len(doc['allergies'])}):")
            for a in doc['allergies']:
                print(f"    - {a['allergen']}: {a['status']} | Conflict: {a['conflict_details']}")
            print(f"  Labs ({len(doc['relevant_labs'])}):")
            for l in doc['relevant_labs']:
                print(f"    - {l['test_name']}: {l['value']} {l['unit']} ({l['date']})")
            print(f"  Documented Changes ({len(doc['documented_changes'])}):")
            for c in doc['documented_changes']:
                print(f"    - {c['entity']} ({c['change_type']}): {c['description']}")
            print(f"  Follow-up Actions ({len(doc['follow_up_actions'])}):")
            for act in doc['follow_up_actions']:
                print(f"    - [{act['urgency'].upper()}] {act['description']}")
            print(f"  Clinical References Linked: {len(doc['clinical_references'])}")
        elif "/document" in ep and "P999" in ep:
            doc = json.loads(raw)
            print(f"\n{method} {ep:<34} -> Status: {status} | Patient: {doc['patient_id']} (Empty clean record)")
        else:
            payload = json.loads(raw)
            preview = json.dumps(payload)[:60] + "..." if len(json.dumps(payload)) > 60 else json.dumps(payload)
            print(f"\n{method} {ep:<34} -> Status: {status} | {preview}")

print("\n=== ALL PHASE 5 LIVE HTTP TESTS COMPLETED SUCCESSFULLY ===")
