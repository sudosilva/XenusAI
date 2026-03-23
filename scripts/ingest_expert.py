import os
import sys
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExpertIngest")

def run():
    target_file = os.path.join(PROJECT_ROOT, "expert_training_manual.md")
    logger.info("Queuing Expert Hacker Manual ingestion...")
    logger.info("Waiting for primary Wikipedia bulk ingestion to release SQLite lock...")
    
    max_retries = 300  # Up to 2 hours of retry polling
    for i in range(max_retries):
        try:
            logger.info("Attempting specialized ingestion...")
            result = ingest(target_file, verbose=False)
            
            if result.get("status") == "success":
                logger.info(f"[SUCCESS] Expert Knowledge base successfully wired into XenusAI. ({result.get('chunks_stored')} chunks)")
                # Delete file after ingestion to keep repo clean
                os.remove(target_file)
                logger.info("Cleaned up source markdown.")
                break
        except Exception as e:
            if "database is locked" in str(e).lower() or "timeout" in str(e).lower():
                logger.info(f"Database currently locked by main Wikipedia ingest thread. Waiting 20 seconds... (Attempt {i}/{max_retries})")
                time.sleep(20)
            else:
                logger.error(f"Unexpected embed error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    run()
