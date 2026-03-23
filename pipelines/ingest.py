"""
XenusAI — Ingest Pipeline
One-command pipeline: source (URL or file) → download → clean → chunk → embed → store

Usage:
    python -m pipelines.ingest "https://example.com/article"
    python -m pipelines.ingest "/path/to/document.pdf"
    python -m pipelines.ingest "/path/to/folder/"
"""

import sys
import logging
import time
from pathlib import Path
from urllib.parse import urlparse

from pipelines.downloader import download_url, read_file, read_directory
from pipelines.processor import process_text
from pipelines.chunker import chunk_text, count_tokens
from pipelines.embedder import embed_and_store, get_stats

logger = logging.getLogger(__name__)


def _is_url(source: str) -> bool:
    """Check if a string looks like a URL."""
    try:
        result = urlparse(source)
        return result.scheme in ("http", "https", "ftp")
    except Exception:
        return False


def ingest(
    source: str,
    verbose: bool = True,
    collection_name: str = None,
) -> dict:
    """
    Master ingest pipeline: takes a URL, file path, or directory
    and processes it end-to-end into the knowledge base.

    Args:
        source: URL, file path, or directory path.
        verbose: Whether to print progress.
        collection_name: Optional ChromaDB collection name.

    Returns:
        Dict with processing stats.
    """
    start_time = time.time()

    if verbose:
        print(f"\n{'='*60}")
        print(f"  XenusAI - Ingesting: {source}")
        print(f"{'='*60}\n")

    # ── Step 1: Download / Read ────────────────────────────
    if verbose:
        print("[1/4] >> Downloading / Reading source...")

    documents = []

    if _is_url(source):
        result = download_url(source)
        documents.append(result)
    else:
        path = Path(source).resolve()
        if path.is_dir():
            documents = read_directory(str(path))
        elif path.is_file():
            documents.append(read_file(str(path)))
        else:
            raise FileNotFoundError(f"Source not found: {source}")

    if not documents:
        print("[ERROR] No documents found to process")
        return {"status": "error", "message": "No documents found"}

    if verbose:
        print(f"   Found {len(documents)} document(s)")

    # ── Step 2: Clean & Process ────────────────────────────
    if verbose:
        print("[2/4] >> Cleaning and processing text...")

    total_chunks_stored = 0
    total_tokens = 0
    processed_docs = 0

    for doc in documents:
        raw_text = doc.get("text", "")
        if not raw_text.strip():
            logger.warning(
                f"Empty text from source: {doc.get('source', 'unknown')}"
            )
            continue

        # Clean the text
        clean = process_text(raw_text)
        if not clean.strip():
            logger.warning(
                f"Text empty after cleaning: {doc.get('source', 'unknown')}"
            )
            continue

        tokens = count_tokens(clean)
        total_tokens += tokens

        if verbose:
            title = doc.get("title", "Untitled")
            print(f"   [*] {title}: {tokens:,} tokens")

        # ── Step 3: Chunk ──────────────────────────────────
        chunks = chunk_text(clean)

        if not chunks:
            logger.warning(
                f"No chunks created from: {doc.get('source', 'unknown')}"
            )
            continue

        if verbose:
            print(f"   [+] Split into {len(chunks)} chunks")

        # ── Step 4: Embed & Store ──────────────────────────
        stored = embed_and_store(
            chunks=chunks,
            source=doc.get("source", source),
            source_type=doc.get("source_type", "unknown"),
            title=doc.get("title"),
            collection_name=collection_name,
        )

        total_chunks_stored += stored
        processed_docs += 1

    elapsed = time.time() - start_time

    # ── Summary ────────────────────────────────────────────
    stats = get_stats(collection_name)

    result = {
        "status": "success",
        "source": source,
        "documents_processed": processed_docs,
        "total_tokens": total_tokens,
        "chunks_stored": total_chunks_stored,
        "elapsed_seconds": round(elapsed, 2),
        "knowledge_base_total": stats["total_chunks"],
    }

    if verbose:
        print(f"\n{'='*60}")
        print(f"  [OK] Ingestion Complete!")
        print(f"{'='*60}")
        print(f"  Documents processed: {processed_docs}")
        print(f"  Total tokens:        {total_tokens:,}")
        print(f"  Chunks stored:       {total_chunks_stored}")
        print(f"  Time elapsed:        {elapsed:.1f}s")
        print(f"  Knowledge base size: {stats['total_chunks']} total chunks")
        print(f"{'='*60}\n")

    return result


def ingest_batch(sources: list, **kwargs) -> list:
    """
    Ingest multiple sources sequentially.

    Args:
        sources: List of URLs/paths to ingest.
        **kwargs: Additional args passed to ingest().

    Returns:
        List of result dicts.
    """
    results = []
    for i, source in enumerate(sources, 1):
        print(f"\n[{i}/{len(sources)}] Processing: {source}")
        try:
            result = ingest(source, **kwargs)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to ingest {source}: {e}")
            results.append({
                "status": "error",
                "source": source,
                "message": str(e),
            })
    return results


# ─── CLI Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if len(sys.argv) < 2:
        print("Usage: python -m pipelines.ingest <url_or_path> [url_or_path ...]")
        print("")
        print("Examples:")
        print('  python -m pipelines.ingest "https://en.wikipedia.org/wiki/Binary_search"')
        print('  python -m pipelines.ingest "./documents/notes.txt"')
        print('  python -m pipelines.ingest "./docs/"')
        sys.exit(1)

    sources = sys.argv[1:]

    if len(sources) == 1:
        ingest(sources[0])
    else:
        ingest_batch(sources)
