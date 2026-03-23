"""
XenusAI — Processor
Cleans and normalizes raw text for chunking and embedding.
"""

import re
import logging
import unicodedata

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean raw text for processing.

    Steps:
        1. Normalize Unicode (NFC form)
        2. Fix common encoding artifacts
        3. Collapse excessive whitespace and blank lines
        4. Remove null bytes and control characters
        5. Strip leading/trailing whitespace

    Args:
        text: Raw text string.

    Returns:
        Cleaned text string.
    """
    if not text:
        return ""

    # 1. Normalize Unicode to composed form
    text = unicodedata.normalize("NFC", text)

    # 2. Fix common encoding artifacts
    replacements = {
        "\u00a0": " ",       # non-breaking space → regular space
        "\u200b": "",        # zero-width space → remove
        "\u200c": "",        # zero-width non-joiner
        "\u200d": "",        # zero-width joiner
        "\ufeff": "",        # BOM
        "\u2018": "'",       # left single quote
        "\u2019": "'",       # right single quote
        "\u201c": '"',       # left double quote
        "\u201d": '"',       # right double quote
        "\u2013": "-",       # en-dash
        "\u2014": "—",       # em-dash (keep as-is, it's useful)
        "\u2026": "...",     # ellipsis
        "\u00ad": "",        # soft hyphen
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # 3. Remove null bytes and control characters (keep newlines, tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)

    # 4. Collapse multiple spaces (but preserve newlines)
    text = re.sub(r"[^\S\n]+", " ", text)

    # 5. Collapse 3+ consecutive newlines into 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 6. Strip each line
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(lines)

    # 7. Final strip
    text = text.strip()

    return text


def remove_boilerplate(text: str) -> str:
    """
    Remove common web boilerplate patterns from text.

    Removes:
        - Cookie/privacy notices
        - Navigation breadcrumbs
        - "Skip to content" links
        - Social share buttons text
        - Common footer patterns
    """
    if not text:
        return ""

    # Patterns to remove (case-insensitive)
    boilerplate_patterns = [
        r"(?i)^skip to (?:main )?content\s*$",
        r"(?i)^cookie\s*(?:policy|notice|consent).*$",
        r"(?i)^we use cookies.*$",
        r"(?i)^accept\s*(?:all)?\s*cookies?\s*$",
        r"(?i)^share\s*(?:on|via)\s*(?:twitter|facebook|linkedin|reddit).*$",
        r"(?i)^(?:tweet|share|pin|email)\s*$",
        r"(?i)^(?:previous|next)\s*(?:article|post|page).*$",
        r"(?i)^table of contents\s*$",
        r"(?i)^advertisement\s*$",
        r"(?i)^sponsored\s*$",
    ]

    lines = text.splitlines()
    cleaned_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append(line)
            continue

        is_boilerplate = False
        for pattern in boilerplate_patterns:
            if re.match(pattern, stripped):
                is_boilerplate = True
                break

        if not is_boilerplate:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def normalize_whitespace(text: str) -> str:
    """
    Aggressively normalize whitespace for embedding.
    Collapses all whitespace into single spaces and strips the result.
    Useful for search-optimized text, not for display.
    """
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def extract_sections(text: str) -> list:
    """
    Split text into logical sections based on headers/structure.

    Tries to detect Markdown headers, blank-line-separated paragraphs,
    and numbered/bulleted lists as section boundaries.

    Returns:
        List of dicts with keys: title (optional), content
    """
    if not text:
        return []

    sections = []
    current_title = None
    current_lines = []

    for line in text.splitlines():
        stripped = line.strip()

        # Detect markdown headers
        header_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if header_match:
            # Save previous section
            if current_lines:
                content = "\n".join(current_lines).strip()
                if content:
                    sections.append({
                        "title": current_title,
                        "content": content,
                    })
            current_title = header_match.group(2).strip()
            current_lines = []
            continue

        # Detect underline-style headers (===== or -----)
        if stripped and re.match(r"^[=]{3,}$", stripped):
            if current_lines:
                current_title = current_lines.pop().strip()
            continue
        if stripped and re.match(r"^[-]{3,}$", stripped):
            if current_lines:
                current_title = current_lines.pop().strip()
            continue

        current_lines.append(line)

    # Don't forget the last section
    if current_lines:
        content = "\n".join(current_lines).strip()
        if content:
            sections.append({
                "title": current_title,
                "content": content,
            })

    return sections


def process_text(text: str, remove_boiler: bool = True) -> str:
    """
    Full processing pipeline for raw text.

    Args:
        text: Raw text.
        remove_boiler: Whether to remove boilerplate patterns.

    Returns:
        Cleaned, processed text ready for chunking.
    """
    text = clean_text(text)
    if remove_boiler:
        text = remove_boilerplate(text)
    text = clean_text(text)  # second pass to fix any artifacts from removal
    return text
