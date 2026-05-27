#!/usr/bin/env python3
"""
Skrypt do pobierania polskich aktow prawnych z ISAP (Internetowy System Aktow Prawnych).

Korzysta z API ISAP: https://isap.sejm.gov.pl/api/isap/
Pobiera teksty ustaw dotyczacych prawa zywnosciowego.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("Brak modulu 'requests'. Zainstaluj: pip install requests")
    sys.exit(1)

# Add scripts directory to path for utils import
sys.path.insert(0, str(Path(__file__).resolve().parent))

from utils.http_client import create_http_client

# Domyslne akty prawne do pobrania
DEFAULT_ACTS = [
    {
        "id": "WDU20061711225",
        "name": "ustawa-bezpieczenstwo-zywnosci",
        "title": "Ustawa z dnia 25 sierpnia 2006 r. o bezpieczenstwie zywnosci i zywienia",
        "dziennik": "Dz.U. 2006 nr 171 poz. 1225",
    },
    {
        "id": "WDU19850120049",
        "name": "ustawa-pis",
        "title": "Ustawa z dnia 14 marca 1985 r. o Panstwowej Inspekcji Sanitarnej",
        "dziennik": "Dz.U. 1985 nr 12 poz. 49",
    },
]

ISAP_API_BASE = "https://isap.sejm.gov.pl/api/isap"
ISAP_DOWNLOAD_BASE = "https://isap.sejm.gov.pl/isap.nsf/download.xsp"

USER_AGENT = "foodlaw-ai/1.0 (https://github.com/supplemental-pl/foodlaw-ai; prawo zywnosciowe PL/EU)"

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguruje logowanie."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def fetch_act_details(act_id: str, client: requests.Session = None) -> dict:
    """
    Pobiera szczegoly aktu prawnego z API ISAP.

    Args:
        act_id: Identyfikator aktu w ISAP (np. WDU20061711225)
        client: Optional configured requests.Session (uses shared http_client if None)

    Returns:
        Slownik z metadanymi aktu
    """
    if client is None:
        client = create_http_client(max_retries=3, backoff_factor=2.0, timeout=30)

    url = f"{ISAP_API_BASE}/deeds/{act_id}"
    logger.info(f"Pobieranie metadanych aktu: {url}")

    headers = {
        "Accept": "application/json",
    }

    try:
        response = client.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    except requests.exceptions.Timeout:
        logger.error(f"Timeout przy pobieraniu metadanych aktu {act_id}")
        return {}
    except requests.exceptions.HTTPError as e:
        logger.error(f"Blad HTTP {e.response.status_code} dla aktu {act_id}: {e}")
        return {}
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Blad polaczenia dla aktu {act_id}: {e}")
        return {}
    except json.JSONDecodeError as e:
        logger.error(f"Blad dekodowania JSON dla aktu {act_id}: {e}")
        return {}
    except requests.exceptions.RequestException as e:
        logger.error(f"Blad zadania dla aktu {act_id}: {e}")
        return {}


def fetch_act_text(act_id: str, text_type: str = "T", client: requests.Session = None) -> str:
    """
    Pobiera tekst aktu prawnego z ISAP.

    Probuje najpierw API REST, a w razie niepowodzenia uzywa ISAP_DOWNLOAD_BASE
    (https://isap.sejm.gov.pl/isap.nsf/download.xsp) z parametrem DocId.

    Args:
        act_id: Identyfikator aktu (np. WDU20061711225)
        text_type: Typ tekstu - 'T' (tekst jednolity), 'O' (tekst ogloszony)
        client: Optional configured requests.Session (uses shared http_client if None)

    Returns:
        Tresc dokumentu jako string (HTML lub PDF URL)
    """
    if client is None:
        client = create_http_client(max_retries=3, backoff_factor=2.0, timeout=60)

    headers = {
        "Accept": "text/html, application/pdf, */*",
    }

    # Proba 1: API REST (moze nie obslugiwac tekstu bezposrednio)
    api_url = f"{ISAP_API_BASE}/deeds/{act_id}/text/{text_type}"
    logger.info(f"Pobieranie tekstu aktu (API): {api_url}")

    try:
        response = client.get(api_url, headers=headers, timeout=60, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "html" in content_type or "text" in content_type:
            return response.text
        else:
            logger.info(f"Tekst aktu dostepny jako: {content_type}")
            return f"[Dokument dostepny pod adresem: {response.url}]"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.info(f"API nie zwrocilo tekstu typu '{text_type}' - probuje download.xsp")
        else:
            logger.warning(f"Blad HTTP {e.response.status_code} z API dla aktu {act_id}")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Blad API przy pobieraniu tekstu aktu {act_id}: {e}")

    # Proba 2: ISAP download.xsp z DocId (znany dzialajacy wzorzec URL)
    download_url = f"{ISAP_DOWNLOAD_BASE}/{act_id}/{text_type}/{act_id}.pdf"
    logger.info(f"Pobieranie tekstu aktu (download.xsp): {download_url}")

    try:
        response = client.get(download_url, headers=headers, timeout=60, allow_redirects=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        if "html" in content_type or "text" in content_type:
            return response.text
        else:
            logger.info(f"Tekst aktu dostepny jako PDF: {content_type}")
            return f"[Dokument PDF dostepny pod adresem: {response.url}]"

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            logger.warning(f"Brak tekstu typu '{text_type}' dla aktu {act_id} "
                           f"rowniez przez download.xsp")
        else:
            logger.error(f"Blad HTTP {e.response.status_code} (download.xsp) "
                         f"dla aktu {act_id}: {e}")
        return ""
    except requests.exceptions.Timeout:
        logger.error(f"Timeout przy pobieraniu tekstu aktu {act_id}")
        return ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Blad polaczenia przy pobieraniu tekstu aktu {act_id}: {e}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Blad zadania przy pobieraniu tekstu aktu {act_id}: {e}")
        return ""


def search_acts(keyword: str, publisher: str = "WDU", limit: int = 20, client: requests.Session = None) -> list:
    """
    Wyszukuje akty prawne w ISAP.

    Args:
        keyword: Slowo kluczowe
        publisher: Wydawca (WDU - Dziennik Ustaw, MMP - Monitor Polski)
        limit: Maksymalna liczba wynikow
        client: Optional configured requests.Session (uses shared http_client if None)

    Returns:
        Lista znalezionych aktow
    """
    if client is None:
        client = create_http_client(max_retries=3, backoff_factor=2.0, timeout=30)

    url = f"{ISAP_API_BASE}/deeds/search"
    params = {
        "publisher": publisher,
        "title": keyword,
        "limit": limit,
        "sortBy": "DATE_DESC",
    }
    logger.info(f"Wyszukiwanie aktow: '{keyword}' w {publisher}")

    headers = {
        "Accept": "application/json",
    }

    try:
        response = client.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("items", data) if isinstance(data, dict) else data
        logger.info(f"Znaleziono {len(items) if isinstance(items, list) else '?'} wynikow")
        return items if isinstance(items, list) else []

    except requests.exceptions.RequestException as e:
        logger.error(f"Blad wyszukiwania w ISAP: {e}")
        return []
    except json.JSONDecodeError:
        logger.error("Blad dekodowania odpowiedzi JSON z ISAP")
        return []


def save_act(act_info: dict, content: str, details: dict, output_dir: Path) -> Path:
    """
    Zapisuje pobrany akt prawny do pliku.

    Args:
        act_info: Informacje o akcie (z DEFAULT_ACTS)
        content: Tresc dokumentu
        details: Szczegolowe metadane z API
        output_dir: Katalog wyjsciowy

    Returns:
        Sciezka do zapisanego pliku
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Zapisz tresc
    filename = f"{act_info['name']}.html"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Zapisano: {filepath} ({len(content)} bajtow)")

    # Zapisz metadane
    meta_path = output_dir / f"{act_info['name']}.meta.json"
    meta = {
        "id": act_info["id"],
        "title": act_info["title"],
        "dziennik": act_info["dziennik"],
        "api_details": details,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    return filepath


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia pobieranie."""
    parser = argparse.ArgumentParser(
        description="Pobiera polskie akty prawne z ISAP (isap.sejm.gov.pl). "
                    "Domyslnie pobiera ustawy dotyczace prawa zywnosciowego: "
                    "Ustawe o bezpieczenstwie zywnosci i zywienia oraz "
                    "Ustawe o Panstwowej Inspekcji Sanitarnej.",
        epilog="Przyklad: python fetch_isap.py --output ./data/isap/ --verbose",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output/isap",
        help="Katalog wyjsciowy (domyslnie: ./output/isap)",
    )
    parser.add_argument(
        "--act-id",
        type=str,
        nargs="+",
        default=None,
        help="Identyfikatory aktow do pobrania (np. WDU20061711225). "
             "Domyslnie pobiera predefiniowane akty prawa zywnosciowego.",
    )
    parser.add_argument(
        "--search",
        type=str,
        default=None,
        help="Wyszukaj akty wg slowa kluczowego (zamiast pobierac)",
    )
    parser.add_argument(
        "--text-type",
        type=str,
        default="T",
        choices=["T", "O"],
        help="Typ tekstu: T (jednolity/ujednolicony), O (ogloszony). Domyslnie: T",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Opoznienie miedzy zadaniami w sekundach (domyslnie: 2.0)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Wlacz szczegolowe logowanie (DEBUG)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Tryb wyszukiwania
    if args.search:
        results = search_acts(args.search)
        if results:
            print(f"\nZnaleziono {len(results)} aktow:")
            for item in results:
                if isinstance(item, dict):
                    print(f"  - {item.get('title', 'brak tytulu')} "
                          f"({item.get('address', item.get('id', '?'))})")
        else:
            print("Nie znaleziono wynikow.")
        return

    output_dir = Path(args.output)

    # Ustal liste aktow do pobrania
    if args.act_id:
        acts = [{"id": aid, "name": aid, "title": "", "dziennik": ""} for aid in args.act_id]
    else:
        acts = DEFAULT_ACTS

    logger.info(f"Start pobierania {len(acts)} aktow z ISAP")

    success_count = 0
    error_count = 0

    for i, act_info in enumerate(acts, 1):
        logger.info(f"[{i}/{len(acts)}] Przetwarzanie: {act_info['title'] or act_info['id']}")

        # Pobierz metadane
        details = fetch_act_details(act_info["id"])
        time.sleep(1)

        # Pobierz tekst
        content = fetch_act_text(act_info["id"], args.text_type)

        if not content:
            # Probuj tekst ogloszony jesli jednolity niedostepny
            if args.text_type == "T":
                logger.info("Probuje tekst ogloszony...")
                content = fetch_act_text(act_info["id"], "O")

        if content:
            save_act(act_info, content, details, output_dir)
            success_count += 1
        else:
            logger.warning(f"Nie udalo sie pobrac tekstu aktu: {act_info['id']}")
            error_count += 1

        if i < len(acts):
            time.sleep(args.delay)

    logger.info(
        f"Zakonczono: {success_count} sukces(ow), {error_count} blad(ow) "
        f"z {len(acts)} aktow"
    )

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
