"""
Unit tests for EUR-Lex Web Service integration in fetch_eurlex.py.
"""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from xml.etree import ElementTree as ET

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_eurlex import (
    build_soap_request,
    parse_soap_response,
    generate_front_matter,
    generate_judgment_filename,
    load_credentials,
    execute_soap_query,
    fetch_html_content,
    convert_html_to_markdown,
    _extract_document_info,
    _parse_response_text,
)


# --- Tests for load_credentials ---


class TestLoadCredentials:
    """Tests for load_credentials()."""

    @patch.dict("os.environ", {"EURLEX_USERNAME": "user1", "EURLEX_PASSWORD": "pass1"})
    @patch("fetch_eurlex.load_dotenv")
    def test_returns_tuple_when_both_set(self, mock_dotenv):
        """When both env vars are set, returns (username, password) tuple."""
        result = load_credentials()
        assert result == ("user1", "pass1")

    @patch.dict("os.environ", {"EURLEX_PASSWORD": "pass1"}, clear=True)
    @patch("fetch_eurlex.load_dotenv")
    def test_exits_when_username_missing(self, mock_dotenv):
        """When EURLEX_USERNAME is missing, calls sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            load_credentials()
        assert exc_info.value.code == 1

    @patch.dict("os.environ", {"EURLEX_USERNAME": "user1"}, clear=True)
    @patch("fetch_eurlex.load_dotenv")
    def test_exits_when_password_missing(self, mock_dotenv):
        """When EURLEX_PASSWORD is missing, calls sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            load_credentials()
        assert exc_info.value.code == 1

    @patch.dict("os.environ", {}, clear=True)
    @patch("fetch_eurlex.load_dotenv")
    def test_exits_when_both_missing(self, mock_dotenv):
        """When both env vars are missing, calls sys.exit(1)."""
        with pytest.raises(SystemExit) as exc_info:
            load_credentials()
        assert exc_info.value.code == 1


# --- Tests for build_soap_request ---


class TestBuildSoapRequest:
    """Tests for build_soap_request()."""

    def test_dn_search_type(self):
        """With search_type='DN', returns SELECT DN WHERE DN = {celex}."""
        result = build_soap_request("32002R0178", "DN")
        assert result == "SELECT DN WHERE DN = 32002R0178"

    def test_ct_search_type(self):
        """With search_type='CT', returns SELECT CT WHERE CT = 6 AND DD = {celex}."""
        result = build_soap_request("03.65", "CT")
        assert result == "SELECT CT WHERE CT = 6 AND DD = 03.65"

    def test_default_search_type_is_dn(self):
        """Default search_type returns DN format."""
        result = build_soap_request("62012CJ0299")
        assert result == "SELECT DN WHERE DN = 62012CJ0299"

    def test_unknown_search_type_falls_back_to_dn(self):
        """Unknown search_type falls back to DN format."""
        result = build_soap_request("32011R1169", "UNKNOWN")
        assert result == "SELECT DN WHERE DN = 32011R1169"


# --- Tests for parse_soap_response ---


