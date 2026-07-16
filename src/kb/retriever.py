"""Semantic retrieval over KB chunks: local embeddings + FAISS.

Design notes:
- Groq exposes no embeddings endpoint, so embeddings are computed locally with
  all-MiniLM-L6-v2 (small, fast on CPU, downloads once on first run).
- Embeddings are L2-normalized and searched with an inner-product index
  (IndexFlatIP), which makes the score = cosine similarity.
- Flat (exact) index is the right call for a corpus this size (~dozens of
  chunks); approximate indexes only pay off at scale -- a Task 4 talking point.
- Public interface (retrieve -> scored chunks) is stable, so the pipeline
  never cares what backs it.
"""

import faiss
from sentence_transformers import SentenceTransformer

from .chunker import chunk_kb

_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class KBRetriever:
    def __init__(self):
        self.chunks = chunk_kb()
        self._model = SentenceTransformer(_EMBED_MODEL)
        texts = [f"{c['section']}\n{c['text']}" for c in self.chunks]
        emb = self._model.encode(
            texts, normalize_embeddings=True, show_progress_bar=False
        ).astype("float32")
        self._index = faiss.IndexFlatIP(emb.shape[1])  # cosine via normalized IP
        self._index.add(emb)

    def retrieve(self, query: str, k: int = 3) -> list[dict]:
        q = self._model.encode(
            [query], normalize_embeddings=True, show_progress_bar=False
        ).astype("float32")
        scores, ids = self._index.search(q, k)
        return [
            {**self.chunks[i], "score": round(float(s), 3)}
            for s, i in zip(scores[0], ids[0])
            if i != -1
        ]
