"""
XenusAI — World Knowledge Bulk Ingestion
Populates the knowledge base with AI/ML, Science, History, Economics, and DevOps.
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("WorldIngest")

URLS = [
    # AI & Machine Learning
    "https://en.wikipedia.org/wiki/Machine_learning",
    "https://en.wikipedia.org/wiki/Neural_network",
    "https://en.wikipedia.org/wiki/Deep_learning",
    "https://en.wikipedia.org/wiki/Natural_language_processing",
    "https://en.wikipedia.org/wiki/Transformer_(deep_learning_architecture)",
    "https://en.wikipedia.org/wiki/Large_language_model",
    "https://en.wikipedia.org/wiki/Retrieval-augmented_generation",
    
    # Advanced Tech & DevOps
    "https://en.wikipedia.org/wiki/Git",
    "https://en.wikipedia.org/wiki/Docker_(software)",
    "https://en.wikipedia.org/wiki/Kubernetes",
    "https://en.wikipedia.org/wiki/Linux",
    "https://en.wikipedia.org/wiki/C%2B%2B",
    "https://en.wikipedia.org/wiki/Rust_(programming_language)",
    "https://en.wikipedia.org/wiki/Go_(programming_language)",
    "https://en.wikipedia.org/wiki/Cloud_computing",
    
    # Physics & Advanced Science
    "https://en.wikipedia.org/wiki/Physics",
    "https://en.wikipedia.org/wiki/Quantum_mechanics",
    "https://en.wikipedia.org/wiki/Theory_of_relativity",
    "https://en.wikipedia.org/wiki/Classical_mechanics",
    "https://en.wikipedia.org/wiki/Thermodynamics",
    "https://en.wikipedia.org/wiki/Standard_Model",
    "https://en.wikipedia.org/wiki/Astronomy",
    "https://en.wikipedia.org/wiki/Black_hole",
    
    # Biology & Medical
    "https://en.wikipedia.org/wiki/Biology",
    "https://en.wikipedia.org/wiki/DNA",
    "https://en.wikipedia.org/wiki/Cell_(biology)",
    "https://en.wikipedia.org/wiki/Human_anatomy",
    "https://en.wikipedia.org/wiki/Evolution",
    "https://en.wikipedia.org/wiki/Virus",
    
    # History
    "https://en.wikipedia.org/wiki/History_of_the_world",
    "https://en.wikipedia.org/wiki/Roman_Empire",
    "https://en.wikipedia.org/wiki/Industrial_Revolution",
    "https://en.wikipedia.org/wiki/World_War_I",
    "https://en.wikipedia.org/wiki/World_War_II",
    "https://en.wikipedia.org/wiki/Cold_War",
    "https://en.wikipedia.org/wiki/Information_Age",
    
    # Economics & Finance
    "https://en.wikipedia.org/wiki/Economics",
    "https://en.wikipedia.org/wiki/Microeconomics",
    "https://en.wikipedia.org/wiki/Macroeconomics",
    "https://en.wikipedia.org/wiki/Stock_market",
    "https://en.wikipedia.org/wiki/Cryptocurrency",
    "https://en.wikipedia.org/wiki/Inflation",
    "https://en.wikipedia.org/wiki/Capitalism",
    "https://en.wikipedia.org/wiki/Socialism"
]

def main():
    logger.info("="*50)
    logger.info(f"Starting WORLD KNOWLEDGE Bulk Ingest of {len(URLS)} elite sources...")
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
    logger.info(f"World Knowledge Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(URLS)} sources.")
    logger.info(f"Added {total_chunks} NEW critical knowledge chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
