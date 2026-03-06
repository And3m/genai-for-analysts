"""
Retrieval module: query ChromaDB and return relevant chunks with sources.
"""

import os
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "policy_docs"
TOP_K = 5


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )
    return client.get_collection(COLLECTION_NAME, embedding_function=ef)


def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """
    Retrieve the top_k most relevant chunks for a query.

    Returns a list of dicts with keys: text, source, chunk_index, distance.
    """
    collection = get_collection()
    results = collection.query(query_texts=[query], n_results=top_k)

    chunks = []
    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "source": results["metadatas"][0][i].get("source", "unknown"),
            "chunk_index": results["metadatas"][0][i].get("chunk_index", i),
            "distance": results["distances"][0][i] if results.get("distances") else None,
        })
    return chunks
