"""
XenusAI — Chunker
Splits processed text into semantically meaningful, overlapping chunks
optimized for embedding and retrieval.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Tokenizer (lazy-loaded) ────────────────────────────────────

_tokenizer = None


def _get_tokenizer():
    """Lazy-load tiktoken tokenizer."""
    global _tokenizer
    if _tokenizer is None:
        import tiktoken
        _tokenizer = tiktoken.get_encoding("cl100k_base")
    return _tokenizer


def count_tokens(text: str) -> int:
    """Count tokens in a string using tiktoken."""
    enc = _get_tokenizer()
    return len(enc.encode(text))


# ─── Sentence Splitting ────────────────────────────────────────

def split_into_sentences(text: str) -> list:
    """
    Split text into sentences using regex.
    Handles abbreviations, decimals, and common edge cases.
    """
    # Split on sentence-ending punctuation followed by whitespace + uppercase
    # but protect abbreviations like Mr. Mrs. Dr. etc.
    abbreviations = r"(?:Mr|Mrs|Ms|Dr|Prof|Sr|Jr|St|vs|etc|i\.e|e\.g|al|approx|dept|est|govt|inc)"

    # First, protect abbreviations by replacing their periods
    protected = text
    protected = re.sub(
        rf"({abbreviations})\.",
        r"\1<PERIOD>",
        protected,
        flags=re.IGNORECASE,
    )

    # Protect decimal numbers
    protected = re.sub(r"(\d)\.", r"\1<PERIOD>", protected)

    # Split on sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z\"\'\(])", protected)

    # Also split on newlines that look like paragraph breaks
    expanded = []
    for sent in sentences:
        parts = re.split(r"\n\n+", sent)
        expanded.extend(parts)

    # Restore protected periods
    result = [s.replace("<PERIOD>", ".").strip() for s in expanded if s.strip()]
    return result


# ─── Primary Chunking Function ─────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: Optional[int] = None,
    chunk_overlap: Optional[int] = None,
    min_chunk_size: Optional[int] = None,
) -> list:
    """
    Split text into chunks of approximately `chunk_size` tokens,
    with `chunk_overlap` tokens of overlap between consecutive chunks.

    Strategy:
        1. Split text into sentences
        2. Group sentences into chunks that don't exceed chunk_size
        3. Add overlap by including trailing sentences from the previous chunk

    Args:
        text: Processed text to chunk.
        chunk_size: Target tokens per chunk (default from config).
        chunk_overlap: Overlap tokens between chunks (default from config).
        min_chunk_size: Minimum tokens for a chunk to be kept (default from config).

    Returns:
        List of chunk strings.
    """
    from config import CHUNK_SIZE, CHUNK_OVERLAP, MIN_CHUNK_SIZE

    chunk_size = chunk_size or CHUNK_SIZE
    chunk_overlap = chunk_overlap or CHUNK_OVERLAP
    min_chunk_size = min_chunk_size or MIN_CHUNK_SIZE

    if not text or not text.strip():
        return []

    sentences = split_into_sentences(text)

    if not sentences:
        return [text.strip()] if count_tokens(text) >= min_chunk_size else []

    # Build chunks by accumulating sentences
    chunks = []
    current_sentences = []
    current_token_count = 0

    for sentence in sentences:
        sentence_tokens = count_tokens(sentence)

        # If a single sentence exceeds chunk_size, split it by words
        if sentence_tokens > chunk_size:
            # First, flush the current accumulator
            if current_sentences:
                chunks.append(" ".join(current_sentences))
                current_sentences = []
                current_token_count = 0

            # Split the long sentence into sub-chunks
            sub_chunks = _split_long_text(sentence, chunk_size)
            chunks.extend(sub_chunks)
            continue

        # Would adding this sentence exceed the chunk size?
        if current_token_count + sentence_tokens > chunk_size and current_sentences:
            # Flush current chunk
            chunks.append(" ".join(current_sentences))

            # Start new chunk with overlap from the end of previous
            overlap_sentences = _get_overlap_sentences(
                current_sentences, chunk_overlap
            )
            current_sentences = overlap_sentences
            current_token_count = count_tokens(" ".join(current_sentences))

        current_sentences.append(sentence)
        current_token_count += sentence_tokens

    # Don't forget the last chunk
    if current_sentences:
        chunks.append(" ".join(current_sentences))

    # Filter out chunks that are too small
    chunks = [c for c in chunks if count_tokens(c) >= min_chunk_size]

    logger.info(
        f"Created {len(chunks)} chunks "
        f"(avg {sum(count_tokens(c) for c in chunks) // max(len(chunks), 1)} tokens)"
    )

    return chunks


def chunk_by_sections(text: str, chunk_size: Optional[int] = None) -> list:
    """
    Chunk text section-by-section (preserving header structure).
    Falls back to regular chunking for sections that are too large.

    Returns:
        List of dicts with keys: text, title (optional)
    """
    from pipelines.processor import extract_sections
    from config import CHUNK_SIZE

    chunk_size = chunk_size or CHUNK_SIZE
    sections = extract_sections(text)

    results = []
    for section in sections:
        content = section["content"]
        title = section.get("title")

        if count_tokens(content) <= chunk_size:
            # Section fits in one chunk — prefix with title if available
            chunk_text_str = f"{title}\n\n{content}" if title else content
            results.append({"text": chunk_text_str, "title": title})
        else:
            # Section too large — chunk it further
            sub_chunks = chunk_text(content, chunk_size=chunk_size)
            for i, sub in enumerate(sub_chunks):
                sub_title = f"{title} (part {i + 1})" if title else None
                chunk_text_str = f"{sub_title}\n\n{sub}" if sub_title else sub
                results.append({"text": chunk_text_str, "title": sub_title})

    return results


# ─── Private Helpers ────────────────────────────────────────────

def _get_overlap_sentences(sentences: list, target_overlap_tokens: int) -> list:
    """Get sentences from the end of a list that total ~target_overlap_tokens."""
    overlap = []
    token_count = 0

    for sentence in reversed(sentences):
        s_tokens = count_tokens(sentence)
        if token_count + s_tokens > target_overlap_tokens:
            break
        overlap.insert(0, sentence)
        token_count += s_tokens

    return overlap


def _split_long_text(text: str, chunk_size: int) -> list:
    """Split text that exceeds chunk_size by words."""
    enc = _get_tokenizer()
    tokens = enc.encode(text)
    chunks = []

    for i in range(0, len(tokens), chunk_size):
        chunk_tokens = tokens[i : i + chunk_size]
        chunk_str = enc.decode(chunk_tokens)
        chunks.append(chunk_str)

    return chunks
