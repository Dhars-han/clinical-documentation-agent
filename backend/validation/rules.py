"""Deterministic Validation Rule Definitions for Phase 6 Validation & Verification Agent."""

from typing import Dict, NamedTuple


class ValidationRule(NamedTuple):
    rule_id: str
    category: str
    title: str
    description: str
    default_severity: str


RULES: Dict[str, ValidationRule] = {
    "RULE-001": ValidationRule(
        rule_id="RULE-001",
        category="evidence_grounding",
        title="Medication Evidence Grounding",
        description="Every documented medication must have valid supporting evidence references with source and excerpt.",
        default_severity="error"
    ),
    "RULE-002": ValidationRule(
        rule_id="RULE-002",
        category="evidence_grounding",
        title="Allergy Evidence Grounding",
        description="Every documented allergy must have valid supporting evidence references with source and excerpt.",
        default_severity="error"
    ),
    "RULE-003": ValidationRule(
        rule_id="RULE-003",
        category="evidence_grounding",
        title="Laboratory Evidence Grounding",
        description="Every documented laboratory result must have valid supporting evidence references with source and excerpt.",
        default_severity="error"
    ),
    "RULE-004": ValidationRule(
        rule_id="RULE-004",
        category="reconciliation_consistency",
        title="Reconciliation Status Consistency",
        description="Documentation medication status must agree with Phase 3 reconciliation results and current state.",
        default_severity="error"
    ),
    "RULE-005": ValidationRule(
        rule_id="RULE-005",
        category="conflict_preservation",
        title="Unresolved Conflict Preservation",
        description="Unresolved reconciliation conflicts must remain explicitly preserved in documentation unresolved_conflicts and trigger human review.",
        default_severity="error"
    ),
    "RULE-006": ValidationRule(
        rule_id="RULE-006",
        category="allergy_safety",
        title="Allergy Discrepancy Escalation",
        description="Allergy discrepancies (e.g. database allergy vs consultation denial) must trigger human review and must not be erased to 'no known allergies'.",
        default_severity="error"
    ),
    "RULE-007": ValidationRule(
        rule_id="RULE-007",
        category="rag_separation",
        title="RAG Reference Segregation",
        description="Clinical reference guidelines from RAG must not be cited as patient evidence or converted into patient facts.",
        default_severity="error"
    ),
    "RULE-008": ValidationRule(
        rule_id="RULE-008",
        category="hallucination",
        title="Unsupported Factual Claims / Hallucination Detection",
        description="Documentation must not contain medications, dosages, lab measurements, or allergens absent from or contradictory to underlying evidence.",
        default_severity="error"
    ),
    "RULE-009": ValidationRule(
        rule_id="RULE-009",
        category="uncertainty_handling",
        title="Uncertainty and Ambiguity Representation",
        description="Unknown, ambiguous, or conflicting clinical information must not be converted into definite, unflagged assertions.",
        default_severity="error"
    ),
    "RULE-010": ValidationRule(
        rule_id="RULE-010",
        category="safety_boundary",
        title="Autonomous Clinical Action Boundary",
        description="Follow-up actions must not contain autonomous diagnoses, prescribing, dosage adjustments, or clinical treatment decisions.",
        default_severity="error"
    ),
}
