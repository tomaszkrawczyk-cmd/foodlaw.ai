"""
Unit tests for validate_content.py validation logic.
"""

import json
import sys
from pathlib import Path

# Add scripts directory to path so we can import the modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from validate_content import validate_file


class TestValidateFileJsonWithResults:
    """Tests for JSON files containing a 'results' key (search-result files)."""

    def test_small_json_with_empty_results_passes(self, tmp_path):
        """A small JSON file with {"keyword": "test", "results": []} passes validation."""
        data = {"keyword": "test", "results": []}
        filepath = tmp_path / "food_safety.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is True

    def test_small_json_with_populated_results_passes(self, tmp_path):
        """A JSON file with {"keyword": "x", "results": [{"item": 1}]} passes even if small."""
        data = {"keyword": "x", "results": [{"item": 1}]}
        filepath = tmp_path / "GIS.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is True

    def test_large_json_with_results_passes(self, tmp_path):
        """A normal-size JSON file with 'results' key passes."""
        data = {"keyword": "bezpieczenstwo zywnosci", "results": [{"id": i} for i in range(50)]}
        filepath = tmp_path / "results.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size >= 100
        assert validate_file(filepath) is True


class TestValidateFileJsonWithoutResults:
    """Tests for JSON files that do NOT contain a 'results' key."""

    def test_small_json_without_results_key_fails(self, tmp_path):
        """A small JSON file without a 'results' key fails validation (under 100 bytes)."""
        data = {"status": "ok"}
        filepath = tmp_path / "summary.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_small_json_with_results_null_fails(self, tmp_path):
        """A small JSON file with {"results": null} fails validation (null is not a list)."""
        data = {"keyword": "test", "results": None}
        filepath = tmp_path / "corrupted.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_small_json_with_results_string_fails(self, tmp_path):
        """A small JSON file with {"results": "error"} fails validation (string is not a list)."""
        data = {"keyword": "test", "results": "error"}
        filepath = tmp_path / "broken.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_normal_size_json_without_results_key_passes(self, tmp_path):
        """A normal-size JSON file without 'results' key passes (over 100 bytes)."""
        data = {"keyword_" + str(i): ["result"] * 5 for i in range(20)}
        filepath = tmp_path / "curia_wyniki.json"
        filepath.write_text(json.dumps(data), encoding="utf-8")
        assert filepath.stat().st_size >= 100
        assert validate_file(filepath) is True


class TestValidateFileNonJson:
    """Tests for non-JSON files (.md, .html) - size check still applies."""

    def test_small_md_file_fails(self, tmp_path):
        """A small .md file still fails validation."""
        filepath = tmp_path / "doc.md"
        filepath.write_text("# Short", encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_small_html_file_fails(self, tmp_path):
        """A small .html file still fails validation."""
        filepath = tmp_path / "page.html"
        filepath.write_text("<html><body>Hi</body></html>", encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_large_md_file_passes(self, tmp_path):
        """A .md file over 100 bytes passes validation."""
        filepath = tmp_path / "doc.md"
        filepath.write_text("# Title\n\n" + "Some content. " * 20, encoding="utf-8")
        assert filepath.stat().st_size >= 100
        assert validate_file(filepath) is True

    def test_large_html_file_passes(self, tmp_path):
        """A .html file over 100 bytes passes validation."""
        filepath = tmp_path / "page.html"
        content = "<html><body>" + "<p>Paragraph content here.</p>" * 10 + "</body></html>"
        filepath.write_text(content, encoding="utf-8")
        assert filepath.stat().st_size >= 100
        assert validate_file(filepath) is True


class TestValidateFileInvalidJson:
    """Tests for invalid JSON files."""

    def test_invalid_json_small_file_fails(self, tmp_path):
        """An invalid JSON file (not parseable) still fails the size check."""
        filepath = tmp_path / "broken.json"
        filepath.write_text("{not valid json", encoding="utf-8")
        assert filepath.stat().st_size < 100
        assert validate_file(filepath) is False

    def test_invalid_json_large_file_passes(self, tmp_path):
        """An invalid JSON file over 100 bytes passes (size check passes, UTF-8 check passes)."""
        filepath = tmp_path / "broken_large.json"
        filepath.write_text("{not valid json " + "x" * 100, encoding="utf-8")
        assert filepath.stat().st_size >= 100
        assert validate_file(filepath) is True
