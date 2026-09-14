import re
import math
from collections import Counter
from typing import Dict, List, Optional, Set, Tuple

try:
    from backend.rag.schemas import DocumentChunk, SearchResult, DocumentSummary
except ImportError:
    from .schemas import DocumentChunk, SearchResult, DocumentSummary


# Clinical and common English stop words to filter noise
STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can", "can't", "cannot", "could",
    "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from",
    "further", "had", "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own",
    "same", "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
    "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you",
    "your", "yours", "yourself", "yourselves"
}


class LocalVectorStore:
    """Lightweight, deterministic, local vector space engine using TF-IDF and Cosine Similarity.
    
    Zero external C-dependencies; runs cross-platform with full provenance tracking.
    """

    def __init__(self):
        self.chunks: List[DocumentChunk] = []
        self.doc_term_freqs: List[Counter] = []
        self.idf: Dict[str, float] = {}
        self.vectors: List[Dict[str, float]] = []
        self.vector_norms: List[float] = []

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes text into cleaned lowercase words and clinical bigrams."""
        raw_tokens = re.findall(r"[a-zA-Z0-9_]{2,}", text.lower())
        filtered = [t for t in raw_tokens if t not in STOP_WORDS]

        # Generate adjacent bigrams for phrase matching (e.g., 'kidney function', 'penicillin allergy')
        tokens = list(filtered)
        for i in range(len(filtered) - 1):
            tokens.append(f"{filtered[i]}_{filtered[i+1]}")
        return tokens

    def add_chunks(self, new_chunks: List[DocumentChunk]):
        """Indexes a list of DocumentChunk objects into the vector space."""
        for chunk in new_chunks:
            # Combine title, section, and body for rich semantic representation
            full_text = f"{chunk.title} {chunk.section} {chunk.content}"
            tf = Counter(self._tokenize(full_text))
            self.chunks.append(chunk)
            self.doc_term_freqs.append(tf)

        self._recompute_index()

    def _recompute_index(self):
        """Recomputes IDF weights and document vector norms."""
        n_docs = len(self.chunks)
        if n_docs == 0:
            self.idf = {}
            self.vectors = []
            self.vector_norms = []
            return

        # Document frequencies
        df = Counter()
        for tf in self.doc_term_freqs:
            for term in tf.keys():
                df[term] += 1

        # Smooth IDF: ln(1 + N / (1 + df)) + 1
        self.idf = {
            term: math.log(1.0 + (n_docs / (1.0 + count))) + 1.0
            for term, count in df.items()
        }

        # Build TF-IDF vectors
        self.vectors = []
        self.vector_norms = []
        for tf in self.doc_term_freqs:
            total_terms = sum(tf.values()) or 1
            vec = {}
            sum_sq = 0.0
            for term, count in tf.items():
                tfidf = (count / total_terms) * self.idf.get(term, 1.0)
                vec[term] = tfidf
                sum_sq += tfidf * tfidf

            norm = math.sqrt(sum_sq) or 1.0
            self.vectors.append(vec)
            self.vector_norms.append(norm)

    def search(
        self,
        query: str,
        top_k: int = 3,
        score_threshold: float = 0.15,
        document_id: Optional[str] = None
    ) -> List[SearchResult]:
        """Computes Cosine Similarity between query vector and indexed document vectors.
        
        Applies score_thresholding to filter irrelevant queries and preserves complete provenance.
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        query_tf = Counter(query_tokens)
        total_q_terms = sum(query_tf.values()) or 1

        # Build query vector
        query_vec = {}
        q_sum_sq = 0.0
        for term, count in query_tf.items():
            if term in self.idf:
                tfidf = (count / total_q_terms) * self.idf[term]
                query_vec[term] = tfidf
                q_sum_sq += tfidf * tfidf

        q_norm = math.sqrt(q_sum_sq)
        if q_norm == 0.0:
            return []

        scored_results: List[Tuple[float, DocumentChunk, List[str]]] = []

        for idx, chunk in enumerate(self.chunks):
            if document_id and chunk.document_id.upper() != document_id.upper():
                continue

            doc_vec = self.vectors[idx]
            doc_norm = self.vector_norms[idx]

            # Dot product
            dot_product = 0.0
            matched = []
            for term, q_val in query_vec.items():
                if term in doc_vec:
                    dot_product += q_val * doc_vec[term]
                    if "_" not in term:
                        matched.append(term)

            # Cosine similarity
            cosine_sim = dot_product / (q_norm * doc_norm)

            # Modest title/section boost for exact clinical entity matches
            q_clean = query.lower()
            if any(w in chunk.title.lower() or w in chunk.section.lower() for w in query_tokens if len(w) > 3):
                cosine_sim = min(1.0, cosine_sim * 1.25)

            if cosine_sim >= score_threshold:
                scored_results.append((cosine_sim, chunk, matched))

        # Sort descending by score
        scored_results.sort(key=lambda x: x[0], reverse=True)

        results: List[SearchResult] = []
        for score, chunk, matched in scored_results[:top_k]:
            results.append(SearchResult(
                chunk_id=chunk.chunk_id,
                document_id=chunk.document_id,
                title=chunk.title,
                source=chunk.source,
                section=chunk.section,
                publication_date=chunk.publication_date,
                snippet=chunk.content,
                score=round(score, 4),
                matched_terms=sorted(list(set(matched)))
            ))

        return results

    def get_document_summaries(self) -> List[DocumentSummary]:
        """Returns metadata summaries of all indexed reference documents."""
        docs_map: Dict[str, Tuple[str, str, Optional[str], int]] = {}
        for chunk in self.chunks:
            did = chunk.document_id
            if did not in docs_map:
                docs_map[did] = (chunk.title, chunk.source, chunk.publication_date, 0)
            t, s, d, count = docs_map[did]
            docs_map[did] = (t, s, d, count + 1)

        return [
            DocumentSummary(
                document_id=did,
                title=t,
                source=s,
                publication_date=d,
                chunk_count=count
            )
            for did, (t, s, d, count) in docs_map.items()
        ]

    def clear(self):
        """Clears all indexed chunks and vectors."""
        self.chunks.clear()
        self.doc_term_freqs.clear()
        self.idf.clear()
        self.vectors.clear()
        self.vector_norms.clear()
