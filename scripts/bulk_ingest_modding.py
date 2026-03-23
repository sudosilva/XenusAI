"""
XenusAI — Advanced Game Modding & Graphics Ingestion
Populates the knowledge base with Graphics Math, Coordinate Systems, JVMTI, ASM, Hooking, and Fabric Modding.
"""

import os
import sys
import logging

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from pipelines.ingest import ingest

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("ModdingIngest")

URLS = [
    # 3D Coordinates & Graphics Rendering
    "https://en.wikipedia.org/wiki/Cartesian_coordinate_system",
    "https://en.wikipedia.org/wiki/3D_projection",
    "https://en.wikipedia.org/wiki/Viewing_frustum",
    "https://en.wikipedia.org/wiki/Hidden-surface_determination",
    "https://en.wikipedia.org/wiki/Transformation_matrix",
    "https://en.wikipedia.org/wiki/Euler_angles",
    "https://en.wikipedia.org/wiki/Quaternions_and_spatial_rotation",
    "https://en.wikipedia.org/wiki/Computer_graphics_pipeline",
    "https://en.wikipedia.org/wiki/Z-buffering",
    "https://en.wikipedia.org/wiki/Ray_tracing_(graphics)",
    
    # JVM, JVMTI, Bytecode, & Modding
    "https://en.wikipedia.org/wiki/Java_Virtual_Machine_Tools_Interface",
    "https://en.wikipedia.org/wiki/Java_Native_Interface",
    "https://en.wikipedia.org/wiki/Java_bytecode",
    "https://en.wikipedia.org/wiki/Instrumentation_(computer_programming)",
    "https://en.wikipedia.org/wiki/Bytecode",
    "https://en.wikipedia.org/wiki/Hooking",
    "https://en.wikipedia.org/wiki/Software_modding",
    "https://en.wikipedia.org/wiki/Reverse_engineering",
    "https://en.wikipedia.org/wiki/Reflection_(computer_programming)",
    
    # Minecraft Fabric
    "https://wiki.fabricmc.net/tutorial:setup",
    "https://wiki.fabricmc.net/tutorial:mixin",
    "https://wiki.fabricmc.net/tutorial:events",
    "https://wiki.fabricmc.net/tutorial:callbacks",
    "https://wiki.fabricmc.net/tutorial:commands",
    "https://wiki.fabricmc.net/tutorial:networking"
]

def main():
    logger.info("="*50)
    logger.info(f"Starting MODDING & GRAPHICS Ingest of {len(URLS)} advanced sources...")
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
    logger.info(f"Modding & Graphics Ingest Complete!")
    logger.info(f"Successfully processed {successful}/{len(URLS)} sources.")
    logger.info(f"Added {total_chunks} NEW hardcore modding chunks to ChromaDB.")
    logger.info("="*50)

if __name__ == "__main__":
    main()
