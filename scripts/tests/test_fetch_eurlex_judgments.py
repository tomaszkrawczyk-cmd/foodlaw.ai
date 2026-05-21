"""Unit tests for fetch_eurlex_judgments.py"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_eurlex_judgments import (
    build_expert_query_by_celex,
    build_expert_query_food_legislation,
    convert_html_to_markdown,
    extract_date_from_html,
    fetch_html_with_retry,
    fetch_judgment,
    generate_front_matter,
    generate_judgment_filename,
    get_credentials,
    parse_celex_to_case_info,
    save_judgment,
)


class TestGetCredentials:
    """Tests for credential loading."""

    def test_credentials_both_present(self, monkeypatch):
        monkeypatch.setenv("EURLEX_USERNAME", "testuser")
        monkeypatch.setenv("EURLEX_PASSWORD", "testpass")
        username, password = get_credentials()
        assert username == "testuser"
        assert password == "testpass"

    def test_credentials_missing(self, monkeypatch):
        monkeypatch.delenv("EURLEX_USERNAME", raising=False)
        monkeypatch.delenv("EURLEX_PASSWORD", raising=False)
        username, password = get_credentials()
        assert username is None
        assert password is None

    def test_credentials_partial_username_only(self, monkeypatch):
        monkeypatch.setenv("EURLEX_USERNAME", "testuser")
        monkeypatch.delenv("EURLEX_PASSWORD", raising=False)
        username, password = get_credentials()
        assert username == "testuser"
        assert password is None

    def test_credentials_partial_password_only(self, monkeypatch):
        monkeypatch.delenv("EURLEX_USERNAME", raising=False)
        monkeypatch.setenv("EURLEX_PASSWORD", "testpass")
        username, password = get_credentials()
        assert username is None
        assert password == "testpass"


class TestBuildExpertQuery:
    """Tests for SOAP request query building."""

    def test_query_by_celex_dn(self):
        query = build_expert_query_by_celex("62012CJ0299")
        assert query == "SELECT DN WHERE DN = 62012CJ0299"

    def test_query_by_celex_different_number(self):
        query = build_expert_query_by_celex("62018CJ0663")
        assert query == "SELECT DN WHERE DN = 62018CJ0663"

    def test_query_food_legislation_ct(self):
        query = build_expert_query_food_legislation()
        assert query == "SELECT CT WHERE CT = 6 AND DD = 03.65"


class TestParseCelexToCaseInfo:
    """Tests for CELEX number parsing."""

    def test_parse_standard_celex(self):
        info = parse_celex_to_case_info("62012CJ0299")
        assert info == {"year": "2012", "case_number": "299", "short_year": "12"}

    def test_parse_celex_with_leading_zeros(self):
        info = parse_celex_to_case_info("62001CJ0236")
        assert info == {"year": "2001", "case_number": "236", "short_year": "01"}

    def test_parse_celex_invalid(self):
        info = parse_celex_to_case_info("INVALID")
        assert info is None

    def test_parse_celex_wrong_prefix(self):
        info = parse_celex_to_case_info("32012R0001")
        assert info is None


class TestGenerateJudgmentFilename:
    """Tests for judgment filename generation."""

    def test_filename_with_date(self):
        filename = generate_judgment_filename("62012CJ0299", date="2013-10-03")
        assert filename == "2013-10-03-C-299-12.md"

    def test_filename_without_date(self):
        filename = generate_judgment_filename("62012CJ0299", date=None)
        assert filename == "unknown-date-C-299-12.md"

    def test_filename_different_case(self):
        filename = generate_judgment_filename("62018CJ0663", date="2020-11-19")
        assert filename == "2020-11-19-C-663-18.md"

    def test_filename_invalid_celex(self):
        filename = generate_judgment_filename("INVALID", date="2020-01-01")
        assert filename == "unknown-INVALID.md"


class TestGenerateFrontMatter:
    """Tests for YAML front-matter generation."""

    def test_front_matter_full(self):
        fm = generate_front_matter(
            celex="62012CJ0299",
            title="Test Judgment",
            date="2013-10-03",
            language="PL",
        )
        assert "---" in fm
        assert 'celex: "62012CJ0299"' in fm
        assert 'title: "Test Judgment"' in fm
        assert 'date: "2013-10-03"' in fm
        assert "CELEX:62012CJ0299" in fm

    def test_front_matter_no_title(self):
        fm = generate_front_matter(celex="62012CJ0299", date="2013-10-03")
        assert "title" not in fm
        assert 'celex: "62012CJ0299"' in fm

    def test_front_matter_no_date(self):
        fm = generate_front_matter(celex="62012CJ0299", title="Test")
        assert "date" not in fm

    def test_front_matter_title_with_quotes(self):
        fm = generate_front_matter(celex="62012CJ0299", title='A "quoted" title')
        assert 'title: "A \\"quoted\\" title"' in fm


class TestFetchHtmlWithRetry:
    """Tests for HTML fetching with retry logic."""

    @patch("fetch_eurlex_judgments.requests.get")
    def test_fetch_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = fetch_html_with_retry("http://example.com", max_retries=3, delay=0.01)
        assert result == "<html>test</html>"

    @patch("fetch_eurlex_judgments.requests.get")
    def test_fetch_timeout_retries(self, mock_get):
        import requests as req

        mock_get.side_effect = req.exceptions.Timeout("timeout")

        with pytest.raises(req.exceptions.Timeout):
            fetch_html_with_retry("http://example.com", max_retries=2, delay=0.01)
        assert mock_get.call_count == 2

    @patch("fetch_eurlex_judgments.requests.get")
    def test_fetch_403_no_retry(self, mock_get):
        import requests as req

        mock_response = MagicMock()
        mock_response.status_code = 403
        error = req.exceptions.HTTPError(response=mock_response)
        mock_get.side_effect = error

        with pytest.raises(req.exceptions.HTTPError):
            fetch_html_with_retry("http://example.com", max_retries=3, delay=0.01)
        # 403 should not retry
        assert mock_get.call_count == 1

    @patch("fetch_eurlex_judgments.requests.get")
    def test_fetch_connection_error_retries(self, mock_get):
        import requests as req

        mock_get.side_effect = req.exceptions.ConnectionError("conn error")

        with pytest.raises(req.exceptions.ConnectionError):
            fetch_html_with_retry("http://example.com", max_retries=3, delay=0.01)
        assert mock_get.call_count == 3


class TestSoapFaultHandling:
    """Tests for SOAP fault handling."""

    @patch("fetch_eurlex_judgments.fetch_html_with_retry")
    def test_soap_fault_falls_back_to_direct_download(self, mock_fetch_html):
        mock_fetch_html.return_value = "<html><body><p>Judgment text</p></body></html>"

        # Create a mock SOAP client that raises on doQuery
        mock_client = MagicMock()
        mock_client.service.doQuery.side_effect = Exception("SOAP rate limit exceeded")

        result = fetch_judgment("62012CJ0299", language="PL", soap_client=mock_client, delay=0.01)

        assert result is not None
        assert result["markdown"] is not None
        assert result["soap_used"] is False

    @patch("fetch_eurlex_judgments.fetch_html_with_retry")
    def test_soap_syntax_error_falls_back(self, mock_fetch_html):
        mock_fetch_html.return_value = "<html><body><p>Content</p></body></html>"

        mock_client = MagicMock()
        mock_client.service.doQuery.side_effect = Exception("Expert query syntax error")

        result = fetch_judgment("62012CJ0299", language="PL", soap_client=mock_client, delay=0.01)

        assert result is not None
        assert result["soap_used"] is False


class TestFallbackLogic:
    """Tests for fallback logic when SOAP fails."""

    @patch("fetch_eurlex_judgments.fetch_html_with_retry")
    def test_no_soap_client_direct_download(self, mock_fetch_html):
        mock_fetch_html.return_value = "<html><body><h1>Judgment</h1><p>Text</p></body></html>"

        result = fetch_judgment("62012CJ0299", language="PL", soap_client=None, delay=0.01)

        assert result is not None
        assert result["markdown"] is not None
        assert result["soap_used"] is False

    @patch("fetch_eurlex_judgments.fetch_html_with_retry")
    def test_html_download_fails_returns_none(self, mock_fetch_html):
        import requests as req

        mock_fetch_html.side_effect = req.exceptions.ConnectionError("failed")

        result = fetch_judgment("62012CJ0299", language="PL", soap_client=None, delay=0.01)

        assert result is None

    @patch("fetch_eurlex_judgments.fetch_html_with_retry")
    def test_html_returns_none_returns_none(self, mock_fetch_html):
        mock_fetch_html.return_value = None

        result = fetch_judgment("62012CJ0299", language="PL", soap_client=None, delay=0.01)

        assert result is None


class TestConvertHtmlToMarkdown:
    """Tests for HTML to Markdown conversion."""

    def test_basic_conversion(self):
        html = "<h1>Title</h1><p>Paragraph text.</p>"
        md = convert_html_to_markdown(html)
        assert "Title" in md
        assert "Paragraph text." in md

    def test_links_preserved(self):
        html = '<p><a href="http://example.com">Link</a></p>'
        md = convert_html_to_markdown(html)
        assert "http://example.com" in md


class TestExtractDateFromHtml:
    """Tests for date extraction from HTML."""

    def test_extract_english_date(self):
        html = "<p>Delivered on 3 October 2013 in open court.</p>"
        date = extract_date_from_html(html)
        assert date == "2013-10-03"

    def test_extract_iso_date(self):
        html = '<meta name="date" content="2013-10-03">'
        date = extract_date_from_html(html)
        assert date == "2013-10-03"

    def test_no_date_found(self):
        html = "<p>No date information here.</p>"
        date = extract_date_from_html(html)
        assert date is None


class TestSaveJudgment:
    """Tests for saving judgments to disk."""

    def test_save_creates_file(self, tmp_path):
        judgment_data = {
            "markdown": "# Test Judgment\n\nContent here.",
            "date": "2013-10-03",
            "title": "Test",
            "soap_used": False,
        }

        filepath = save_judgment("62012CJ0299", judgment_data, str(tmp_path), language="PL")

        assert filepath.exists()
        content = filepath.read_text()
        assert "---" in content
        assert "62012CJ0299" in content
        assert "# Test Judgment" in content

    def test_save_creates_output_dir(self, tmp_path):
        output_dir = tmp_path / "subdir" / "nested"
        judgment_data = {
            "markdown": "Content",
            "date": "2020-01-01",
            "title": "Title",
            "soap_used": False,
        }

        filepath = save_judgment("62018CJ0663", judgment_data, str(output_dir))

        assert filepath.exists()
        assert output_dir.exists()
