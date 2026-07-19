"""
FAISS-backed long-term memory. Stores past research findings and lets the
Research agent pull relevant past context before doing fresh web searches.
"""

import os
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

INDEX_PATH = "rune_memory.index"
DOCS_PATH = "rune_memory_docs.npy"
EMBED_DIM = 384  # matches all-MiniLM-L6-v2

_model = None


def _get_model():
    """Lazily loads the sentence transformer model on first use, rather than
    at import time - this lets the server bind its port and report healthy
    immediately, instead of blocking startup on a model download."""
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def _load_or_create_index():
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        docs = list(np.load(DOCS_PATH, allow_pickle=True))
    else:
        index = faiss.IndexFlatL2(EMBED_DIM)
        docs = []
    return index, docs


def faiss_retrieve(query: str, k: int = 3) -> list[dict]:
    """Returns up to k most similar past findings as [{"content": str}, ...]."""
    index, docs = _load_or_create_index()
    if index.ntotal == 0:
        return []

    query_vec = _get_model().encode([query]).astype("float32")
    k = min(k, index.ntotal)
    _, indices = index.search(query_vec, k)

    return [{"content": docs[i]} for i in indices[0] if i < len(docs)]


def faiss_store(text: str):
    """Write a new finding into long-term memory."""
    index, docs = _load_or_create_index()
    vec = _get_model().encode([text]).astype("float32")
    index.add(vec)
    docs.append(text)
    faiss.write_index(index, INDEX_PATH)
    np.save(DOCS_PATH, np.array(docs, dtype=object))