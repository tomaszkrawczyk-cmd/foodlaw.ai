#!/usr/bin/env python3
"""
Skrypt do konwersji pobranych plikow HTML/XML na ustrukturyzowany Markdown.

Obsluguje format HTML z EUR-Lex (artykuly, motywy, zalaczniki) oraz
format ISAP. Zachowuje numeracje artykulow i strukture paragrafow.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0 OR MIT
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path

try:
    import html2text
except ImportError:
    print("Brak modulu 'html2text'. Zainstaluj: pip install html2text")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Brak modulu 'beautifulsoup4'. Zainstaluj: pip install beautifulsoup4")
    sys.exit(1)

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """Konfiguruje logowanie."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def create_html2text_converter() -> html2text.HTML2Text:
    """Tworzy skonfigurowany konwerter HTML2Text."""
    converter = html2text.HTML2Text()
    converter.body_width = 0  # Bez zawijania linii
    converter.unicode_snob = True
    converter.protect_links = True
    converter.wrap_links = False
    converter.mark_code = True
    converter.default_image_alt = ""
    converter.ignore_images = True
    converter.ignore_emphasis = False
    return converter


def detect_source_type(html_content: str, filename: str) -> str:
    """
    Wykrywa typ zrodla dokumentu (EUR-Lex, ISAP, inny).

    Args:
        html_content: Tresc HTML
        filename: Nazwa pliku

    Returns:
        Typ zrodla: 'eurlex', 'isap', 'unknown'
    """
    if "eur-lex" in html_content.lower() or filename.startswith("3"):
        return "eurlex"
    elif "isap" in html_content.lower() or "sejm" in html_content.lower():
        return "isap"
    else:
        return "unknown"


def process_eurlex_html(html_content: str) -> str:
    """
    Przetwarza HTML z EUR-Lex zachowujac strukture aktu prawnego.

    Args:
        html_content: Tresc HTML z EUR-Lex

    Returns:
        Ustrukturyzowany Markdown
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Usun niepotrzebne elementy
    for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    # Znajdz tresc glowna
    content = soup.find("div", id="TexteOnly") or soup.find("body")
    if not content:
        content = soup

    # Przetworz artykuly - dodaj formatowanie Markdown
    for article in content.find_all(string=re.compile(r"^Artyku[lł]\s+\d+")):
        parent = article.parent
        if parent:
            parent.insert_before("\n\n### ")

    # Przetworz rozdzialy
    for chapter in content.find_all(string=re.compile(r"^ROZDZIA[LŁ]\s+[IVX\d]+")):
        parent = chapter.parent
        if parent:
            parent.insert_before("\n\n## ")

    # Przetworz tytuly
    for title_tag in content.find_all(string=re.compile(r"^TYTU[LŁ]\s+[IVX\d]+")):
        parent = title_tag.parent
        if parent:
            parent.insert_before("\n\n# ")

    # Konwertuj na Markdown
    converter = create_html2text_converter()
    markdown = converter.handle(str(content))

    # Post-processing
    markdown = clean_markdown(markdown)
    return markdown


def process_isap_html(html_content: str) -> str:
    """
    Przetwarza HTML z ISAP zachowujac strukture ustawy.

    Args:
        html_content: Tresc HTML z ISAP

    Returns:
        Ustrukturyzowany Markdown
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Usun niepotrzebne elementy
    for tag in soup.find_all(["script", "style", "nav", "footer"]):
        tag.decompose()

    # Znajdz tresc
    content = soup.find("div", class_="textContent") or soup.find("body")
    if not content:
        content = soup

    # Konwertuj na Markdown
    converter = create_html2text_converter()
    markdown = converter.handle(str(content))

    # Post-processing specyficzny dla ISAP
    # Oznacz artykuly
    markdown = re.sub(
        r"^(Art\.\s+\d+[a-z]?\.)",
        r"\n### \1",
        markdown,
        flags=re.MULTILINE,
    )

    # Oznacz rozdzialy
    markdown = re.sub(
        r"^(Rozdzia[lł]\s+\d+[a-z]?)",
        r"\n## \1",
        markdown,
        flags=re.MULTILINE,
    )

    # Oznacz dzialy
    markdown = re.sub(
        r"^(DZIA[LŁ]\s+[IVX\d]+)",
        r"\n# \1",
        markdown,
        flags=re.MULTILINE,
    )

    markdown = clean_markdown(markdown)
    return markdown


