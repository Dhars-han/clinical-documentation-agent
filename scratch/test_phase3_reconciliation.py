import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.evidence_agent import EvidenceItem, EvidenceCategory, EvidenceModality
from backend.reconciliation.schemas import (
    ReconciliationStatus,
    ReconciliationResult,
    ReconciliationReport,
    EvidenceReference,
)
from backend.reconciliation.rules import (
    reconcile_medication,
    reconcile_allergy,
    reconcile_lab,
    reconcile_clinical_observation,
)
from backend.reconciliation.reconciler import ReconciliationService
from backend.main import (
    app, home, get_patient, get_notes, get_medications,
    get_allergies, get_labs, get_consultation, get_evidence,
    get_agent_evidence, run_agent_evidence,
    reconcile_patient_evidence, get_reconciled_patient_evidence
)


def test_1_consistent_medication():
    print("\n--- Test 1: Consistent Medication (Metformin in P001) ---")
    db = SessionLocal()
    try:
        service = ReconciliationService(db)
        report = service.reconcile("P001")
        met = next((r for r in report.results if r.entity == "Metformin"), None)

        assert met is not None, "Metformin missing from reconciliation results"
        assert met.status == ReconciliationStatus.CONSISTENT, f"Expected consistent, got {met.status}"
        assert met.requires_human_review is False, "Consistent med should not require human review"
        assert "500 mg" in (met.current_state or ""), f"Unexpected state: {met.current_state}"
        assert len(met.conflicting_evidence) == 0, "Consistent med should have no conflicting evidence"
        assert len(met.supporting_evidence) >= 2, "Expected multiple supporting evidence items"

        print(f"PASS: Metformin -> status={met.status.value}, state={met.current_state}, review={met.requires_human_review}")
    finally:
        db.close()


def test_2_resolved_medication_discontinuation():
    print("\n--- Test 2: Resolved Medication Discontinuation (Drug B in P001) ---")
    db = SessionLocal()
    try:
        service = ReconciliationService(db)
        report = service.reconcile("P001")
        drug_b = next((r for r in report.results if r.entity == "Drug B"), None)

        assert drug_b is not None, "Drug B missing from reconciliation results"
        assert drug_b.status == ReconciliationStatus.RESOLVED, f"Expected resolved, got {drug_b.status}"
        assert drug_b.current_state == "discontinued", f"Expected discontinued, got {drug_b.current_state}"
        assert drug_b.requires_human_review is False, "Resolved discontinuation should not require review"
        
        # Provenance check: conflicting past active evidence must NOT be discarded
        assert len(drug_b.conflicting_evidence) >= 1, "Older active record must be preserved in conflicting evidence"
        assert len(drug_b.supporting_evidence) >= 1, "Discontinuation records must be in supporting evidence"

        print(f"PASS: Drug B -> status={drug_b.status.value}, state={drug_b.current_state}, review={drug_b.requires_human_review}")
        print(f"      Supporting: {[e.source for e in drug_b.supporting_evidence]} | Conflicting: {[e.source for e in drug_b.conflicting_evidence]}")
    finally:
        db.close()


def test_3_allergy_conflict():
    print("\n--- Test 3: Allergy Conflict (Penicillin in P001) ---")
    db = SessionLocal()
    try:
        service = ReconciliationService(db)
        report = service.reconcile("P001")
        pen = next((r for r in report.results if r.entity == "Penicillin"), None)

        assert pen is not None, "Penicillin missing from reconciliation results"
        assert pen.status == ReconciliationStatus.CONFLICT, f"Expected conflict, got {pen.status}"
        assert pen.current_state is None, f"State must be null on conflict, got {pen.current_state}"
        assert pen.requires_human_review is True, "Allergy conflict MUST require human review"
        
        # Provenance check
        assert len(pen.supporting_evidence) >= 1, "Documented allergy must be preserved"
        assert len(pen.conflicting_evidence) >= 1, "Denial statement must be preserved"
        assert any("allergy_database" in e.source for e in pen.supporting_evidence)
        assert any("consultation" in e.source for e in pen.conflicting_evidence)

        print(f"PASS: Penicillin -> status={pen.status.value}, state={pen.current_state}, review={pen.requires_human_review}")
        print(f"      Reason: {pen.reason}")
    finally:
        db.close()


def test_4_conflicting_medication_dose():
    print("\n--- Test 4: Conflicting Medication Dose (Synthetic) ---")
    items = [
        EvidenceItem(
            id="ev-synth-1",
            category=EvidenceCategory.MEDICATION,
            entity_name="Lisinopril",
            source="previous_note",
            source_date="2026-08-01",
            raw_text="Patient taking Lisinopril 10 mg once daily",
            attributes={"dose": "10 mg", "frequency": "once daily", "status": "active"},
            modality=EvidenceModality.UNSTRUCTURED_TEXT
        ),
        EvidenceItem(
            id="ev-synth-2",
            category=EvidenceCategory.MEDICATION,
            entity_name="Lisinopril",
            source="medication_database",
            source_date="2026-09-01",
            raw_text="Lisinopril 20 mg once daily (status: active)",
            attributes={"dose": "20 mg", "frequency": "once daily", "status": "active"},
            modality=EvidenceModality.STRUCTURED_RECORD
        ),
        EvidenceItem(
            id="ev-synth-3",
            category=EvidenceCategory.MEDICATION,
            entity_name="Lisinopril",
            source="consultation",
            source_date="2026-09-13",
            raw_text="Patient reports taking Lisinopril 10 mg once daily",
            attributes={"dose": "10 mg", "frequency": "once daily", "reported_status": "reported_active"},
            modality=EvidenceModality.UNSTRUCTURED_TEXT
        )
    ]

    res = reconcile_medication("Lisinopril", items, "TEST-PATIENT")
    assert res.status == ReconciliationStatus.CONFLICT, f"Expected conflict, got {res.status}"
    assert res.current_state is None, "Current state must be None on dose conflict"
    assert res.requires_human_review is True, "Dose conflict must require human review"
    assert len(res.conflicting_evidence) >= 2, "Conflicting items must be preserved"

    print(f"PASS: Lisinopril -> status={res.status.value}, review={res.requires_human_review}")
    print(f"      Reason: {res.reason}")


