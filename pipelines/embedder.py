"""
XenusAI — Embedder
Generates embeddings and stores them in ChromaDB.
"""

import hashlib
import logging
from typing import Optional

import chromadb

logger = logging.getLogger(__name__)

# ─── Singleton Instances (lazy-loaded) ──────────────────────────

_embedding_model = None
_chroma_client = None


def get_embedding_model():
    """
    Load the sentence-transformers embedding model (singleton).
    Uses all-MiniLM-L6-v2 by default — 384 dimensions, ~80MB, fast on CPU.
    """
    global _embedding_model
    if _embedding_model is None:
        from sentence_transformers import SentenceTransformer
        from config import EMBEDDING_MODEL_NAME
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL_NAME} natively on {device.upper()}")
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        logger.info("Embedding model loaded successfully to compute cluster")

    return _embedding_model


def get_chroma_client():
    """Get or create a persistent ChromaDB client (singleton)."""
    global _chroma_client
    if _chroma_client is None:
        from config import CHROMA_DIR

        logger.info(f"Initializing ChromaDB at: {CHROMA_DIR}")
        _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    return _chroma_client


def get_collection(collection_name: Optional[str] = None):
    """
    Get or create a ChromaDB collection.

    Args:
        collection_name: Name of the collection. Defaults to config value.

    Returns:
        ChromaDB Collection object.
    """
    from config import CHROMA_COLLECTION_NAME

    name = collection_name or CHROMA_COLLECTION_NAME
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},  # cosine similarity
    )

    return collection


def embed_texts(texts: list) -> list:
    """
    Generate embeddings for a list of text strings.

    Args:
        texts: List of text strings.

    Returns:
        List of embedding vectors (list of floats).
    """
    model = get_embedding_model()
    embeddings = model.encode(texts, show_progress_bar=len(texts) > 50)
    return embeddings.tolist()


def embed_and_store(
    chunks: list,
    source: str,
    source_type: str = "unknown",
    title: Optional[str] = None,
    collection_name: Optional[str] = None,
    batch_size: int = 64,
) -> int:
    """
    Embed text chunks and store them in ChromaDB.

    Args:
        chunks: List of text chunks to embed and store.
        source: Source identifier (URL, file path, etc.).
        source_type: Type of source ('url', 'file', etc.).
        title: Optional document title.
        collection_name: Optional collection name override.
        batch_size: Number of chunks to embed at once.

    Returns:
        Number of chunks stored.
    """
    if not chunks:
        logger.warning("No chunks to embed")
        return 0

    collection = get_collection(collection_name)

    total_stored = 0

    # Process in batches to manage memory
    for batch_start in range(0, len(chunks), batch_size):
        batch_end = min(batch_start + batch_size, len(chunks))
        batch = chunks[batch_start:batch_end]

        # Generate unique IDs based on content hash + index
        source_hash = hashlib.md5(source.encode()).hexdigest()[:8]
        ids = [
            f"{source_hash}_chunk_{batch_start + i}"
            for i in range(len(batch))
        ]

        # Create metadata for each chunk
        metadatas = [
            {
                "source": source,
                "source_type": source_type,
                "title": title or "",
                "chunk_index": batch_start + i,
                "total_chunks": len(chunks),
            }
            for i in range(len(batch))
        ]

        # Generate embeddings
        embeddings = embed_texts(batch)

        # Upsert into ChromaDB (upsert = insert or update)
        collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=batch,
            metadatas=metadatas,
        )

        total_stored += len(batch)
        logger.info(
            f"Stored batch {batch_start // batch_size + 1}: "
            f"{total_stored}/{len(chunks)} chunks"
        )

    logger.info(
        f"Successfully stored {total_stored} chunks from: {source}"
    )

    return total_stored


def get_stats(collection_name: Optional[str] = None) -> dict:
    """
    Get statistics about the knowledge base.

    Returns:
        Dict with count, sources, and collection info.
    """
    collection = get_collection(collection_name)
    count = collection.count()

    # Get unique sources
    sources = set()
    if count > 0:
        # Sample metadata to get sources
        results = collection.peek(limit=min(count, 100))
        if results and results.get("metadatas"):
            for meta in results["metadatas"]:
                sources.add(meta.get("source", "unknown"))

    return {
        "total_chunks": count,
        "unique_sources": len(sources),
        "sources": sorted(sources),
        "collection_name": collection.name,
    }


def delete_source(source: str, collection_name: Optional[str] = None) -> int:
    """
    Delete all chunks from a specific source.

    Args:
        source: Source identifier to delete.
        collection_name: Optional collection name.

    Returns:
        Number of chunks deleted.
    """
    collection = get_collection(collection_name)

    # Find all IDs with this source
    results = collection.get(
        where={"source": source},
        include=[],
    )

    if not results or not results["ids"]:
        logger.info(f"No chunks found for source: {source}")
        return 0

    ids_to_delete = results["ids"]
    collection.delete(ids=ids_to_delete)

    logger.info(f"Deleted {len(ids_to_delete)} chunks from: {source}")
    return len(ids_to_delete)


def reset_collection(collection_name: Optional[str] = None):
    """Delete and recreate the collection (WARNING: destroys all data)."""
    from config import CHROMA_COLLECTION_NAME

    name = collection_name or CHROMA_COLLECTION_NAME
    client = get_chroma_client()

    try:
        client.delete_collection(name)
        logger.info(f"Collection '{name}' deleted")
    except Exception:
        pass

    # Recreate
    get_collection(name)
    logger.info(f"Collection '{name}' recreated")