def clean_markdown(markdown: str) -> str:
    """
    Oczyszcza i formatuje wynikowy Markdown.

    Args:
        markdown: Surowy Markdown

    Returns:
        Oczyszczony Markdown
    """
    # Usun nadmierne puste linie
    markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

    # Usun spacje na koncach linii
    markdown = re.sub(r" +$", "", markdown, flags=re.MULTILINE)

    # Napraw formatowanie list numerowanych
    markdown = re.sub(r"^(\d+)\)", r"\1.", markdown, flags=re.MULTILINE)

    # Usun puste naglowki
    markdown = re.sub(r"^#{1,6}\s*$", "", markdown, flags=re.MULTILINE)

    return markdown.strip() + "\n"


def convert_file(input_path: Path, output_path: Path) -> bool:
    """
    Konwertuje pojedynczy plik HTML/XML na Markdown.

    Args:
        input_path: Sciezka do pliku wejsciowego
        output_path: Sciezka do pliku wyjsciowego

    Returns:
        True jesli sukces
    """
    logger.info(f"Konwersja: {input_path} -> {output_path}")

    try:
        with open(input_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        try:
            with open(input_path, "r", encoding="latin-1") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Blad odczytu pliku {input_path}: {e}")
            return False
    except Exception as e:
        logger.error(f"Blad odczytu pliku {input_path}: {e}")
        return False

    if not content.strip():
        logger.warning(f"Pusty plik: {input_path}")
        return False

    # Wykryj typ zrodla
    source_type = detect_source_type(content, input_path.name)
    logger.debug(f"Wykryty typ zrodla: {source_type}")

    # Przetworz wedlug typu
    if source_type == "eurlex":
        markdown = process_eurlex_html(content)
    elif source_type == "isap":
        markdown = process_isap_html(content)
    else:
        # Generyczna konwersja
        converter = create_html2text_converter()
        markdown = converter.handle(content)
        markdown = clean_markdown(markdown)

    # Zapisz
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown)

    logger.info(f"Zapisano: {output_path} ({len(markdown)} znakow)")
    return True


def main():
    """Glowna funkcja - parsuje argumenty i uruchamia konwersje."""
    parser = argparse.ArgumentParser(
        description="Konwertuje pobrane pliki HTML/XML na ustrukturyzowany Markdown. "
                    "Obsluguje format EUR-Lex (artykuly, motywy, zalaczniki) oraz "
                    "format ISAP (ustawy polskie). Zachowuje numeracje artykulow "
                    "i paragrafow.",
        epilog="Przyklad: python convert_to_markdown.py --input ./output/eurlex/ "
               "--output ./przepisy/unijne/",
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="Katalog wejsciowy z plikami HTML/XML lub pojedynczy plik",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        required=True,
        help="Katalog wyjsciowy dla plikow Markdown",
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".html", ".htm", ".xml", ".xhtml"],
        help="Rozszerzenia plikow do przetworzenia (domyslnie: .html .htm .xml .xhtml)",
    )
    parser.add_argument(
        "--recursive", "-r",
        action="store_true",
        help="Przetwarzaj podkatalogi rekursywnie",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Wlacz szczegolowe logowanie (DEBUG)",
    )

    args = parser.parse_args()
    setup_logging(args.verbose)

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        logger.error(f"Sciezka wejsciowa nie istnieje: {input_path}")
        sys.exit(1)

    # Zbierz pliki do przetworzenia
    if input_path.is_file():
        files = [input_path]
    else:
        if args.recursive:
            files = []
            for ext in args.extensions:
                files.extend(input_path.rglob(f"*{ext}"))
        else:
            files = []
            for ext in args.extensions:
                files.extend(input_path.glob(f"*{ext}"))

    if not files:
        logger.warning(f"Brak plikow do przetworzenia w: {input_path}")
        sys.exit(0)

    logger.info(f"Znaleziono {len(files)} plikow do konwersji")

    success_count = 0
    error_count = 0

    for filepath in sorted(files):
        # Oblicz sciezke wyjsciowa
        if input_path.is_file():
            out_path = output_dir / (filepath.stem + ".md")
        else:
            relative = filepath.relative_to(input_path)
            out_path = output_dir / relative.with_suffix(".md")

        if convert_file(filepath, out_path):
            success_count += 1
        else:
            error_count += 1

    logger.info(
        f"Zakonczono: {success_count} skonwertowano, {error_count} bledow "
        f"z {len(files)} plikow"
    )

    if error_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
