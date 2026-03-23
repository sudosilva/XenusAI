"""
XenusAI — Bulk Ingestion Script
Feeds the knowledge base with high-quality reference data.
"""

import os
import sys
import logging

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("BulkIngest")

# High-quality technical sources
SOURCES = [
    # General CS & Algorithms
    "https://en.wikipedia.org/wiki/Algorithm",
    "https://en.wikipedia.org/wiki/Data_structure",
    "https://en.wikipedia.org/wiki/Hash_table",
    "https://en.wikipedia.org/wiki/Binary_search_tree",
    "https://en.wikipedia.org/wiki/Dynamic_programming",
    "https://en.wikipedia.org/wiki/Graph_theory",
    
    # Modern Web Dev
    "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction",
    "https://developer.mozilla.org/en-US/docs/Web/HTML",
    "https://developer.mozilla.org/en-US/docs/Web/CSS",
    "https://react.dev/learn",
    
    # Python & Systems
    "https://docs.python.org/3/tutorial/index.html",
    "https://en.wikipedia.org/wiki/Garbage_collection_(computer_science)",
    "https://en.wikipedia.org/wiki/Virtual_memory",
    
    # Minecraft Tech
    "https://minecraft.wiki/w/Redstone",
    "https://minecraft.wiki/w/Command",
    "https://minecraft.wiki/w/Tick"
]

def main():
    logger.info("="*50)
    logger.info(f"Starting Bulk Ingest of {len(SOURCES)} sources...")
    logger.info("="*50)
    
    total_chunks = 0
    successful = 0
    
    for i, url in enumerate(SOURCES, 1):
        logger.info(f"[{i}/{len(SOURCES)}] Ingesting: {url}")
        try:
            result = ingest(url, verbose=False)
            if result.get("status") == "success":
                chunks = result.get("chunks_stored", 0)
                total_chunks += chunks
                successful += 1
                logger.info(f"  ✓ Success: extracted {chunks} chunks")
            else:
                logger.error(f"  ✗ Failed: {result.get('message', 'Unknown error')}")
        except Exception as e:
            logger.error(f"  ✗ Exception: {e}")
            
    logger.info("="*50)
    logger.info(f"Bulk Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(SOURCES)} sources.")
    logger.info(f"Added {total_chunks} total knowledge chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
