"""
Document ingestion pipeline: load → chunk → embed → store in ChromaDB.
Run: python ingest.py --docs_dir ./sample_docs
"""

import os
import argparse
import logging
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "policy_docs"
CHUNK_SIZE = 500  # characters
CHUNK_OVERLAP = 50


def load_documents(docs_dir: str) -> list[dict]:
    """Load all .txt and .pdf files from a directory."""
    docs = []
    for path in Path(docs_dir).rglob("*"):
        if path.suffix == ".txt":
            text = path.read_text(encoding="utf-8")
            docs.append({"source": str(path), "text": text})
        elif path.suffix == ".pdf":
            try:
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    text = "\n".join(p.extract_text() or "" for p in pdf.pages)
                docs.append({"source": str(path), "text": text})
            except ImportError:
                logger.warning("pdfplumber not installed; skipping %s", path)
    logger.info("Loaded %d documents", len(docs))
    return docs


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping character chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def ingest(docs_dir: str) -> None:
    client = chromadb.PersistentClient(path=CHROMA_PATH)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    # Delete existing collection to allow re-ingestion
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info("Deleted existing collection '%s'", COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(COLLECTION_NAME, embedding_function=ef)

    documents = load_documents(docs_dir)
    ids, texts, metadatas = [], [], []

    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{Path(doc['source']).stem}_chunk_{i}"
            ids.append(chunk_id)
            texts.append(chunk)
            metadatas.append({"source": doc["source"], "chunk_index": i})

    collection.add(documents=texts, ids=ids, metadatas=metadatas)
    logger.info("Ingested %d chunks into ChromaDB at '%s'", len(ids), CHROMA_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into ChromaDB")
    parser.add_argument("--docs_dir", default="./sample_docs", help="Directory containing documents")
    args = parser.parse_args()
    ingest(args.docs_dir)
