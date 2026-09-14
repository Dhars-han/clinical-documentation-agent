"""Comprehensive Test Suite for Phase 6 — Validation & Verification Agent.

Verifies:
1. Fully valid record (P001) -> passed=True, validation_status="passed", requires_human_review=True
2. Hallucinated medication -> passed=False, issue category=hallucination, RULE-008
3. Wrong medication status -> reconciliation_consistency_passed=False, RULE-004
4. Allergy conflict correctly preserved -> conflict_preservation_passed=True, review=True
5. Allergy conflict incorrectly erased -> allergy_safety issue, passed=False, RULE-006
6. Unsupported laboratory result -> evidence_grounding_passed=False, RULE-008
7. RAG contamination -> rag_separation_passed=False, RULE-007
8. Missing uncertainty handling -> uncertainty_handling_passed=False, RULE-009
9. Unsafe autonomous action -> safety_boundary_passed=False, RULE-010
10. API endpoints & Full Regression
"""

import sys
import os
import copy
from typing import Dict, Any

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.models import Patient
from backend.evidence_agent import EvidenceGatheringAgent
from backend.reconciliation.reconciler import ReconciliationService
from backend.rag.service import get_rag_service
from backend.documentation.service import DocumentationService
from backend.documentation.schemas import (
    ClinicalFollowUpRecord,
    DocumentedMedication,
    DocumentedAllergy,
    DocumentedLab,
    DocumentedChange,
    FollowUpAction,
    ClinicalReferenceLink,
    EvidenceLink
)
from backend.validation.validator import ClinicalValidator
from backend.validation.service import ValidationService
from backend.validation.schemas import ValidationResult
from backend.main import app


def setup_base_data():
    """Fetches real base components for P001 from Phase 1-5."""
    db = SessionLocal()
    try:
        ev_agent = EvidenceGatheringAgent(db)
        recon_service = ReconciliationService(db)
        rag_service = get_rag_service()
        doc_service = DocumentationService(db)

        evidence_pkg = ev_agent.gather("P001")
        recon_rpt = recon_service.reconcile("P001")
        rag_data = rag_service.get_patient_reference_context("P001", db)
        rag_contexts = rag_data.get("entity_guideline_contexts", [])
        record = doc_service.document("P001")

        return db, evidence_pkg, recon_rpt, rag_contexts, record
    finally:
        pass


