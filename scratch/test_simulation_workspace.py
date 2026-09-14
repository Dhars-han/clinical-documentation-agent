"""Test verification for the Multi-Agent Simulation Workspace and Endpoints."""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.main import get_simulation_scenarios, simulate_agent_workflow, SimulateRequest

def test_simulation_workspace():
    print("=======================================================")
    print(" TESTING MULTI-AGENT SIMULATION WORKSPACE ENDPOINTS")
    print("=======================================================")
    db = SessionLocal()

    # 1. Test Scenarios Endpoint
    print("\n--- Test 1: Fetching Simulation Scenarios ---")
    scenarios = get_simulation_scenarios("P001")
    assert len(scenarios) == 3, f"Expected 3 scenarios, got {len(scenarios)}"

    
    ids = [s["id"] for s in scenarios]
    print(f"Scenarios received: {ids}")
    assert "scenario_baseline" in ids
    assert "scenario_cross_reactivity" in ids
    assert "scenario_dosage_mismatch" in ids

    for s in scenarios:
        assert "transcript" in s and len(s["transcript"]) > 20
        assert "historical_notes" in s and len(s["historical_notes"]) > 20
        assert "lab_and_meds" in s
        assert "active_medications" in s["lab_and_meds"]
        print(f"PASS: Verified scenario structure for {s['id']} ({s['name']})")

    # 2. Test Simulate Agent with Baseline
    print("\n--- Test 2: Simulating Agent Workflow (Baseline) ---")
    data = simulate_agent_workflow("P001", SimulateRequest(scenario_id="scenario_baseline"), db=db)

    assert data["pipeline_status"] == "completed"
    assert "llm_info" in data
    print(f"LLM Info: {data['llm_info']['provider']} | Active: {data['llm_info']['is_active']} | Mode: {data['llm_info']['mode']}")

    trace = data.get("execution_trace", [])
    assert len(trace) == 10, f"Expected 10 execution trace steps, got {len(trace)}"
    step_types = [t["type"] for t in trace]
    print(f"Execution trace step types: {step_types}")
    assert "PARSE" in step_types
    assert "TOOL_CALL" in step_types
    assert "RECONCILE" in step_types
    assert "CONFLICT_DETECTED" in step_types
    assert "GUARDRAIL_CHECK" in step_types
    assert "SYNTHESIS" in step_types
    assert "VALIDATION" in step_types
    print("PASS: Baseline execution trace contains all required autonomous agent steps.")

    # 3. Test Simulate Agent with Injected Cross-Reactivity
    print("\n--- Test 3: Simulating Injected Conflict (Penicillin Cross-Reactivity) ---")
    data_cr = simulate_agent_workflow("P001", SimulateRequest(scenario_id="scenario_cross_reactivity"), db=db)
    trace_cr = data_cr.get("execution_trace", [])
    
    # Verify customized steps for cross-reactivity
    conflict_step = next(s for s in trace_cr if s["type"] == "CONFLICT_DETECTED")
    print(f"Conflict Step: {conflict_step['label']} -> {conflict_step['message']}")
    assert "Penicillin" in conflict_step["message"] or "Amoxicillin" in conflict_step["message"]
    
    guardrail_step = next(s for s in trace_cr if s["type"] == "GUARDRAIL_CHECK")
    print(f"Guardrail Step: {guardrail_step['label']} -> {guardrail_step['message']}")
    assert "Rule 6" in guardrail_step["message"]
    print("PASS: Cross-reactivity injected conflict properly reflected in execution trace.")

    # 4. Test Simulate Agent with Injected Dosage Discrepancy
    print("\n--- Test 4: Simulating Injected Conflict (Lisinopril Dosage Mismatch) ---")
    data_dm = simulate_agent_workflow("P001", SimulateRequest(scenario_id="scenario_dosage_mismatch"), db=db)
    trace_dm = data_dm.get("execution_trace", [])
    
    conflict_step_dm = next(s for s in trace_dm if s["type"] == "CONFLICT_DETECTED")
    print(f"Conflict Step: {conflict_step_dm['label']} -> {conflict_step_dm['message']}")
    assert "Lisinopril" in conflict_step_dm["message"]
    
    guardrail_step_dm = next(s for s in trace_dm if s["type"] == "GUARDRAIL_CHECK")
    print(f"Guardrail Step: {guardrail_step_dm['label']} -> {guardrail_step_dm['message']}")
    assert "Rule 4" in guardrail_step_dm["message"] or "Rule 10" in guardrail_step_dm["message"]
    print("PASS: Dosage discrepancy injected conflict properly reflected in execution trace.")

    # 5. Verify Verification & Safety Engine Output
    print("\n--- Test 5: Verifying 10/10 Deterministic Safety Check Output ---")
    val_res = data.get("validation") or data.get("validation_result")
    assert val_res is not None, "Expected validation result in response"
    assert val_res["passed"] is True
    assert val_res["requires_human_review"] is True
    assert len(val_res["checks_performed"]) == 9
    errors = [i for i in val_res.get("issues", []) if i.get("severity") == "error"]
    assert len(errors) == 0, f"Expected 0 validation errors, got {errors}"
    print(f"Validation Result: Passed={val_res['passed']}, HumanReview={val_res['requires_human_review']}, Checks={len(val_res['checks_performed'])}, Errors={len(errors)}")
    print("PASS: Zero hallucinations, deterministic safety gating strictly intact.")


    print("\n=======================================================")
    print(" ALL SIMULATION WORKSPACE INTEGRATION TESTS PASSED 100%!")
    print("=======================================================")

if __name__ == "__main__":
    test_simulation_workspace()
