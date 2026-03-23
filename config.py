"""
XenusAI — Configuration
Central settings for paths, models, and pipeline parameters.
"""

from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
CHROMA_DIR = DATA_DIR / "chroma_db"

# Create directories on import
for d in (RAW_DIR, PROCESSED_DIR, CHROMA_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────
# Embedding Model
# ──────────────────────────────────────────────
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIMENSIONS = 384

# ──────────────────────────────────────────────
# Chunking
# ──────────────────────────────────────────────
CHUNK_SIZE = 512          # target tokens per chunk
CHUNK_OVERLAP = 50        # overlapping tokens between consecutive chunks
MIN_CHUNK_SIZE = 30       # discard chunks smaller than this (tokens)

# ──────────────────────────────────────────────
# ChromaDB
# ──────────────────────────────────────────────
CHROMA_COLLECTION_NAME = "xenus_knowledge"

# ──────────────────────────────────────────────
# Retrieval
# ──────────────────────────────────────────────
LLM_NUM_RESULTS = 5             # top-K retrieval results to return per query
