import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.documentation.schemas import ClinicalFollowUpRecord
from backend.documentation.generator import FollowUpRecordGenerator
from backend.documentation.service import DocumentationService
from backend.evidence_agent import EvidencePackage, EvidenceSummary, EvidenceItem, EvidenceCategory, EvidenceModality
from backend.rag.schemas import RAGQuery
from backend.reconciliation.schemas import (
    ReconciliationReport,
    ReconciliationResult,
    ReconciliationStatus,
    EvidenceReference,
)
from backend.main import (
    app, home, get_patient, get_evidence, get_agent_evidence,
    reconcile_patient_evidence, query_clinical_rag,
    generate_patient_document, get_patient_document
)


def test_1_all_evidence_consistent():
    print("\n--- Test 1: All Evidence is Consistent ---")
    # Synthetic consistent report
    recon_report = ReconciliationReport(
        patient_id="SYNTH-001",
        reconciled_at="2026-09-14T00:00:00Z",
        total_entities=2,
        requires_human_review_count=0,
        results=[
            ReconciliationResult(
                patient_id="SYNTH-001",
                entity="Metformin",
                category="medication",
                status=ReconciliationStatus.CONSISTENT,
                current_state="active (500 mg once daily)",
                confidence=1.0,
                reason="All sources agree on Metformin adherence.",
                supporting_evidence=[
                    EvidenceReference(source="consultation", source_date="2026-09-14", raw_excerpt="Taking 500mg daily", attributes={"dose": "500mg"})
                ],
                requires_human_review=False
            ),
            ReconciliationResult(
                patient_id="SYNTH-001",
                entity="HbA1c",
                category="lab",
                status=ReconciliationStatus.CONSISTENT,
                current_state="6.8 % as of 2026-09-10",
                confidence=1.0,
                reason="Lab test within stable range.",
                supporting_evidence=[
                    EvidenceReference(source="laboratory_database", source_date="2026-09-10", raw_excerpt="HbA1c: 6.8 %", attributes={"value": "6.8", "unit": "%"})
                ],
                requires_human_review=False
            )
        ]
    )

    ev_pkg = EvidencePackage(
        patient_id="SYNTH-001",
        patient_name="Consistent Patient",
        summary=EvidenceSummary(),
        items=[
            EvidenceItem(
                id="ev-1",
                category=EvidenceCategory.LAB,
                entity_name="HbA1c",
                source="laboratory_database",
                source_date="2026-09-10",
                raw_text="HbA1c: 6.8 %",
                attributes={"value": "6.8", "unit": "%"},
                modality=EvidenceModality.STRUCTURED_RECORD
            )
        ]
    )

    record = FollowUpRecordGenerator.generate(
        patient_id="SYNTH-001",
        patient_name="Consistent Patient",
        patient_age=50,
        consultation_transcript="Patient taking Metformin 500 mg once daily.",
        evidence_package=ev_pkg,
        reconciliation_report=recon_report,
        rag_contexts=[]
    )

    assert record.patient_id == "SYNTH-001"
    assert record.requires_human_review is False, "Consistent record should not require review"
    assert record.unresolved_conflict_count == 0, "Consistent record should have 0 conflicts"
    assert len(record.unresolved_conflicts) == 0
    assert len(record.medications) == 1
    assert record.medications[0].status == "active"
    assert record.medications[0].regimen == "500 mg once daily"

    print(f"PASS: Consistent record generated: review={record.requires_human_review}, conflicts={record.unresolved_conflict_count}")


def test_2_medication_conflict_resolved_by_phase3():
    print("\n--- Test 2: Medication Conflict Resolved by Phase 3 (Drug B Discontinuation) ---")
    db = SessionLocal()
    try:
        service = DocumentationService(db)
        record = service.document("P001")

        drug_b = next((m for m in record.medications if m.name == "Drug B"), None)
        assert drug_b is not None, "Drug B missing from record medications"
        assert drug_b.status == "discontinued", f"Expected discontinued, got {drug_b.status}"
        assert drug_b.reconciliation_status == "resolved"
        assert drug_b.requires_human_review is False

        # Provenance check: past active evidence is preserved
        sources_in_prov = [e.source for e in drug_b.evidence_references]
        assert "previous_note" in sources_in_prov, "Previous note must be preserved in provenance"
        assert "medication_database" in sources_in_prov
        assert "consultation" in sources_in_prov

        # Documented change check
        change_b = next((c for c in record.documented_changes if c.entity == "Drug B"), None)
        assert change_b is not None, "Drug B change missing from documented_changes"
        assert change_b.change_type == "discontinuation"
        assert "approximately one week" in (change_b.timeline or "")

        print(f"PASS: Reconciled medication Drug B documented as: {drug_b.status} ({drug_b.reconciliation_status})")
        print(f"      Provenance preserved: {sources_in_prov}")
        print(f"      Change logged: {change_b.description} (Timeline: {change_b.timeline})")
    finally:
        db.close()


