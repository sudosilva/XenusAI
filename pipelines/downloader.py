"""
XenusAI — Downloader
Downloads content from URLs and reads local files.
Supports: URLs (HTML pages), .txt, .md, .html, .pdf, .docx
"""

import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

import requests
import chardet

logger = logging.getLogger(__name__)


def _detect_encoding(raw_bytes: bytes) -> str:
    """Detect text encoding of raw bytes."""
    result = chardet.detect(raw_bytes)
    return result.get("encoding") or "utf-8"


def download_url(url: str, save_raw: bool = True) -> dict:
    """
    Download and extract text content from a URL.

    Args:
        url: The web URL to download.
        save_raw: Whether to save the raw HTML to data/raw/.

    Returns:
        dict with keys: text, title, source, source_type, timestamp
    """
    from config import RAW_DIR

    logger.info(f"Downloading: {url}")

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Failed to download {url}: {e}")
        raise

    raw_html = response.text

    # Save raw HTML if requested
    if save_raw:
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        raw_path = RAW_DIR / f"url_{url_hash}.html"
        raw_path.write_text(raw_html, encoding="utf-8")
        logger.info(f"Raw HTML saved to {raw_path}")

    # Extract clean text using trafilatura (best for article extraction)
    try:
        import trafilatura

        downloaded = trafilatura.fetch_url(url)
        text = trafilatura.extract(
            downloaded,
            include_comments=False,
            include_tables=True,
            include_links=False,
            include_images=False,
            favor_recall=True,   # extract more content
        )

        # Fallback: try extracting directly from our fetched HTML
        if not text:
            text = trafilatura.extract(
                raw_html,
                include_comments=False,
                include_tables=True,
                include_links=False,
                include_images=False,
                favor_recall=True,
            )
    except ImportError:
        text = None

    # Fallback to BeautifulSoup if trafilatura fails
    if not text:
        text = _extract_with_bs4(raw_html)

    # Try to get the title
    title = _extract_title(raw_html) or url

    return {
        "text": text or "",
        "title": title,
        "source": url,
        "source_type": "url",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def read_file(file_path: str, save_raw: bool = True) -> dict:
    """
    Read text content from a local file.

    Supports: .txt, .md, .html, .htm, .pdf, .docx

    Args:
        file_path: Path to the local file.
        save_raw: Whether to copy the file to data/raw/.

    Returns:
        dict with keys: text, title, source, source_type, timestamp
    """
    from config import RAW_DIR

    path = Path(file_path).resolve()

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()
    logger.info(f"Reading file: {path} (type: {suffix})")

    # Save a copy to raw/
    if save_raw:
        import shutil
        dest = RAW_DIR / f"file_{path.name}"
        shutil.copy2(path, dest)

    # Extract text based on file type
    if suffix in (".txt", ".md", ".log", ".csv", ".json"):
        raw_bytes = path.read_bytes()
        encoding = _detect_encoding(raw_bytes)
        text = raw_bytes.decode(encoding, errors="replace")

    elif suffix in (".html", ".htm"):
        raw_bytes = path.read_bytes()
        encoding = _detect_encoding(raw_bytes)
        html = raw_bytes.decode(encoding, errors="replace")
        try:
            import trafilatura
            text = trafilatura.extract(html, favor_recall=True)
            if not text:
                text = _extract_with_bs4(html)
        except ImportError:
            text = _extract_with_bs4(html)

    elif suffix == ".pdf":
        text = _read_pdf(path)

    elif suffix == ".docx":
        text = _read_docx(path)

    else:
        # Try reading as plain text
        raw_bytes = path.read_bytes()
        encoding = _detect_encoding(raw_bytes)
        text = raw_bytes.decode(encoding, errors="replace")

    return {
        "text": text or "",
        "title": path.stem,
        "source": str(path),
        "source_type": "file",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def read_directory(dir_path: str, extensions: Optional[list] = None) -> list:
    """
    Read all supported files from a directory (non-recursive by default).

    Args:
        dir_path: Path to directory.
        extensions: List of extensions to include (e.g. ['.txt', '.md']).
                   If None, includes all supported types.

    Returns:
        List of result dicts from read_file().
    """
    supported = extensions or [
        ".txt", ".md", ".html", ".htm", ".pdf", ".docx",
        ".log", ".csv", ".json",
    ]

    directory = Path(dir_path).resolve()
    if not directory.is_dir():
        raise NotADirectoryError(f"Not a directory: {directory}")

    results = []
    for file in sorted(directory.iterdir()):
        if file.is_file() and file.suffix.lower() in supported:
            try:
                result = read_file(str(file))
                results.append(result)
            except Exception as e:
                logger.warning(f"Skipping {file.name}: {e}")

    logger.info(f"Read {len(results)} files from {directory}")
    return results


# ─── Private Helpers ────────────────────────────────────────────

def _extract_with_bs4(html: str) -> str:
    """Fallback HTML text extraction using BeautifulSoup."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    # Remove script, style, nav, footer, header elements
    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)

    return text


def _extract_title(html: str) -> Optional[str]:
    """Extract page title from HTML."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")

    # Try <title> tag first
    if soup.title and soup.title.string:
        return soup.title.string.strip()

    # Try first <h1>
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)

    return None


def _read_pdf(path: Path) -> str:
    """Extract text from a PDF file."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
        return "\n\n".join(pages)
    except ImportError:
        logger.warning("PyPDF2 not installed — skipping PDF extraction")
        return ""
    except Exception as e:
        logger.error(f"PDF extraction failed for {path}: {e}")
        return ""


def _read_docx(path: Path) -> str:
    """Extract text from a .docx file."""
    try:
        from docx import Document
        doc = Document(str(path))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except ImportError:
        logger.warning("python-docx not installed — skipping DOCX extraction")
        return ""
    except Exception as e:
        logger.error(f"DOCX extraction failed for {path}: {e}")
        return ""
