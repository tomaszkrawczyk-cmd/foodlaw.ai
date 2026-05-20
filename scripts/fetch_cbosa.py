#!/usr/bin/env python3
"""
Skrypt do wyszukiwania orzeczen NSA/WSA w Centralnej Bazie Orzeczen Sadow
Administracyjnych (CBOSA) - orzeczenia.nsa.gov.pl.

Wyszukuje orzeczenia dotyczace prawa zywnosciowego na podstawie slow kluczowych.

UWAGA: CBOSA aktywnie blokuje polaczenia z adresow IP nalezacych do
centrow danych i chmur obliczeniowych (np. AWS, GCP, Azure). Polaczenie TLS
zostaje natychmiast zamkniete (SSLZeroReturnError). Skrypt dziala najlepiej
z rezydencjalnego adresu IP lub przez VPN z wyjsciem rezydencjalnym.

Selektory CSS uzyte w tym skrypcie (table.lista tr, .wyniki .wynik,
.result-item) sa spekulatywne i musza byc skalibrowane wobec aktualnej struktury
HTML strony orzeczenia.nsa.gov.pl przed pierwszym urzyciem produkcyjnym.
CBOSA uzywa interfejsu JSF, ktory generuje dynamiczne identyfikatory elementow.
W razie problemow z parsowaniem, uzyj flagi --output-raw aby zapisac surowy HTML
do katalogu wyjsciowego w celu recznej analizy struktury DOM.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
import json
import logging
import os
import re
import ssl
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Brak modulu 'requests'. Zainstaluj: pip install requests")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Brak modulu 'beautifulsoup4'. Zainstaluj: pip install beautifulsoup4")
    sys.exit(1)

# Domyslne slowa kluczowe dotyczace prawa zywnosciowego
DEFAULT_KEYWORDS = [
    "bezpieczenstwo zywnosci",
    "suplement diety",
    "GIS",
    "Glowny Inspektor Sanitarny",
    "zywnosc",
    "etykietowanie zywnosci",
    "oswiadczenia zdrowotne",
]

CBOSA_BASE_URL = "https://orzeczenia.nsa.gov.pl"
CBOSA_SEARCH_URL = f"{CBOSA_BASE_URL}/cbo/find"

USER_AGENT = "foodlaw-ai/1.0 (https://github.com/supplemental-pl/foodlaw-ai; prawo zywnosciowe PL/EU)"

# Retry configuration
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = [2, 4, 8]

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguruje logowanie."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_session() -> requests.Session:
    """Tworzy sesje HTTP z odpowiednimi naglowkami."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl,en;q=0.5",
    })
    return session


