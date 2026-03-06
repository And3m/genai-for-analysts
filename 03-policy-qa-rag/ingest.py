"""
Document ingestion pipeline: load → chunk → embed → store as numpy vectors.
Run: python ingest.py --docs_dir ./sample_docs
"""

import argparse
import json
import logging
import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

STORE_PATH = "./vector_store"
CHUNK_SIZE = 500   # characters
CHUNK_OVERLAP = 50
MODEL_NAME = "all-MiniLM-L6-v2"


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
    store = Path(STORE_PATH)
    store.mkdir(exist_ok=True)

    model = SentenceTransformer(MODEL_NAME)
    documents = load_documents(docs_dir)

    texts, metadatas = [], []
    for doc in documents:
        chunks = chunk_text(doc["text"])
        for i, chunk in enumerate(chunks):
            texts.append(chunk)
            metadatas.append({"source": doc["source"], "chunk_index": i})

    logger.info("Embedding %d chunks...", len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    np.save(store / "embeddings.npy", embeddings)
    with open(store / "texts.pkl", "wb") as f:
        pickle.dump(texts, f)
    with open(store / "metadatas.json", "w") as f:
        json.dump(metadatas, f)

    logger.info("Saved %d chunks to '%s'", len(texts), STORE_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest documents into numpy vector store")
    parser.add_argument("--docs_dir", default="./sample_docs", help="Directory containing documents")
    args = parser.parse_args()
    ingest(args.docs_dir)
