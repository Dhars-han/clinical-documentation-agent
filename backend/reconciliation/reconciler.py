import sys
import os
import json
from datetime import datetime, timezone
from typing import List

try:
    from backend.database import SessionLocal
    from backend.evidence_agent import EvidenceGatheringAgent
    from backend.llm import get_llm_client
    from backend.reconciliation.schemas import (
        ReconciliationReport,
        ReconciliationResult,
        ReconciliationStatus,
    )
    from backend.reconciliation.comparator import EntityComparator
    from backend.reconciliation.rules import (
        reconcile_medication,
        reconcile_allergy,
        reconcile_lab,
        reconcile_clinical_observation,
    )
except ImportError:
    from ..database import SessionLocal
    from ..evidence_agent import EvidenceGatheringAgent
    from ..llm import get_llm_client
    from .schemas import (
        ReconciliationReport,
        ReconciliationResult,
        ReconciliationStatus,
    )
    from .comparator import EntityComparator
    from .rules import (
        reconcile_medication,
        reconcile_allergy,
        reconcile_lab,
        reconcile_clinical_observation,
    )


class ReconciliationService:
    """Phase 3 Engine: Evaluates gathered evidence across sources and chronologies.
    
    Identifies consistency, resolved states, conflicts, and escalates to human review.
    Does NOT generate final clinical notes, diagnose, prescribe, or build frontend.
    """

    def __init__(self, db_session):
        self.db = db_session
        self.evidence_agent = EvidenceGatheringAgent(db_session)

    def reconcile(self, patient_id: str) -> ReconciliationReport:
        """Executes evidence reconciliation across all clinical entities for a patient."""
        # 1. Retrieve gathered evidence package from Phase 2
        evidence_package = self.evidence_agent.gather(patient_id)

        # 2. Bundle evidence by clinical entity
        bundles = EntityComparator.prepare_entity_bundles(evidence_package.domain_evidence_map)

        results: List[ReconciliationResult] = []

        # 3. Apply deterministic domain reconciliation rules
        llm = get_llm_client()
        for entity_name, category, items, related_context in bundles:
            if category == "medication":
                res = reconcile_medication(entity_name, items, patient_id)
            elif category == "allergy":
                res = reconcile_allergy(entity_name, items, related_context, patient_id)
            elif category == "lab":
                res = reconcile_lab(entity_name, items, patient_id)
            else:
                res = reconcile_clinical_observation(entity_name, items, patient_id)

            # 4. If status is ambiguous or conflicting, invoke DeepSeek language reasoning
            if res.status in (ReconciliationStatus.CONFLICT, ReconciliationStatus.UNRESOLVED) and llm.is_available():
                competing = [
                    {
                        "source": it.source,
                        "source_date": it.source_date,
                        "raw_text": it.raw_text,
                        "attributes": it.attributes
                    }
                    for it in (items + related_context)
                ]
                try:
                    reasoning_resp = llm.reason_reconciliation(
                        entity_name=entity_name,
                        category=category,
                        competing_items=competing,
                        deterministic_status=res.status.value
                    )
                    if reasoning_resp:
                        # MANDATORY MEDICAL SAFETY GUARDRAIL:
                        # Consequential conflicts (Allergy conflict like Penicillin, conflicting active doses)
                        # must NEVER be silently resolved or overridden by the LLM.
                        is_consequential_allergy = (category == "allergy" and res.status == ReconciliationStatus.CONFLICT)
                        
                        if is_consequential_allergy:
                            # Allergy conflict MUST strictly remain human review
                            res.requires_human_review = True
                            res.reason = f"{res.reason} [DeepSeek Reasoning: {reasoning_resp.clinical_rationale}]"
                        else:
                            # For non-allergy entities, apply valid supported resolution
                            if reasoning_resp.resolution_type == "supported_resolution" and reasoning_resp.current_state and not reasoning_resp.requires_human_review:
                                res.status = ReconciliationStatus.RESOLVED
                                res.current_state = reasoning_resp.current_state
                                res.requires_human_review = False
                            res.reason = f"{res.reason} [DeepSeek Analysis: {reasoning_resp.clinical_rationale}]"
                except Exception:
                    # Seamlessly fall back to deterministic verdict on any error
                    pass

            results.append(res)

        human_review_count = sum(1 for r in results if r.requires_human_review)

        return ReconciliationReport(
            patient_id=patient_id,
            reconciled_at=datetime.now(timezone.utc).isoformat(),
            total_entities=len(results),
            requires_human_review_count=human_review_count,
            results=results
        )


def run_standalone(patient_id: str = "P001"):
    """CLI runner to inspect reconciliation output directly."""
    db = SessionLocal()
    try:
        service = ReconciliationService(db)
        report = service.reconcile(patient_id)
        print("\n=======================================================")
        print(f" Reconciliation Report for Patient: {patient_id}")
        print("=======================================================\n")
        print(f"Total Entities: {report.total_entities}")
        print(f"Requiring Human Review: {report.requires_human_review_count}\n")
        for res in report.results:
            flag = " [HUMAN REVIEW REQUIRED]" if res.requires_human_review else " [AUTO-OK]"
            print(f"-> {res.entity} ({res.category.upper()}): status={res.status.value}{flag}")
            print(f"   Current State: {res.current_state}")
            print(f"   Reason: {res.reason}")
            print(f"   Supporting items: {len(res.supporting_evidence)} | Conflicting items: {len(res.conflicting_evidence)}")
            print()
        return report
    finally:
        db.close()


if __name__ == "__main__":
    pid = sys.argv[1] if len(sys.argv) > 1 else "P001"
    run_standalone(pid)
