import os, glob
from dataclasses import dataclass
from typing import List, Dict, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100

def _read_docs(path_glob: str) -> List[Tuple[str, str]]:
    """Read all markdown files and return (title, content)."""
    docs = []
    for fp in sorted(glob.glob(path_glob)):
        title = os.path.splitext(os.path.basename(fp))[0].replace('_', ' ').title()
        with open(fp, "r", encoding="utf-8") as f:
            docs.append((title, f.read()))
    return docs

def _chunk(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into overlapping chunks."""
    chunks, start = [], 0
    n = len(text)
    while start < n:
        end = min(n, start + size)
        chunks.append(text[start:end])
        start = end - overlap
        if start < 0: start = 0
        if start >= n: break
    return chunks

@dataclass
class KBEntry:
    """
    Represents one chunk of knowledge.
    - text: the actual chunk content
    - reference: where it came from (doc title + chunk number)
    """
    text: str
    reference: str

class KnowledgeBase:
    def __init__(self, docs_glob: str = "data/docs/*.md", 
                 model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.entries: List[KBEntry] = []

        # Load docs and split into chunks
        for title, content in _read_docs(docs_glob):
            for i, ch in enumerate(_chunk(content)):
                ref = f"{title}, chunk {i+1}"
                self.entries.append(KBEntry(text=ch, reference=ref))

                # Create embeddings for all chunks
        texts = [e.text for e in self.entries]
        embs = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False
        )

        # Store in FAISS index
        dim = embs.shape[1]  # embedding size
        self.index = faiss.IndexFlatIP(dim)  # cosine similarity via inner product
        self.index.add(embs.astype("float32"))
        self._embs = embs  # keep for debugging/inspection

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        """Retrieve top-k most relevant chunks for the query."""
        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        scores, idxs = self.index.search(q_emb, top_k)

        results = []
        for i in idxs[0]:
            e = self.entries[int(i)]
            results.append({"text": e.text, "reference": e.reference})
        return results