def test_5_lab_timeline():
    print("\n--- Test 5: Lab Timeline Progression (Synthetic) ---")
    items = [
        EvidenceItem(
            id="ev-lab-hist",
            category=EvidenceCategory.LAB,
            entity_name="HbA1c",
            source="laboratory_database",
            source_date="2026-07-01",
            raw_text="HbA1c: 7.8 %",
            attributes={"value": "7.8", "unit": "%"},
            modality=EvidenceModality.STRUCTURED_RECORD
        ),
        EvidenceItem(
            id="ev-lab-curr",
            category=EvidenceCategory.LAB,
            entity_name="HbA1c",
            source="laboratory_database",
            source_date="2026-09-10",
            raw_text="HbA1c: 7.1 %",
            attributes={"value": "7.1", "unit": "%"},
            modality=EvidenceModality.STRUCTURED_RECORD
        )
    ]

    res = reconcile_lab("HbA1c", items, "TEST-PATIENT")
    assert res.status == ReconciliationStatus.CONSISTENT, f"Lab timeline should be consistent progression, got {res.status}"
    assert "7.1 % as of 2026-09-10" in res.current_state, f"Latest value not reflected: {res.current_state}"
    assert res.requires_human_review is False, "Normal lab progression should not require review"
    assert len(res.supporting_evidence) == 2, "Both historical and recent labs should be preserved"

    print(f"PASS: HbA1c -> status={res.status.value}, state={res.current_state}, review={res.requires_human_review}")
    print(f"      Reason: {res.reason}")


def test_6_single_source_and_missing_evidence():
    print("\n--- Test 6: Single-source and Missing Evidence ---")
    db = SessionLocal()
    try:
        service = ReconciliationService(db)
        report = service.reconcile("P001")
        creat = next((r for r in report.results if r.entity == "Creatinine"), None)

        assert creat is not None
        assert creat.status == ReconciliationStatus.CONSISTENT
        assert creat.requires_human_review is False
        assert "1.0 mg/dL" in creat.current_state
        print(f"PASS: Creatinine single baseline -> status={creat.status.value}, state={creat.current_state}")

        # Missing patient P999
        rep_999 = service.reconcile("P999")
        assert rep_999.patient_id == "P999"
        assert rep_999.total_entities == 0
        assert rep_999.requires_human_review_count == 0
        print("PASS: Non-existent patient P999 -> 0 entities, 0 review items")
    finally:
        db.close()


def test_7_full_patient_and_api_integration():
    print("\n--- Test 7: Full Patient P001 and API Routes ---")
    db = SessionLocal()
    try:
        # 1. Test POST /patients/{patient_id}/reconcile
        rep_post = reconcile_patient_evidence("P001", db)
        assert isinstance(rep_post, ReconciliationReport)
        assert rep_post.patient_id == "P001"
        assert rep_post.total_entities == 6
        assert rep_post.requires_human_review_count == 1  # Penicillin allergy conflict

        # 2. Test GET /patients/{patient_id}/reconcile
        rep_get = get_reconciled_patient_evidence("P001", db)
        assert isinstance(rep_get, ReconciliationReport)
        assert rep_get.total_entities == 6

        print("PASS: POST & GET /patients/P001/reconcile returned valid reports:")
        print(f"      Total entities: {rep_post.total_entities}")
        print(f"      Requiring human review: {rep_post.requires_human_review_count}")

        # 3. Regression verification of previous endpoints
        assert home()["message"] == "Clinical Documentation Agent API"
        assert get_patient("P001", db).id == "P001"
        assert len(get_notes("P001", db)) >= 1
        assert len(get_medications("P001", db)) >= 2
        assert len(get_allergies("P001", db)) >= 1
        assert len(get_labs("P001", db)) >= 2
        assert get_consultation("P001", db).patient_id == "P001"
        assert get_evidence("P001", db)["patient_id"] == "P001"
        assert get_agent_evidence("P001", db).patient_id == "P001"
        assert run_agent_evidence("P001", db).patient_id == "P001"
        print("PASS: All 10 pre-existing endpoints confirmed operational with zero regression!")
    finally:
        db.close()


if __name__ == "__main__":
    test_1_consistent_medication()
    test_2_resolved_medication_discontinuation()
    test_3_allergy_conflict()
    test_4_conflicting_medication_dose()
    test_5_lab_timeline()
    test_6_single_source_and_missing_evidence()
    test_7_full_patient_and_api_integration()
    print("\n=======================================================")
    print(" ALL 7 PHASE 3 RECONCILIATION TESTS PASSED 100%!")
    print("=======================================================")
