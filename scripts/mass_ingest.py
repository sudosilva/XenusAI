import os
import sys
import time
import logging
import wikipedia

# Ensure backend imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("MassIngest")

# 10 categories, 100 articles each = 1,000 elite knowledge bases
CATEGORIES = [
    "Artificial Intelligence algorithms",
    "Quantum Mechanics and Physics",
    "Software Engineering patterns",
    "Cybersecurity and Cryptography",
    "World War II timeline",
    "Advanced Mathematics and Calculus",
    "Philosophy and Ethics",
    "Macroeconomics and Markets",
    "Space Exploration and Astronomy",
    "History of Computing and the Internet"
]

def run_mass_ingest():
    logger.info("Initializing Master Knowledge Ingestion Protocol (1,000 Pages)...")
    
    total_successful = 0
    target = 1000
    
    for category in CATEGORIES:
        logger.info(f"==> Searching for 100 topics in: {category}")
        try:
            topics = wikipedia.search(category, results=100)
            for topic in topics:
                if total_successful >= target:
                    break
                    
                try:
                    page = wikipedia.page(topic, auto_suggest=False)
                    url = page.url
                    logger.info(f"[{total_successful+1}/{target}] Scraping: {page.title}")
                    
                    result = ingest(url, verbose=False)
                    if result.get('status') == 'success':
                        total_successful += 1
                        logger.info(f"    [+] Success! Memory expanded by {result.get('chunks_stored')} chunks. ({total_successful}/{target})")
                    else:
                        logger.warning(f"    [-] Failed to ingest {url}")
                        
                except wikipedia.exceptions.DisambiguationError as e:
                    logger.warning(f"    [-] Disambiguation hit for '{topic}', skipping.")
                except wikipedia.exceptions.PageError:
                    logger.warning(f"    [-] Page missing for '{topic}', skipping.")
                except Exception as e:
                    logger.error(f"    [-] Error on '{topic}': {e}")
                    
                # Small sleep to prevent Wikipedia API bans
                time.sleep(0.2)
                
        except Exception as e:
            logger.error(f"Category search failed for {category}: {e}")
            
    logger.info(f"MASS INGESTION COMPLETE. Successfully downloaded and stored {total_successful} elite knowledge pages into ChromaDB.")

if __name__ == "__main__":
    run_mass_ingest()
