#!/usr/bin/env python3
"""
Fetch CJEU judgments from EUR-Lex via SOAP Web Service.

Uses the EUR-Lex Web Service (doQuery) to search for judgments by CELEX number,
then downloads HTML and converts to Markdown with YAML front-matter.

Falls back to direct HTML download if SOAP authentication fails.
"""

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

import html2text
import requests
from dotenv import load_dotenv

# Load .env from project root (two levels up from scripts/)
load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / ".env")

logger = logging.getLogger(__name__)

EURLEX_WSDL = "https://eur-lex.europa.eu/EURLexWebService?wsdl"
EURLEX_HTML_URL = "https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"

DEFAULT_JUDGMENT_CELEX_NUMBERS = [
    "62012CJ0299",  # C-299/12 - Deutsches Weintor, health claims wine
    "62018CJ0663",  # C-663/18 - B.D./novel food CBD
    "62012CJ0609",  # C-609/12 - Ehrmann, health claims
    "62014CJ0195",  # C-195/14 - Teekanne, misleading labelling
    "62009CJ0382",  # C-382/09 - Stichting Natuur en Milieu
    "62001CJ0236",  # C-236/01 - Monsanto, precautionary principle
    "62007CJ0140",  # C-140/07 - Hecht-Pharma, food/medicine borderline
    "62010CJ0544",  # C-544/10 - Deutsches Weintor, health claims
    "62017CJ0616",  # C-616/17 - Procureur de la Republique
    "62004CJ0210",  # C-210/04 - FCE Bank
]


def get_credentials():
    """Load EUR-Lex credentials from environment variables."""
    username = os.environ.get("EURLEX_USERNAME")
    password = os.environ.get("EURLEX_PASSWORD")
    return username, password


def create_soap_client(username, password):
    """Create a SOAP client for EUR-Lex Web Service with WS-Security."""
    try:
        from zeep import Client
        from zeep.wsse.username import UsernameToken

        wsse = UsernameToken(username, password)
        client = Client(EURLEX_WSDL, wsse=wsse)
        return client
    except Exception as e:
        logger.error(f"Failed to create SOAP client: {e}")
        return None


def build_expert_query_by_celex(celex):
    """Build expert query to search by CELEX number."""
    return f"SELECT DN WHERE DN = {celex}"


def build_expert_query_food_legislation():
    """Build expert query for food legislation judgments (directory code 03.65)."""
    return "SELECT CT WHERE CT = 6 AND DD = 03.65"


def soap_do_query(client, expert_query, page=1, page_size=10, language="PL"):
    """Execute doQuery on the EUR-Lex SOAP Web Service."""
    try:
        result = client.service.doQuery(
            expertQuery=expert_query,
            page=page,
            pageSize=page_size,
            searchLanguage=language,
        )
        return result
    except Exception as e:
        logger.error(f"SOAP doQuery failed: {e}")
        raise