class TestParseSoapResponse:
    """Tests for parse_soap_response()."""

    def test_valid_xml_with_documents(self):
        """Valid XML with DOCUMENT elements returns list of document dicts."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <SEARCH_RESULTS>
            <DOCUMENT>
                <ID_CELEX>32002R0178</ID_CELEX>
                <EXPRESSION_TITLE>Regulation 178/2002</EXPRESSION_TITLE>
                <WORK_DATE_DOCUMENT>2002-01-28</WORK_DATE_DOCUMENT>
                <CONTENT_URL>https://eur-lex.europa.eu/document/123</CONTENT_URL>
            </DOCUMENT>
        </SEARCH_RESULTS>
        """
        result = parse_soap_response(xml)
        assert len(result) >= 1
        doc = result[0]
        assert doc["celex"] == "32002R0178"
        assert doc["title"] == "Regulation 178/2002"
        assert doc["date"] == "2002-01-28"
        assert doc["content_url"] == "https://eur-lex.europa.eu/document/123"

    def test_empty_string_returns_empty_list(self):
        """Empty string returns empty list."""
        result = parse_soap_response("")
        assert result == []

    def test_none_returns_empty_list(self):
        """None-like empty input returns empty list."""
        result = parse_soap_response("   ")
        assert result == []

    def test_invalid_xml_falls_back_to_text_parsing(self):
        """Invalid XML (not parseable) falls back to text parsing."""
        text = "Some text with CELEX 32002R0178 and https://eur-lex.europa.eu/doc"
        result = parse_soap_response(text)
        assert len(result) >= 1
        assert result[0]["celex"] == "32002R0178"

    def test_multiple_documents(self):
        """Multiple DOCUMENT elements are all extracted."""
        xml = """<?xml version="1.0" encoding="UTF-8"?>
        <SEARCH_RESULTS>
            <DOCUMENT>
                <ID_CELEX>32002R0178</ID_CELEX>
                <EXPRESSION_TITLE>Regulation 178/2002</EXPRESSION_TITLE>
            </DOCUMENT>
            <DOCUMENT>
                <ID_CELEX>32011R1169</ID_CELEX>
                <EXPRESSION_TITLE>Regulation 1169/2011</EXPRESSION_TITLE>
            </DOCUMENT>
        </SEARCH_RESULTS>
        """
        result = parse_soap_response(xml)
        assert len(result) == 2


# --- Tests for _extract_document_info ---


class TestExtractDocumentInfo:
    """Tests for _extract_document_info()."""

    def test_extracts_all_fields(self):
        """Element with celex, title, date, content_url extracts all fields."""
        xml = """<DOCUMENT>
            <ID_CELEX>32002R0178</ID_CELEX>
            <EXPRESSION_TITLE>Test Title</EXPRESSION_TITLE>
            <WORK_DATE_DOCUMENT>2002-01-28</WORK_DATE_DOCUMENT>
            <CONTENT_URL>https://example.com/doc</CONTENT_URL>
        </DOCUMENT>"""
        elem = ET.fromstring(xml)
        result = _extract_document_info(elem)
        assert result is not None
        assert result["celex"] == "32002R0178"
        assert result["title"] == "Test Title"
        assert result["date"] == "2002-01-28"
        assert result["content_url"] == "https://example.com/doc"

    def test_returns_none_for_empty_element(self):
        """Element with no recognized tags returns None."""
        xml = "<DOCUMENT><UNKNOWN_TAG>value</UNKNOWN_TAG></DOCUMENT>"
        elem = ET.fromstring(xml)
        result = _extract_document_info(elem)
        assert result is None

    def test_alternative_tag_names(self):
        """Element with alternative tag names (CELEX, TITLE, DATE) works."""
        xml = """<result>
            <CELEX>62012CJ0299</CELEX>
            <TITLE>Judgment C-299/12</TITLE>
            <DATE>2013-10-03</DATE>
            <DRECONTENT>https://example.com/content</DRECONTENT>
        </result>"""
        elem = ET.fromstring(xml)
        result = _extract_document_info(elem)
        assert result is not None
        assert result["celex"] == "62012CJ0299"
        assert result["title"] == "Judgment C-299/12"
        assert result["date"] == "2013-10-03"
        assert result["content_url"] == "https://example.com/content"


# --- Tests for _parse_response_text ---


