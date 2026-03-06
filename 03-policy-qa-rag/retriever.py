"""
Retrieval module: embed query, cosine-similarity search over numpy vector store.
"""

import json
import pickle
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

STORE_PATH = "./vector_store"
TOP_K = 5
MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_store = None


def _load_store():
    global _model, _store
    if _store is None:
        store = Path(STORE_PATH)
        embeddings = np.load(store / "embeddings.npy")
        with open(store / "texts.pkl", "rb") as f:
            texts = pickle.load(f)
        with open(store / "metadatas.json") as f:
            metadatas = json.load(f)
        _store = {"embeddings": embeddings, "texts": texts, "metadatas": metadatas}
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model, _store


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query using cosine similarity.
    Returns a list of dicts with keys: text, source, chunk_index, score.
    """
    model, store = _load_store()
    query_vec = model.encode([query], normalize_embeddings=True)[0]
    scores = store["embeddings"] @ query_vec   # dot product == cosine sim (normalized)
    top_indices = np.argsort(scores)[::-1][:top_k]

    return [
        {
            "text": store["texts"][i],
            "source": store["metadatas"][i].get("source", "unknown"),
            "chunk_index": store["metadatas"][i].get("chunk_index", i),
            "score": float(scores[i]),
        }
        for i in top_indices
    ]
