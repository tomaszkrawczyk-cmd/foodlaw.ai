#!/usr/bin/env python3
"""
Skrypt do pobierania rozporzadzen UE i orzecznictwa TSUE z EUR-Lex.

Wykorzystuje EUR-Lex SOAP Web Service (WS-Security) jako metode podstawowa
oraz CELLAR SPARQL endpoint jako fallback.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
import logging
import os
import sys
import time
import re
from pathlib import Path
from xml.etree import ElementTree as ET

try:
    from dotenv import load_dotenv
except ImportError:
    print("Brak modulu 'python-dotenv'. Zainstaluj: pip install python-dotenv")
    sys.exit(1)

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

try:
    from zeep import Client
    from zeep.wsse.username import UsernameToken
    from zeep.exceptions import Fault as ZeepFault
    from zeep.transports import Transport
except ImportError:
    print("Brak modulu 'zeep'. Zainstaluj: pip install zeep")
    sys.exit(1)

try:
    from convert_to_markdown import process_eurlex_html
except ImportError:
    # Fallback: try relative import
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from convert_to_markdown import process_eurlex_html
    except ImportError:
        process_eurlex_html = None

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

# Numery CELEX orzecznictwa TSUE dotyczacego prawa zywnosciowego
DEFAULT_JUDGMENT_CELEX_NUMBERS = [
    "62012CJ0299",  # C-299/12 - GMO, prawo zywnosciowe
    "62018CJ0663",  # C-663/18 - Novel food, nowa zywnosc
    "62012CJ0609",  # C-609/12 - Green Swan, health claims
    "62014CJ0195",  # C-195/14 - Oznakowanie zywnosci
    "62009CJ0382",  # C-382/09 - Dodatki do zywnosci
    "62001CJ0236",  # C-236/01 - Zasada ostroznosci
    "62007CJ0140",  # C-140/07 - Granica suplement/lek
    "62010CJ0544",  # C-544/10 - Health claims, wino
    "62017CJ0616",  # C-616/17 - Prawo zywnosciowe, etykietowanie
    "62004CJ0210",  # C-210/04 - Bezpieczenstwo zywnosci
]

EURLEX_WS_ENDPOINT = "https://eur-lex.europa.eu/EURLexWebService"
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


def load_credentials() -> tuple:
    """
    Laduje dane dostepu do EUR-Lex Web Service z pliku .env.

    Returns:
        Tuple (username, password) lub (None, None) jesli brak danych
    """
    load_dotenv()
    username = os.environ.get("EURLEX_USERNAME")
    password = os.environ.get("EURLEX_PASSWORD")

    if not username or not password:
        logger.warning(
            "Brak danych dostepu do EUR-Lex Web Service. "
            "Ustaw zmienne EURLEX_USERNAME i EURLEX_PASSWORD w pliku .env. "
            "Kontynuuje w trybie SPARQL-only."
        )
        return None, None

    return username, password


def create_soap_client(username: str, password: str) -> Client:
    """
    Tworzy klienta SOAP z WS-Security UsernameToken.

    Args:
        username: Nazwa uzytkownika EUR-Lex
        password: Haslo EUR-Lex

    Returns:
        Skonfigurowany klient zeep
    """
    wsse = UsernameToken(username, password)
    transport = Transport(timeout=60, operation_timeout=60)
    try:
        client = Client(
            f"{EURLEX_WS_ENDPOINT}?wsdl",
            wsse=wsse,
            transport=transport,
        )
        logger.info("Utworzono klienta SOAP EUR-Lex Web Service")
        return client
    except Exception as e:
        logger.error(f"Blad tworzenia klienta SOAP: {e}")
        return None


def build_soap_request(celex: str, search_type: str = "DN") -> str:
    """
    Buduje expert query dla EUR-Lex SOAP Web Service.

    Args:
        celex: Numer CELEX dokumentu lub wartosc wyszukiwania
        search_type: Typ wyszukiwania (DN = Document Number, CT = Classification)

    Returns:
        Expert query jako string
    """
    if search_type == "DN":
        return f"SELECT DN WHERE DN = {celex}"
    elif search_type == "CT":
        return f"SELECT CT WHERE CT = 6 AND DD = {celex}"
    else:
        return f"SELECT DN WHERE DN = {celex}"


def execute_soap_query(client: Client, expert_query: str,
                       page: int = 1, page_size: int = 10,
                       language: str = "en") -> str:
    """
    Wykonuje zapytanie SOAP do EUR-Lex Web Service.

    Args:
        client: Klient SOAP zeep
        expert_query: Zapytanie expert query
        page: Numer strony (od 1)
        page_size: Wynikow na stronie (max 100)
        language: Jezyk wyszukiwania

    Returns:
        Odpowiedz XML jako string lub pusty string w przypadku bledu
    """
    try:
        response = client.service.doQuery(
            expertQuery=expert_query,
            page=page,
            pageSize=page_size,
            searchLanguage=language,
        )
        logger.debug(f"Odpowiedz SOAP (pierwsze 500 znakow): {str(response)[:500]}")
        return str(response) if response else ""
    except ZeepFault as e:
        fault_string = str(e)
        if "WS_MAXIMUM_NB_OF_WS_CALLS" in fault_string:
            logger.error(
                "Przekroczono limit polaczen EUR-Lex Web Service. "
                "Poczekaj i sprobuj ponownie pozniej."
            )
        else:
            logger.error(f"Blad SOAP (Fault): {e}")
        return ""
    except Exception as e:
        logger.error(f"Blad zapytania SOAP: {e}")
        return ""


def parse_soap_response(response_xml: str) -> list:
    """
    Parsuje odpowiedz XML z EUR-Lex SOAP Web Service.

    Wyodrebnia informacje o dokumentach: CELEX, tytul, date, URL tresci.

    Args:
        response_xml: Odpowiedz XML jako string

    Returns:
        Lista slownikow z metadanymi dokumentow
    """
    documents = []

    if not response_xml or not response_xml.strip():
        return documents

    try:
        # Proba parsowania jako XML
        root = ET.fromstring(response_xml)
    except ET.ParseError:
        # Jesli nie jest poprawnym XML, szukaj wzorcow tekstowo
        logger.debug("Odpowiedz nie jest poprawnym XML, proba parsowania tekstowego")
        return _parse_response_text(response_xml)

    # Szukaj elementow RESULT/DOCUMENT w roznych namespacach
    for doc_elem in _find_document_elements(root):
        doc_info = _extract_document_info(doc_elem)
        if doc_info:
            documents.append(doc_info)

    return documents


def _find_document_elements(root: ET.Element) -> list:
    """Znajduje elementy dokumentow w drzewie XML."""
    elements = []

    # Szukaj bez namespace
    for elem in root.iter():
        tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
        if tag in ("DOCUMENT", "DOC", "result", "SEARCH_RESULT"):
            elements.append(elem)

    # Jesli nie znaleziono, uzyj calego root
    if not elements:
        elements = [root]

    return elements


def _extract_document_info(elem: ET.Element) -> dict:
    """Wyodrebnia metadane dokumentu z elementu XML."""
    info = {}

    for child in elem.iter():
        tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
        text = (child.text or "").strip()

        if tag == "ID_CELEX" or tag == "CELEX":
            info["celex"] = text
        elif tag == "EXPRESSION_TITLE" or tag == "TITLE":
            info["title"] = text
        elif tag == "WORK_DATE_DOCUMENT" or tag == "DATE":
            info["date"] = text
        elif tag == "CONTENT_URL" or tag == "DRECONTENT":
            info["content_url"] = text
        elif tag == "MANIFESTATION_OFFICIALJOURNAL_PART_URI":
            if "content_url" not in info:
                info["content_url"] = text

    return info if info else None


def _parse_response_text(response_text: str) -> list:
    """Parsuje odpowiedz jako tekst jesli nie jest poprawnym XML."""
    documents = []

    # Szukaj numerow CELEX w tekscie
    celex_pattern = re.compile(r"(\d{5}[A-Z]\d{4}|6\d{4}[A-Z]{2}\d{4})")
    url_pattern = re.compile(r'(https?://[^\s<>"]+)')

    celex_matches = celex_pattern.findall(response_text)
    url_matches = url_pattern.findall(response_text)

    for celex in celex_matches:
        doc = {"celex": celex}
        # Sprobuj dopasowac URL
        for url in url_matches:
            if celex in url or "eur-lex" in url:
                doc["content_url"] = url
                break
        documents.append(doc)

    return documents


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
    Pobiera metadane dokumentu z CELLAR za pomoca SPARQL (fallback).

    Args:
        celex: Numer CELEX
        language: Kod jezyka

    Returns:
        Slownik z metadanymi (title, date, uri)
    """
    logger.info(f"[SPARQL fallback] Pobieranie metadanych dla CELEX: {celex}")

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

        logger.debug(f"Metadane SPARQL: {metadata}")
        return metadata

    except Exception as e:
        logger.error(f"Blad SPARQL dla CELEX {celex}: {e}")
        return {}


