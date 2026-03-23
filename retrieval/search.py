"""
XenusAI — Search & Retrieval
Queries the vector store to find relevant knowledge chunks.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def search(
    query: str,
    n_results: int = None,
    collection_name: Optional[str] = None,
    filter_source: Optional[str] = None,
) -> list:
    """
    Search the knowledge base for chunks relevant to a query.

    Args:
        query: The search query string.
        n_results: Number of results to return (default from config).
        collection_name: Optional collection name override.
        filter_source: Optional source filter (only search within this source).

    Returns:
        List of result dicts with keys:
            - document: the chunk text
            - source: where the chunk came from
            - title: document title
            - score: similarity score (0-1, higher is better)
            - chunk_index: position in original document
    """
    from config import LLM_NUM_RESULTS
    from pipelines.embedder import embed_texts, get_collection

    n_results = n_results or LLM_NUM_RESULTS

    collection = get_collection(collection_name)

    if collection.count() == 0:
        logger.warning("Knowledge base is empty — nothing to search")
        return []

    # Build query parameters
    query_params = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count()),
        "include": ["documents", "metadatas", "distances"],
    }

    # Optional source filter
    if filter_source:
        query_params["where"] = {"source": filter_source}

    # Execute search
    results = collection.query(**query_params)

    # Format results
    formatted = []
    if results and results.get("documents") and results["documents"][0]:
        for i in range(len(results["documents"][0])):
            doc = results["documents"][0][i]
            meta = results["metadatas"][0][i] if results.get("metadatas") else {}
            distance = results["distances"][0][i] if results.get("distances") else 0

            # ChromaDB returns cosine distance; convert to similarity
            # cosine distance = 1 - cosine similarity
            similarity = 1 - distance

            formatted.append({
                "document": doc,
                "source": meta.get("source", "unknown"),
                "title": meta.get("title", ""),
                "score": round(similarity, 4),
                "chunk_index": meta.get("chunk_index", -1),
                "total_chunks": meta.get("total_chunks", -1),
            })

    logger.info(f"Search for '{query[:50]}...' returned {len(formatted)} results")
    return formatted


def get_context(
    query: str,
    n_results: int = None,
    collection_name: Optional[str] = None,
    min_score: float = 0.1,
) -> str:
    """
    Get formatted context string for LLM prompting.

    Retrieves relevant chunks and formats them into a context block
    that can be injected into an LLM prompt.

    Args:
        query: The search query.
        n_results: Number of results.
        collection_name: Optional collection name.
        min_score: Minimum similarity score to include (0-1).

    Returns:
        Formatted context string with source citations.
    """
    results = search(query, n_results, collection_name)

    if not results:
        return "No relevant information found in the knowledge base."

    # Filter by minimum score
    results = [r for r in results if r["score"] >= min_score]

    if not results:
        return "No sufficiently relevant information found in the knowledge base."

    # Build context string
    context_parts = []
    for i, result in enumerate(results, 1):
        source = result["source"]
        title = result["title"]
        score = result["score"]
        text = result["document"]

        header = f"[Source {i}]"
        if title:
            header += f" {title}"
        header += f" (relevance: {score:.0%})"
        header += f"\nFrom: {source}"

        context_parts.append(f"{header}\n{text}")

    context = "\n\n---\n\n".join(context_parts)

    return context


def search_similar(
    text: str,
    n_results: int = 5,
    collection_name: Optional[str] = None,
) -> list:
    """
    Find chunks similar to a given text (not a question, but content).
    Useful for deduplication or finding related sections.
    """
    return search(text, n_results, collection_name)
