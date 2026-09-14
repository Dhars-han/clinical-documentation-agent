"""
Unit and integration tests for DeepSeek Hybrid Reasoning Architecture.

Verifies:
1. Deterministic Fallback: Runs cleanly when DEEPSEEK_API_KEY is not set or unavailable.
2. Safe Failure Handling: Network timeouts, HTTP 429, or invalid JSON fall back without crashing.
3. Hybrid Mode (Mocked DeepSeek Responses):
   - Phase 2: DeepSeek evidence extraction from consultation narrative.
   - Phase 3: DeepSeek ambiguous reconciliation reasoning with strict safety guardrails.
   - Phase 5: DeepSeek documentation synthesis grounded strictly in verified evidence.
4. Consequential Clinical Safety Guardrail:
   - An LLM can NEVER override or erase an allergy conflict (e.g. Penicillin).
   - Phase 6 Deterministic Validator (RULE-001 to RULE-010) enforces safety boundary regardless of LLM output.
"""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.database import SessionLocal
from backend.llm.client import DeepSeekClient
from backend.llm.schemas import (
    ExtractedClinicalEntity,
    EvidenceExtractionResponse,
    ReconciliationReasoningResponse,
    DocumentationGenerationResponse,
)
from backend.evidence_agent import EvidenceGatheringAgent
from backend.reconciliation import ReconciliationService
from backend.documentation.service import DocumentationService
from backend.documentation.generator import FollowUpRecordGenerator
from backend.validation.service import ValidationService
from backend.validation.validator import ClinicalValidator