def fetch_html_content(url: str) -> str:
    """
    Pobiera tresc HTML z podanego URL.

    Args:
        url: URL dokumentu

    Returns:
        Tresc HTML jako string
    """
    logger.info(f"Pobieranie HTML z: {url}")

    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html",
        "Accept-Language": "pl,en;q=0.5",
    }

    try:
        response = requests.get(url, headers=headers, timeout=60)
        response.raise_for_status()
        return response.text

    except requests.exceptions.Timeout:
        logger.error(f"Timeout przy pobieraniu: {url}")
        return ""
    except requests.exceptions.HTTPError as e:
        logger.error(f"Blad HTTP {e.response.status_code} dla: {url}")
        return ""
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Blad polaczenia dla: {url}")
        return ""
    except requests.exceptions.RequestException as e:
        logger.error(f"Blad zadania dla: {url}")
        return ""


def fetch_html_by_celex(celex: str, language: str = "PL") -> str:
    """
    Pobiera tresc HTML dokumentu z EUR-Lex po numerze CELEX.

    Args:
        celex: Numer CELEX
        language: Kod jezyka

    Returns:
        Tresc HTML jako string
    """
    url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"
    return fetch_html_content(url)


def generate_front_matter(celex: str, title: str = "", date: str = "",
                          source_url: str = "") -> str:
    """
    Generuje YAML front-matter dla pliku Markdown.

    Args:
        celex: Numer CELEX
        title: Tytul dokumentu
        date: Data dokumentu
        source_url: URL zrodlowy

    Returns:
        Front-matter jako string
    """
    lines = ["---"]
    lines.append('celex: "' + celex + '"')
    if title:
        safe_title = title.replace('"', '\\"')
        lines.append('title: "' + safe_title + '"')
    if date:
        lines.append('date: "' + date + '"')
    if source_url:
        lines.append('source_url: "' + source_url + '"')
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def convert_html_to_markdown(html_content: str) -> str:
    """
    Konwertuje HTML na Markdown, uzywajac process_eurlex_html jesli dostepne.

    Args:
        html_content: Tresc HTML

    Returns:
        Tresc Markdown
    """
    if process_eurlex_html is not None:
        return process_eurlex_html(html_content)
    else:
        # Prosta konwersja fallback
        try:
            import html2text
            converter = html2text.HTML2Text()
            converter.body_width = 0
            converter.unicode_snob = True
            return converter.handle(html_content)
        except ImportError:
            logger.warning("Brak html2text - zwracam surowy tekst")
            return html_content


