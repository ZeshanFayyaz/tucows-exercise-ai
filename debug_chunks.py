import logging
from src.rag import _read_docs, _chunk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug")

docs = _read_docs("data/docs/*.md")
logger.info(f"Read {len(docs)} docs")

total_chunks = 0
for title, content in docs:
    chunks = _chunk(content, size=300, overlap=50)
    logger.info(f"{title}: {len(chunks)} chunks")
    total_chunks += len(chunks)

logger.info(f"Total chunks: {total_chunks}")