class TestParseResponseText:
    """Tests for _parse_response_text()."""

    def test_extracts_celex_from_text(self):
        """Text with CELEX patterns extracts documents."""
        text = "Found document 32002R0178 in the response"
        result = _parse_response_text(text)
        assert len(result) >= 1
        assert result[0]["celex"] == "32002R0178"

    def test_extracts_judgment_celex(self):
        """Text with judgment CELEX pattern is extracted."""
        text = "Judgment 62012CJ0299 was delivered"
        result = _parse_response_text(text)
        assert len(result) >= 1
        assert result[0]["celex"] == "62012CJ0299"

    def test_extracts_url_matching_celex(self):
        """URL containing celex number is associated with the document."""
        text = "Document 32002R0178 at https://eur-lex.europa.eu/doc/32002R0178"
        result = _parse_response_text(text)
        assert len(result) >= 1
        assert "content_url" in result[0]
        assert "32002R0178" in result[0]["content_url"]


# --- Tests for generate_front_matter ---


class TestGenerateFrontMatter:
    """Tests for generate_front_matter()."""

    def test_all_fields_provided(self):
        """All fields provided generates correct YAML front-matter."""
        result = generate_front_matter(
            celex="32002R0178",
            title="Regulation 178/2002",
            date="2002-01-28",
            source_url="https://eur-lex.europa.eu/doc/32002R0178",
        )
        assert result.startswith("---\n")
        assert "---" in result.strip().split("\n")[-1]
        assert 'celex: "32002R0178"' in result
        assert 'title: "Regulation 178/2002"' in result
        assert 'date: "2002-01-28"' in result
        assert 'source_url: "https://eur-lex.europa.eu/doc/32002R0178"' in result

    def test_only_celex_provided(self):
        """Only celex provided (rest empty) generates minimal front-matter."""
        result = generate_front_matter(celex="32002R0178")
        assert 'celex: "32002R0178"' in result
        assert "title:" not in result
        assert "date:" not in result
        assert "source_url:" not in result

    def test_title_with_quotes_escaped(self):
        """Title with quotes is properly escaped."""
        result = generate_front_matter(
            celex="32002R0178",
            title='Regulation "178/2002" on food safety',
        )
        assert 'title: "Regulation \\"178/2002\\" on food safety"' in result


# --- Tests for generate_judgment_filename ---


class TestGenerateJudgmentFilename:
    """Tests for generate_judgment_filename()."""

    def test_celex_62012cj0299_with_date(self):
        """CELEX '62012CJ0299' with date '2013-10-03' returns correct filename."""
        result = generate_judgment_filename("62012CJ0299", {"date": "2013-10-03"})
        assert result == "2013-10-03-C-299-12.md"

    def test_celex_62010cj0544_with_date(self):
        """CELEX '62010CJ0544' with date '2012-09-06' returns correct filename."""
        result = generate_judgment_filename("62010CJ0544", {"date": "2012-09-06"})
        assert result == "2012-09-06-C-544-10.md"

    def test_missing_date_returns_unknown_date(self):
        """Missing date returns 'unknown-date-C-NNN-RR.md' pattern."""
        result = generate_judgment_filename("62012CJ0299", {})
        assert result.startswith("unknown-date-")
        assert "C-299-12" in result
        assert result.endswith(".md")

    def test_non_matching_celex_uses_celex_as_ref(self):
        """Non-matching CELEX pattern uses CELEX as case_ref."""
        result = generate_judgment_filename("INVALID_CELEX", {"date": "2020-01-01"})
        assert "INVALID_CELEX" in result
        assert result == "2020-01-01-INVALID_CELEX.md"


# --- Tests for execute_soap_query ---