def search_judgments(session: requests.Session, keyword: str,
                     court_type: str = "all", limit: int = 20,
                     output_raw: bool = False, output_dir: Path = None) -> list:
    """
    Wyszukuje orzeczenia w CBOSA.

    Args:
        session: Sesja HTTP
        keyword: Slowo kluczowe do wyszukania
        court_type: Typ sadu - 'all', 'nsa', 'wsa'
        limit: Maksymalna liczba wynikow do przetworzenia
        output_raw: Jesli True, zapisz surowy HTML odpowiedzi
        output_dir: Katalog wyjsciowy (dla raw HTML)

    Returns:
        Lista slownikow z informacjami o orzeczeniach
    """
    logger.info(f"Wyszukiwanie: '{keyword}' (typ sadu: {court_type})")

    params = {
        "q": keyword,
        "pSad": "" if court_type == "all" else court_type.upper(),
        "pOkresSzuk": "",
        "pRodzajSzuk": "wszystko",
    }

    results = []
    response = None

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(CBOSA_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            break  # Success - exit retry loop

        except (requests.exceptions.SSLError, ssl.SSLError) as e:
            logger.error(
                f"Blad SSL przy wyszukiwaniu '{keyword}' (proba {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            logger.error(
                "CBOSA rejects connections from cloud/datacenter IPs. "
                "Use a residential network or VPN, or consider using the "
                "--output-raw flag from a local machine."
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            if "ConnectionReset" in error_str or "Connection aborted" in error_str:
                logger.error(
                    f"Polaczenie przerwane przy wyszukiwaniu '{keyword}' "
                    f"(proba {attempt + 1}/{MAX_RETRIES}): {e}"
                )
                logger.error(
                    "CBOSA rejects connections from cloud/datacenter IPs. "
                    "Use a residential network or VPN, or consider using the "
                    "--output-raw flag from a local machine."
                )
            else:
                logger.error(
                    f"Blad polaczenia przy wyszukiwaniu '{keyword}' "
                    f"(proba {attempt + 1}/{MAX_RETRIES}): {e}"
                )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout przy wyszukiwaniu '{keyword}' "
                f"(proba {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.HTTPError as e:
            logger.error(f"Blad HTTP {e.response.status_code} przy wyszukiwaniu '{keyword}'")
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Blad zadania przy wyszukiwaniu '{keyword}': {e}")
            return results

        except Exception as e:
            logger.error(f"Nieoczekiwany blad przy wyszukiwaniu '{keyword}': {e}")
            return results

    if response is None:
        return results

    try:
        # Zapisz surowy HTML jesli wymagane (do debugowania selektorow)
        if output_raw and output_dir:
            raw_dir = output_dir / "raw_html"
            raw_dir.mkdir(parents=True, exist_ok=True)
            safe_name = re.sub(r"[^\w\-]", "_", keyword)[:50]
            raw_path = raw_dir / f"{safe_name}.html"
            with open(raw_path, "w", encoding="utf-8") as f:
                f.write(response.text)
            logger.info(f"Zapisano surowy HTML: {raw_path}")

        soup = BeautifulSoup(response.text, "lxml")

        # Szukaj wynikow w tabeli/liscie
        # Struktura CBOSA moze sie zmieniac - obsluga roznych wariantow
        result_items = soup.select("table.lista tr, .wyniki .wynik, .result-item")

        if not result_items:
            # Probuj alternatywne selektory
            result_items = soup.find_all("tr", class_=re.compile(r"row|result|item"))

        logger.debug(f"Znaleziono {len(result_items)} elementow HTML")

        for item in result_items[:limit]:
            judgment = parse_result_item(item)
            if judgment:
                results.append(judgment)

        # Jesli nie znaleziono wynikow przez parsowanie HTML, zapisz surowy HTML
        if not results:
            logger.info(f"Nie udalo sie sparsowac wynikow HTML dla '{keyword}', "
                        f"zapisze surowa strone")
            results.append({
                "keyword": keyword,
                "raw_html_available": True,
                "url": response.url,
                "note": "Wyniki dostepne pod powyzszym URL - struktura HTML "
                        "moze wymagac aktualizacji parsera",
            })

    except Exception as e:
        logger.error(f"Blad parsowania wynikow dla '{keyword}': {e}")

    logger.info(f"Wynik dla '{keyword}': {len(results)} orzeczen")
    return results


def parse_result_item(item) -> dict:
    """
    Parsuje pojedynczy element wyniku wyszukiwania CBOSA.

    Args:
        item: Element BeautifulSoup

    Returns:
        Slownik z danymi orzeczenia lub None
    """
    try:
        # Probuj rozne formaty
        links = item.find_all("a", href=True)
        text = item.get_text(separator=" ", strip=True)

        if not text or len(text) < 10:
            return None

        # Wyodrebnij sygnature (wzorzec: II GSK 1234/20 lub II SA/Wa 1234/20)
        signature_pattern = r"[IVX]+\s+[A-Z]+(?:/[A-Z]+)?\s+\d+/\d+"
        signature_match = re.search(signature_pattern, text)

        # Wyodrebnij date (wzorzec: YYYY-MM-DD lub DD.MM.YYYY)
        date_pattern = r"\d{4}-\d{2}-\d{2}|\d{2}\.\d{2}\.\d{4}"
        date_match = re.search(date_pattern, text)

        judgment = {
            "text_snippet": text[:500],
        }

        if signature_match:
            judgment["signature"] = signature_match.group()
        if date_match:
            judgment["date"] = date_match.group()
        if links:
            href = links[0].get("href", "")
            if href and not href.startswith("http"):
                href = f"{CBOSA_BASE_URL}{href}"
            judgment["url"] = href

        return judgment if (signature_match or date_match or links) else None

    except Exception:
        return None


def fetch_judgment_details(session: requests.Session, url: str) -> dict:
    """
    Pobiera szczegoly pojedynczego orzeczenia.

    Args:
        session: Sesja HTTP
        url: URL orzeczenia

    Returns:
        Slownik ze szczegolami orzeczenia
    """
    if not url:
        return {}

    logger.debug(f"Pobieranie szczegolow: {url}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            details = {
                "url": url,
                "full_text": "",
            }

            # Probuj wyodrebnic tresc uzasadnienia
            content_div = soup.select_one(".orzeczenie-tresc, .content, #content")
            if content_div:
                details["full_text"] = content_div.get_text(separator="\n", strip=True)

            return details

        except (requests.exceptions.SSLError, ssl.SSLError) as e:
            logger.error(
                f"Blad SSL przy pobieraniu szczegolow (proba {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            logger.error(
                "CBOSA rejects connections from cloud/datacenter IPs. "
                "Use a residential network or VPN, or consider using the "
                "--output-raw flag from a local machine."
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

        except requests.exceptions.ConnectionError as e:
            error_str = str(e)
            if "ConnectionReset" in error_str or "Connection aborted" in error_str:
                logger.error(
                    "CBOSA rejects connections from cloud/datacenter IPs. "
                    "Use a residential network or VPN, or consider using the "
                    "--output-raw flag from a local machine."
                )
            logger.error(
                f"Blad polaczenia przy pobieraniu szczegolow "
                f"(proba {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Blad pobierania szczegolow orzeczenia: {e}")
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

    return {}


def save_results(results: dict, output_dir: Path) -> None:
    """
    Zapisuje wyniki wyszukiwania do plikow.

    Args:
        results: Slownik {keyword: [lista orzeczen]}
        output_dir: Katalog wyjsciowy
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zapisz zbiorczy plik JSON
    summary_path = output_dir / "cbosa_wyniki.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Zapisano podsumowanie: {summary_path}")

    # Zapisz osobne pliki dla kazdego slowa kluczowego
    for keyword, judgments in results.items():
        safe_name = re.sub(r"[^\w\-]", "_", keyword)[:50]
        keyword_path = output_dir / f"{safe_name}.json"
        with open(keyword_path, "w", encoding="utf-8") as f:
            json.dump({"keyword": keyword, "results": judgments}, f,
                      ensure_ascii=False, indent=2)


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia wyszukiwanie."""
    parser = argparse.ArgumentParser(
        description="Wyszukuje orzeczenia NSA/WSA w CBOSA (orzeczenia.nsa.gov.pl) "
                    "dotyczace prawa zywnosciowego. Domyslnie uzywa predefiniowanych "
                    "slow kluczowych: bezpieczenstwo zywnosci, suplement diety, GIS, "
                    "Glowny Inspektor Sanitarny, zywnosc, etykietowanie zywnosci, "
                    "oswiadczenia zdrowotne.",
        epilog="Przyklad: python fetch_cbosa.py --keywords 'suplement diety' 'GIS' --output ./data/cbosa/",
    )
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        default=DEFAULT_KEYWORDS,
        help="Slowa kluczowe do wyszukania (domyslnie: predefiniowana lista)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Katalog wyjsciowy. Domyslnie: ./orzecznictwo/nsa/ lub ./orzecznictwo/wsa/ "
             "(zalezne od --court-type; 'all' zapisuje do ./orzecznictwo/nsa/)",
    )
    parser.add_argument(
        "--court-type", "-c",
        type=str,
        default="all",
        choices=["all", "nsa", "wsa"],
        help="Typ sadu: all (wszystkie), nsa (NSA), wsa (WSA). Domyslnie: all",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=20,
        help="Maksymalna liczba wynikow na slowo kluczowe (domyslnie: 20)",
    )
    parser.add_argument(
        "--fetch-details",
        action="store_true",
        help="Pobierz pelne teksty orzeczen (wolniejsze)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=3.0,
        help="Opoznienie miedzy zadaniami w sekundach (domyslnie: 3.0)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Wlacz szczegolowe logowanie (DEBUG)",
    )
    parser.add_argument(
        "--output-raw",
        action="store_true",
        help="Zawsze zapisuj surowa odpowiedz HTML (do debugowania selektorow)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Domyslny katalog wyjsciowy zalezny od typu sadu
    if args.output:
        output_dir = Path(args.output)
    elif args.court_type == "wsa":
        output_dir = Path("./orzecznictwo/wsa")
    else:
        output_dir = Path("./orzecznictwo/nsa")

    session = create_session()

    logger.info(f"Start wyszukiwania w CBOSA: {len(args.keywords)} slow kluczowych")
    logger.info(f"Typ sadu: {args.court_type}, Limit: {args.limit}")

    all_results = {}

    for i, keyword in enumerate(args.keywords, 1):
        logger.info(f"[{i}/{len(args.keywords)}] Wyszukiwanie: '{keyword}'")

        results = search_judgments(session, keyword, args.court_type, args.limit,
                                   output_raw=args.output_raw, output_dir=output_dir)
        all_results[keyword] = results

        # Opcjonalnie pobierz szczegoly
        if args.fetch_details and results:
            for j, judgment in enumerate(results):
                url = judgment.get("url", "")
                if url and url.startswith("http"):
                    details = fetch_judgment_details(session, url)
                    results[j].update(details)
                    time.sleep(1)

        if i < len(args.keywords):
            time.sleep(args.delay)

    save_results(all_results, output_dir)

    total = sum(len(v) for v in all_results.values())
    logger.info(f"Zakonczono: znaleziono lacznie {total} wynikow")


if __name__ == "__main__":
    main()
