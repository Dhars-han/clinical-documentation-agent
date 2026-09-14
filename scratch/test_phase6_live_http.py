import subprocess
import time
import urllib.request
import json
import sys
import os

port = 8008
base_url = f"http://127.0.0.1:{port}"

print(f"Starting uvicorn server on port {port}...")
server_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--port", str(port)],
    cwd=os.path.abspath("backend"),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to start
time.sleep(2)

try:
    endpoints = [
        ("GET", "/", None, None),
        ("POST", "/patients/P001/validate", b"", "application/json"),
        ("GET", "/patients/P001/validate", None, None),
        ("POST", "/patients/P001/run-agent", b"", "application/json"),
        ("GET", "/openapi.json", None, None)
    ]

    print("\n=== RUNNING PHASE 6 LIVE HTTP SERVER TESTS ===")
    for method, ep, data, content_type in endpoints:
        url = base_url + ep
        headers = {"Content-Type": content_type} if content_type else {}
        req = urllib.request.Request(url, data=data, method=method, headers=headers)
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            raw = resp.read().decode("utf-8")
            if ep == "/openapi.json":
                spec = json.loads(raw)
                print(f"\n{method} {ep:<34} -> Status: {status}")
                print(f"Documented routes ({len(spec['paths'])} total): {list(spec['paths'].keys())}")
                assert "/patients/{patient_id}/validate" in spec['paths']
                assert "/patients/{patient_id}/run-agent" in spec['paths']
            elif "/validate" in ep:
                val = json.loads(raw)
                print(f"\n{method} {ep:<34} -> Status: {status}")
                print(f"  Patient: {val['patient_id']}")
                print(f"  Passed: {val['passed']} | Status: {val['validation_status']}")
                print(f"  Requires Human Review: {val['requires_human_review']}")
                print(f"  Checks: {val['checks_performed']}")
                print(f"  Issues Count: {len(val['issues'])}")
                assert val["passed"] is True
                assert val["validation_status"] == "passed"
                assert val["requires_human_review"] is True
            elif "/run-agent" in ep:
                res = json.loads(raw)
                print(f"\n{method} {ep:<34} -> Status: {status}")
                print(f"  Pipeline Status: {res['pipeline_status']}")
                print(f"  Evidence Items: {res['evidence_summary']['total_evidence_items']}")
                print(f"  Reconciliation Entities: {res['reconciliation_summary']['total_entities']}")
                print(f"  RAG Guideline Contexts: {res['rag_reference_count']}")
                print(f"  Documented Conflicts: {res['documentation']['unresolved_conflict_count']}")
                print(f"  Validation Verdict: Passed={res['validation']['passed']} (Review={res['validation']['requires_human_review']})")
                assert res["pipeline_status"] == "completed"
                assert res["validation"]["passed"] is True
            else:
                payload = json.loads(raw)
                print(f"\n{method} {ep:<34} -> Status: {status} | {json.dumps(payload)}")

    print("\n=== ALL PHASE 6 LIVE HTTP TESTS COMPLETED SUCCESSFULLY ===")

finally:
    server_proc.terminate()
    server_proc.wait()
    print("Server stopped cleanly.")
