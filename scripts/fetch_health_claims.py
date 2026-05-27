#!/usr/bin/env python3
"""
Fetch EU health claims register data.

Uses the EU food/feed portal backend API to retrieve authorized and
non-authorized nutrition and health claims from the EU Register.

Output: JSON file with claims data.
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

HEALTH_CLAIMS_API_URL = (
    "https://ec.europa.eu/food/food-feed-portal/backend/claims/search"
)


def build_search_payload(status="all", page=0, page_size=50):
    """
    Build the JSON payload for health claims search API.

    Args:
        status: Filter by claim status - 'authorized', 'non-authorized', or 'all'
        page: Page number (0-indexed)
        page_size: Number of results per page
    """
    payload = {
        "pageNumber": page,
        "pageSize": page_size,
        "searchTerms": "",
    }

    if status == "authorized":
        payload["claimStatus"] = ["AUTHORISED"]
    elif status == "non-authorized":
        payload["claimStatus"] = ["NON_AUTHORISED"]
    # For 'all' we don't filter by status

    return payload


def fetch_claims_page(client, status="all", page=0, page_size=50):
    """
    Fetch a single page of health claims.

    Returns parsed JSON response or None on failure.
    """
    payload = build_search_payload(status=status, page=page, page_size=page_size)

    try:
        response = client.post(
            HEALTH_CLAIMS_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Failed to fetch health claims page %d: %s", page, e)
        return None


def parse_claim(raw):
    """
    Parse a single claim from the API response.

    Extracts key fields, handling missing/unexpected data gracefully.
    Returns a dict with normalized claim data.
    """
    if not isinstance(raw, dict):
        logger.warning("Unexpected claim format: %s", type(raw))
        return None

    try:
        return {
            "id": raw.get("id", ""),
            "claim_wording": raw.get("claimWording", raw.get("wording", "")),
            "conditions_of_use": raw.get("conditionsOfUse", ""),
            "status": raw.get("claimStatus", raw.get("status", "")),
            "food_category": raw.get("foodCategory", raw.get("category", "")),
            "nutrient_substance": raw.get(
                "nutrientSubstance", raw.get("substance", "")
            ),
            "regulation_reference": raw.get("regulationReference", ""),
            "entry_type": raw.get("entryType", ""),
        }
    except Exception as e:
        logger.warning("Error parsing claim: %s", e)
        return None


def parse_claims_response(data):
    """
    Parse the full API response and extract claims list.

    Returns a tuple of (claims_list, total_count).
    """
    if not isinstance(data, dict):
        logger.warning("Unexpected response format: %s", type(data))
        return [], 0

    total = data.get("totalElements", data.get("totalRecords", 0))
    raw_items = data.get("content", data.get("claims", data.get("results", [])))

    if not isinstance(raw_items, list):
        logger.warning("Unexpected items format in response")
        return [], total

    claims = []
    for item in raw_items:
        parsed = parse_claim(item)
        if parsed:
            claims.append(parsed)

    return claims, total


def save_results(claims, output_dir):
    """Save claims as JSON."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_file = output_path / "health_claims.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(
            {
                "fetched_at": datetime.now().isoformat(),
                "total_claims": len(claims),
                "claims": claims,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    logger.info("Saved %d claims to %s", len(claims), json_file)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch EU health claims register data from the food/feed portal"
    )
    parser.add_argument(
        "--output",
        default="./output/health-claims/",
        help="Output directory (default: ./output/health-claims/)",
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
    parser.add_argument(
        "--status",
        choices=["authorized", "non-authorized", "all"],
        default="all",
        help="Filter by claim status (default: all)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting EU health claims fetch...")
    logger.info("Status filter: %s, Max pages: %d", args.status, args.max_pages)

    # Create HTTP client with retry logic
    client = create_http_client(
        max_retries=3,
        backoff_factor=2.0,
        user_agent_rotate=False,
        timeout=30,
    )

    all_claims = []

    for page in range(args.max_pages):
        logger.info("Fetching page %d...", page + 1)

        data = fetch_claims_page(
            client, status=args.status, page=page, page_size=50
        )

        if data is None:
            logger.warning("Failed to fetch page %d, stopping.", page + 1)
            break

        claims, total = parse_claims_response(data)

        if not claims:
            logger.info("No more claims on page %d.", page + 1)
            break

        all_claims.extend(claims)
        logger.info(
            "Page %d: got %d claims (total so far: %d, API total: %d)",
            page + 1,
            len(claims),
            len(all_claims),
            total,
        )

        # Check if we have all available claims
        if len(all_claims) >= total:
            logger.info("Fetched all available claims.")
            break

        # Delay between pages
        if page < args.max_pages - 1:
            time.sleep(args.delay)

    # Save results
    if all_claims:
        save_results(all_claims, args.output)
    else:
        logger.warning("No claims fetched.")

    # Log statistics
    logger.info("=" * 50)
    logger.info("Fetch complete. Total claims: %d", len(all_claims))
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
