import numpy as np
from src.rag import KnowledgeBase, KBEntry

# Dummy model that always matches FAISS dim (384)
class DummyModel:
    def encode(self, texts, **kwargs):
        dim = 384
        arr = np.zeros((len(texts), dim), dtype=np.float32)
        for i, t in enumerate(texts):
            arr[i, 0] = len(t)  # encode length as signal
        return arr

def test_kb_retrieval():
    kb = KnowledgeBase("data/docs/*.md")
    kb.model = DummyModel()

    kb.entries = [
        KBEntry(text="short", reference="doc1"),
        KBEntry(text="a much longer entry", reference="doc2"),
    ]

    # Reset FAISS index with correct size (len(entries))
    vectors = kb.model.encode([e.text for e in kb.entries])
    kb.index.reset()
    kb.index.add(vectors)

    # Query should retrieve longest entry
    results = kb.retrieve("something long", top_k=1)

    assert len(results) == 1
    assert results[0]["reference"] == "doc2"