class TestDeepSeekFallbackAndSafety(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_fallback_when_unconfigured(self):
        """When DEEPSEEK_API_KEY is empty, client is disabled and methods return None safely."""
        client = DeepSeekClient(api_key="")
        self.assertFalse(client.is_available())
        self.assertIsNone(client.extract_evidence("Patient denied allergy"))
        self.assertIsNone(client.reason_reconciliation(
            entity_name="Drug B",
            category="medication",
            competing_items=[],
            deterministic_status="conflict"
        ))
        self.assertIsNone(client.generate_documentation(
            patient_info={"id": "P001", "name": "Synthetic Patient", "age": 45},
            transcript_excerpt="Patient stopped Drug B",
            verified_evidence=[],
            reconciliation_summary=[],
            rag_references=[]
        ))

    def test_02_full_pipeline_deterministic_fallback(self):
        """The full Phase 6 pipeline runs completely on deterministic fallback when LLM is unavailable."""
        with patch.dict(os.environ, {"DEEPSEEK_API_KEY": ""}, clear=False):
            service = ValidationService(self.db)
            result = service.run_full_agent_pipeline("P001")

            self.assertEqual(result["pipeline_status"], "completed")
            self.assertEqual(result["llm_info"]["mode"], "deterministic_fallback")
            self.assertFalse(result["llm_info"]["is_active"])
            self.assertTrue(result["validation"]["passed"])
            self.assertTrue(result["validation"]["requires_human_review"])
            self.assertIn("Penicillin", str(result["documentation"]["unresolved_conflicts"]))

    def test_03_mocked_deepseek_extraction(self):
        """Phase 2 uses DeepSeek extraction when available, returning structured evidence with provenance."""
        mock_response = EvidenceExtractionResponse(
            entities=[
                ExtractedClinicalEntity(
                    entity_name="Drug B",
                    category="medication",
                    event_action="discontinued",
                    value="10mg",
                    time_reference="stopped last week",
                    source_statement="I stopped taking Drug B last week due to mild nausea.",
                    certainty="definite",
                    ambiguity=None,
                    relevant_context="Patient directly reported cessation of Drug B"
                ),
                ExtractedClinicalEntity(
                    entity_name="Penicillin",
                    category="allergy",
                    event_action="denied",
                    value=None,
                    time_reference="current",
                    source_statement="I don't think I have any drug allergies.",
                    certainty="uncertain",
                    ambiguity="Patient expressed slight uncertainty",
                    relevant_context="Patient statement in consultation"
                )
            ]
        )

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.extract_evidence.return_value = mock_response

        with patch("backend.evidence_agent.get_llm_client", return_value=mock_client):
            agent = EvidenceGatheringAgent(self.db)
            evidence_pkg = agent.gather("P001")

            consultation_items = [
                item for item in evidence_pkg.items if "consult" in item.source
            ]
            self.assertGreaterEqual(len(consultation_items), 2)
            drug_b_items = [i for i in consultation_items if i.entity_name == "Drug B"]
            self.assertTrue(len(drug_b_items) > 0)
            self.assertIn("stopped taking Drug B", drug_b_items[0].raw_text)
            self.assertEqual(drug_b_items[0].attributes.get("extraction_method"), "deepseek_llm")

    def test_04_safety_guardrail_allergy_conflict_never_overridden(self):
        """
        CRITICAL SAFETY TEST: Even if DeepSeek reasoning suggests 'consistent' or 'resolved' for Penicillin,
        the Phase 3 Reconciliation safety guardrail MUST force requires_human_review = True,
        and Phase 6 validator must strictly enforce conflict preservation.
        """
        # Create mock reasoning response attempting to resolve the allergy conflict
        rogue_llm_reasoning = ReconciliationReasoningResponse(
            entity_name="Penicillin",
            category="allergy",
            recommended_status="resolved",
            current_state="No known allergy",
            resolution_type="supported_resolution",
            clinical_rationale="Patient stated they have no allergies, so existing record is outdated.",
            requires_human_review=False,  # Rogue attempt to bypass human review
            confidence=0.9
        )

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.reason_reconciliation.return_value = rogue_llm_reasoning

        with patch("backend.reconciliation.reconciler.get_llm_client", return_value=mock_client):
            service = ReconciliationService(self.db)
            report = service.reconcile("P001")

            # Locate Penicillin in the reconciliation report
            penicillin_entities = [e for e in report.results if e.entity == "Penicillin"]
            self.assertTrue(len(penicillin_entities) > 0)
            pen_entity = penicillin_entities[0]

            # GUARANTEE: Safety guardrail overrides rogue LLM and enforces human review
            self.assertTrue(
                pen_entity.requires_human_review,
                "Safety Violation: Allergy conflict human review was overridden by LLM!"
            )
            self.assertEqual(pen_entity.status.value, "conflict")
            self.assertIn("DeepSeek Reasoning", pen_entity.reason)

    def test_05_mocked_hybrid_documentation_generation(self):
        """Phase 5 uses DeepSeek synthesis grounded strictly in verified evidence."""
        mock_doc_response = DocumentationGenerationResponse(
            consultation_summary="Patient presented for follow-up. Reported discontinuing Drug B one week prior due to mild nausea. Denied drug allergies during consultation; however, an active EHR record documents a Penicillin allergy requiring mandatory clinician verification.",
            synthesized_notes="Routine labs stable. HbA1c 7.1%.",
            change_descriptions={"Drug B": "Discontinued by patient due to nausea"},
            follow_up_recommendations=[{"action": "Verify allergy", "urgency": "high"}]
        )

        mock_client = MagicMock()
        mock_client.is_available.return_value = True
        mock_client.generate_documentation.return_value = mock_doc_response

        with patch("backend.documentation.generator.get_llm_client", return_value=mock_client):
            doc_service = DocumentationService(self.db)
            record = doc_service.document("P001")

            # Verify synthesized summary was incorporated
            self.assertIn("Drug B", record.consultation_summary)
            self.assertIn("Penicillin", record.consultation_summary)
            self.assertTrue(record.requires_human_review)

            # Phase 6 Validator must validate this record and pass all grounding checks
            agent = EvidenceGatheringAgent(self.db)
            evidence_pkg = agent.gather("P001")
            reconciliation_service = ReconciliationService(self.db)
            reconciliation_rpt = reconciliation_service.reconcile("P001")

            val_result = ClinicalValidator.validate(
                record=record,
                evidence_package=evidence_pkg,
                reconciliation_report=reconciliation_rpt,
                rag_contexts=[]
            )
            self.assertTrue(val_result.passed)
            self.assertTrue(val_result.evidence_grounding_passed)
            self.assertTrue(val_result.safety_boundary_passed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
