import sys
import os
import json
from typing import Optional

try:
    from backend.database import SessionLocal
    from backend.models import Patient, Consultation
    from backend.evidence_agent import EvidenceGatheringAgent
    from backend.reconciliation.reconciler import ReconciliationService
    from backend.rag.service import get_rag_service
    from backend.documentation.schemas import ClinicalFollowUpRecord
    from backend.documentation.generator import FollowUpRecordGenerator
except ImportError:
    from ..database import SessionLocal
    from ..models import Patient, Consultation
    from ..evidence_agent import EvidenceGatheringAgent
    from ..reconciliation.reconciler import ReconciliationService
    from ..rag.service import get_rag_service
    from .schemas import ClinicalFollowUpRecord
    from .generator import FollowUpRecordGenerator


class DocumentationService:
    """Phase 5 Documentation Agent Service.
    
    Converts consultation transcript, Phase 2 evidence, Phase 3 reconciliation results,
    and Phase 4 RAG references into a structured, evidence-traceable follow-up record.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.evidence_agent = EvidenceGatheringAgent(db_session)
        self.reconciliation_service = ReconciliationService(db_session)
        self.rag_service = get_rag_service()

    def document(self, patient_id: str) -> ClinicalFollowUpRecord:
        """Executes full documentation pipeline for a patient."""
        # 1. Fetch Patient and Consultation metadata
        patient = self.db.query(Patient).filter(Patient.id == patient_id).first()
        patient_name = patient.name if patient else None
        patient_age = patient.age if patient else None

        consultation = self.db.query(Consultation).filter(
            Consultation.patient_id == patient_id
        ).order_by(Consultation.created_at.desc()).first()

        transcript = consultation.transcript if consultation else None

        # 2. Retrieve Phase 2 evidence package
        evidence_pkg = self.evidence_agent.gather(patient_id)

        # 3. Retrieve Phase 3 reconciliation report
        reconciliation_rpt = self.reconciliation_service.reconcile(patient_id)

        # 4. Retrieve Phase 4 clinical reference contexts
        rag_context_data = self.rag_service.get_patient_reference_context(patient_id, self.db)
        rag_contexts = rag_context_data.get("entity_guideline_contexts", [])

        # 5. Synthesize structured follow-up record
        return FollowUpRecordGenerator.generate(
            patient_id=patient_id,
            patient_name=patient_name,
            patient_age=patient_age,
            consultation_transcript=transcript,
            evidence_package=evidence_pkg,
            reconciliation_report=reconciliation_rpt,
            rag_contexts=rag_contexts
        )


def run_standalone(patient_id: str = "P001"):
    """CLI runner to test and inspect Documentation Agent output directly."""
    db = SessionLocal()
    try:
        service = DocumentationService(db)
        record = service.document(patient_id)
        print(f"\n=======================================================")
        print(f" Clinical Follow-up Record for Patient: {patient_id}")
        print(f" Patient: {record.patient_name} (Age: {record.patient_age})")
        print(f" Requires Human Review: {record.requires_human_review}")
        print(f" Unresolved Conflicts: {record.unresolved_conflict_count}")
        print(f"=======================================================\n")
        print(json.dumps(record.model_dump(), indent=2))
        return record
    finally:
        db.close()


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "P001"
    run_standalone(pid)
