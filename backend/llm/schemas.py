"""Pydantic schemas for DeepSeek structured LLM extraction, reasoning, and documentation."""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ExtractedClinicalEntity(BaseModel):
    """Represents a single clinical entity extracted from unstructured text."""
    entity_name: str = Field(..., description="Name of the medication, allergy, lab test, or clinical finding")
    category: str = Field(..., description="Category: medication, allergy, lab, or clinical_observation")
    event_action: Optional[str] = Field(None, description="Action or status: taking, stopped, started, denied, affirmed, tested, etc.")
    value: Optional[str] = Field(None, description="Observed dose, measurement, reaction, or value (e.g. 500 mg, 7.1%, rash)")
    time_reference: Optional[str] = Field(None, description="Reported timing or timeline reference (e.g. approximately one week ago, daily)")
    source_statement: str = Field(..., description="Exact or verbatim source sentence containing the statement")
    certainty: str = Field("definite", description="Certainty level: definite, probable, possible, uncertain, or denied")
    ambiguity: Optional[str] = Field(None, description="Description of any ambiguity, contradiction, or vagueness detected in the statement")
    relevant_context: Optional[str] = Field(None, description="Additional clinical context or surrounding details")


class EvidenceExtractionResponse(BaseModel):
    """Structured response for DeepSeek evidence understanding."""
    entities: List[ExtractedClinicalEntity] = Field(default_factory=list)
    reasoning_summary: Optional[str] = Field(None, description="Brief summary of language reasoning applied during extraction")


class ReconciliationReasoningRequest(BaseModel):
    """Context passed to DeepSeek for ambiguous or conflicting reconciliation scenarios."""
    entity_name: str
    category: str
    competing_evidence: List[Dict[str, Any]]
    deterministic_status: str


class ReconciliationReasoningResponse(BaseModel):
    """Structured reasoning output from DeepSeek evaluating competing clinical evidence."""
    entity_name: str
    category: str
    recommended_status: str = Field(..., description="consistent, resolved, conflict, or unresolved")
    current_state: Optional[str] = Field(None, description="Current clinically established state or null if conflicting/uncertain")
    resolution_type: str = Field(..., description="supported_resolution, unresolved_conflict, or insufficient_evidence")
    clinical_rationale: str = Field(..., description="Detailed explanation of evidence progression, timeline, and sources")
    requires_human_review: bool = Field(..., description="True if consequential uncertainty or safety boundary mandates human review")
    confidence: float = Field(default=0.8, description="Confidence score in the reasoning analysis (0.0 to 1.0)")


class DocumentationGenerationResponse(BaseModel):
    """Structured output from DeepSeek generating grounded clinical follow-up documentation."""
    consultation_summary: str = Field(..., description="Professional, evidence-grounded summary of the consultation encounter")
    synthesized_notes: Optional[str] = Field(None, description="Additional contextual follow-up notes grounded in verified facts")
    change_descriptions: Dict[str, str] = Field(default_factory=dict, description="Explanations of medication changes keyed by entity name")
    follow_up_recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Non-prescriptive care coordination and safety verification actions")