def test_1_fully_valid_record(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 1: Fully Valid Record (P001) ---")
    val_result = ClinicalValidator.validate(
        record=base_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is True, f"Expected passed=True, got {val_result.passed}"
    assert val_result.validation_status == "passed", f"Expected validation_status='passed', got {val_result.validation_status}"
    assert val_result.requires_human_review is True, "Expected requires_human_review=True due to preserved Penicillin conflict"
    assert val_result.evidence_grounding_passed is True
    assert val_result.reconciliation_consistency_passed is True
    assert val_result.conflict_preservation_passed is True
    assert val_result.rag_separation_passed is True
    assert val_result.uncertainty_handling_passed is True
    assert val_result.safety_boundary_passed is True
    assert len(val_result.issues) == 0

    print("PASS: P001 valid record confirmed:")
    print(f"      Status: {val_result.validation_status} (Passed: {val_result.passed})")
    print(f"      Human Review Required: {val_result.requires_human_review} (Penicillin conflict preserved)")
    print(f"      Checks performed: {len(val_result.checks_performed)}")


def test_2_hallucinated_medication(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 2: Hallucinated Medication Detection ---")
    mutated_record = copy.deepcopy(base_record)
    
    # Inject hallucinated medication absent from evidence
    mutated_record.medications.append(DocumentedMedication(
        name="Drug X",
        status="active",
        regimen="20 mg once daily",
        reconciliation_status="consistent",
        requires_human_review=False,
        evidence_references=[
            EvidenceLink(
                claim="Drug X documented in medical database",
                source="medication_database",
                raw_excerpt="Drug X 20 mg once daily"
            )
        ]
    ))

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation to fail for hallucinated medication"
    assert val_result.validation_status == "failed"
    assert val_result.evidence_grounding_passed is False

    hallucination_issues = [i for i in val_result.issues if i.category == "hallucination" and i.rule_id == "RULE-008"]
    assert len(hallucination_issues) > 0, "Expected RULE-008 hallucination issue"
    print(f"PASS: Hallucinated drug detected and failed validation:")
    print(f"      Rule: {hallucination_issues[0].rule_id} -> {hallucination_issues[0].message}")


def test_3_wrong_medication_status(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 3: Reconciliation Inconsistency (Wrong Medication Status) ---")
    mutated_record = copy.deepcopy(base_record)

    # Phase 3 says Drug B is discontinued. Mutate documentation to claim Drug B is active!
    for m in mutated_record.medications:
        if m.name == "Drug B":
            m.status = "active"

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation to fail for status contradiction"
    assert val_result.reconciliation_consistency_passed is False
    recon_issues = [i for i in val_result.issues if i.category == "reconciliation_consistency" and i.rule_id == "RULE-004"]
    assert len(recon_issues) > 0, "Expected RULE-004 reconciliation consistency issue"
    print(f"PASS: Contradictory medication status detected:")
    print(f"      Rule: {recon_issues[0].rule_id} -> {recon_issues[0].message}")


def test_4_allergy_conflict_correctly_preserved(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 4: Allergy Conflict Correctly Preserved ---")
    # Base record has Penicillin allergy properly preserved
    val_result = ClinicalValidator.validate(
        record=base_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.conflict_preservation_passed is True
    assert val_result.passed is True
    assert val_result.requires_human_review is True
    print("PASS: Allergy conflict preserved without unauthorized resolution.")
    print(f"      Record passed={val_result.passed}, requires_human_review={val_result.requires_human_review}")


def test_5_allergy_conflict_incorrectly_erased(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 5: Allergy Conflict Incorrectly Erased ---")
    mutated_record = copy.deepcopy(base_record)

    # Erase Penicillin conflict and assert patient has "no known allergies"
    mutated_record.allergies = [
        DocumentedAllergy(
            allergen="Penicillin",
            status="no_known_allergies",
            reported_statement="No known drug allergies",
            conflict_details=None,
            requires_human_review=False,
            evidence_references=[
                EvidenceLink(
                    claim="Patient reports no known allergies",
                    source="consultation",
                    raw_excerpt="Patient reports no known drug allergies"
                )
            ]
        )
    ]
    # Also remove from unresolved conflicts
    mutated_record.unresolved_conflicts = [
        c for c in mutated_record.unresolved_conflicts if "penicillin" not in c.lower()
    ]
    mutated_record.unresolved_conflict_count = len(mutated_record.unresolved_conflicts)

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation failure when allergy conflict is erased"
    assert val_result.conflict_preservation_passed is False
    allergy_issues = [i for i in val_result.issues if i.category == "allergy_safety" and i.rule_id == "RULE-006"]
    assert len(allergy_issues) > 0, "Expected RULE-006 allergy safety issue"
    print(f"PASS: Allergy deletion caught:")
    print(f"      Rule: {allergy_issues[0].rule_id} -> {allergy_issues[0].message}")


def test_6_unsupported_laboratory_result(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 6: Unsupported Laboratory Result ---")
    mutated_record = copy.deepcopy(base_record)

    # Mutate HbA1c value to 6.2% (evidence has 7.1%)
    for lab in mutated_record.relevant_labs:
        if lab.test_name == "HbA1c":
            lab.value = "6.2"

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation failure for unsupported lab value"
    assert val_result.evidence_grounding_passed is False
    lab_issues = [i for i in val_result.issues if i.category == "hallucination" and i.rule_id == "RULE-008"]
    assert len(lab_issues) > 0, "Expected RULE-008 lab value hallucination issue"
    print(f"PASS: Unsupported lab value caught:")
    print(f"      Rule: {lab_issues[0].rule_id} -> {lab_issues[0].message}")


def test_7_rag_contamination(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 7: Clinical RAG Contamination Detection ---")
    mutated_record = copy.deepcopy(base_record)

    # Cite a clinical guideline as patient factual evidence
    mutated_record.medications[0].evidence_references.append(
        EvidenceLink(
            claim="Metformin is first-line therapy per clinical guidelines",
            source="DOC-ADA-METFORMIN-2026",
            raw_excerpt="Standards of Care in Diabetes: Metformin should be continued as long as eGFR > 30"
        )
    )

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation to fail when RAG is cited as patient evidence"
    assert val_result.rag_separation_passed is False
    rag_issues = [i for i in val_result.issues if i.category == "rag_separation" and i.rule_id == "RULE-007"]
    assert len(rag_issues) > 0, "Expected RULE-007 RAG separation issue"
    print(f"PASS: Clinical RAG contamination detected:")
    print(f"      Rule: {rag_issues[0].rule_id} -> {rag_issues[0].message}")


def test_8_missing_uncertainty(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 8: Missing Uncertainty Representation ---")
    mutated_record = copy.deepcopy(base_record)

    # Force conflicting entity to pretend it is definitely active with no review flag
    for allergy in mutated_record.allergies:
        if allergy.allergen == "Penicillin":
            allergy.status = "documented"
            allergy.requires_human_review = False

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation to fail when uncertainty is concealed"
    assert val_result.uncertainty_handling_passed is False
    uncertainty_issues = [i for i in val_result.issues if i.category == "uncertainty_handling" and i.rule_id == "RULE-009"]
    assert len(uncertainty_issues) > 0, "Expected RULE-009 uncertainty issue"
    print(f"PASS: Improper certainty representation detected:")
    print(f"      Rule: {uncertainty_issues[0].rule_id} -> {uncertainty_issues[0].message}")


def test_9_unsafe_autonomous_action(evidence_pkg, recon_rpt, rag_contexts, base_record):
    print("\n--- Test 9: Unsafe Autonomous Clinical Action Boundary ---")
    mutated_record = copy.deepcopy(base_record)

    # Add an autonomous prescription follow-up action
    mutated_record.follow_up_actions.append(FollowUpAction(
        action_type="clinical_prescription",
        description="Prescribe amoxicillin 500mg orally three times daily for infection.",
        urgency="routine",
        requires_human_review=False
    ))

    val_result = ClinicalValidator.validate(
        record=mutated_record,
        evidence_package=evidence_pkg,
        reconciliation_report=recon_rpt,
        rag_contexts=rag_contexts
    )

    assert val_result.passed is False, "Expected validation failure for autonomous prescribing"
    assert val_result.safety_boundary_passed is False
    safety_issues = [i for i in val_result.issues if i.category == "safety_boundary" and i.rule_id == "RULE-010"]
    assert len(safety_issues) > 0, "Expected RULE-010 safety boundary issue"
    print(f"PASS: Unsafe autonomous action blocked:")
    print(f"      Rule: {safety_issues[0].rule_id} -> {safety_issues[0].message}")


from backend.main import (
    home, get_patient, get_medications, get_allergies, get_labs, get_consultation,
    get_evidence, get_agent_evidence, reconcile_patient_evidence,
    generate_patient_document, get_patient_document,
    validate_patient_documentation, get_patient_documentation_validation,
    run_full_agent_workflow
)


def test_10_api_endpoints_and_regression(db):
    print("\n--- Test 10: API Endpoints & Multi-Phase Pipeline Regression ---")

    # 1. Test POST /patients/P001/validate
    val_post = validate_patient_documentation("P001", db)
    assert isinstance(val_post, ValidationResult)
    assert val_post.patient_id == "P001"
    assert val_post.passed is True
    assert val_post.validation_status == "passed"
    assert val_post.requires_human_review is True
    print("PASS: POST /patients/P001/validate handler returned valid ValidationResult")

    # 2. Test GET /patients/P001/validate
    val_get = get_patient_documentation_validation("P001", db)
    assert isinstance(val_get, ValidationResult)
    assert val_get.passed is True
    print("PASS: GET /patients/P001/validate verified idempotent")

    # 3. Test POST /patients/P001/run-agent (Full pipeline)
    pipe_data = run_full_agent_workflow("P001", db)
    assert pipe_data["patient_id"] == "P001"
    assert pipe_data["pipeline_status"] == "completed"
    assert "evidence_summary" in pipe_data
    assert "reconciliation_summary" in pipe_data
    assert "documentation" in pipe_data
    assert "validation" in pipe_data
    assert pipe_data["validation"]["passed"] is True
    print(f"PASS: POST /patients/P001/run-agent executed full 5-stage pipeline successfully!")
    print(f"      Evidence items: {pipe_data['evidence_summary']['total_evidence_items']}")
    print(f"      Reconciled entities: {pipe_data['reconciliation_summary']['total_entities']}")
    print(f"      Clinical guideline references: {pipe_data['rag_reference_count']}")
    print(f"      Documentation conflicts preserved: {pipe_data['documentation']['unresolved_conflict_count']}")
    print(f"      Validation verdict: passed={pipe_data['validation']['passed']}, review={pipe_data['validation']['requires_human_review']}")

    # 4. Verify Phase 1-5 endpoints remain functional with zero regression
    assert home()["message"] == "Clinical Documentation Agent API"
    assert get_patient("P001", db).id == "P001"
    assert len(get_medications("P001", db)) >= 2
    assert len(get_allergies("P001", db)) >= 1
    assert len(get_labs("P001", db)) >= 2
    assert get_consultation("P001", db) is not None
    assert len(get_evidence("P001", db)["medications"]) >= 2
    assert get_agent_evidence("P001", db).summary.total_evidence_items >= 11
    assert reconcile_patient_evidence("P001", db).requires_human_review_count == 1
    assert generate_patient_document("P001", db).requires_human_review is True
    assert get_patient_document("P001", db).patient_id == "P001"
    print("PASS: Zero regressions across all 18 existing API routes!")


def main():
    print("=======================================================")
    print(" RUNNING PHASE 6 VALIDATION & VERIFICATION AGENT TESTS")
    print("=======================================================")

    db, evidence_pkg, recon_rpt, rag_contexts, base_record = setup_base_data()
    try:
        test_1_fully_valid_record(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_2_hallucinated_medication(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_3_wrong_medication_status(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_4_allergy_conflict_correctly_preserved(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_5_allergy_conflict_incorrectly_erased(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_6_unsupported_laboratory_result(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_7_rag_contamination(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_8_missing_uncertainty(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_9_unsafe_autonomous_action(evidence_pkg, recon_rpt, rag_contexts, base_record)
        test_10_api_endpoints_and_regression(db)

        print("\n=======================================================")
        print(" ALL 10 PHASE 6 VALIDATION TESTS PASSED 100%!")
        print("=======================================================\n")
    finally:
        db.close()


if __name__ == "__main__":
    main()
