import sys
import os
import json

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database import SessionLocal
from backend.rag.document_loader import DocumentLoader
from backend.rag.vector_store import LocalVectorStore
from backend.rag.service import ClinicalRAGService, get_rag_service
from backend.rag.schemas import RAGQuery, RAGResponse, SearchResult
from backend.main import (
    app, query_clinical_rag, list_rag_documents, get_patient_rag_context,
    reconcile_patient_evidence, get_agent_evidence
)


def test_1_document_ingestion():
    print("\n--- Test 1: Document Ingestion and Chunking ---")
    data_dir = os.path.join(project_root, "data", "clinical_docs")
    chunks = DocumentLoader.load_directory(data_dir)

    assert len(chunks) >= 15, f"Expected at least 15 chunks, got {len(chunks)}"

    doc_ids = {c.document_id for c in chunks}
    expected_docs = {
        "DOC-ADA-METFORMIN-2026",
        "DOC-AAAAI-PENICILLIN-2025",
        "DOC-ENDO-HBA1C-2026",
        "DOC-KDIGO-CREATININE-2025",
        "DOC-DEPRESCRIBING-SAFETY-2026"
    }
    for ed in expected_docs:
        assert ed in doc_ids, f"Missing expected document ID: {ed}"

    # Verify vector store indexing
    store = LocalVectorStore()
    store.add_chunks(chunks)
    summaries = store.get_document_summaries()
    assert len(summaries) == 5, f"Expected 5 document summaries, got {len(summaries)}"

    print(f"PASS: Successfully ingested {len(chunks)} chunks across {len(summaries)} reference documents:")
    for s in summaries:
        print(f"      - [{s.document_id}] '{s.title}' ({s.chunk_count} chunks, Source: {s.source})")


def test_2_clinical_retrieval():
    print("\n--- Test 2: Clinical Retrieval Quality ---")
    service = get_rag_service()

    queries = [
        ("Metformin dosing titration and renal monitoring eGFR", "DOC-ADA-METFORMIN-2026"),
        ("Penicillin allergy evaluation and skin testing challenge", "DOC-AAAAI-PENICILLIN-2025"),
        ("Hemoglobin HbA1c target goals and glycemic monitoring frequency", "DOC-ENDO-HBA1C-2026"),
        ("Serum creatinine clearance and renal function monitoring", "DOC-KDIGO-CREATININE-2025"),
        ("Patient-initiated medication cessation and deprescribing", "DOC-DEPRESCRIBING-SAFETY-2026")
    ]

    for q, expected_doc_id in queries:
        resp = service.query(q, top_k=3, score_threshold=0.15)
        assert resp.total_results > 0, f"Query '{q}' returned 0 results"
        top_res = resp.results[0]
        assert top_res.document_id == expected_doc_id, f"Expected top match {expected_doc_id}, got {top_res.document_id}"
        assert top_res.score >= 0.15, f"Expected score >= 0.15, got {top_res.score}"
        print(f"PASS: Query: '{q[:40]}...' -> Top Match: [{top_res.document_id}] {top_res.section} (Score: {top_res.score})")


def test_3_provenance_preservation():
    print("\n--- Test 3: Provenance Preservation ---")
    service = get_rag_service()
    resp = service.query("Penicillin allergy electronic health record discrepancy", top_k=2)

    assert resp.total_results > 0
    for r in resp.results:
        assert r.chunk_id, "Missing chunk_id"
        assert r.document_id, "Missing document_id"
        assert r.title, "Missing title"
        assert r.source, "Missing source"
        assert r.section, "Missing section"
        assert r.publication_date, "Missing publication_date"
        assert r.snippet, "Missing snippet text"
        assert 0.0 <= r.score <= 1.0, f"Score out of range: {r.score}"

        print(f"PASS: Chunk [{r.chunk_id}] retains full provenance:")
        print(f"      Title: {r.title}")
        print(f"      Source: {r.source}")
        print(f"      Section: {r.section}")
        print(f"      Date: {r.publication_date}")
        print(f"      Score: {r.score}")