def fetch_document_soap(client: Client, celex: str, language: str = "PL",
                        output_dir: Path = None) -> bool:
    """
    Pobiera pojedynczy dokument za pomoca SOAP Web Service.

    Args:
        client: Klient SOAP
        celex: Numer CELEX
        language: Kod jezyka
        output_dir: Katalog wyjsciowy

    Returns:
        True jesli sukces, False w przypadku bledu
    """
    lang_lower = language.lower()
    expert_query = build_soap_request(celex, "DN")
    logger.info(f"Zapytanie SOAP: {expert_query}")

    response = execute_soap_query(client, expert_query, page=1, page_size=10,
                                  language=lang_lower)

    metadata = {"celex": celex, "title": "", "date": "", "content_url": ""}

    if response:
        documents = parse_soap_response(response)
        if documents:
            # Uzyj pierwszego znalezionego dokumentu
            doc = documents[0]
            metadata.update(doc)
            logger.info(f"Znaleziono dokument SOAP: {metadata.get('celex', celex)}")

    # Jesli mamy URL z SOAP, uzyj go; w przeciwnym razie buduj URL standardowy
    content_url = metadata.get("content_url", "")
    if content_url:
        html_content = fetch_html_content(content_url)
    else:
        html_content = fetch_html_by_celex(celex, language)
        content_url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"

    if not html_content:
        logger.warning(f"Brak tresci HTML dla CELEX {celex}")
        return False

    # Konwertuj na Markdown
    markdown_content = convert_html_to_markdown(html_content)

    # Dodaj front-matter
    front_matter = generate_front_matter(
        celex=celex,
        title=metadata.get("title", ""),
        date=metadata.get("date", ""),
        source_url=content_url,
    )
    full_content = front_matter + markdown_content

    # Zapisz plik
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        filepath = output_dir / f"{celex}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)
        logger.info(f"Zapisano: {filepath}")

    return True


