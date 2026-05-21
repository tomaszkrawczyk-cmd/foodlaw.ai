#!/usr/bin/env python3
"""
Skrypt do pobierania rozporzadzen UE z EUR-Lex za pomoca CELLAR content negotiation.

Pobiera polskie wersje jezykowe aktow prawnych na podstawie numerow CELEX.
Wykorzystuje content negotiation z URI: http://publications.europa.eu/resource/celex/{celex}
z naglowkami Accept: application/xhtml+xml i Accept-Language: pl.

SPARQL endpoint jest dostepny jako opcjonalne wzbogacenie metadanych, ale
glowna metoda pobierania to content negotiation (CELLAR zwraca 303 -> tresc).

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
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

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
except ImportError:
    SPARQLWrapper = None
    JSON = None
    # SPARQL is optional - content negotiation is the primary method

# Domyslne numery CELEX rozporzadzen prawa zywnosciowego
DEFAULT_CELEX_NUMBERS = [
    "32002R0178",  # Rozp. 178/2002 - Ogolne prawo zywnosciowe
    "32011R1169",  # Rozp. 1169/2011 - Informacja o zywnosci
    "32006R1924",  # Rozp. 1924/2006 - Oswiadczenia zdrowotne
    "32006R1925",  # Rozp. 1925/2006 - Wzbogacanie zywnosci
    "32015R2283",  # Rozp. 2015/2283 - Nowa zywnosc
    "32004R0852",  # Rozp. 852/2004 - Higiena zywnosci
    "32004R0853",  # Rozp. 853/2004 - Higiena zywnosci zwierzecego
    "32023R0915",  # Rozp. 2023/915 - Zanieczyszczenia
    "32013R0609",  # Rozp. 609/2013 - Zywnosc specjalna
    "32005R0396",  # Rozp. 396/2005 - Najwyzsze dopuszczalne poziomy pozostalosci pestycydow
    "32016R0127",  # Rozp. del. 2016/127 - Preparaty dla niemowlat
    "32016R0128",  # Rozp. del. 2016/128 - Zywnosc specjalnego przeznaczenia medycznego (FSMP)
    "32017R1798",  # Rozp. del. 2017/1798 - Srodki zastepujace cala diete do kontroli masy ciala
    "32008R1333",  # Rozp. 1333/2008 - Dodatki do zywnosci
    "32008R1334",  # Rozp. 1334/2008 - Srodki aromatyzujace
    "32008R1332",  # Rozp. 1332/2008 - Enzymy spozywcze
    "32011R0010",  # Rozp. 10/2011 - Materialy z tworzyw sztucznych do kontaktu z zywnoscia (FCM)
    "32004R1935",  # Rozp. 1935/2004 - Materialy do kontaktu z zywnoscia (FCM ramowe)
    "32003R2065",  # Rozp. 2065/2003 - Srodki aromatyzujace dym wedzarniczy
    "32009R1107",  # Rozp. 1107/2009 - Srodki ochrony roslin
    "32006R1881",  # Rozp. 1881/2006 - Najwyzsze dopuszczalne poziomy zanieczyszczen (zastapione przez 2023/915)
]

CELLAR_RESOURCE_BASE = "http://publications.europa.eu/resource/celex/"
CELLAR_SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"

USER_AGENT = "foodlaw-ai/1.0 (prawo zywnosciowe PL/EU)"

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguruje logowanie."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def fetch_cellar_content(celex: str, language: str = "pl") -> str:
    """
    Pobiera tresc dokumentu z CELLAR za pomoca content negotiation.

    Metoda: HTTP GET na http://publications.europa.eu/resource/celex/{celex}
    z naglowkami Accept i Accept-Language. Serwer zwraca 303 redirect do tresci.

    Proba 1: Accept: application/xhtml+xml (nowsze dokumenty)
    Proba 2: Accept: text/html (starsze dokumenty, pre-2006)

    Args:
        celex: Numer CELEX dokumentu
        language: Kod jezyka (domyslnie 'pl')

    Returns:
        Tresc HTML/XHTML jako string, pusty string w przypadku bledu
    """
    url = f"{CELLAR_RESOURCE_BASE}{celex}"

    # Try XHTML first (preferred - structured format), then HTML fallback
    accept_types = ["application/xhtml+xml", "text/html"]

    for accept_type in accept_types:
        logger.info(f"Pobieranie z CELLAR: {url} (jezyk: {language}, accept: {accept_type})")

        headers = {
            "Accept": accept_type,
            "Accept-Language": language,
            "User-Agent": USER_AGENT,
        }

        try:
            response = requests.get(url, headers=headers, timeout=120, allow_redirects=True)

            if response.status_code == 200:
                content = response.text
                logger.info(
                    f"Pobrano CELEX {celex}: {len(content)} bajtow, "
                    f"content-type: {response.headers.get('Content-Type', 'unknown')}"
                )
                return content
            elif response.status_code == 404:
                logger.debug(
                    f"CELEX {celex}: 404 dla {accept_type}, probuje nastepny format"
                )
                continue
            elif response.status_code == 406:
                logger.debug(
                    f"CELEX {celex}: 406 dla {accept_type}, probuje nastepny format"
                )
                continue
            else:
                logger.warning(
                    f"CELEX {celex}: status {response.status_code} dla {accept_type}"
                )
                continue

        except requests.exceptions.Timeout:
            logger.error(f"Timeout przy pobieraniu CELEX {celex} ({accept_type})")
            continue
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Blad polaczenia dla CELEX {celex}: {e}")
            return ""
        except requests.exceptions.RequestException as e:
            logger.error(f"Blad zadania dla CELEX {celex}: {e}")
            return ""

    logger.warning(f"CELEX {celex}: nie udalo sie pobrac w zadnym formacie")
    return ""


def fetch_metadata_sparql(celex: str, language: str = "PL") -> dict:
    """
    Pobiera metadane dokumentu z CELLAR za pomoca SPARQL (opcjonalne).

    SPARQL endpoint czesto zwraca puste wyniki dla CELEX, wiec ta metoda
    jest traktowana jako opcjonalne wzbogacenie - nie blokuje pobierania.

    Args:
        celex: Numer CELEX
        language: Kod jezyka (uppercase)

    Returns:
        Slownik z metadanymi (title, date) lub pusty slownik
    """
    if SPARQLWrapper is None:
        logger.debug("SPARQLWrapper niedostepny - pomijam metadane SPARQL")
        return {}

    logger.debug(f"Probuje pobrac metadane SPARQL dla CELEX: {celex}")

    try:
        sparql = SPARQLWrapper(CELLAR_SPARQL_ENDPOINT)
        sparql.addCustomHttpHeader("User-Agent", USER_AGENT)

        query = f"""
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

        SELECT DISTINCT ?title ?date
        WHERE {{
            ?work cdm:resource_legal_id_celex "{celex}"^^xsd:string .
            ?work cdm:work_date_document ?date .
            ?expression cdm:expression_belongs_to_work ?work .
            ?expression cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/{language}> .
            ?expression cdm:expression_title ?title .
        }}
        LIMIT 1
        """

        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)

        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])

        if not bindings:
            logger.debug(f"Brak wynikow SPARQL dla CELEX: {celex}")
            return {}

        first = bindings[0]
        metadata = {
            "title": first.get("title", {}).get("value", ""),
            "date": first.get("date", {}).get("value", ""),
        }
        logger.debug(f"Metadane SPARQL: {metadata}")
        return metadata

    except Exception as e:
        logger.debug(f"Blad SPARQL dla CELEX {celex} (nieblokujacy): {e}")
        return {}


def save_document(celex: str, content: str, metadata: dict, output_dir: Path) -> Path:
    """
    Zapisuje pobrany dokument do pliku.

    Args:
        celex: Numer CELEX
        content: Tresc XHTML/HTML
        metadata: Metadane dokumentu (opcjonalne)
        output_dir: Katalog wyjsciowy

    Returns:
        Sciezka do zapisanego pliku
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{celex}.html"
    filepath = output_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"Zapisano: {filepath} ({len(content)} bajtow)")

    # Zapisz metadane jesli dostepne
    if metadata:
        meta_path = output_dir / f"{celex}.meta.txt"
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"celex: {celex}\n")
            for key, value in metadata.items():
                f.write(f"{key}: {value}\n")

    return filepath


