#!/usr/bin/env python3
"""
Skrypt do pobierania rozporzadzen UE z EUR-Lex za pomoca CELLAR SPARQL endpoint.

Pobiera polskie wersje jezykowe aktow prawnych na podstawie numerow CELEX.
Wykorzystuje endpoint SPARQL: https://publications.europa.eu/webapi/rdf/sparql

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
    print("Brak modulu 'SPARQLWrapper'. Zainstaluj: pip install SPARQLWrapper")
    sys.exit(1)

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
    "32008R1333",  # Rozp. 1333/2008 - Dodatki do zywnosci
    "32003R1829",  # Rozp. 1829/2003 - Genetycznie zmodyfikowana zywnosc i pasza
    "32003R1830",  # Rozp. 1830/2003 - Identyfikowalnosc i etykietowanie GMO
    "32018R0848",  # Rozp. 2018/848 - Produkcja ekologiczna
    "32004R1935",  # Rozp. 1935/2004 - Materialy kontaktowe z zywnoscia (framework)
    "32011R0010",  # Rozp. 10/2011 - Materialy z tworzyw sztucznych do kontaktu z zywnoscia
    "32008R1334",  # Rozp. 1334/2008 - Aromaty
    "32008R1332",  # Rozp. 1332/2008 - Enzymy spozywcze
    "32005R0396",  # Rozp. 396/2005 - Najwyzsze dopuszczalne poziomy pozostalosci pestycydow
    "32016R0127",  # Rozp. del. 2016/127 - Preparaty dla niemowlat
    "32016R0128",  # Rozp. del. 2016/128 - Zywnosc specjalnego przeznaczenia medycznego (FSMP)
    "32017R1798",  # Rozp. del. 2017/1798 - Srodki zastepujace cala diete do kontroli masy ciala
]

CELLAR_SPARQL_ENDPOINT = "https://publications.europa.eu/webapi/rdf/sparql"
EURLEX_REST_BASE = "https://eur-lex.europa.eu/legal-content/PL/TXT/HTML/"

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


def build_sparql_query(celex: str, language: str = "PL") -> str:
    """
    Buduje zapytanie SPARQL do pobrania metadanych i URI dokumentu z CELLAR.

    Args:
        celex: Numer CELEX dokumentu
        language: Kod jezyka (domyslnie PL)

    Returns:
        Zapytanie SPARQL jako string
    """
    query = f"""
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
    PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

    SELECT DISTINCT ?title ?date ?expression ?manifestation
    WHERE {{
        ?work cdm:resource_legal_id_celex "{celex}"^^xsd:string .
        ?work cdm:work_date_document ?date .
        ?expression cdm:expression_belongs_to_work ?work .
        ?expression cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/{language}> .
        ?expression cdm:expression_title ?title .
        OPTIONAL {{
            ?manifestation cdm:manifestation_manifests_expression ?expression .
            ?manifestation cdm:manifestation_type <http://publications.europa.eu/resource/authority/file-type/HTML> .
        }}
    }}
    LIMIT 10
    """
    return query


def fetch_metadata_sparql(celex: str, language: str = "PL") -> dict:
    """
    Pobiera metadane dokumentu z CELLAR za pomoca SPARQL.

    Args:
        celex: Numer CELEX
        language: Kod jezyka

    Returns:
        Slownik z metadanymi (title, date, uri)
    """
    logger.info(f"Pobieranie metadanych SPARQL dla CELEX: {celex}")

    sparql = SPARQLWrapper(CELLAR_SPARQL_ENDPOINT)
    sparql.addCustomHttpHeader("User-Agent", USER_AGENT)

    query = build_sparql_query(celex, language)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)

    try:
        results = sparql.query().convert()
        bindings = results.get("results", {}).get("bindings", [])

        if not bindings:
            logger.warning(f"Brak wynikow SPARQL dla CELEX: {celex}")
            return {}

        first = bindings[0]
        metadata = {
            "celex": celex,
            "title": first.get("title", {}).get("value", ""),
            "date": first.get("date", {}).get("value", ""),
            "expression_uri": first.get("expression", {}).get("value", ""),
            "manifestation_uri": first.get("manifestation", {}).get("value", ""),
        }

        logger.debug(f"Metadane: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Blad SPARQL dla CELEX {celex}: {e}")
        return {}


def fetch_html_content(celex: str, language: str = "PL") -> str:
    """
    Pobiera tresc HTML dokumentu z EUR-Lex REST.

    Args:
        celex: Numer CELEX
        language: Kod jezyka

    Returns:
        Tresc HTML jako string
    """
    url = f"{EURLEX_REST_BASE}?uri=CELEX:{celex}"
    logger.info(f"Pobieranie HTML z: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html",
        "Accept-Language": f"{language.lower()},en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text

    except requests.exceptions.Timeout:
        logger.error(f"Timeout przy pobieraniu CELEX {celex}")
        return ""
    except requests.exceptions.HTTPError as e:
        logger.error(f"Blad HTTP {e.response.status_code} dla CELEX {celex}: {e}")
        return ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Blad polaczenia dla CELEX {celex}: {e}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Blad zadania dla CELEX {celex}: {e}")
        return ""


def save_document(celex: str, content: str, metadata: dict, output_dir: Path) -> Path:
    """
    Zapisuje pobrany dokument do pliku.

    Args:
        celex: Numer CELEX
        content: Tresc HTML
        metadata: Metadane dokumentu
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

    # Zapisz metadane
    meta_path = output_dir / f"{celex}.meta.txt"
    with open(meta_path, "w", encoding="utf-8") as f:
        for key, value in metadata.items():
            f.write(f"{key}: {value}\n")

    return filepath


