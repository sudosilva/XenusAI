"""
XenusAI — Niche Tech & Obfuscation Bulk Ingestion
Populates the knowledge base with specific user requests on NanoVG, Vulkan, Obfuscators (ZKM, Skidfuscator), Transpilers, and MC 1.21.11 Mappings.
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("NicheTechIngest")

URLS_AND_FILES = [
    # Rendering & Graphics APIs
    "https://en.wikipedia.org/wiki/Vulkan_(API)",
    "https://en.wikipedia.org/wiki/Subpixel_rendering",
    "https://en.wikipedia.org/wiki/Text_rendering",
    
    # Obfuscation, Anti-Reversal, Transpiling
    "https://en.wikipedia.org/wiki/Obfuscation_(software)",
    "https://en.wikipedia.org/wiki/Control_flow_flattening",
    "https://en.wikipedia.org/wiki/Name_mangling",
    "https://en.wikipedia.org/wiki/Source-to-source_compiler",
    "https://en.wikipedia.org/wiki/ProGuard_(software)",
    
    # The Custom Expert Notes generated via Web Research
    os.path.join(PROJECT_ROOT, "data", "expert_modding_notes.md")
]

def main():
    logger.info("="*50)
    logger.info(f"Starting NICHE TECH & OBFUSCATOR Ingest of {len(URLS_AND_FILES)} advanced sources...")
    logger.info("="*50)
    
    total_chunks = 0
    successful = 0
    
    for i, target in enumerate(URLS_AND_FILES, 1):
        logger.info(f"[{i}/{len(URLS_AND_FILES)}] Ingesting:\n    {target}")
        try:
            result = ingest(target, verbose=False)
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
    logger.info(f"Niche Tech & Obfuscator Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(URLS_AND_FILES)} sources.")
    logger.info(f"Added {total_chunks} NEW hardcore modding chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