def test_4_irrelevant_query_filtering():
    print("\n--- Test 4: Irrelevant Query Filtering (Rejection Threshold) ---")
    service = get_rag_service()

    irrelevant_queries = [
        "How to bake a chocolate cake with cream cheese frosting",
        "Quantum mechanics black hole astrophysics event horizon",
        "Automotive manual transmission clutch replacement cost",
        "Python django react frontend tutorial",
        "World cup football soccer championship final score"
    ]

    for iq in irrelevant_queries:
        resp = service.query(iq, top_k=3, score_threshold=0.15)
        assert resp.total_results == 0, f"Irrelevant query '{iq}' should return 0 results, got {resp.total_results}"
        print(f"PASS: Irrelevant query rejected: '{iq}' -> {resp.total_results} results")


def test_5_patient_context_and_api():
    print("\n--- Test 5: Patient Context Endpoint and API Handlers ---")
    db = SessionLocal()
    try:
        # 1. Test POST /rag/query
        q_obj = RAGQuery(query="Metformin kidney contraindication", top_k=2, score_threshold=0.15)
        resp_q = query_clinical_rag(q_obj)
        assert isinstance(resp_q, RAGResponse)
        assert resp_q.total_results >= 1
        print(f"PASS: POST /rag/query returned {resp_q.total_results} results")

        # 2. Test GET /rag/documents
        docs = list_rag_documents()
        assert len(docs) == 5
        print(f"PASS: GET /rag/documents returned {len(docs)} document summaries")

        # 3. Test GET /patients/{patient_id}/rag/context
        p_ctx = get_patient_rag_context("P001", db)
        assert p_ctx["patient_id"] == "P001"
        assert p_ctx["total_entities_evaluated"] >= 5
        assert len(p_ctx["entity_guideline_contexts"]) >= 5

        # Check that Metformin and Penicillin got relevant guideline chunks
        met_ctx = next(c for c in p_ctx["entity_guideline_contexts"] if c["entity"] == "Metformin")
        assert len(met_ctx["relevant_guideline_chunks"]) > 0
        assert any("DOC-ADA-METFORMIN" in chunk["document_id"] for chunk in met_ctx["relevant_guideline_chunks"])

        pen_ctx = next(c for c in p_ctx["entity_guideline_contexts"] if c["entity"] == "Penicillin")
        assert len(pen_ctx["relevant_guideline_chunks"]) > 0
        assert any("DOC-AAAAI-PENICILLIN" in chunk["document_id"] for chunk in pen_ctx["relevant_guideline_chunks"])

        print("PASS: GET /patients/P001/rag/context returned clinical contexts for all patient entities:")
        for c in p_ctx["entity_guideline_contexts"]:
            print(f"      * {c['entity']} ({c['category']}) -> {len(c['relevant_guideline_chunks'])} reference chunks retrieved")

        # 4. Phase 1-3 Regression Verification: Reconciliation & Evidence endpoints
        rec = reconcile_patient_evidence("P001", db)
        assert rec.patient_id == "P001"
        assert rec.requires_human_review_count == 1  # Penicillin allergy conflict strictly preserved
        ev = get_agent_evidence("P001", db)
        assert ev.patient_id == "P001"
        assert len(ev.items) >= 11

        print("PASS: Phase 1–3 integrity verified with ZERO regression!")
    finally:
        db.close()


if __name__ == "__main__":
    test_1_document_ingestion()
    test_2_clinical_retrieval()
    test_3_provenance_preservation()
    test_4_irrelevant_query_filtering()
    test_5_patient_context_and_api()
    print("\n=======================================================")
    print(" ALL 5 PHASE 4 RAG TESTS PASSED 100%!")
    print("=======================================================")
