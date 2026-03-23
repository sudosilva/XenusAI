"""
XenusAI — Behavioral & Linguistic Bulk Ingestion
Populates the knowledge base with Psychology, Cognitive Biases, Linguistics, and Logic.
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("PsychoIngest")

URLS = [
    # Psychology & Neuroscience
    "https://en.wikipedia.org/wiki/Psychology",
    "https://en.wikipedia.org/wiki/Cognitive_psychology",
    "https://en.wikipedia.org/wiki/Behaviorism",
    "https://en.wikipedia.org/wiki/Clinical_psychology",
    "https://en.wikipedia.org/wiki/Neuroscience",
    
    # Biases and Logic
    "https://en.wikipedia.org/wiki/Cognitive_bias",
    "https://en.wikipedia.org/wiki/List_of_cognitive_biases",
    "https://en.wikipedia.org/wiki/Logic",
    "https://en.wikipedia.org/wiki/Critical_thinking",
    
    # Truth & Objectivity
    "https://en.wikipedia.org/wiki/Truth",
    "https://en.wikipedia.org/wiki/Objectivity_(philosophy)",
    "https://en.wikipedia.org/wiki/Fact",
    "https://en.wikipedia.org/wiki/Epistemology",
    
    # Dictionary, Linguistics, & Language
    "https://en.wikipedia.org/wiki/Dictionary",
    "https://en.wikipedia.org/wiki/Linguistics",
    "https://en.wikipedia.org/wiki/English_language",
    "https://en.wikipedia.org/wiki/Etymology",
    "https://en.wikipedia.org/wiki/Semantics",
    "https://en.wikipedia.org/wiki/Oxford_English_Dictionary"
]

def main():
    logger.info("="*50)
    logger.info(f"Starting PSYCHOLOGY & LANGUAGE Ingest of {len(URLS)} elite sources...")
    logger.info("="*50)
    
    total_chunks = 0
    successful = 0
    
    for i, url in enumerate(URLS, 1):
        logger.info(f"[{i}/{len(URLS)}] Ingesting:\n    {url}")
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
    logger.info(f"Behavioral & Linguistic Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(URLS)} sources.")
    logger.info(f"Added {total_chunks} NEW psychological/linguistic chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