def fetch_document(celex: str, output_dir: Path, language: str = "PL",
                   delay: float = 2.0) -> bool:
    """
    Pobiera pojedynczy dokument (metadane + tresc).

    Args:
        celex: Numer CELEX
        output_dir: Katalog wyjsciowy
        language: Kod jezyka
        delay: Opoznienie miedzy zadaniami (sekundy)

    Returns:
        True jesli sukces, False w przypadku bledu
    """
    # Pobierz metadane z CELLAR SPARQL
    metadata = fetch_metadata_sparql(celex, language)

    time.sleep(delay)

    # Pobierz tresc HTML
    content = fetch_html_content(celex, language)

    if not content:
        logger.warning(f"Brak tresci dla CELEX {celex} - pomijam")
        return False

    save_document(celex, content, metadata, output_dir)
    return True


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia pobieranie."""
    parser = argparse.ArgumentParser(
        description="Pobiera rozporzadzenia UE z EUR-Lex (CELLAR SPARQL + REST API). "
                    "Domyslnie pobiera 21 kluczowych rozporzadzen prawa zywnosciowego "
                    "w polskiej wersji jezykowej.",
        epilog="Przyklad: python fetch_eurlex.py --celex 32002R0178 32011R1169 --output ./data/",
    )
    parser.add_argument(
        "--celex",
        nargs="+",
        default=DEFAULT_CELEX_NUMBERS,
        help="Numery CELEX do pobrania (domyslnie: 21 rozporzadzen prawa zywnosciowego)",
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
        default="PL",
        choices=["PL", "EN", "DE", "FR", "ES", "IT"],
        help="Jezyk dokumentu (domyslnie: PL)",
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

    output_dir = Path(args.output)
    logger.info(f"Start pobierania {len(args.celex)} dokumentow z EUR-Lex")
    logger.info(f"Jezyk: {args.language}, Katalog wyjsciowy: {output_dir}")

    success_count = 0
    error_count = 0

    for i, celex in enumerate(args.celex, 1):
        logger.info(f"[{i}/{len(args.celex)}] Przetwarzanie CELEX: {celex}")

        if fetch_document(celex, output_dir, args.language, args.delay):
            success_count += 1
        else:
            error_count += 1

        # Opoznienie miedzy dokumentami
        if i < len(args.celex):
            time.sleep(args.delay)

    logger.info(
        f"Zakonczono: {success_count} sukces(ow), {error_count} blad(ow) "
        f"z {len(args.celex)} dokumentow"
    )

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
