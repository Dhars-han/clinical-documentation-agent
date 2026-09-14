from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ReconciliationStatus(str, Enum):
    CONSISTENT = "consistent"
    RESOLVED = "resolved"
    CONFLICT = "conflict"
    UNRESOLVED = "unresolved"


class EvidenceReference(BaseModel):
    """Preserves full provenance of an individual piece of evidence used during reconciliation."""
    source: str = Field(..., description="Source origin of the evidence")
    source_date: Optional[str] = Field(None, description="Date or timestamp of the source record")
    raw_excerpt: str = Field(..., description="Exact quote or serialized record from the source")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Structured attributes extracted")
    modality: Optional[str] = Field(None, description="structured_record vs unstructured_text")

    @classmethod
    def from_item(cls, item) -> "EvidenceReference":
        mod_val = item.modality.value if hasattr(item.modality, "value") else str(item.modality)
        return cls(
            source=item.source,
            source_date=item.source_date,
            raw_excerpt=item.raw_text,
            attributes=item.attributes or {},
            modality=mod_val
        )


class ReconciliationResult(BaseModel):
    """Structured reconciliation verdict for a single clinical entity."""
    patient_id: str
    entity: str
    category: str
    status: ReconciliationStatus
    current_state: Optional[str] = Field(
        None,
        description="The safely established current clinical state, or null if in conflict/unresolved"
    )
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    reason: str = Field(..., description="Deterministic rationale explaining the reconciliation decision")
    supporting_evidence: List[EvidenceReference] = Field(default_factory=list)
    conflicting_evidence: List[EvidenceReference] = Field(default_factory=list)
    requires_human_review: bool = Field(..., description="Explicit escalation flag when autonomous resolution is unsafe")


class ReconciliationReport(BaseModel):
    """Aggregate reconciliation report for all clinical entities associated with a patient."""
    patient_id: str
    reconciled_at: str
    total_entities: int
    requires_human_review_count: int
    results: List[ReconciliationResult] = Field(default_factory=list)
