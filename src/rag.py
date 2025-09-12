import os, glob, logging
from dataclasses import dataclass
from typing import List, Dict, Tuple
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

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
    """Split text into overlapping chunks safely."""
    if overlap >= size:
        raise ValueError(f"Overlap {overlap} must be smaller than chunk size {size}")

    chunks, start = [], 0
    n = len(text)

    while start < n:
        end = min(n, start + size)
        chunks.append(text[start:end])
        start = start + size - overlap  # always move forward

    return chunks


@dataclass
class KBEntry:
    text: str
    reference: str


class KnowledgeBase:
    def __init__(self, docs_glob: str = "data/docs/*.md", model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)
        self.entries: List[KBEntry] = []

        logger.info("Reading documentation files…")
        for title, content in _read_docs(docs_glob):
            for i, ch in enumerate(_chunk(content)):
                ref = f"{title}, chunk {i+1}"
                self.entries.append(KBEntry(text=ch, reference=ref))

        logger.info(f"Total chunks collected: {len(self.entries)}")

        # Encode all chunks
        texts = [e.text for e in self.entries]
        logger.info("Encoding chunks into embeddings… (this may take a minute on first run)")
        embs = self.model.encode(
            texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )
        logger.info("Encoding complete.")

        # Build FAISS index
        dim = embs.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embs.astype("float32"))
        self._embs = embs

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict]:
        q_emb = self.model.encode([query], convert_to_numpy=True, normalize_embeddings=True).astype("float32")
        scores, idxs = self.index.search(q_emb, top_k)

        results = []
        for i in idxs[0]:
            e = self.entries[int(i)]
            results.append({"text": e.text, "reference": e.reference})
        return results
