#!/usr/bin/env python3
"""
Skrypt do konwersji pobranych plikow HTML/XML na ustrukturyzowany Markdown.

Obsluguje format XHTML z CELLAR (EUR-Lex content negotiation) z klasami CSS:
- eli-container, eli-subdivision, eli-main-title
- oj-ti-art, oj-ti-section-1, oj-ti-section-2
- oj-normal, oj-doc-ti, oj-sti-art

Obsluguje tez starszy format HTML z EUR-Lex oraz format ISAP.
Zachowuje numeracje artykulow i strukture paragrafow.

Autor: Tomasz Krawczyk / supplemental.pl
Licencja: Apache-2.0
"""

import argparse
import logging
import os
import re
import sys
from pathlib import Path

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
    import warnings
    try:
        from bs4 import XMLParsedAsHTMLWarning
        warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
    except ImportError:
        pass  # older beautifulsoup4 versions don't have this warning
except ImportError:
    print("Brak modulu 'beautifulsoup4'. Zainstaluj: pip install beautifulsoup4")
    sys.exit(1)

try:
    import lxml  # noqa: F401 - needed as parser backend
except ImportError:
    print("Brak modulu 'lxml'. Zainstaluj: pip install lxml")
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


def detect_source_type(html_content: str, filename: str) -> str:
    """
    Wykrywa typ zrodla dokumentu (CELLAR XHTML, EUR-Lex HTML, ISAP, inny).

    Args:
        html_content: Tresc HTML
        filename: Nazwa pliku

    Returns:
        Typ zrodla: 'cellar', 'eurlex', 'isap', 'unknown'
    """
    if "eli-container" in html_content or "oj-ti-art" in html_content:
        return "cellar"
    elif "eur-lex" in html_content.lower() or filename.startswith("3"):
        return "eurlex"
    elif "isap" in html_content.lower() or "sejm" in html_content.lower():
        return "isap"
    else:
        return "unknown"


def extract_text_from_element(element) -> str:
    """Wyciaga tekst z elementu, usuwajac nadmierne biale znaki."""
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def process_cellar_xhtml(html_content: str) -> str:
    """
    Przetwarza XHTML z CELLAR (content negotiation) zachowujac pelna
    strukture aktu prawnego.

    Format CELLAR uzywa klas CSS:
    - oj-doc-ti: tytul dokumentu
    - oj-ti-section-1: rozdzialy (ROZDZIAL I, II...)
    - oj-ti-section-2: podtytuly rozdzialow
    - oj-ti-art: artykuly (Artykul 1, 2...)
    - oj-sti-art: podtytuly artykulow
    - oj-normal: zwykly tekst
    - eli-subdivision: kontenery strukturalne (art_1, chp_1, rct_1...)

    Args:
        html_content: Tresc XHTML z CELLAR

    Returns:
        Ustrukturyzowany Markdown
    """
    soup = BeautifulSoup(html_content, "lxml")

    # Remove scripts, styles
    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    lines = []

    # Extract title
    title_div = soup.find("div", class_="eli-main-title")
    if title_div:
        title_parts = []
        for p in title_div.find_all("p", class_="oj-doc-ti"):
            text = extract_text_from_element(p)
            if text:
                title_parts.append(text)
        if title_parts:
            lines.append(f"# {' '.join(title_parts)}")
            lines.append("")

    # Find the main eli-container
    container = soup.find("div", class_="eli-container")
    if not container:
        container = soup.find("body")
    if not container:
        container = soup

    # Process the document structure
    _process_cellar_element(container, lines, skip_title=True)

    markdown = "\n".join(lines)
    markdown = clean_markdown(markdown)
    return markdown


def _process_cellar_element(element, lines, skip_title=False):
    """
    Rekurencyjnie przetwarza elementy CELLAR XHTML.

    Args:
        element: Element BeautifulSoup
        lines: Lista linii wynikowych (modyfikowana in-place)
        skip_title: Czy pominac eli-main-title (juz przetworzone)
    """
    if isinstance(element, NavigableString):
        return

    if not isinstance(element, Tag):
        return

    # Skip title div if already processed
    if skip_title and element.get("class") and "eli-main-title" in element.get("class", []):
        return

    # Handle specific CSS classes
    classes = element.get("class", [])

    # Chapter headers (ROZDZIAL I, II...)
    if "oj-ti-section-1" in classes:
        text = extract_text_from_element(element)
        if text:
            lines.append("")
            lines.append(f"## {text}")
            lines.append("")
        return

    # Chapter subtitles
    if "oj-ti-section-2" in classes:
        text = extract_text_from_element(element)
        if text:
            lines.append(f"### {text}")
            lines.append("")
        return

    # Article titles
    if "oj-ti-art" in classes:
        text = extract_text_from_element(element)
        if text:
            lines.append("")
            lines.append(f"#### {text}")
            lines.append("")
        return

    # Article subtitles (e.g. "Zakres stosowania")
    if "oj-sti-art" in classes:
        text = extract_text_from_element(element)
        if text:
            lines.append(f"**{text}**")
            lines.append("")
        return

    # Normal text paragraphs
    if "oj-normal" in classes and element.name == "p":
        text = extract_text_from_element(element)
        if text:
            lines.append(text)
            lines.append("")
        return

    # Table-based numbered items (recitals, article points)
    if element.name == "table":
        _process_cellar_table(element, lines)
        return

    # Annexes
    if "oj-ti-grseq-1" in classes:
        text = extract_text_from_element(element)
        if text:
            lines.append("")
            lines.append(f"## {text}")
            lines.append("")
        return

    # For div containers, process children
    if element.name in ("div", "body", "html"):
        for child in element.children:
            _process_cellar_element(child, lines, skip_title=skip_title)
        return

    # For other elements (p without oj- class, span, etc.), extract if they have content
    if element.name == "p":
        text = extract_text_from_element(element)
        if text and len(text) > 1:
            lines.append(text)
            lines.append("")
        return

    # For any other container, recurse
    for child in element.children:
        _process_cellar_element(child, lines, skip_title=skip_title)


