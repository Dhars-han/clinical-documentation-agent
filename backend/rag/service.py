import os
import sys
from typing import Dict, List, Optional, Any

try:
    from backend.rag.schemas import RAGQuery, RAGResponse, SearchResult, DocumentSummary, DocumentChunk
    from backend.rag.document_loader import DocumentLoader
    from backend.rag.vector_store import LocalVectorStore
    from backend.reconciliation.reconciler import ReconciliationService
except ImportError:
    from .schemas import RAGQuery, RAGResponse, SearchResult, DocumentSummary, DocumentChunk
    from .document_loader import DocumentLoader
    from .vector_store import LocalVectorStore
    from ..reconciliation.reconciler import ReconciliationService


class ClinicalRAGService:
    """Phase 4 Engine: Clinical Reference RAG and local vector-search service.
    
    Provides accurate reference document retrieval with full provenance.
    Strictly does NOT generate SOAP notes, diagnose, prescribe, or make clinical decisions.
    """

    _instance = None

    def __init__(self, data_dir: Optional[str] = None):
        self.vector_store = LocalVectorStore()

        # Locate clinical docs directory
        if data_dir is None:
            # Check relative to project root
            backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            project_root = os.path.dirname(backend_dir)
            data_dir = os.path.join(project_root, "data", "clinical_docs")

        self.data_dir = data_dir
        self.ingest_default_docs()

    def ingest_default_docs(self) -> int:
        """Loads and indexes all clinical guideline documents from the data directory."""
        if not os.path.exists(self.data_dir):
            return 0

        chunks = DocumentLoader.load_directory(self.data_dir)
        self.vector_store.clear()
        self.vector_store.add_chunks(chunks)
        return len(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        score_threshold: float = 0.15,
        document_id: Optional[str] = None
    ) -> RAGResponse:
        """Performs vector search across indexed clinical reference documents."""
        results = self.vector_store.search(
            query=query_text,
            top_k=top_k,
            score_threshold=score_threshold,
            document_id=document_id
        )

        return RAGResponse(
            query=query_text,
            total_results=len(results),
            results=results
        )

    def get_patient_reference_context(self, patient_id: str, db_session) -> Dict[str, Any]:
        """Gathers relevant clinical reference guidelines for a patient's reconciled clinical entities.
        
        Does NOT diagnose, prescribe, or generate notes.
        """
        reconciler = ReconciliationService(db_session)
        report = reconciler.reconcile(patient_id)

        entity_contexts = []
        for result in report.results:
            # Query guidelines for this entity
            entity_query = f"{result.entity} clinical guidelines and recommendations"
            retrieval = self.query(entity_query, top_k=2, score_threshold=0.15)

            entity_contexts.append({
                "entity": result.entity,
                "category": result.category,
                "status": result.status.value,
                "current_state": result.current_state,
                "requires_human_review": result.requires_human_review,
                "relevant_guideline_chunks": [r.model_dump() for r in retrieval.results]
            })

        return {
            "patient_id": patient_id,
            "total_entities_evaluated": len(report.results),
            "entity_guideline_contexts": entity_contexts
        }

    def list_documents(self) -> List[DocumentSummary]:
        """Lists all ingested reference documents and chunk counts."""
        return self.vector_store.get_document_summaries()


# Global singleton instance for easy import across endpoints
_rag_service: Optional[ClinicalRAGService] = None


def get_rag_service() -> ClinicalRAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = ClinicalRAGService()
    return _rag_service


def run_standalone(query: str = "Metformin dosing and renal monitoring"):
    """CLI runner to test clinical RAG queries directly."""
    service = get_rag_service()
    docs = service.list_documents()
    print(f"\n=======================================================")
    print(f" Clinical RAG Service Standalone Query")
    print(f" Total Ingested Reference Documents: {len(docs)}")
    for d in docs:
        print(f"   * [{d.document_id}] {d.title} ({d.chunk_count} chunks)")
    print(f"=======================================================\n")
    print(f"Query: '{query}'\n")

    resp = service.query(query, top_k=3, score_threshold=0.15)
    print(f"Results returned: {resp.total_results}\n")
    for idx, r in enumerate(resp.results, 1):
        print(f"[{idx}] Score: {r.score} | Document: {r.document_id} - {r.title}")
        print(f"    Source: {r.source} | Section: {r.section} ({r.publication_date})")
        print(f"    Snippet: {r.snippet[:180]}...\n")


if __name__ == "__main__":
    q = sys.argv[1] if len(sys.argv) > 1 else "Metformin dosing and renal monitoring"
    run_standalone(q)