def fetch_document_sparql_fallback(celex: str, language: str = "PL",
                                   output_dir: Path = None,
                                   doc_type: str = "regulation") -> bool:
    """
    Pobiera dokument za pomoca SPARQL + bezposredni download (fallback).

    Args:
        celex: Numer CELEX
        language: Kod jezyka
        output_dir: Katalog wyjsciowy
        doc_type: Typ dokumentu ('regulation' lub 'judgment')

    Returns:
        True jesli sukces, False w przypadku bledu
    """
    metadata = fetch_metadata_sparql(celex, language)

    html_content = fetch_html_by_celex(celex, language)
    source_url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"

    if not html_content:
        logger.warning(f"[SPARQL fallback] Brak tresci dla CELEX {celex}")
        return False

    # Konwertuj na Markdown
    markdown_content = convert_html_to_markdown(html_content)

    # Dodaj front-matter
    front_matter = generate_front_matter(
        celex=celex,
        title=metadata.get("title", ""),
        date=metadata.get("date", ""),
        source_url=source_url,
    )
    full_content = front_matter + markdown_content

    # Zapisz plik
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        if doc_type == "judgment":
            filename = generate_judgment_filename(celex, metadata)
        else:
            filename = f"{celex}.md"
        filepath = output_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(full_content)
        logger.info(f"[SPARQL fallback] Zapisano: {filepath}")

    return True


def generate_judgment_filename(celex: str, metadata: dict) -> str:
    """
    Generuje nazwe pliku dla orzeczenia TSUE na podstawie konwencji.

    Format: RRRR-MM-DD-C-NNN-RR-krotki-opis.md

    Args:
        celex: Numer CELEX (np. 62012CJ0299)
        metadata: Metadane dokumentu

    Returns:
        Nazwa pliku
    """
    # Wyodrebnij numer sprawy z CELEX
    # Format CELEX: 6RRRRCC####  (6=orzecznictwo, RRRR=rok, CC=typ sadu, ####=numer)
    case_match = re.match(r"6(\d{4})(CJ|TJ)(\d{4})", celex)
    if case_match:
        year = case_match.group(1)
        case_num = str(int(case_match.group(3)))  # Usun wiodace zera
        case_ref = f"C-{case_num}-{year[2:]}"
    else:
        case_ref = celex

    # Data z metadanych
    date = metadata.get("date", "")
    if date and len(date) >= 10:
        date_part = date[:10]
    else:
        date_part = "unknown-date"

    filename = f"{date_part}-{case_ref}.md"
    return filename


