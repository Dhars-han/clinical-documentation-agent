import os
import re
from typing import List, Dict, Any, Optional

try:
    from backend.rag.schemas import DocumentChunk
except ImportError:
    from .schemas import DocumentChunk


class DocumentLoader:
    """Parses clinical markdown files into structured DocumentChunk objects with full provenance."""

    @staticmethod
    def load_directory(directory_path: str) -> List[DocumentChunk]:
        """Loads all markdown reference files from a directory."""
        if not os.path.exists(directory_path):
            return []

        all_chunks: List[DocumentChunk] = []
        for filename in sorted(os.listdir(directory_path)):
            if filename.endswith(".md") or filename.endswith(".txt"):
                file_path = os.path.join(directory_path, filename)
                chunks = DocumentLoader.load_file(file_path)
                all_chunks.extend(chunks)

        return all_chunks

    @staticmethod
    def load_file(file_path: str) -> List[DocumentChunk]:
        """Loads and chunks a single clinical guideline markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        filename = os.path.basename(file_path)
        return DocumentLoader.parse_markdown(raw_text, filename)

    @staticmethod
    def parse_markdown(content: str, filename: str) -> List[DocumentChunk]:
        """Parses markdown text, extracts metadata headers, and chunks by section (##)."""
        lines = content.split("\n")

        # 1. Extract document title from first # Header
        title = "Clinical Guideline"
        doc_id = os.path.splitext(filename)[0].upper()
        source = "Clinical Reference Library"
        pub_date = None
        category = "Clinical Practice Guideline"

        header_lines = []
        body_lines = []
        is_header = True

        for line in lines:
            if line.startswith("# ") and title == "Clinical Guideline":
                title = line[2:].strip()
                continue

            if is_header:
                if line.startswith("## "):
                    is_header = False
                    body_lines.append(line)
                else:
                    header_lines.append(line)
                    # Extract metadata key-values
                    if "Source Organization:" in line:
                        source = line.split("Source Organization:")[1].replace("*", "").strip()
                    elif "Publication Date:" in line:
                        pub_date = line.split("Publication Date:")[1].replace("*", "").strip()
                    elif "Document ID:" in line:
                        doc_id = line.split("Document ID:")[1].replace("*", "").strip()
                    elif "Category:" in line:
                        category = line.split("Category:")[1].replace("*", "").strip()
            else:
                body_lines.append(line)

        # 2. Split body by ## Section
        chunks: List[DocumentChunk] = []
        body_text = "\n".join(body_lines)
        sections = re.split(r"\n(?=## )", body_text)

        chunk_idx = 1
        for sec in sections:
            sec_trimmed = sec.strip()
            if not sec_trimmed:
                continue

            sec_lines = sec_trimmed.split("\n")
            sec_header = sec_lines[0].replace("##", "").strip()
            sec_body = "\n".join(sec_lines[1:]).strip() if len(sec_lines) > 1 else sec_trimmed

            chunk_id = f"{doc_id}-CHK{chunk_idx:02d}"
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=doc_id,
                title=title,
                source=source,
                section=sec_header,
                publication_date=pub_date,
                content=sec_body or sec_trimmed,
                metadata={
                    "category": category,
                    "filename": filename,
                    "chunk_index": chunk_idx
                }
            )
            chunks.append(chunk)
            chunk_idx += 1

        return chunks
