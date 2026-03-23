import os
import sys
import time
import logging

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ExpertIngestV2")

def run():
    target_file = os.path.join(PROJECT_ROOT, "expert_training_manual_v2.md")
    logger.info("Queuing Expert Hacker Manual V2 (Shell/ASM/PHP) ingestion...")
    
    max_retries = 300
    for i in range(max_retries):
        try:
            logger.info("Attempting specialized ingestion V2...")
            result = ingest(target_file, verbose=False)
            
            if result.get("status") == "success":
                logger.info(f"[SUCCESS] Expert Knowledge V2 successfully wired into XenusAI. ({result.get('chunks_stored')} chunks)")
                os.remove(target_file)
                logger.info("Cleaned up source markdown.")
                break
        except Exception as e:
            if "database is locked" in str(e).lower() or "timeout" in str(e).lower():
                time.sleep(15)
            else:
                logger.error(f"Unexpected embed error: {e}")
                time.sleep(10)

if __name__ == "__main__":
    run()
