"""DeepSeek Language Reasoning Module for Autonomous Clinical Documentation."""

from .client import DeepSeekClient, get_llm_client
from .schemas import (
    ExtractedClinicalEntity,
    EvidenceExtractionResponse,
    ReconciliationReasoningRequest,
    ReconciliationReasoningResponse,
    DocumentationGenerationResponse,
)

__all__ = [
    "DeepSeekClient",
    "get_llm_client",
    "ExtractedClinicalEntity",
    "EvidenceExtractionResponse",
    "ReconciliationReasoningRequest",
    "ReconciliationReasoningResponse",
    "DocumentationGenerationResponse",
]
