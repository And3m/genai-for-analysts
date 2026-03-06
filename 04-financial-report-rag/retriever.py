"""
FAISS retrieval module for financial report Q&A.
"""

import os
import pickle
import numpy as np

INDEX_PATH = "./faiss_index"
TOP_K = 5


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Embed a query and return the top_k most relevant chunks from FAISS.
    """
    import faiss
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer("all-MiniLM-L6-v2")
    query_embedding = model.encode([query], normalize_embeddings=True)

    index = faiss.read_index(os.path.join(INDEX_PATH, "index.faiss"))
    with open(os.path.join(INDEX_PATH, "chunks.pkl"), "rb") as f:
        chunks = pickle.load(f)

    scores, indices = index.search(query_embedding, top_k)

    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(chunks):
            chunk = dict(chunks[idx])
            chunk["score"] = float(score)
            results.append(chunk)

    return results
