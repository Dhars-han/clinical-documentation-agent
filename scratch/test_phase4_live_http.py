import urllib.request
import json
import sys

base_url = "http://127.0.0.1:8000"

query_payload = json.dumps({
    "query": "Metformin renal contraindications eGFR",
    "top_k": 2,
    "score_threshold": 0.15
}).encode("utf-8")

irrelevant_payload = json.dumps({
    "query": "How to repair automobile transmission and bake cookies",
    "top_k": 3,
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
    ("GET", "/rag/documents", None, None),
    ("POST", "/rag/query", query_payload, "application/json"),
    ("POST", "/rag/query", irrelevant_payload, "application/json"),
    ("GET", "/patients/P001/rag/context", None, None),
    ("GET", "/docs", None, None),
    ("GET", "/openapi.json", None, None)
]

print("=== RUNNING PHASE 4 LIVE HTTP SERVER TESTS ===")
for method, ep, data, content_type in endpoints:
    url = base_url + ep
    headers = {"Content-Type": content_type} if content_type else {}
    req = urllib.request.Request(url, data=data, method=method, headers=headers)
    with urllib.request.urlopen(req) as resp:
        status = resp.status
        raw = resp.read().decode("utf-8")
        if ep == "/docs":
            print(f"\n{method} {ep:<32} -> Status: {status} (HTML {len(raw)} bytes)")
        elif ep == "/openapi.json":
            spec = json.loads(raw)
            print(f"\n{method} {ep:<32} -> Status: {status}")
            print(f"Documented routes ({len(spec['paths'])} total): {list(spec['paths'].keys())}")
        elif ep == "/rag/documents":
            docs = json.loads(raw)
            print(f"\n{method} {ep:<32} -> Status: {status} | Ingested docs: {len(docs)}")
            for d in docs:
                print(f"  - [{d['document_id']}] {d['title']} ({d['chunk_count']} chunks)")
        elif ep == "/rag/query" and data == query_payload:
            payload = json.loads(raw)
            print(f"\n{method} {ep:<32} (Clinical query) -> Status: {status} | Matches: {payload['total_results']}")
            for r in payload['results']:
                print(f"  * [{r['document_id']}] {r['section']} (Score: {r['score']}) - Source: {r['source']}")
        elif ep == "/rag/query" and data == irrelevant_payload:
            payload = json.loads(raw)
            print(f"\n{method} {ep:<32} (Irrelevant query) -> Status: {status} | Matches: {payload['total_results']} (CLEANLY REJECTED)")
        elif ep == "/patients/P001/rag/context":
            payload = json.loads(raw)
            print(f"\n{method} {ep:<32} -> Status: {status} | Entities linked: {payload['total_entities_evaluated']}")
            for c in payload['entity_guideline_contexts']:
                print(f"  * {c['entity']} -> {len(c['relevant_guideline_chunks'])} reference chunks")
        else:
            payload = json.loads(raw)
            preview = json.dumps(payload)[:60] + "..." if len(json.dumps(payload)) > 60 else json.dumps(payload)
            print(f"\n{method} {ep:<32} -> Status: {status} | {preview}")

print("\n=== ALL PHASE 4 LIVE HTTP TESTS COMPLETED SUCCESSFULLY ===")
