#!/usr/bin/env python3
"""
Skrypt do wyszukiwania orzeczen Trybunalu Sprawiedliwosci UE (TSUE) w bazie CURIA.

Wyszukuje orzeczenia dotyczace prawa zywnosciowego za pomoca interfejsu CURIA
(curia.europa.eu).

UWAGA: CURIA (infocuria.curia.europa.eu) jest obecnie aplikacja Angular SPA.
Zwykle zadania HTTP (requests) otrzymuja jedynie pusty szkielet HTML z tagiem
<app-root></app-root> i zestawem bundli JavaScript - brak tresci renderowanej
po stronie serwera. Oznacza to, ze parsowanie HTML przez ten skrypt nie zwroci
zadnych wynikow. Do pobrania danych potrzebna jest automatyzacja przegladarki
(np. Playwright) lub alternatywne zrodlo danych.

ALTERNATYWA: Endpoint SPARQL EU CELLAR (publications.europa.eu/webapi/rdf/sparql)
pozwala na odpytywanie metadanych orzeczen TSUE (ECLI, CELEX, daty, typ zasobu)
bez potrzeby renderowania JavaScript. Patrz scripts/fetch_cellar_sparql.py
(jesli istnieje) lub dokumentacja EU CELLAR.

Selektory CSS uzyte w tym skrypcie (table.detail_table_documents tr,
.liste_table tr, .result_table tr, #listeDocuments tr) sa spekulatywne i nie
odpowiadaja biezacemu DOM aplikacji Angular. W razie problemow z parsowaniem,
uzyj flagi --output-raw aby zapisac surowy HTML do katalogu wyjsciowego w celu
recznej analizy struktury.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
import json
import logging
import re
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

# Domyslne slowa kluczowe do wyszukiwania w CURIA
DEFAULT_KEYWORDS = [
    "food safety",
    "food labelling",
    "health claims",
    "novel food",
    "food supplement",
    "Regulation 178/2002",
    "Regulation 1169/2011",
    "Regulation 1924/2006",
]

# CURIA search API
CURIA_SEARCH_URL = "https://curia.europa.eu/juris/liste.jsf"

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


def search_curia(session: requests.Session, keyword: str,
                 language: str = "pl", limit: int = 20,
                 output_raw: bool = False, output_dir: Path = None) -> list:
    """
    Wyszukuje orzeczenia w CURIA.

    Args:
        session: Sesja HTTP
        keyword: Slowo kluczowe lub fraza
        language: Jezyk wynikow (pl, en, fr, de)
        limit: Maksymalna liczba wynikow
        output_raw: Jesli True, zapisz surowy HTML odpowiedzi
        output_dir: Katalog wyjsciowy (dla raw HTML)

    Returns:
        Lista slownikow z informacjami o orzeczeniach
    """
    logger.info(f"Wyszukiwanie CURIA: '{keyword}' (jezyk: {language})")

    params = {
        "language": language,
        "jur": "C,T,F",  # Trybunal Sprawiedliwosci, Sad, Sad ds. Sluzby Publicznej
        "td": "ALL",
        "textFree": keyword,
        "page": "1",
        "pageSize": str(limit),
    }

    results = []
    response = None

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(CURIA_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            break  # Success - exit retry loop

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout przy wyszukiwaniu CURIA: '{keyword}' "
                f"(proba {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.HTTPError as e:
            logger.error(
                f"Blad HTTP {e.response.status_code} przy wyszukiwaniu '{keyword}' "
                f"(proba {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Blad polaczenia przy wyszukiwaniu CURIA: '{keyword}' "
                f"(proba {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                logger.info(f"Ponowna proba za {wait}s...")
                time.sleep(wait)
            else:
                return results

        except requests.exceptions.RequestException as e:
            logger.error(f"Blad zadania przy wyszukiwaniu CURIA: {e}")
            return results

        except Exception as e:
            logger.error(f"Nieoczekiwany blad przy wyszukiwaniu CURIA: {e}")
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

        # Parsuj wyniki z CURIA
        # UWAGA: Ponizsze selektory CSS NIE zostaly zweryfikowane wobec aktualnego
        # DOM strony CURIA. Witryna jest aplikacja Angular SPA i zwraca pusty
        # szkielet HTML przez zwykle zadania HTTP. Selektory sa spekulatywne
        # i wymagaja walidacji za pomoca automatyzacji przegladarki (Playwright)
        # lub analizy surowego HTML (--output-raw).
        result_rows = soup.select(
            "table.detail_table_documents tr, "
            ".liste_table tr, "
            ".result_table tr, "
            "#listeDocuments tr"
        )

        if not result_rows:
            # Alternatywna struktura
            result_rows = soup.find_all("tr", attrs={"class": re.compile(r"row|result")})

        logger.debug(f"Znaleziono {len(result_rows)} wierszy wynikow")

        for row in result_rows[:limit]:
            case = parse_curia_result(row)
            if case:
                results.append(case)

        # Jesli nie sparsowano wynikow, zwroc informacje o URL
        if not results and response.status_code == 200:
            # Sprawdz, czy strona w ogole ma wyniki
            page_text = soup.get_text()
            if keyword.lower() in page_text.lower() or "document" in page_text.lower():
                results.append({
                    "keyword": keyword,
                    "search_url": response.url,
                    "note": "Wyniki dostepne pod powyzszym URL - "
                            "sprawdz recznie lub zaktualizuj parser",
                })

    except Exception as e:
        logger.error(f"Blad parsowania wynikow CURIA dla '{keyword}': {e}")

    logger.info(f"Wynik CURIA dla '{keyword}': {len(results)} orzeczen")
    return results


def parse_curia_result(row) -> dict:
    """
    Parsuje wiersz wyniku wyszukiwania CURIA.

    Args:
        row: Element BeautifulSoup (wiersz tabeli)

    Returns:
        Slownik z danymi orzeczenia lub None
    """
    try:
        text = row.get_text(separator=" ", strip=True)
        if not text or len(text) < 10:
            return None

        links = row.find_all("a", href=True)

        case = {"text_snippet": text[:500]}

        # Szukaj numeru sprawy (C-123/20, T-456/21)
        case_number_pattern = r"[CT]-\d+/\d+"
        case_match = re.search(case_number_pattern, text)
        if case_match:
            case["case_number"] = case_match.group()

        # Szukaj ECLI
        ecli_pattern = r"ECLI:EU:[CTF]:\d{4}:\d+"
        ecli_match = re.search(ecli_pattern, text)
        if ecli_match:
            case["ecli"] = ecli_match.group()

        # Szukaj daty
        date_pattern = r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}"
        date_match = re.search(date_pattern, text)
        if date_match:
            case["date"] = date_match.group()

        # Pobierz URL
        if links:
            href = links[0].get("href", "")
            if href and not href.startswith("http"):
                href = f"https://curia.europa.eu{href}"
            case["url"] = href

        # Zwroc tylko jesli znaleziono cos uzytecznego
        if case_match or ecli_match or date_match:
            return case

        return None

    except Exception:
        return None


def fetch_case_details(session: requests.Session, url: str) -> dict:
    """
    Pobiera szczegoly orzeczenia TSUE.

    Args:
        session: Sesja HTTP
        url: URL orzeczenia na CURIA

    Returns:
        Slownik z informacjami o orzeczeniu
    """
    if not url or not url.startswith("http"):
        return {}

    logger.debug(f"Pobieranie szczegolow orzeczenia: {url}")

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "lxml")

            details = {"url": url}

            # Szukaj tresci orzeczenia
            content_div = soup.select_one("#document_content, .document_content, .content")
            if content_div:
                details["full_text"] = content_div.get_text(separator="\n", strip=True)[:10000]

            return details

        except requests.exceptions.Timeout:
            logger.error(
                f"Timeout przy pobieraniu orzeczenia CURIA "
                f"(proba {attempt + 1}/{MAX_RETRIES})"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

        except requests.exceptions.ConnectionError as e:
            logger.error(
                f"Blad polaczenia przy pobieraniu orzeczenia CURIA "
                f"(proba {attempt + 1}/{MAX_RETRIES}): {e}"
            )
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

        except requests.exceptions.RequestException as e:
            logger.error(f"Blad pobierania orzeczenia CURIA: {e}")
            if attempt < MAX_RETRIES - 1:
                wait = RETRY_BACKOFF_SECONDS[attempt]
                time.sleep(wait)
            else:
                return {}

    return {}


def save_results(results: dict, output_dir: Path) -> None:
    """
    Zapisuje wyniki do plikow.

    Args:
        results: Slownik {keyword: [lista orzeczen]}
        output_dir: Katalog wyjsciowy
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zapisz zbiorczy plik JSON
    summary_path = output_dir / "curia_wyniki.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    logger.info(f"Zapisano podsumowanie: {summary_path}")

    # Zapisz pliki per slowo kluczowe
    for keyword, cases in results.items():
        safe_name = re.sub(r"[^\w\-]", "_", keyword)[:50]
        keyword_path = output_dir / f"{safe_name}.json"
        with open(keyword_path, "w", encoding="utf-8") as f:
            json.dump({"keyword": keyword, "results": cases}, f,
                      ensure_ascii=False, indent=2)


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia wyszukiwanie."""
    parser = argparse.ArgumentParser(
        description="Wyszukuje orzeczenia TSUE w bazie CURIA (curia.europa.eu) "
                    "dotyczace prawa zywnosciowego. Domyslnie uzywa slow "
                    "kluczowych: food safety, food labelling, health claims, "
                    "novel food, food supplement i numery rozporzadzen.",
        epilog="Przyklad: python fetch_curia.py --keywords 'health claims' 'novel food' "
               "--output ./data/curia/ --language pl",
    )
    parser.add_argument(
        "--keywords", "-k",
        nargs="+",
        default=DEFAULT_KEYWORDS,
        help="Slowa kluczowe lub frazy do wyszukania (domyslnie: predefiniowana lista)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./orzecznictwo/tsue",
        help="Katalog wyjsciowy (domyslnie: ./orzecznictwo/tsue)",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="pl",
        choices=["pl", "en", "fr", "de", "es", "it"],
        help="Jezyk wynikow (domyslnie: pl)",
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

    output_dir = Path(args.output)
    session = create_session()

    logger.info(f"Start wyszukiwania w CURIA: {len(args.keywords)} slow kluczowych")
    logger.info(f"Jezyk: {args.language}, Limit: {args.limit}")

    all_results = {}

    for i, keyword in enumerate(args.keywords, 1):
        logger.info(f"[{i}/{len(args.keywords)}] Wyszukiwanie: '{keyword}'")

        results = search_curia(session, keyword, args.language, args.limit,
                              output_raw=args.output_raw, output_dir=output_dir)
        all_results[keyword] = results

        # Opcjonalnie pobierz szczegoly
        if args.fetch_details and results:
            for j, case in enumerate(results):
                url = case.get("url", "")
                if url and url.startswith("http"):
                    details = fetch_case_details(session, url)
                    results[j].update(details)
                    time.sleep(1)

        if i < len(args.keywords):
            time.sleep(args.delay)

    save_results(all_results, output_dir)

    total = sum(len(v) for v in all_results.values())
    logger.info(f"Zakonczono: znaleziono lacznie {total} wynikow")


if __name__ == "__main__":
    main()