class TestExecuteSoapQuery:
    """Tests for execute_soap_query()."""

    def test_successful_query_returns_response(self):
        """Mock client.service.doQuery returning XML string returns that string."""
        mock_client = MagicMock()
        mock_client.service.doQuery.return_value = "<results><doc/></results>"

        result = execute_soap_query(mock_client, "SELECT DN WHERE DN = 32002R0178")
        assert result == "<results><doc/></results>"
        mock_client.service.doQuery.assert_called_once_with(
            expertQuery="SELECT DN WHERE DN = 32002R0178",
            page=1,
            pageSize=10,
            searchLanguage="en",
        )

    def test_rate_limit_fault_returns_empty(self):
        """ZeepFault with WS_MAXIMUM_NB_OF_WS_CALLS returns '' and logs error."""
        from zeep.exceptions import Fault as ZeepFault

        mock_client = MagicMock()
        mock_client.service.doQuery.side_effect = ZeepFault(
            "WS_MAXIMUM_NB_OF_WS_CALLS exceeded"
        )

        result = execute_soap_query(mock_client, "SELECT DN WHERE DN = 32002R0178")
        assert result == ""

    def test_other_fault_returns_empty(self):
        """ZeepFault with other message returns '' and logs error."""
        from zeep.exceptions import Fault as ZeepFault

        mock_client = MagicMock()
        mock_client.service.doQuery.side_effect = ZeepFault(
            "WS_QUERY_SYNTAX_ERROR: invalid query"
        )

        result = execute_soap_query(mock_client, "SELECT BAD QUERY")
        assert result == ""

    def test_generic_exception_returns_empty(self):
        """Generic Exception from doQuery returns ''."""
        mock_client = MagicMock()
        mock_client.service.doQuery.side_effect = ConnectionError("network error")

        result = execute_soap_query(mock_client, "SELECT DN WHERE DN = 32002R0178")
        assert result == ""

    def test_none_response_returns_empty(self):
        """doQuery returning None returns empty string."""
        mock_client = MagicMock()
        mock_client.service.doQuery.return_value = None

        result = execute_soap_query(mock_client, "SELECT DN WHERE DN = 32002R0178")
        assert result == ""


# --- Tests for fetch_html_content ---


class TestFetchHtmlContent:
    """Tests for fetch_html_content()."""

    @patch("fetch_eurlex.requests.get")
    def test_successful_response(self, mock_get):
        """Mock requests.get returning 200 with HTML returns HTML text."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = fetch_html_content("https://example.com/doc")
        assert result == "<html><body>Test content</body></html>"

    @patch("fetch_eurlex.requests.get")
    def test_timeout_returns_empty(self, mock_get):
        """Mock requests.get raising Timeout returns ''."""
        import requests

        mock_get.side_effect = requests.exceptions.Timeout("connection timed out")

        result = fetch_html_content("https://example.com/doc")
        assert result == ""

    @patch("fetch_eurlex.requests.get")
    def test_http_error_403_returns_empty(self, mock_get):
        """Mock requests.get returning 403 returns ''."""
        import requests

        mock_response = MagicMock()
        mock_response.status_code = 403
        http_error = requests.exceptions.HTTPError(response=mock_response)
        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        result = fetch_html_content("https://example.com/doc")
        assert result == ""

    @patch("fetch_eurlex.requests.get")
    def test_connection_error_returns_empty(self, mock_get):
        """Mock requests.get raising ConnectionError returns ''."""
        import requests

        mock_get.side_effect = requests.exceptions.ConnectionError("refused")

        result = fetch_html_content("https://example.com/doc")
        assert result == ""


# --- Tests for convert_html_to_markdown ---


class TestConvertHtmlToMarkdown:
    """Tests for convert_html_to_markdown()."""

    def test_basic_html_returns_nonempty_markdown(self):
        """Basic HTML is converted to non-empty markdown."""
        html = "<html><body><h1>Title</h1><p>Paragraph text.</p></body></html>"
        result = convert_html_to_markdown(html)
        assert len(result) > 0
        # The result should contain something from the heading/paragraph
        assert "Title" in result or "Paragraph" in result

    @patch("fetch_eurlex.process_eurlex_html")
    def test_delegates_to_process_eurlex_html_when_available(self, mock_process):
        """With process_eurlex_html available, delegates to it."""
        mock_process.return_value = "# Converted\n\nContent"
        html = "<html><body><p>test</p></body></html>"
        result = convert_html_to_markdown(html)
        mock_process.assert_called_once_with(html)
        assert result == "# Converted\n\nContent"