def test_3_allergy_conflict_requires_human_review():
    print("\n--- Test 3: Allergy Conflict Escalated and Preserved (Penicillin in P001) ---")
    db = SessionLocal()
    try:
        service = DocumentationService(db)
        record = service.document("P001")

        pen = next((a for a in record.allergies if a.allergen == "Penicillin"), None)
        assert pen is not None, "Penicillin missing from record allergies"
        assert pen.status == "conflicting", f"Expected conflicting, got {pen.status}"
        assert pen.requires_human_review is True, "Penicillin conflict MUST require human review"
        assert pen.documented_reaction == "Unknown"
        assert "Patient reports no known drug allergies" in (pen.reported_statement or "")

        # Crucial safety check: the record MUST NOT say 'no allergies' or erase Penicillin
        assert record.requires_human_review is True, "Overall record must require human review"
        assert any("Penicillin" in conflict for conflict in record.unresolved_conflicts)

        # Action check
        action = next((act for act in record.follow_up_actions if "Penicillin" in act.description), None)
        assert action is not None, "High-urgency allergy review action missing"
        assert action.urgency == "high"
        assert action.requires_human_review is True

        print(f"PASS: Allergy Penicillin safely documented as: {pen.status} (review={pen.requires_human_review})")
        print(f"      Conflict details: {pen.conflict_details}")
        print(f"      Safety action logged: {action.description}")
    finally:
        db.close()


def test_4_missing_information_handling():
    print("\n--- Test 4: Missing Information Handling (No Hallucinations) ---")
    recon_report = ReconciliationReport(
        patient_id="SYNTH-MISSING",
        reconciled_at="2026-09-14T00:00:00Z",
        total_entities=1,
        requires_human_review_count=1,
        results=[
            ReconciliationResult(
                patient_id="SYNTH-MISSING",
                entity="UnknownDrug",
                category="medication",
                status=ReconciliationStatus.UNRESOLVED,
                current_state=None,  # missing dose/regimen
                confidence=0.5,
                reason="Mentioned in past note without dose or confirmation.",
                supporting_evidence=[],
                conflicting_evidence=[],
                requires_human_review=True
            )
        ]
    )

    ev_pkg = EvidencePackage(
        patient_id="SYNTH-MISSING",
        summary=EvidenceSummary(),
        items=[]
    )

    record = FollowUpRecordGenerator.generate(
        patient_id="SYNTH-MISSING",
        patient_name=None,
        patient_age=None,
        consultation_transcript=None,  # missing transcript
        evidence_package=ev_pkg,
        reconciliation_report=recon_report,
        rag_contexts=[]
    )

    assert record.patient_name is None
    assert record.consultation_summary == "No consultation transcript recorded for this encounter."
    assert len(record.medications) == 1
    assert record.medications[0].regimen is None, "Missing regimen must remain None (no hallucinated dose)"
    assert record.medications[0].status == "unresolved"

    print("PASS: Missing fields explicitly preserved as None/unknown without hallucination.")


