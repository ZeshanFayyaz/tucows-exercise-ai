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
    def __init__(self, docs_glob: str = "data/docs/*.md"):
        self.entries: List[KBEntry] = []

        # Load docs and split into chunks
        for title, content in _read_docs(docs_glob):
            for i, ch in enumerate(_chunk(content)):
                ref = f"{title}, chunk {i+1}"
                self.entries.append(KBEntry(text=ch, reference=ref))
