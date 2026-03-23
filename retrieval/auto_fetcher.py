import logging
import wikipedia
from pipelines.ingest import ingest

logger = logging.getLogger(__name__)

class AutoFetcher:
    def __init__(self):
        # We use the existing pipeline ingest mechanics
        pass
        
    def fetch_and_ingest(self, query: str) -> bool:
        """Searches Wikipedia for the query, and if found, ingests it into ChromaDB."""
        try:
            # Search for the best matching page title
            search_results = wikipedia.search(query, results=1)
            if not search_results:
                logger.info(f"AutoFetcher: No Wikipedia results found for '{query}'.")
                return False
                
            page_title = search_results[0]
            logger.info(f"AutoFetcher: Found conceptual match '{page_title}' for query '{query}'. Downloading...")
            
            # Fetch the actual page url securely
            page = wikipedia.page(page_title, auto_suggest=False)
            url = page.url
            
            # Use the exact same ingest pipeline the user uses
            logger.info(f"AutoFetcher: Auto-ingesting {url} into local knowledge base...")
            result = ingest(url, verbose=False)
            
            if result.get('status') == 'success':
                logger.info(f"AutoFetcher: Successfully expanded knowledge base with {result.get('chunks_stored')} chunks from '{page_title}'.")
                return True
            else:
                logger.warning(f"AutoFetcher: Ingestion failed for '{page_title}'.")
                return False
            
        except wikipedia.exceptions.DisambiguationError as e:
            logger.warning(f"AutoFetcher: Disambiguation error for '{query}': {e.options[:3]}")
            return False
        except wikipedia.exceptions.PageError:
            logger.warning(f"AutoFetcher: Page error for '{query}'.")
            return False
        except Exception as e:
            logger.error(f"AutoFetcher: Unexpected error fetching '{query}': {e}")
            return False
