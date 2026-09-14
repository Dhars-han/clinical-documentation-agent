"""Verification test for Vercel Serverless Function entry point and routing using standard library."""

import os
import sys
import time
import subprocess
import urllib.request
import json

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
test_port = 8001

print(f"Starting api.index:app on port {test_port}...")
proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "api.index:app", "--port", str(test_port)],
    cwd=project_root,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(2)

try:
    base_url = f"http://127.0.0.1:{test_port}"

    # 1. Root
    req = urllib.request.Request(f"{base_url}/")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode())
        print(f"PASS: GET / -> {data}")

    # 2. /patients
    req = urllib.request.Request(f"{base_url}/patients")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        pts = json.loads(resp.read().decode())
        print(f"PASS: GET /patients returned {len(pts)} patients")
        assert len(pts) == 51, f"Expected 51 patients, got {len(pts)}"
        ids = [p["id"] for p in pts]
        assert "P001" in ids
        assert "P007" in ids
        assert "P056" in ids

    # 3. /api/patients (verifying ASGI PathRewriterMiddleware)
    req = urllib.request.Request(f"{base_url}/api/patients")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        pts_api = json.loads(resp.read().decode())
        assert len(pts_api) == 51
        print(f"PASS: GET /api/patients returned {len(pts_api)} patients through prefix rewriter")

    # 4. /config/llm-status (zero leaks)
    req = urllib.request.Request(f"{base_url}/config/llm-status")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        st = json.loads(resp.read().decode())
        print(f"PASS: GET /config/llm-status -> {st}")
        assert "api_key" not in st
        assert "sk-" not in str(st)

    # 5. Patient P007 details
    req = urllib.request.Request(f"{base_url}/patients/P007")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        p7 = json.loads(resp.read().decode())
        assert p7["id"] == "P007"
        assert p7["age"] == 72
        print(f"PASS: GET /patients/P007 -> ID: {p7['id']}, Name: {p7['name']}, Age: {p7['age']}")

    # 6. Patient P007 evidence
    req = urllib.request.Request(f"{base_url}/patients/P007/evidence")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        ev = json.loads(resp.read().decode())
        assert len(ev["notes"]) >= 1
        assert len(ev["medications"]) >= 2
        assert len(ev["labs"]) >= 2
        assert len(ev["consultations"]) >= 1
        print(f"PASS: GET /patients/P007/evidence -> Meds: {len(ev['medications'])}, Labs: {len(ev['labs'])}")

    # 7. Patient P007 reconciliation
    req = urllib.request.Request(
        f"{base_url}/patients/P007/reconcile",
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        rec = json.loads(resp.read().decode())
        assert rec["total_entities"] > 0
        print(f"PASS: POST /patients/P007/reconcile -> Reconciled entities: {rec['total_entities']}")

    # 8. Patient P056 (the 50th synthetic patient)
    req = urllib.request.Request(f"{base_url}/patients/P056")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        p56 = json.loads(resp.read().decode())
        assert p56["id"] == "P056"
        assert p56["age"] == 70
        print(f"PASS: GET /patients/P056 -> ID: {p56['id']}, Name: {p56['name']}, Age: {p56['age']}")

    # 9. Clinical RAG documents list
    req = urllib.request.Request(f"{base_url}/rag/documents")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        docs = json.loads(resp.read().decode())
        assert len(docs) >= 5
        print(f"PASS: GET /rag/documents -> {len(docs)} clinical guidelines loaded in vector store")

    print("\n=======================================================")
    print(" ALL 9 VERCEL SERVERLESS FUNCTION INTEGRATION TESTS PASS!")
    print("=======================================================")

finally:
    proc.terminate()
    proc.wait()
    print("Server stopped cleanly.")