def fetch_judgments_soap(client: Client, language: str = "PL",
                         output_dir: Path = None, max_judgments: int = 50,
                         delay: float = 2.0) -> tuple:
    """
    Pobiera orzeczenia TSUE dotyczace prawa zywnosciowego.

    Args:
        client: Klient SOAP
        language: Kod jezyka
        output_dir: Katalog wyjsciowy
        max_judgments: Maksymalna liczba orzeczen do pobrania
        delay: Opoznienie miedzy zapytaniami

    Returns:
        Tuple (success_count, error_count)
    """
    success_count = 0
    error_count = 0
    processed_celex = set()

    lang_lower = language.lower()

    # 1. Pobierz znane orzeczenia po CELEX
    for i, celex in enumerate(DEFAULT_JUDGMENT_CELEX_NUMBERS):
        if success_count >= max_judgments:
            break

        logger.info(f"[{i+1}/{len(DEFAULT_JUDGMENT_CELEX_NUMBERS)}] Orzeczenie CELEX: {celex}")

        expert_query = build_soap_request(celex, "DN")
        response = execute_soap_query(client, expert_query, page=1, page_size=10,
                                      language=lang_lower)

        metadata = {"celex": celex, "title": "", "date": "", "content_url": ""}
        if response:
            documents = parse_soap_response(response)
            if documents:
                metadata.update(documents[0])

        # Pobierz HTML
        content_url = metadata.get("content_url", "")
        if content_url:
            html_content = fetch_html_content(content_url)
        else:
            html_content = fetch_html_by_celex(celex, language)
            content_url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"

        if html_content:
            markdown_content = convert_html_to_markdown(html_content)
            front_matter = generate_front_matter(
                celex=celex,
                title=metadata.get("title", ""),
                date=metadata.get("date", ""),
                source_url=content_url,
            )
            full_content = front_matter + markdown_content

            if output_dir:
                output_dir.mkdir(parents=True, exist_ok=True)
                filename = generate_judgment_filename(celex, metadata)
                filepath = output_dir / filename
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(full_content)
                logger.info(f"Zapisano orzeczenie: {filepath}")

            success_count += 1
            processed_celex.add(celex)
        else:
            error_count += 1

        time.sleep(delay)

    # 2. Wyszukaj dodatkowe orzeczenia wg tematu (prawo zywnosciowe)
    if success_count < max_judgments:
        logger.info("Wyszukiwanie dodatkowych orzeczen wg tematu (DD = 03.65)")
        subject_query = "SELECT CT WHERE CT = 6 AND DD = 03.65"
        response = execute_soap_query(client, subject_query, page=1,
                                      page_size=min(50, max_judgments - success_count),
                                      language=lang_lower)

        if response:
            documents = parse_soap_response(response)
            for doc in documents:
                if success_count >= max_judgments:
                    break
                celex = doc.get("celex", "")
                if not celex or celex in processed_celex:
                    continue

                logger.info(f"Dodatkowe orzeczenie: {celex}")
                content_url = doc.get("content_url", "")
                if content_url:
                    html_content = fetch_html_content(content_url)
                else:
                    html_content = fetch_html_by_celex(celex, language)
                    content_url = f"https://eur-lex.europa.eu/legal-content/{language}/TXT/HTML/?uri=CELEX:{celex}"

                if html_content:
                    markdown_content = convert_html_to_markdown(html_content)
                    front_matter = generate_front_matter(
                        celex=celex,
                        title=doc.get("title", ""),
                        date=doc.get("date", ""),
                        source_url=content_url,
                    )
                    full_content = front_matter + markdown_content

                    if output_dir:
                        filename = generate_judgment_filename(celex, doc)
                        filepath = output_dir / filename
                        with open(filepath, "w", encoding="utf-8") as f:
                            f.write(full_content)
                        logger.info(f"Zapisano orzeczenie: {filepath}")

                    success_count += 1
                    processed_celex.add(celex)
                else:
                    error_count += 1

                time.sleep(delay)

    return success_count, error_count


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia pobieranie."""
    parser = argparse.ArgumentParser(
        description="Pobiera rozporzadzenia UE i orzecznictwo TSUE z EUR-Lex "
                    "za pomoca SOAP Web Service (z fallbackiem na SPARQL). "
                    "Domyslnie pobiera kluczowe rozporzadzenia prawa zywnosciowego "
                    "w polskiej wersji jezykowej.",
        epilog="Przyklad: python fetch_eurlex.py --celex 32002R0178 32011R1169 --output ./data/",
    )
    parser.add_argument(
        "--celex",
        nargs="+",
        default=None,
        help="Numery CELEX do pobrania (domyslnie: lista rozporzadzen prawa zywnosciowego)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="Katalog wyjsciowy (domyslnie: przepisy/unijne/pelne-teksty/ lub orzecznictwo/tsue/)",
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
    parser.add_argument(
        "--type",
        type=str,
        default="regulation",
        choices=["regulation", "judgment"],
        help="Typ dokumentow do pobrania: regulation (rozporzadzenia) lub judgment (orzeczenia TSUE)",
    )
    parser.add_argument(
        "--max-judgments",
        type=int,
        default=50,
        help="Maksymalna liczba orzeczen TSUE do pobrania (domyslnie: 50)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Ustaw domyslny katalog wyjsciowy w zaleznosci od typu
    if args.output is None:
        if args.type == "regulation":
            output_dir = Path("przepisy/unijne/pelne-teksty/")
        else:
            output_dir = Path("orzecznictwo/tsue/")
    else:
        output_dir = Path(args.output)

    # Ustaw domyslna liste CELEX
    if args.celex is None:
        if args.type == "regulation":
            celex_list = DEFAULT_CELEX_NUMBERS
        else:
            celex_list = DEFAULT_JUDGMENT_CELEX_NUMBERS
    else:
        celex_list = args.celex

    logger.info(f"Typ: {args.type}, Jezyk: {args.language}, Katalog: {output_dir}")

    # Zaladuj dane dostepu
    username, password = load_credentials()

    # Sprobuj utworzyc klienta SOAP (tylko jesli sa dane dostepu)
    soap_client = None
    if username and password:
        logger.info("Zaladowano dane dostepu do EUR-Lex Web Service")
        soap_client = create_soap_client(username, password)

    use_soap = soap_client is not None

    if not use_soap:
        logger.warning(
            "Nie udalo sie utworzyc klienta SOAP. "
            "Uzywam metody SPARQL + bezposredni download jako fallback."
        )

    success_count = 0
    error_count = 0

    if args.type == "judgment" and use_soap:
        # Tryb orzecznictwa z SOAP
        logger.info(f"Pobieranie orzeczen TSUE (max: {args.max_judgments})")
        success_count, error_count = fetch_judgments_soap(
            soap_client, args.language, output_dir,
            max_judgments=args.max_judgments, delay=args.delay,
        )
    else:
        # Tryb rozporzadzen lub fallback
        total = len(celex_list)
        logger.info(f"Pobieranie {total} dokumentow")

        for i, celex in enumerate(celex_list, 1):
            logger.info(f"[{i}/{total}] Przetwarzanie CELEX: {celex}")

            success = False
            if use_soap:
                try:
                    success = fetch_document_soap(
                        soap_client, celex, args.language, output_dir
                    )
                except Exception as e:
                    logger.error(f"Blad SOAP dla {celex}: {e}")
                    logger.info("Przelaczam na fallback SPARQL")
                    success = False

            if not success:
                # Fallback do SPARQL
                success = fetch_document_sparql_fallback(
                    celex, args.language, output_dir, doc_type=args.type
                )

            if success:
                success_count += 1
            else:
                error_count += 1

            # Opoznienie miedzy dokumentami
            if i < total:
                time.sleep(args.delay)

    logger.info(
        f"Zakonczono: {success_count} sukces(ow), {error_count} blad(ow)"
    )

    if error_count > 0 and success_count == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
