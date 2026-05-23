"""
Entry-point script to run the full ingestion pipeline.

Usage:
    python ingestion/run_ingestion.py
    python ingestion/run_ingestion.py --force   # re-ingest even if data exists
"""

import argparse
import sys
from pathlib import Path

# Ensure project root is on the path when running this script directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ingestion.quran_ingestor import QuranIngestor
from ingestion.hadith_ingestor import HadithIngestor
from utils.logger import logger


def main() -> None:
    parser = argparse.ArgumentParser(description="HIKMAH AI — Data Ingestion Pipeline")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-ingestion even if data already exists in ChromaDB",
    )
    parser.add_argument(
        "--source",
        choices=["quran", "hadith", "all"],
        default="all",
        help="Which source to ingest (default: all)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("HIKMAH AI — Starting Data Ingestion")
    logger.info("=" * 60)

    if args.source in ("quran", "all"):
        logger.info("--- Quran Ingestion ---")
        ingestor = QuranIngestor()
        count = ingestor.ingest(force=args.force)
        logger.info(f"Quran: {count} verses in ChromaDB")

    if args.source in ("hadith", "all"):
        logger.info("--- Hadith Ingestion ---")
        ingestor = HadithIngestor()
        count = ingestor.ingest(force=args.force)
        logger.info(f"Hadith: {count} records in ChromaDB")

    logger.info("=" * 60)
    logger.info("Ingestion complete. HIKMAH AI is ready.")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
