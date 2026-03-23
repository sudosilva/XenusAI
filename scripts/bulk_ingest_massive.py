"""
XenusAI — Massive Bulk Ingestion Script
Populates the knowledge base with Math, CS, Programming, and Graphics.
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("MassiveIngest")

URLS = [
    # Mathematics
    "https://en.wikipedia.org/wiki/Algebra",
    "https://en.wikipedia.org/wiki/Calculus",
    "https://en.wikipedia.org/wiki/Trigonometry",
    "https://en.wikipedia.org/wiki/Geometry",
    "https://en.wikipedia.org/wiki/Linear_algebra",
    "https://en.wikipedia.org/wiki/Discrete_mathematics",
    
    # Computer Science & Algorithms
    "https://en.wikipedia.org/wiki/Computer_science",
    "https://en.wikipedia.org/wiki/Sorting_algorithm",
    "https://en.wikipedia.org/wiki/Time_complexity",
    "https://en.wikipedia.org/wiki/Systems_design",
    "https://en.wikipedia.org/wiki/Operating_system",
    "https://en.wikipedia.org/wiki/Computer_network",
    "https://en.wikipedia.org/wiki/Database",
    "https://en.wikipedia.org/wiki/Artificial_intelligence",
    
    # Programming Languages
    "https://en.wikipedia.org/wiki/Java_(programming_language)",
    "https://en.wikipedia.org/wiki/Python_(programming_language)",
    "https://en.wikipedia.org/wiki/JavaScript",
    "https://en.wikipedia.org/wiki/HTML",
    "https://en.wikipedia.org/wiki/CSS",
    "https://developer.mozilla.org/en-US/docs/Learn/CSS/First_steps/What_is_CSS",
    "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/First_steps/What_is_JavaScript",
    
    # Graphics
    "https://en.wikipedia.org/wiki/OpenGL",
    "https://en.wikipedia.org/wiki/Computer_graphics",
    "https://en.wikipedia.org/wiki/Vector_graphics",
    "https://en.wikipedia.org/wiki/Shading_language",
    
    # Minecraft / Modding
    "https://en.wikipedia.org/wiki/Minecraft",
    "https://fabricmc.net/wiki/tutorial:setup"
]

def main():
    logger.info("="*50)
    logger.info(f"Starting MASSIVE Bulk Ingest of {len(URLS)} top-tier sources...")
    logger.info("="*50)
    
    total_chunks = 0
    successful = 0
    
    for i, url in enumerate(URLS, 1):
        logger.info(f"[{i}/{len(URLS)}] Ingesting: {url}")
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
    logger.info(f"Massive Bulk Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(URLS)} sources.")
    logger.info(f"Added {total_chunks} NEW total knowledge chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