def test_5_multiple_conflicts_preserved():
    print("\n--- Test 5: Multiple Conflicts Preserved ---")
    recon_report = ReconciliationReport(
        patient_id="SYNTH-MULTI",
        reconciled_at="2026-09-14T00:00:00Z",
        total_entities=3,
        requires_human_review_count=2,
        results=[
            ReconciliationResult(
                patient_id="SYNTH-MULTI",
                entity="Drug X",
                category="medication",
                status=ReconciliationStatus.CONFLICT,
                current_state=None,
                confidence=0.8,
                reason="Dose conflict between 10mg and 20mg.",
                requires_human_review=True
            ),
            ReconciliationResult(
                patient_id="SYNTH-MULTI",
                entity="Sulfa",
                category="allergy",
                status=ReconciliationStatus.CONFLICT,
                current_state=None,
                confidence=0.8,
                reason="Documented allergy conflicts with denial.",
                requires_human_review=True
            ),
            ReconciliationResult(
                patient_id="SYNTH-MULTI",
                entity="Creatinine",
                category="lab",
                status=ReconciliationStatus.CONSISTENT,
                current_state="1.2 mg/dL",
                confidence=1.0,
                reason="Single baseline.",
                requires_human_review=False
            )
        ]
    )

    record = FollowUpRecordGenerator.generate(
        patient_id="SYNTH-MULTI",
        patient_name="Multi Conflict Patient",
        patient_age=60,
        consultation_transcript="Patient reports stopped Drug X and no allergies.",
        evidence_package=EvidencePackage(patient_id="SYNTH-MULTI", summary=EvidenceSummary(), items=[]),
        reconciliation_report=recon_report,
        rag_contexts=[]
    )

    assert record.unresolved_conflict_count == 2
    assert len(record.unresolved_conflicts) == 2
    assert any("Drug X" in c for c in record.unresolved_conflicts)
    assert any("Sulfa" in c for c in record.unresolved_conflicts)
    assert record.requires_human_review is True

    print(f"PASS: All {record.unresolved_conflict_count} conflicts preserved in unresolved_conflicts list:")
    for c in record.unresolved_conflicts:
        print(f"      - {c}")


def test_6_rag_information_segregated():
    print("\n--- Test 6: RAG Information Segregated from Patient Facts ---")
    db = SessionLocal()
    try:
        service = DocumentationService(db)
        record = service.document("P001")

        assert len(record.clinical_references) >= 3, "Expected at least 3 clinical reference chunks"

        for cr in record.clinical_references:
            assert cr.document_id, "Missing document_id in clinical reference"
            assert cr.title, "Missing title in clinical reference"
            assert cr.source_organization, "Missing source_organization in clinical reference"
            assert cr.section, "Missing section in clinical reference"
            assert cr.snippet, "Missing snippet in clinical reference"
            assert cr.relevance_score > 0.0

        # Verify reference documents are clinical guidelines, not patient facts
        titles = {cr.title for cr in record.clinical_references}
        assert any("ADA Standards of Care" in t or "Diabetes" in t for t in titles)
        assert any("AAAAI Practice Parameter" in t or "Penicillin" in t for t in titles)

        print(f"PASS: {len(record.clinical_references)} reference chunks preserved under clinical_references:")
        for cr in record.clinical_references[:3]:
            print(f"      * [{cr.document_id}] {cr.title} - Section: {cr.section} (Score: {cr.relevance_score})")
    finally:
        db.close()


def test_7_api_and_full_regression():
    print("\n--- Test 7: API Endpoints & Full Phase 1–4 Regression ---")
    db = SessionLocal()
    try:
        # Test POST and GET /patients/{id}/document
        rec_post = generate_patient_document("P001", db)
        assert isinstance(rec_post, ClinicalFollowUpRecord)
        assert rec_post.patient_id == "P001"
        assert rec_post.patient_name == "Synthetic Patient 001"
        assert rec_post.requires_human_review is True
        assert len(rec_post.medications) >= 2
        assert len(rec_post.allergies) >= 1
        assert len(rec_post.relevant_labs) >= 2

        rec_get = get_patient_document("P001", db)
        assert rec_get.patient_id == "P001"
        assert len(rec_get.documented_changes) >= 1

        print("PASS: POST & GET /patients/P001/document returned valid ClinicalFollowUpRecord")

        # Full regression check across all prior phases
        assert home()["message"] == "Clinical Documentation Agent API"
        assert get_patient("P001", db).id == "P001"
        assert len(get_evidence("P001", db)["medications"]) >= 2
        assert get_agent_evidence("P001", db).summary.total_evidence_items >= 11
        assert reconcile_patient_evidence("P001", db).requires_human_review_count == 1
        assert len(query_clinical_rag(RAGQuery(query="Metformin renal")).results) >= 1

        print("PASS: Phase 1–4 endpoints verified operational with 0 regression!")
    finally:
        db.close()


if __name__ == "__main__":
    test_1_all_evidence_consistent()
    test_2_medication_conflict_resolved_by_phase3()
    test_3_allergy_conflict_requires_human_review()
    test_4_missing_information_handling()
    test_5_multiple_conflicts_preserved()
    test_6_rag_information_segregated()
    test_7_api_and_full_regression()
    print("\n=======================================================")
    print(" ALL 7 PHASE 5 DOCUMENTATION TESTS PASSED 100%!")
    print("=======================================================")
