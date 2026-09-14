from typing import Dict, List, Optional, Any
# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a discrete indexed section of a clinical reference document."""
    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document identifier")
    title: str = Field(..., description="Guideline or document title")
    source: str = Field(..., description="Issuing organization or formal guideline citation")
    section: str = Field(..., description="Section title or topic")
    publication_date: Optional[str] = Field(None, description="Date or year of publication")
    content: str = Field(..., description="Full text content of the chunk")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provenance attributes")


class SearchResult(BaseModel):
    """A retrieved reference document chunk with similarity score and provenance."""
    chunk_id: str
    document_id: str
    title: str
    source: str
    section: str
    publication_date: Optional[str] = None
    snippet: str
    score: float = Field(..., description="Similarity score between query and document chunk (0.0 to 1.0)")
    matched_terms: List[str] = Field(default_factory=list, description="Key terms matched in query")


class RAGQuery(BaseModel):
    """Input query request for clinical reference retrieval."""
    query: str = Field(..., description="Natural language clinical question or search query")
    top_k: int = Field(default=3, ge=1, le=20, description="Maximum number of chunks to return")
    score_threshold: float = Field(
        default=0.15,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score threshold below which chunks are filtered out"
    )
    document_id: Optional[str] = Field(None, description="Optional filter by document ID")


class RAGResponse(BaseModel):
    """Output payload from clinical RAG retrieval."""
    query: str
    total_results: int
    results: List[SearchResult] = Field(default_factory=list)


class DocumentSummary(BaseModel):
    """Summary of an ingested clinical reference document."""
    document_id: str
    title: str
    source: str
    publication_date: Optional[str] = None
    chunk_count: int