def fetch_document(celex: str, output_dir: Path, language: str = "pl",
                   delay: float = 2.0) -> bool:
    """
    Pobiera pojedynczy dokument za pomoca CELLAR content negotiation.

    Args:
        celex: Numer CELEX
        output_dir: Katalog wyjsciowy
        language: Kod jezyka (lowercase dla Accept-Language)
        delay: Opoznienie miedzy zadaniami (sekundy)

    Returns:
        True jesli sukces, False w przypadku bledu
    """
    # Metoda glowna: CELLAR content negotiation
    content = fetch_cellar_content(celex, language)

    if not content:
        logger.warning(f"Brak tresci dla CELEX {celex} - pomijam")
        return False

    # Opcjonalnie: wzbogac metadanymi z SPARQL (nieblokujace)
    metadata = fetch_metadata_sparql(celex, language.upper())

    save_document(celex, content, metadata, output_dir)
    return True


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia pobieranie."""
    parser = argparse.ArgumentParser(
        description="Pobiera rozporzadzenia UE z EUR-Lex za pomoca CELLAR content negotiation. "
                    "Domyslnie pobiera 21 kluczowych rozporzadzen prawa zywnosciowego "
                    "w polskiej wersji jezykowej.",
        epilog="Przyklad: python fetch_eurlex.py --celex 32002R0178 32011R1169 --output ./data/",
    )
    parser.add_argument(
        "--celex",
        nargs="+",
        default=DEFAULT_CELEX_NUMBERS,
        help=f"Numery CELEX do pobrania (domyslnie: {len(DEFAULT_CELEX_NUMBERS)} rozporzadzen prawa zywnosciowego)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output/eurlex",
        help="Katalog wyjsciowy (domyslnie: ./output/eurlex)",
    )
    parser.add_argument(
        "--language", "-l",
        type=str,
        default="pl",
        choices=["pl", "en", "de", "fr", "es", "it"],
        help="Jezyk dokumentu (domyslnie: pl)",
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
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Pomin dokumenty juz pobrane (plik .html istnieje w katalogu wyjsciowym)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    output_dir = Path(args.output)
    logger.info(f"Start pobierania {len(args.celex)} dokumentow z EUR-Lex (CELLAR)")
    logger.info(f"Jezyk: {args.language}, Katalog wyjsciowy: {output_dir}")

    success_count = 0
    error_count = 0
    skipped_count = 0

    for i, celex in enumerate(args.celex, 1):
        # Sprawdz czy juz pobrano
        if args.skip_existing:
            existing = output_dir / f"{celex}.html"
            if existing.exists() and existing.stat().st_size > 0:
                logger.info(f"[{i}/{len(args.celex)}] Pomijam CELEX {celex} (juz istnieje)")
                skipped_count += 1
                continue

        logger.info(f"[{i}/{len(args.celex)}] Przetwarzanie CELEX: {celex}")

        if fetch_document(celex, output_dir, args.language, args.delay):
            success_count += 1
        else:
            error_count += 1

        # Opoznienie miedzy dokumentami (uprzejmosc wobec serwera)
        if i < len(args.celex):
            time.sleep(args.delay)

    logger.info(
        f"Zakonczono: {success_count} pobrano, {error_count} bledow, "
        f"{skipped_count} pominieto z {len(args.celex)} dokumentow"
    )

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