def _process_cellar_table(table, lines):
    """
    Przetwarza tabele z CELLAR XHTML.

    W formacie CELLAR tabele sa uzywane do formatowania:
    - Motywow (recitals): (1), (2)...
    - Punktow artykulow: a), b), 1., 2.
    - Naglowkow dokumentu

    Args:
        table: Element <table>
        lines: Lista linii wynikowych
    """
    rows = table.find_all("tr")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) >= 2:
            # Numbered item: first cell is number, second is content
            number_text = extract_text_from_element(cells[0])
            content_text = extract_text_from_element(cells[-1])
            if number_text and content_text:
                lines.append(f"{number_text} {content_text}")
                lines.append("")
            elif content_text:
                lines.append(content_text)
                lines.append("")
        elif len(cells) == 1:
            text = extract_text_from_element(cells[0])
            if text:
                lines.append(text)
                lines.append("")


def process_eurlex_html(html_content: str) -> str:
    """
    Przetwarza starszy format HTML z EUR-Lex zachowujac strukture aktu prawnego.

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

    lines = []
    _extract_text_recursive(content, lines)

    markdown = "\n".join(lines)

    # Post-processing - identify articles and chapters
    markdown = re.sub(
        r"^(Artyku[lł]\s+\d+[a-z]?)",
        r"\n#### \1",
        markdown,
        flags=re.MULTILINE,
    )
    markdown = re.sub(
        r"^(ROZDZIA[LŁ]\s+[IVX\d]+)",
        r"\n## \1",
        markdown,
        flags=re.MULTILINE,
    )
    markdown = re.sub(
        r"^(TYTU[LŁ]\s+[IVX\d]+)",
        r"\n# \1",
        markdown,
        flags=re.MULTILINE,
    )

    markdown = clean_markdown(markdown)
    return markdown


def _extract_text_recursive(element, lines):
    """Extracts text recursively for simple HTML processing."""
    if isinstance(element, NavigableString):
        text = str(element).strip()
        if text:
            lines.append(text)
        return

    if not isinstance(element, Tag):
        return

    if element.name in ("script", "style"):
        return

    for child in element.children:
        _extract_text_recursive(child, lines)


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

    lines = []
    _extract_text_recursive(content, lines)

    markdown = "\n".join(lines)

    # Post-processing specyficzny dla ISAP
    markdown = re.sub(
        r"^(Art\.\s+\d+[a-z]?\.)",
        r"\n### \1",
        markdown,
        flags=re.MULTILINE,
    )
    markdown = re.sub(
        r"^(Rozdzia[lł]\s+\d+[a-z]?)",
        r"\n## \1",
        markdown,
        flags=re.MULTILINE,
    )
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
    # Usun nadmierne puste linie (max 2 puste linie)
    markdown = re.sub(r"\n{4,}", "\n\n\n", markdown)

    # Usun spacje na koncach linii
    markdown = re.sub(r" +$", "", markdown, flags=re.MULTILINE)

    # Usun puste naglowki
    markdown = re.sub(r"^#{1,6}\s*$", "", markdown, flags=re.MULTILINE)

    # Usun wielokrotne puste linie po naglowkach
    markdown = re.sub(r"(^#{1,6} .+)\n{3,}", r"\1\n\n", markdown, flags=re.MULTILINE)

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
    logger.debug(f"Wykryty typ zrodla: {source_type} dla {input_path.name}")

    # Przetworz wedlug typu
    if source_type == "cellar":
        markdown = process_cellar_xhtml(content)
    elif source_type == "eurlex":
        markdown = process_eurlex_html(content)
    elif source_type == "isap":
        markdown = process_isap_html(content)
    else:
        # Generyczna konwersja
        soup = BeautifulSoup(content, "lxml")
        for tag in soup.find_all(["script", "style"]):
            tag.decompose()
        body = soup.find("body") or soup
        lines = []
        _extract_text_recursive(body, lines)
        markdown = "\n".join(lines)
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
                    "Obsluguje format XHTML z CELLAR (artykuly, motywy, zalaczniki), "
                    "starszy format EUR-Lex oraz format ISAP (ustawy polskie). "
                    "Zachowuje numeracje artykulow i paragrafow.",
        epilog="Przyklad: python convert_to_markdown.py --input ./output/eurlex/ "
               "--output ./przepisy/unijne/fetched/",
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

    # Filter out .meta.txt files
    files = [f for f in files if not f.name.endswith(".meta.txt")]

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
