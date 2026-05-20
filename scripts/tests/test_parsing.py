"""
Unit tests for parsing functions in fetch_cbosa.py and fetch_curia.py.
"""

import sys
from pathlib import Path

# Add scripts directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup

from fetch_cbosa import parse_result_item
from fetch_curia import parse_curia_result


# --- Tests for parse_result_item (CBOSA) ---


class TestParseResultItemCBOSA:
    """Tests for fetch_cbosa.parse_result_item()."""

    def _make_element(self, html: str) -> "BeautifulSoup":
        """Create a BeautifulSoup element from HTML string."""
        soup = BeautifulSoup(html, "lxml")
        # Return the first meaningful element (skip html/body wrappers)
        body = soup.find("body")
        if body:
            first_child = body.find()
            if first_child:
                return first_child
        return soup

    def test_valid_signature_pattern(self):
        """Test parsing HTML with a valid NSA signature pattern."""
        html = (
            '<tr><td><a href="/cbo/doc/123">II GSK 1234/20</a>'
            " - wyrok z dnia 2020-05-15</td></tr>"
        )
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is not None
        assert result["signature"] == "II GSK 1234/20"

    def test_date_yyyy_mm_dd(self):
        """Test parsing HTML containing a date in YYYY-MM-DD format."""
        html = (
            '<tr><td>Wyrok z dnia 2021-03-22, sygnatura '
            'II GSK 893/21</td></tr>'
        )
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is not None
        assert result["date"] == "2021-03-22"

    def test_date_dd_mm_yyyy(self):
        """Test parsing HTML containing a date in DD.MM.YYYY format."""
        html = (
            '<tr><td>Orzeczenie 15.06.2019, sygn. IV SA/Wa 200/19'
            "</td></tr>"
        )
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is not None
        assert result["date"] == "15.06.2019"

    def test_link_extraction(self):
        """Test parsing HTML with a link to the judgment."""
        html = (
            '<tr><td><a href="/cbo/find?docId=ABC123">'
            "II GSK 2384/17 - wyrok 2019-03-14</a></td></tr>"
        )
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is not None
        assert "url" in result
        assert "orzeczenia.nsa.gov.pl" in result["url"]
        assert "/cbo/find?docId=ABC123" in result["url"]

    def test_empty_text_returns_none(self):
        """Test that empty or very short text returns None."""
        html = "<tr><td></td></tr>"
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is None

    def test_short_text_returns_none(self):
        """Test that text shorter than 10 chars returns None."""
        html = "<tr><td>abc</td></tr>"
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is None

    def test_no_signature_no_date_no_link_returns_none(self):
        """Test that HTML with no recognizable patterns returns None."""
        html = (
            "<tr><td>Jakis zwykly tekst bez sygnatury i bez daty, "
            "wystarczajaco dlugi zeby przejsc filtr dlugosci</td></tr>"
        )
        element = self._make_element(html)
        result = parse_result_item(element)

        assert result is None


# --- Tests for parse_curia_result (CURIA) ---


class TestParseCuriaResult:
    """Tests for fetch_curia.parse_curia_result()."""

    def _make_row(self, html: str) -> "BeautifulSoup":
        """Create a BeautifulSoup table row element from HTML string."""
        # Wrap in table for proper parsing context
        wrapped = f"<table>{html}</table>"
        soup = BeautifulSoup(wrapped, "lxml")
        row = soup.find("tr")
        if row:
            return row
        # Fallback
        body = soup.find("body")
        if body:
            return body.find()
        return soup

    def test_cjeu_case_number(self):
        """Test parsing row with a CJEU case number."""
        html = (
            '<tr><td><a href="/juris/document.jsf?docid=123">'
            "Judgment C-544/10 - health claims wine</a></td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is not None
        assert result["case_number"] == "C-544/10"

    def test_ecli_identifier(self):
        """Test parsing row with an ECLI identifier."""
        html = (
            "<tr><td>Case C-609/12 - ECLI:EU:C:2014:793 - "
            "Green Swan health claims, 23/01/2014</td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is not None
        assert result["ecli"] == "ECLI:EU:C:2014:793"

    def test_date_dd_mm_yyyy(self):
        """Test parsing row with a date in DD/MM/YYYY format."""
        html = (
            "<tr><td>Judgment of 06/09/2012 - Case C-544/10 "
            "concerning health claims</td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is not None
        assert result["date"] == "06/09/2012"

    def test_date_iso_format(self):
        """Test parsing row with a date in YYYY-MM-DD format."""
        html = (
            "<tr><td>Case T-456/21 delivered on 2021-11-15 "
            "regarding novel food</td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is not None
        assert result["date"] == "2021-11-15"

    def test_empty_text_returns_none(self):
        """Test that empty row returns None."""
        html = "<tr><td></td></tr>"
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is None

    def test_short_text_returns_none(self):
        """Test that row with very short text returns None."""
        html = "<tr><td>xyz</td></tr>"
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is None

    def test_no_case_identifiers_returns_none(self):
        """Test that row with no case number/ECLI/date returns None."""
        html = (
            "<tr><td>Some general text about EU law and food regulation "
            "without any case identifiers or dates in proper format</td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is None

    def test_case_with_url(self):
        """Test that URL is extracted from links in the row."""
        html = (
            '<tr><td><a href="/juris/doc.jsf?id=999">'
            "C-140/07 - food supplement boundary</a></td></tr>"
        )
        row = self._make_row(html)
        result = parse_curia_result(row)

        assert result is not None
        assert "url" in result
        assert "curia.europa.eu" in result["url"]
