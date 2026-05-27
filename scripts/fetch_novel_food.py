#!/usr/bin/env python3
"""
Fetch Novel Food catalogue and Union List data.

Uses the EU food/feed portal backend API to retrieve entries from the
Novel Food catalogue, including authorization status and categories.

Output: JSON file with novel food entries.
"""

import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.http_client import create_http_client

logger = logging.getLogger(__name__)

NOVEL_FOOD_API_URL = (
    "https://ec.europa.eu/food/food-feed-portal/backend/novel-food-catalogue/search"
)


def build_search_payload(page=0, page_size=50):
    """Build the JSON payload for Novel Food catalogue search API."""
    return {
        "pageNumber": page,
        "pageSize": page_size,
        "searchTerms": "",
    }


def fetch_novel_food_page(client, page=0, page_size=50):
    """
    Fetch a single page of Novel Food catalogue entries.

    Returns parsed JSON response or None on failure.
    """
    payload = build_search_payload(page=page, page_size=page_size)

    try:
        response = client.post(
            NOVEL_FOOD_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Failed to fetch novel food page %d: %s", page, e)
        return None


def parse_novel_food_entry(raw):
    """
    Parse a single entry from the Novel Food catalogue API response.

    Extracts key fields, handling missing/unexpected data gracefully.
    Returns a dict with normalized entry data.
    """
    if not isinstance(raw, dict):
        logger.warning("Unexpected entry format: %s", type(raw))
        return None

    try:
        return {
            "name": raw.get("name", raw.get("title", "")),
            "status": raw.get("status", raw.get("authorisationStatus", "")),
            "category": raw.get("category", raw.get("foodCategory", "")),
            "applicant": raw.get("applicant", ""),
            "date": raw.get("date", raw.get("authorisationDate", "")),
            "regulation": raw.get("regulation", raw.get("regulationReference", "")),
            "conditions": raw.get("conditions", raw.get("conditionsOfUse", "")),
            "specifications": raw.get("specifications", ""),
        }
    except Exception as e:
        logger.warning("Error parsing novel food entry: %s", e)
        return None


def parse_novel_food_response(data):
    """
    Parse the full API response and extract novel food entries.

    Returns a tuple of (entries_list, total_count).
    """
    if not isinstance(data, dict):
        logger.warning("Unexpected response format: %s", type(data))
        return [], 0

    total = data.get("totalElements", data.get("totalRecords", 0))
    raw_items = data.get("content", data.get("entries", data.get("results", [])))

    if not isinstance(raw_items, list):
        logger.warning("Unexpected items format in response")
        return [], total

    entries = []
    for item in raw_items:
        parsed = parse_novel_food_entry(item)
        if parsed:
            entries.append(parsed)

    return entries, total


def save_results(entries, output_dir):
    """Save novel food entries as JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_file = output_path / "novel_food_catalogue.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at": datetime.now().isoformat(),
                "total_entries": len(entries),
                "entries": entries,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("Saved %d entries to %s", len(entries), json_file)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch Novel Food catalogue data from the EU food/feed portal"
    )
    parser.add_argument(
        "--output",
        default="./output/novel-food/",
        help="Output directory (default: ./output/novel-food/)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=5,
        help="Maximum number of pages to fetch (default: 5)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting Novel Food catalogue fetch...")
    logger.info("Max pages: %d", args.max_pages)

    # Create HTTP client with retry logic
    client = create_http_client(
        max_retries=3,
        backoff_factor=2.0,
        user_agent_rotate=False,
        timeout=30,
    )

    all_entries = []

    for page in range(args.max_pages):
        logger.info("Fetching page %d...", page + 1)

        data = fetch_novel_food_page(client, page=page, page_size=50)

        if data is None:
            logger.warning("Failed to fetch page %d, stopping.", page + 1)
            break

        entries, total = parse_novel_food_response(data)

        if not entries:
            logger.info("No more entries on page %d.", page + 1)
            break

        all_entries.extend(entries)
        logger.info(
            "Page %d: got %d entries (total so far: %d, API total: %d)",
            page + 1,
            len(entries),
            len(all_entries),
            total,
        )

        # Check if we have all available entries
        if len(all_entries) >= total:
            logger.info("Fetched all available entries.")
            break

        # Delay between pages
        if page < args.max_pages - 1:
            time.sleep(args.delay)

    # Save results
    if all_entries:
        save_results(all_entries, args.output)
    else:
        logger.warning("No novel food entries fetched.")

    # Log statistics
    logger.info("=" * 50)
    logger.info("Fetch complete. Total entries: %d", len(all_entries))
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
