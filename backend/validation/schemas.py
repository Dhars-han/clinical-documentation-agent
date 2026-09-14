from typing import List, Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Represents a specific validation finding, failure, or safety escalation."""
    category: str = Field(..., description="Validation category (e.g. evidence_grounding, hallucination, safety_boundary)")
    severity: str = Field(..., description="Severity level: 'error', 'warning', or 'info'")
    message: str = Field(..., description="Detailed explanation of the issue or discrepancy")
    entity: Optional[str] = Field(None, description="Clinical entity involved, if applicable")
    rule_id: Optional[str] = Field(None, description="Identifiable validation rule ID (e.g. RULE-001)")
    evidence_references: List[Any] = Field(default_factory=list, description="Relevant evidence references or links")


class ValidationResult(BaseModel):
    """Machine-readable comprehensive verification verdict for a clinical follow-up record."""
    patient_id: str
    validation_status: str = Field(..., description="'passed', 'failed', or 'requires_human_review'")
    passed: bool = Field(..., description="True if no fatal errors were detected during validation")
    issues: List[ValidationIssue] = Field(default_factory=list)
    checks_performed: List[str] = Field(default_factory=list)
    evidence_grounding_passed: bool = True
    reconciliation_consistency_passed: bool = True
    conflict_preservation_passed: bool = True
    rag_separation_passed: bool = True
    uncertainty_handling_passed: bool = True
    safety_boundary_passed: bool = True
    requires_human_review: bool = Field(..., description="Escalation flag indicating clinical human review is required")
    validated_at: str
