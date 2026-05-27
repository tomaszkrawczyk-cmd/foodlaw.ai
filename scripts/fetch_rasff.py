#!/usr/bin/env python3
"""
Fetch RASFF (Rapid Alert System for Food and Feed) notifications.

Uses the RASFF portal search API to retrieve notifications about food safety
alerts, border rejections, and information notifications across the EU.

Output: JSON file with notification data, optionally Markdown summaries.
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

RASFF_API_URL = (
    "https://webgate.ec.europa.eu/rasff-window/backend/public/notification/search"
)


def build_search_payload(category="food", page=1, page_size=50):
    """Build the JSON payload for RASFF search API."""
    return {
        "searchTerms": "",
        "notificationTypes": [],
        "productCategory": category,
        "page": page,
        "pageSize": page_size,
    }


def fetch_notifications_page(client, category="food", page=1, page_size=50):
    """
    Fetch a single page of RASFF notifications.

    Returns parsed JSON response or None on failure.
    """
    payload = build_search_payload(category=category, page=page, page_size=page_size)

    try:
        response = client.post(
            RASFF_API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error("Failed to fetch RASFF page %d: %s", page, e)
        return None


def parse_notification(raw):
    """
    Parse a single notification from RASFF API response.

    Extracts key fields, handling missing/unexpected data gracefully.
    Returns a dict with normalized notification data.
    """
    if not isinstance(raw, dict):
        logger.warning("Unexpected notification format: %s", type(raw))
        return None

    try:
        return {
            "reference": raw.get("reference", ""),
            "date": raw.get("date", ""),
            "last_update": raw.get("lastUpdate", ""),
            "notification_type": raw.get("notificationType", ""),
            "subject": raw.get("subject", ""),
            "product_category": raw.get("productCategory", ""),
            "hazard": raw.get("hazard", ""),
            "origin_country": raw.get("originCountry", ""),
            "notification_country": raw.get("notificationCountry", ""),
            "distribution_countries": raw.get("distributionCountries", []),
            "status": raw.get("status", ""),
        }
    except Exception as e:
        logger.warning("Error parsing notification: %s", e)
        return None


def parse_notifications_response(data):
    """
    Parse the full API response and extract notification list.

    Returns a tuple of (notifications_list, total_count).
    """
    if not isinstance(data, dict):
        logger.warning("Unexpected response format: %s", type(data))
        return [], 0

    total = data.get("totalElements", data.get("totalRecords", 0))
    raw_items = data.get("content", data.get("notifications", []))

    if not isinstance(raw_items, list):
        logger.warning("Unexpected items format in response")
        return [], total

    notifications = []
    for item in raw_items:
        parsed = parse_notification(item)
        if parsed:
            notifications.append(parsed)

    return notifications, total


def generate_markdown_summary(notifications):
    """Generate a Markdown summary of fetched notifications."""
    lines = [
        "# RASFF Notifications Summary",
        "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"Total notifications: {len(notifications)}",
        "",
        "## Notifications",
        "",
    ]

    for notif in notifications:
        ref = notif.get("reference", "N/A")
        subject = notif.get("subject", "N/A")
        date = notif.get("date", "N/A")
        ntype = notif.get("notification_type", "N/A")
        lines.append(f"### {ref} ({date})")
        lines.append(f"- **Type:** {ntype}")
        lines.append(f"- **Subject:** {subject}")
        lines.append(f"- **Hazard:** {notif.get('hazard', 'N/A')}")
        lines.append(f"- **Origin:** {notif.get('origin_country', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def save_results(notifications, output_dir, save_markdown=True):
    """Save notifications as JSON and optionally as Markdown summary."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Save JSON
    json_file = output_path / "rasff_notifications.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(notifications, f, ensure_ascii=False, indent=2)
    logger.info("Saved %d notifications to %s", len(notifications), json_file)

    # Save Markdown summary
    if save_markdown:
        md_file = output_path / "rasff_summary.md"
        md_content = generate_markdown_summary(notifications)
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(md_content)
        logger.info("Saved Markdown summary to %s", md_file)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch RASFF notifications from EU Rapid Alert System for Food and Feed"
    )
    parser.add_argument(
        "--output",
        default="./output/rasff/",
        help="Output directory (default: ./output/rasff/)",
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
        "--category",
        default="food",
        help="Product category filter (default: food)",
    )
    parser.add_argument(
        "--no-markdown",
        action="store_true",
        help="Skip Markdown summary generation",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting RASFF notifications fetch...")
    logger.info("Category: %s, Max pages: %d", args.category, args.max_pages)

    # Create HTTP client with retry logic
    client = create_http_client(
        max_retries=3,
        backoff_factor=2.0,
        user_agent_rotate=False,
        timeout=30,
    )

    all_notifications = []

    for page in range(1, args.max_pages + 1):
        logger.info("Fetching page %d...", page)

        data = fetch_notifications_page(
            client, category=args.category, page=page, page_size=50
        )

        if data is None:
            logger.warning("Failed to fetch page %d, stopping.", page)
            break

        notifications, total = parse_notifications_response(data)

        if not notifications:
            logger.info("No more notifications on page %d.", page)
            break

        all_notifications.extend(notifications)
        logger.info(
            "Page %d: got %d notifications (total so far: %d, API total: %d)",
            page,
            len(notifications),
            len(all_notifications),
            total,
        )

        # Check if we have all available notifications
        if len(all_notifications) >= total:
            logger.info("Fetched all available notifications.")
            break

        # Delay between pages
        if page < args.max_pages:
            time.sleep(args.delay)

    # Save results
    if all_notifications:
        save_results(
            all_notifications, args.output, save_markdown=not args.no_markdown
        )
    else:
        logger.warning("No notifications fetched.")

    # Log statistics
    logger.info("=" * 50)
    logger.info("Fetch complete. Total notifications: %d", len(all_notifications))
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
