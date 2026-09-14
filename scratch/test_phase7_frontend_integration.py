import subprocess
import time
import urllib.request
import json
import sys
import os

backend_port = 8000
frontend_port = 5173

print(f"1. Starting backend server on port {backend_port}...")
backend_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "backend.main:app", "--port", str(backend_port)],
    cwd=os.path.abspath("."),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(2)

print(f"2. Starting frontend dev server on port {frontend_port}...")
frontend_proc = subprocess.Popen(
    ["npm.cmd", "run", "dev", "--", "--port", str(frontend_port), "--host"],
    cwd=os.path.abspath("frontend"),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

time.sleep(3)

try:
    # Test Backend endpoints
    backend_url = f"http://127.0.0.1:{backend_port}"
    print(f"\nTesting Backend at {backend_url}...")

    # GET /patients
    req = urllib.request.Request(f"{backend_url}/patients")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        patients = json.loads(resp.read().decode())
        print(f"PASS: GET /patients returned {len(patients)} patients: {patients}")
        assert any(p["id"] == "P001" for p in patients)

    # POST /patients/P001/run-agent
    req = urllib.request.Request(
        f"{backend_url}/patients/P001/run-agent",
        data=b"",
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        result = json.loads(resp.read().decode())
        print("PASS: POST /patients/P001/run-agent returned successfully:")
        print(f"      Pipeline status: {result['pipeline_status']}")
        print(f"      Validation passed: {result['validation']['passed']}")
        print(f"      Human review required: {result['validation']['requires_human_review']}")
        print(f"      Unresolved conflicts count: {result['documentation']['unresolved_conflict_count']}")
        assert result["validation"]["passed"] is True
        assert result["validation"]["requires_human_review"] is True
        assert any("penicillin" in c.lower() for c in result["documentation"]["unresolved_conflicts"])

    # Test Frontend HTML serving
    frontend_url = f"http://127.0.0.1:{frontend_port}"
    print(f"\nTesting Frontend Dev Server at {frontend_url}...")
    req = urllib.request.Request(frontend_url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        html = resp.read().decode()
        assert "Clinical Evidence Agent" in html
        print(f"PASS: Frontend served valid index.html ({len(html)} bytes)")

    print("\n=======================================================")
    print(" ALL PHASE 7 FRONTEND & BACKEND INTEGRATION TESTS PASS!")
    print("=======================================================")

finally:
    print("\nStopping dev servers...")
    frontend_proc.terminate()
    backend_proc.terminate()
    frontend_proc.wait()
    backend_proc.wait()
    print("All servers stopped cleanly.")
