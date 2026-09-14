from typing import Dict, List, Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class EvidenceLink(BaseModel):
    """Preserves full provenance of clinical evidence supporting a documented statement."""
    claim: str = Field(..., description="The clinical claim or observation supported by this evidence")
    source: str = Field(..., description="Source origin (e.g. consultation, medication_database, previous_note)")
    source_date: Optional[str] = Field(None, description="Date or timestamp of the source record")
    raw_excerpt: str = Field(..., description="Exact textual excerpt or quote from the source record")


class DocumentedMedication(BaseModel):
    """Structured documentation for a medication evaluated through reconciliation."""
    name: str
    status: str = Field(..., description="Current status: active, discontinued, conflicting, or unknown")
    regimen: Optional[str] = Field(None, description="Reported dose and frequency, or null if unknown")
    reconciliation_status: str = Field(..., description="consistent, resolved, conflict, or unresolved")
    requires_human_review: bool
    evidence_references: List[EvidenceLink] = Field(default_factory=list)


class DocumentedAllergy(BaseModel):
    """Structured documentation for an allergy record preserving conflicts and safety flags."""
    allergen: str
    status: str = Field(..., description="documented, conflicting, no_known_allergies, or unknown")
    documented_reaction: Optional[str] = Field(None, description="Reaction recorded in database, or unknown")
    reported_statement: Optional[str] = Field(None, description="Statement reported during consultation")
    conflict_details: Optional[str] = Field(None, description="Detailed explanation of any conflict")
    requires_human_review: bool
    evidence_references: List[EvidenceLink] = Field(default_factory=list)


class DocumentedLab(BaseModel):
    """Structured documentation for an observed laboratory measurement."""
    test_name: str
    value: str
    unit: str
    date: Optional[str] = None
    source: str
    evidence_references: List[EvidenceLink] = Field(default_factory=list)


class DocumentedChange(BaseModel):
    """Explicit record of clinical changes identified between prior records and current consultation."""
    entity: str
    change_type: str = Field(..., description="discontinuation, dose_adjustment, new_report, etc.")
    description: str
    timeline: Optional[str] = None
    evidence_references: List[EvidenceLink] = Field(default_factory=list)


class FollowUpAction(BaseModel):
    """Non-prescriptive administrative or clinical follow-up coordination item."""
    action_type: str = Field(..., description="clinical_review, lab_monitoring, care_coordination")
    description: str
    urgency: str = Field(default="routine", description="routine vs high")
    requires_human_review: bool = False


class ClinicalReferenceLink(BaseModel):
    """Supporting clinical reference guideline from Phase 4 RAG, strictly segregated from patient facts."""
    entity: str
    document_id: str
    title: str
    source_organization: str
    section: str
    publication_date: Optional[str] = None
    snippet: str
    relevance_score: float


class ClinicalFollowUpRecord(BaseModel):
    """Machine-readable clinical follow-up record integrating Phase 1–4 outputs."""
    patient_id: str
    patient_name: Optional[str] = None
    patient_age: Optional[int] = None
    generated_at: str
    consultation_summary: str = Field(..., description="Factual narrative derived strictly from transcript")
    medications: List[DocumentedMedication] = Field(default_factory=list)
    allergies: List[DocumentedAllergy] = Field(default_factory=list)
    relevant_labs: List[DocumentedLab] = Field(default_factory=list)
    documented_changes: List[DocumentedChange] = Field(default_factory=list)
    unresolved_conflicts: List[str] = Field(default_factory=list)
    follow_up_actions: List[FollowUpAction] = Field(default_factory=list)
    clinical_references: List[ClinicalReferenceLink] = Field(default_factory=list)
    requires_human_review: bool = Field(..., description="Overall escalation flag for the encounter")
    unresolved_conflict_count: int = 0