def fetch_html_with_retry(url, max_retries=3, delay=2.0):
    """Fetch HTML from URL with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code == 403:
                logger.warning(f"403 Forbidden for {url}")
                raise
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                logger.warning(f"Timeout on attempt {attempt + 1}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                wait = delay * (2 ** attempt)
                logger.warning(f"Connection error on attempt {attempt + 1}. Retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise
    return None


def convert_html_to_markdown(html_content):
    """Convert HTML content to Markdown using html2text."""
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width = 0
    return converter.handle(html_content)


def parse_celex_to_case_info(celex):
    """
    Parse a CELEX number to extract case info.

    Example: 62012CJ0299 -> year=2012, case_number=299, type=CJ
    """
    match = re.match(r"^6(\d{4})(CJ|CO|CC|CT)(\d+)$", celex)
    if not match:
        return None
    year = match.group(1)
    case_number = str(int(match.group(3)))  # Remove leading zeros
    return {
        "year": year,
        "case_number": case_number,
        "short_year": year[2:],
    }


def generate_judgment_filename(celex, date=None):
    """
    Generate filename for a judgment.

    Format: {date}-C-{number}-{short_year}.md
    Example: 2013-10-03-C-299-12.md
    """
    info = parse_celex_to_case_info(celex)
    if not info:
        return f"unknown-{celex}.md"

    case_part = f"C-{info['case_number']}-{info['short_year']}"

    if date:
        return f"{date}-{case_part}.md"
    else:
        return f"unknown-date-{case_part}.md"


def generate_front_matter(celex, title=None, date=None, language="PL"):
    """Generate YAML front-matter for a judgment file."""
    source_url = EURLEX_HTML_URL.format(language=language, celex=celex)
    lines = ["---"]
    lines.append(f"celex: \"{celex}\"")
    if title:
        # Escape quotes in title
        escaped_title = title.replace('"', '\\"')
        lines.append(f"title: \"{escaped_title}\"")
    if date:
        lines.append(f"date: \"{date}\"")
    lines.append(f"source_url: \"{source_url}\"")
    lines.append("---")
    return "\n".join(lines)


def extract_date_from_html(html_content):
    """Try to extract judgment date from HTML content."""
    # Look for date patterns in the HTML (common EUR-Lex format)
    patterns = [
        r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
        r"(\d{1,2})\s+(stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|wrze[sś]nia|pa[zź]dziernika|listopada|grudnia)\s+(\d{4})",
        r"(\d{4})-(\d{2})-(\d{2})",
    ]

    month_map_en = {
        "January": "01", "February": "02", "March": "03", "April": "04",
        "May": "05", "June": "06", "July": "07", "August": "08",
        "September": "09", "October": "10", "November": "11", "December": "12",
    }

    month_map_pl = {
        "stycznia": "01", "lutego": "02", "marca": "03", "kwietnia": "04",
        "maja": "05", "czerwca": "06", "lipca": "07", "sierpnia": "08",
    }
    # Add Polish months with special chars
    month_map_pl["wrze\u015bnia"] = "09"
    month_map_pl["wrzesnia"] = "09"
    month_map_pl["pa\u017adziernika"] = "10"
    month_map_pl["pazdziernika"] = "10"
    month_map_pl["listopada"] = "11"
    month_map_pl["grudnia"] = "12"

    # Try English date pattern
    match = re.search(patterns[0], html_content)
    if match:
        day = match.group(1).zfill(2)
        month = month_map_en.get(match.group(2), "01")
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # Try Polish date pattern
    match = re.search(patterns[1], html_content)
    if match:
        day = match.group(1).zfill(2)
        month = month_map_pl.get(match.group(2), "01")
        year = match.group(3)
        return f"{year}-{month}-{day}"

    # Try ISO date pattern
    match = re.search(patterns[2], html_content)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

    return None


def fetch_judgment(celex, language="PL", soap_client=None, delay=2.0):
    """
    Fetch a single judgment by CELEX number.

    Tries SOAP first, falls back to direct HTML download.
    Returns dict with 'html', 'markdown', 'date', 'title' or None on failure.
    """
    html_content = None
    soap_success = False

    # Try SOAP query first
    if soap_client:
        try:
            query = build_expert_query_by_celex(celex)
            result = soap_do_query(soap_client, query, page=1, page_size=1, language=language)
            logger.info(f"SOAP query successful for {celex}")
            soap_success = True
        except Exception as e:
            logger.warning(f"SOAP query failed for {celex}: {e}. Falling back to direct download.")

    # Download HTML (either after SOAP or as fallback)
    url = EURLEX_HTML_URL.format(language=language, celex=celex)
    try:
        html_content = fetch_html_with_retry(url, max_retries=3, delay=delay)
    except Exception as e:
        logger.error(f"Failed to download HTML for {celex}: {e}")
        return None

    if not html_content:
        return None

    # Convert to markdown
    markdown_content = convert_html_to_markdown(html_content)

    # Extract date
    date = extract_date_from_html(html_content)

    # Extract title (first non-empty line of markdown, simplified)
    title = None
    for line in markdown_content.split("\n"):
        stripped = line.strip().strip("#").strip()
        if stripped and len(stripped) > 5:
            title = stripped[:200]
            break

    return {
        "html": html_content,
        "markdown": markdown_content,
        "date": date,
        "title": title,
        "soap_used": soap_success,
    }


def save_judgment(celex, judgment_data, output_dir, language="PL"):
    """Save judgment to output directory as markdown file with front-matter."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    filename = generate_judgment_filename(celex, date=judgment_data.get("date"))
    filepath = output_path / filename

    front_matter = generate_front_matter(
        celex=celex,
        title=judgment_data.get("title"),
        date=judgment_data.get("date"),
        language=language,
    )

    content = front_matter + "\n\n" + judgment_data["markdown"]

    filepath.write_text(content, encoding="utf-8")
    logger.info(f"Saved: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="Fetch CJEU judgments from EUR-Lex via SOAP Web Service"
    )
    parser.add_argument(
        "--celex",
        nargs="*",
        default=None,
        help="CELEX number(s) to fetch. If not provided, uses default list.",
    )
    parser.add_argument(
        "--output",
        default="./orzecznictwo/tsue/",
        help="Output directory (default: ./orzecznictwo/tsue/)",
    )
    parser.add_argument(
        "--language",
        default="PL",
        help="Language code (default: PL)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--max-judgments",
        type=int,
        default=50,
        help="Maximum number of judgments to fetch (default: 50)",
    )

    args = parser.parse_args()

    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Get credentials
    username, password = get_credentials()
    soap_client = None

    if not username or not password:
        logger.warning(
            "EUR-Lex credentials not found in environment. "
            "Set EURLEX_USERNAME and EURLEX_PASSWORD in .env file. "
            "Will attempt direct HTML download without SOAP."
        )
    else:
        soap_client = create_soap_client(username, password)
        if soap_client:
            logger.info("SOAP client created successfully.")
        else:
            logger.warning("Failed to create SOAP client. Will use direct HTML download.")

    # Determine CELEX numbers to fetch
    celex_numbers = args.celex if args.celex else DEFAULT_JUDGMENT_CELEX_NUMBERS
    celex_numbers = celex_numbers[: args.max_judgments]

    logger.info(f"Fetching {len(celex_numbers)} judgment(s)...")

    # Statistics
    success_count = 0
    error_count = 0

    for i, celex in enumerate(celex_numbers):
        logger.info(f"[{i + 1}/{len(celex_numbers)}] Fetching {celex}...")

        try:
            result = fetch_judgment(
                celex=celex,
                language=args.language,
                soap_client=soap_client,
                delay=args.delay,
            )

            if result:
                save_judgment(celex, result, args.output, language=args.language)
                success_count += 1
            else:
                logger.error(f"No content retrieved for {celex}")
                error_count += 1
        except Exception as e:
            logger.error(f"Error fetching {celex}: {e}")
            error_count += 1

        # Delay between requests
        if i < len(celex_numbers) - 1:
            time.sleep(args.delay)

    # Log statistics
    logger.info("=" * 50)
    logger.info(f"Fetch complete. Success: {success_count}, Errors: {error_count}")
    logger.info(f"Total: {success_count + error_count} judgment(s) processed")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
