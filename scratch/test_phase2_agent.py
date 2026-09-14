import sys
import json
import os

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.evidence_agent import EvidenceGatheringAgent, EvidencePackage
from backend.main import (
    app, get_db, home, get_patient, get_notes, get_medications,
    get_allergies, get_labs, get_consultation, get_evidence,
    get_agent_evidence, run_agent_evidence
)

def test_evidence_agent_direct():
    print("\n--- 1. Testing EvidenceGatheringAgent directly ---")
    db = SessionLocal()
    try:
        agent = EvidenceGatheringAgent(db)
        package = agent.gather("P001")

        assert isinstance(package, EvidencePackage), "Result is not an EvidencePackage"
        assert package.patient_id == "P001", f"Expected P001, got {package.patient_id}"
        assert package.patient_name == "Synthetic Patient 001"
        assert package.patient_age == 45

        print(f"Total evidence items gathered: {package.summary.total_evidence_items}")
        print(f"Sources queried: {package.summary.sources_queried}")
        print(f"Counts by source: {package.summary.item_counts_by_source}")
        print(f"Counts by category: {package.summary.item_counts_by_category}")
        print(f"Unique entities: {package.summary.unique_entities_identified}")

        # Check all expected sources are present
        expected_sources = {"previous_note", "medication_database", "allergy_database", "laboratory_database", "consultation"}
        for s in expected_sources:
            assert s in package.summary.sources_queried, f"Missing source: {s}"

        # Check domain evidence map
        domain_map = package.domain_evidence_map
        assert "Metformin" in domain_map, "Metformin missing from domain map"
        assert "Drug B" in domain_map, "Drug B missing from domain map"
        assert "Penicillin" in domain_map, "Penicillin missing from domain map"
        assert "HbA1c" in domain_map, "HbA1c missing from domain map"
        assert "Creatinine" in domain_map, "Creatinine missing from domain map"

        print("\nDomain Evidence Breakdown:")
        for entity, items in domain_map.items():
            print(f"\n  [{entity}] ({len(items)} items):")
            for item in items:
                print(f"    - {item.source_date} [{item.source}] ({item.modality.value}): {item.raw_text}")
                print(f"      Attributes: {item.attributes}")

        # Verify Metformin has evidence across note, DB, and consultation
        met_sources = {item.source for item in domain_map["Metformin"]}
        assert "previous_note" in met_sources
        assert "medication_database" in met_sources
        assert "consultation" in met_sources

        # Verify Drug B has evidence across note, DB, and consultation
        drug_b_sources = {item.source for item in domain_map["Drug B"]}
        assert "previous_note" in drug_b_sources
        assert "medication_database" in drug_b_sources
        assert "consultation" in drug_b_sources

        # Crucial: verify that NO reconciliation was performed
        # Drug B in DB is 'discontinued', consultation reports 'reported_stopped'
        db_item = next(i for i in domain_map["Drug B"] if i.source == "medication_database")
        consult_item = next(i for i in domain_map["Drug B"] if i.source == "consultation")
        assert db_item.attributes.get("status") == "discontinued"
        assert consult_item.attributes.get("reported_status") == "reported_stopped"
        assert consult_item.attributes.get("reported_timing") == "approximately one week ago"

        print("\nDirect agent tests passed successfully!")
    finally:
        db.close()


def test_fastapi_endpoints_direct():
    print("\n--- 2. Testing FastAPI Route Handlers with Database Session ---")
    db = SessionLocal()
    try:
        # Home
        res_home = home()
        assert "message" in res_home
        print("GET /                          -> 200 OK")

        # Patient
        res_patient = get_patient("P001", db)
        assert res_patient.id == "P001"
        print("GET /patients/P001             -> 200 OK")

        # Notes
        res_notes = get_notes("P001", db)
        assert len(res_notes) >= 1
        print("GET /patients/P001/notes       -> 200 OK")

        # Medications
        res_meds = get_medications("P001", db)
        assert len(res_meds) >= 2
        print("GET /patients/P001/medications -> 200 OK")

        # Allergies
        res_allergies = get_allergies("P001", db)
        assert len(res_allergies) >= 1
        print("GET /patients/P001/allergies   -> 200 OK")

        # Labs
        res_labs = get_labs("P001", db)
        assert len(res_labs) >= 2
        print("GET /patients/P001/labs        -> 200 OK")

        # Consultation
        res_consult = get_consultation("P001", db)
        assert res_consult.patient_id == "P001"
        print("GET /patients/P001/consultation-> 200 OK")

        # Evidence (Phase 1.5B raw retrieval)
        res_ev = get_evidence("P001", db)
        assert res_ev["patient_id"] == "P001"
        assert len(res_ev["notes"]) >= 1
        assert len(res_ev["medications"]) >= 2
        assert len(res_ev["allergies"]) >= 1
        assert len(res_ev["labs"]) >= 2
        assert len(res_ev["consultations"]) >= 1
        print("GET /patients/P001/evidence    -> 200 OK")

        # Phase 2 Agent Evidence (GET)
        res_agent_get = get_agent_evidence("P001", db)
        assert isinstance(res_agent_get, EvidencePackage)
        assert res_agent_get.patient_id == "P001"
        assert res_agent_get.summary.total_evidence_items >= 10
        print(f"GET /patients/P001/agent/evidence -> 200 OK (Items gathered: {res_agent_get.summary.total_evidence_items})")

        # Phase 2 Agent Evidence (POST)
        res_agent_post = run_agent_evidence("P001", db)
        assert isinstance(res_agent_post, EvidencePackage)
        assert res_agent_post.patient_id == "P001"
        print(f"POST /patients/P001/agent/gather-evidence -> 200 OK")

        # Non-existent patient P999
        res_agent_999 = get_agent_evidence("P999", db)
        assert res_agent_999.patient_id == "P999"
        assert res_agent_999.summary.total_evidence_items == 0
        print("GET /patients/P999/agent/evidence -> 200 OK (Clean empty package for P999)")

        print("\nAll route handler tests passed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    test_evidence_agent_direct()
    test_fastapi_endpoints_direct()
    print("\n=== ALL PHASE 2 VERIFICATION TESTS COMPLETED SUCCESSFULLY ===")
