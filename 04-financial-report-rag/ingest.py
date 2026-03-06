"""
PDF ingestion pipeline: extract text → chunk → embed → save FAISS index.
Run: python ingest.py --pdf_dir ./sample_pdfs
"""

import os
import json
import pickle
import argparse
import logging
from pathlib import Path

import numpy as np
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

INDEX_PATH = "./faiss_index"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def extract_text_from_pdf(pdf_path: str) -> list[dict]:
    """Extract text page-by-page from a PDF using pdfplumber."""
    import pdfplumber
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text and text.strip():
                pages.append({"page": i + 1, "text": text.strip(), "source": pdf_path})
    return pages


def chunk_pages(pages: list[dict], chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[dict]:
    """Chunk page texts with overlap, preserving source metadata."""
    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        chunk_idx = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunks.append({
                "text": text[start:end],
                "source": page["source"],
                "page": page["page"],
                "chunk_index": chunk_idx,
            })
            start += chunk_size - overlap
            chunk_idx += 1
    return chunks


def embed_chunks(chunks: list[dict]) -> np.ndarray:
    """Embed chunk texts using sentence-transformers."""
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("all-MiniLM-L6-v2")
    texts = [c["text"] for c in chunks]
    logger.info("Embedding %d chunks...", len(texts))
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)
    return embeddings


def build_index(pdf_dir: str) -> None:
    import faiss

    os.makedirs(INDEX_PATH, exist_ok=True)

    all_chunks = []
    for pdf_path in Path(pdf_dir).rglob("*.pdf"):
        logger.info("Processing %s", pdf_path)
        pages = extract_text_from_pdf(str(pdf_path))
        chunks = chunk_pages(pages)
        all_chunks.extend(chunks)
        logger.info("  → %d chunks", len(chunks))

    if not all_chunks:
        logger.warning("No chunks found. Check pdf_dir: %s", pdf_dir)
        return

    embeddings = embed_chunks(all_chunks)
    dim = embeddings.shape[1]

    index = faiss.IndexFlatIP(dim)  # Inner product (cosine with normalised vectors)
    index.add(embeddings)

    faiss.write_index(index, os.path.join(INDEX_PATH, "index.faiss"))
    with open(os.path.join(INDEX_PATH, "chunks.pkl"), "wb") as f:
        pickle.dump(all_chunks, f)

    logger.info("Saved FAISS index with %d vectors to '%s'", len(all_chunks), INDEX_PATH)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pdf_dir", default="./sample_pdfs")
    args = parser.parse_args()
    build_index(args.pdf_dir)
