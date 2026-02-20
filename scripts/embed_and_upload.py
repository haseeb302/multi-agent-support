#!/usr/bin/env python3
"""
One-time embed of policy documents and upload to Pinecone.

Uses Pinecone integrated embedding only (no OpenAI or other APIs). The index
must already exist with an integrated embedding model configured on the platform.
We upsert records with text; Pinecone converts them to vectors. See:
https://docs.pinecone.io/guides/index-data/upsert-data

Env (required): PINECONE_API_KEY, PINECONE_INDEX_NAME
Env (optional): PINECONE_NAMESPACE, PINECONE_REGION, PINECONE_MODEL_NAME, PINECONE_DIMENSION

Usage:
  python scripts/embed_and_upload.py
  ./scripts/embed_and_upload.sh
"""
from __future__ import annotations

import sys
import uuid
from pathlib import Path

# Project root = parent of scripts/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import DOCS_DIR, get_settings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pinecone import Pinecone


# Policy .md files to index (under docs/)
POLICY_DOCS = [
    "return_policy.md",
    "care_plus_benefits.md",
    "troubleshooting_guide.md",
]

SOURCE_FIELD = "source"


def load_documents() -> list[Document]:
    """Load policy markdown files into LangChain Documents with source metadata."""
    docs: list[Document] = []
    for name in POLICY_DOCS:
        path = DOCS_DIR / name
        if not path.exists():
            print(f"Warning: {path} not found, skipping.")
            continue
        text = path.read_text(encoding="utf-8")
        docs.append(
            Document(
                page_content=text,
                metadata={"source": name, "path": str(path)},
            )
        )
    return docs


def chunk_documents(
    documents: list[Document], chunk_size: int = 800, overlap: int = 150
) -> list[Document]:
    """Split documents into smaller chunks for embedding."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=overlap,
        length_function=len,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    return splitter.split_documents(documents)


def build_records(chunks: list[Document], text_field: str = "text") -> list[dict]:
    """Build Pinecone records: _id, text_field, source. Field name must match index's field_map."""
    records = []
    for doc in chunks:
        records.append({
            "_id": str(uuid.uuid4()),
            text_field: doc.page_content,
            SOURCE_FIELD: doc.metadata.get("source", ""),
        })
    return records


def main() -> int:
    settings = get_settings()
    try:
        settings.require_pinecone()
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    index_name = settings.pinecone_index_name
    namespace = settings.pinecone_namespace or "__default__"

    print("Loading policy documents...")
    raw_docs = load_documents()
    if not raw_docs:
        print("No documents to index.", file=sys.stderr)
        return 1
    print(f"Loaded {len(raw_docs)} document(s).")

    print("Chunking...")
    chunks = chunk_documents(raw_docs)
    print(f"Split into {len(chunks)} chunks.")

    text_field = settings.pinecone_text_field
    records = build_records(chunks, text_field=text_field)

    print("Connecting to Pinecone...")
    pc = Pinecone(api_key=settings.pinecone_api_key)
    index = pc.Index(name=index_name)

    print(f"Upserting {len(records)} records to namespace '{namespace}'...")
    index.upsert_records(namespace, records)
    print("Done. Policy documents are indexed in Pinecone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
