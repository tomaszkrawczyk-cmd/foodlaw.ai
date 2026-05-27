"""Unit tests for new data source scrapers: RASFF, health claims, novel food."""

import argparse
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fetch_rasff import (
    build_search_payload,
    fetch_notifications_page,
    generate_markdown_summary,
    parse_notification,
    parse_notifications_response,
    save_results,
)
from fetch_health_claims import (
    build_search_payload as build_claims_payload,
    fetch_claims_page,
    parse_claim,
    parse_claims_response,
    save_results as save_claims_results,
)
from fetch_novel_food import (
    build_search_payload as build_novel_food_payload,
    fetch_novel_food_page,
    parse_novel_food_entry,
    parse_novel_food_response,
    save_results as save_novel_food_results,
)


# ============================================================
# RASFF Tests
# ============================================================


class TestRasffSearchPayload:
    """Tests for RASFF search payload building."""

    def test_default_payload(self):
        payload = build_search_payload()
        assert payload["productCategory"] == "food"
        assert payload["page"] == 1
        assert payload["pageSize"] == 50
        assert payload["searchTerms"] == ""
        assert payload["notificationTypes"] == []

    def test_custom_category(self):
        payload = build_search_payload(category="feed", page=3, page_size=25)
        assert payload["productCategory"] == "feed"
        assert payload["page"] == 3
        assert payload["pageSize"] == 25


class TestRasffParseNotification:
    """Tests for RASFF notification parsing."""

    def test_parse_full_notification(self):
        raw = {
            "reference": "2024.1234",
            "date": "2024-01-15",
            "lastUpdate": "2024-01-16",
            "notificationType": "alert",
            "subject": "Salmonella in chicken",
            "productCategory": "poultry meat",
            "hazard": "Salmonella",
            "originCountry": "Poland",
            "notificationCountry": "Germany",
            "distributionCountries": ["France", "Italy"],
            "status": "open",
        }
        result = parse_notification(raw)
        assert result is not None
        assert result["reference"] == "2024.1234"
        assert result["date"] == "2024-01-15"
        assert result["notification_type"] == "alert"
        assert result["subject"] == "Salmonella in chicken"
        assert result["hazard"] == "Salmonella"
        assert result["origin_country"] == "Poland"
        assert result["distribution_countries"] == ["France", "Italy"]

    def test_parse_minimal_notification(self):
        raw = {"reference": "2024.5678"}
        result = parse_notification(raw)
        assert result is not None
        assert result["reference"] == "2024.5678"
        assert result["date"] == ""
        assert result["subject"] == ""

    def test_parse_invalid_notification(self):
        result = parse_notification("not a dict")
        assert result is None

    def test_parse_none_notification(self):
        result = parse_notification(None)
        assert result is None


class TestRasffParseResponse:
    """Tests for RASFF full response parsing."""

    def test_parse_response_with_content(self):
        data = {
            "totalElements": 100,
            "content": [
                {"reference": "2024.001", "subject": "Test 1"},
                {"reference": "2024.002", "subject": "Test 2"},
            ],
        }
        notifications, total = parse_notifications_response(data)
        assert total == 100
        assert len(notifications) == 2
        assert notifications[0]["reference"] == "2024.001"

    def test_parse_response_with_notifications_key(self):
        data = {
            "totalRecords": 50,
            "notifications": [
                {"reference": "2024.010", "subject": "Alt format"},
            ],
        }
        notifications, total = parse_notifications_response(data)
        assert total == 50
        assert len(notifications) == 1

    def test_parse_empty_response(self):
        data = {"totalElements": 0, "content": []}
        notifications, total = parse_notifications_response(data)
        assert total == 0
        assert notifications == []

    def test_parse_invalid_response(self):
        notifications, total = parse_notifications_response("invalid")
        assert total == 0
        assert notifications == []

    def test_parse_none_response(self):
        notifications, total = parse_notifications_response(None)
        assert total == 0
        assert notifications == []


class TestRasffFetchPage:
    """Tests for RASFF page fetching with mocked HTTP."""

    @patch("fetch_rasff.create_http_client")
    def test_fetch_page_success(self, mock_create):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalElements": 1,
            "content": [{"reference": "2024.001"}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = fetch_notifications_page(mock_client, category="food", page=1)
        assert result is not None
        assert result["totalElements"] == 1

    @patch("fetch_rasff.create_http_client")
    def test_fetch_page_http_error(self, mock_create):
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Connection timeout")

        result = fetch_notifications_page(mock_client, category="food", page=1)
        assert result is None


class TestRasffMarkdownSummary:
    """Tests for RASFF Markdown summary generation."""

    def test_generate_summary(self):
        notifications = [
            {
                "reference": "2024.001",
                "date": "2024-01-15",
                "notification_type": "alert",
                "subject": "Test subject",
                "hazard": "Salmonella",
                "origin_country": "Poland",
            }
        ]
        md = generate_markdown_summary(notifications)
        assert "# RASFF Notifications Summary" in md
        assert "2024.001" in md
        assert "Test subject" in md
        assert "Salmonella" in md

    def test_generate_empty_summary(self):
        md = generate_markdown_summary([])
        assert "Total notifications: 0" in md


class TestRasffSaveResults:
    """Tests for RASFF result saving."""

    def test_save_json_and_markdown(self, tmp_path):
        notifications = [
            {"reference": "2024.001", "subject": "Test", "date": "2024-01-15",
             "notification_type": "alert", "hazard": "Test", "origin_country": "PL"}
        ]
        save_results(notifications, str(tmp_path))
        json_file = tmp_path / "rasff_notifications.json"
        md_file = tmp_path / "rasff_summary.md"
        assert json_file.exists()
        assert md_file.exists()
        data = json.loads(json_file.read_text())
        assert len(data) == 1

    def test_save_json_only(self, tmp_path):
        notifications = [{"reference": "2024.002", "subject": "Test2"}]
        save_results(notifications, str(tmp_path), save_markdown=False)
        json_file = tmp_path / "rasff_notifications.json"
        md_file = tmp_path / "rasff_summary.md"
        assert json_file.exists()
        assert not md_file.exists()


# ============================================================
# Health Claims Tests
# ============================================================


class TestHealthClaimsPayload:
    """Tests for health claims search payload building."""

    def test_default_payload(self):
        payload = build_claims_payload()
        assert payload["pageNumber"] == 0
        assert payload["pageSize"] == 50
        assert payload["searchTerms"] == ""
        assert "claimStatus" not in payload

    def test_authorized_filter(self):
        payload = build_claims_payload(status="authorized")
        assert payload["claimStatus"] == ["AUTHORISED"]

    def test_non_authorized_filter(self):
        payload = build_claims_payload(status="non-authorized")
        assert payload["claimStatus"] == ["NON_AUTHORISED"]

    def test_all_status(self):
        payload = build_claims_payload(status="all")
        assert "claimStatus" not in payload


class TestHealthClaimsParseClaim:
    """Tests for health claims parsing."""

    def test_parse_full_claim(self):
        raw = {
            "id": "HC-001",
            "claimWording": "Calcium contributes to bone health",
            "conditionsOfUse": "100mg per serving",
            "claimStatus": "AUTHORISED",
            "foodCategory": "dairy",
            "nutrientSubstance": "Calcium",
            "regulationReference": "EU 432/2012",
            "entryType": "Art. 13(1)",
        }
        result = parse_claim(raw)
        assert result is not None
        assert result["id"] == "HC-001"
        assert result["claim_wording"] == "Calcium contributes to bone health"
        assert result["conditions_of_use"] == "100mg per serving"
        assert result["status"] == "AUTHORISED"
        assert result["food_category"] == "dairy"
        assert result["nutrient_substance"] == "Calcium"

    def test_parse_minimal_claim(self):
        raw = {"id": "HC-100"}
        result = parse_claim(raw)
        assert result is not None
        assert result["id"] == "HC-100"
        assert result["claim_wording"] == ""

    def test_parse_alternative_keys(self):
        raw = {
            "id": "HC-200",
            "wording": "Alt wording",
            "status": "PENDING",
            "category": "supplements",
            "substance": "Vitamin D",
        }
        result = parse_claim(raw)
        assert result is not None
        assert result["claim_wording"] == "Alt wording"
        assert result["status"] == "PENDING"
        assert result["food_category"] == "supplements"
        assert result["nutrient_substance"] == "Vitamin D"

    def test_parse_invalid_claim(self):
        result = parse_claim("not a dict")
        assert result is None


class TestHealthClaimsParseResponse:
    """Tests for health claims response parsing."""

    def test_parse_response_with_content(self):
        data = {
            "totalElements": 200,
            "content": [
                {"id": "HC-001", "claimWording": "Claim 1"},
                {"id": "HC-002", "claimWording": "Claim 2"},
            ],
        }
        claims, total = parse_claims_response(data)
        assert total == 200
        assert len(claims) == 2

    def test_parse_empty_response(self):
        data = {"totalElements": 0, "content": []}
        claims, total = parse_claims_response(data)
        assert total == 0
        assert claims == []

    def test_parse_invalid_response(self):
        claims, total = parse_claims_response(None)
        assert total == 0
        assert claims == []


class TestHealthClaimsFetchPage:
    """Tests for health claims page fetching with mocked HTTP."""

    def test_fetch_page_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalElements": 1,
            "content": [{"id": "HC-001"}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = fetch_claims_page(mock_client, status="all", page=0)
        assert result is not None

    def test_fetch_page_error(self):
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Server error")

        result = fetch_claims_page(mock_client, status="all", page=0)
        assert result is None


class TestHealthClaimsSaveResults:
    """Tests for health claims saving."""

    def test_save_json(self, tmp_path):
        claims = [
            {"id": "HC-001", "claim_wording": "Test claim", "status": "AUTHORISED"}
        ]
        save_claims_results(claims, str(tmp_path))
        json_file = tmp_path / "health_claims.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert data["total_claims"] == 1
        assert len(data["claims"]) == 1


# ============================================================
# Novel Food Tests
# ============================================================


class TestNovelFoodPayload:
    """Tests for novel food search payload building."""

    def test_default_payload(self):
        payload = build_novel_food_payload()
        assert payload["pageNumber"] == 0
        assert payload["pageSize"] == 50
        assert payload["searchTerms"] == ""

    def test_custom_page(self):
        payload = build_novel_food_payload(page=3, page_size=25)
        assert payload["pageNumber"] == 3
        assert payload["pageSize"] == 25


class TestNovelFoodParseEntry:
    """Tests for novel food entry parsing."""

    def test_parse_full_entry(self):
        raw = {
            "name": "Chia seeds",
            "status": "authorised",
            "category": "Seeds",
            "applicant": "Company XYZ",
            "date": "2020-01-15",
            "regulation": "EU 2017/2470",
            "conditions": "Max 15g per day",
            "specifications": "Salvia hispanica L.",
        }
        result = parse_novel_food_entry(raw)
        assert result is not None
        assert result["name"] == "Chia seeds"
        assert result["status"] == "authorised"
        assert result["category"] == "Seeds"
        assert result["applicant"] == "Company XYZ"
        assert result["date"] == "2020-01-15"
        assert result["regulation"] == "EU 2017/2470"

    def test_parse_minimal_entry(self):
        raw = {"name": "Novel substance"}
        result = parse_novel_food_entry(raw)
        assert result is not None
        assert result["name"] == "Novel substance"
        assert result["status"] == ""

    def test_parse_alternative_keys(self):
        raw = {
            "title": "Alt name",
            "authorisationStatus": "under-assessment",
            "foodCategory": "Extracts",
            "authorisationDate": "2023-05-01",
            "regulationReference": "EU 2023/1",
            "conditionsOfUse": "Supplements only",
        }
        result = parse_novel_food_entry(raw)
        assert result is not None
        assert result["name"] == "Alt name"
        assert result["status"] == "under-assessment"
        assert result["category"] == "Extracts"
        assert result["date"] == "2023-05-01"

    def test_parse_invalid_entry(self):
        result = parse_novel_food_entry("not a dict")
        assert result is None


class TestNovelFoodParseResponse:
    """Tests for novel food response parsing."""

    def test_parse_response_with_content(self):
        data = {
            "totalElements": 150,
            "content": [
                {"name": "Chia seeds", "status": "authorised"},
                {"name": "CBD extract", "status": "under-assessment"},
            ],
        }
        entries, total = parse_novel_food_response(data)
        assert total == 150
        assert len(entries) == 2

    def test_parse_response_with_entries_key(self):
        data = {
            "totalRecords": 50,
            "entries": [
                {"name": "Novel item", "status": "authorised"},
            ],
        }
        entries, total = parse_novel_food_response(data)
        assert total == 50
        assert len(entries) == 1

    def test_parse_empty_response(self):
        data = {"totalElements": 0, "content": []}
        entries, total = parse_novel_food_response(data)
        assert total == 0
        assert entries == []

    def test_parse_invalid_response(self):
        entries, total = parse_novel_food_response(None)
        assert total == 0
        assert entries == []


class TestNovelFoodFetchPage:
    """Tests for novel food page fetching with mocked HTTP."""

    def test_fetch_page_success(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "totalElements": 1,
            "content": [{"name": "Test food"}],
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        result = fetch_novel_food_page(mock_client, page=0)
        assert result is not None

    def test_fetch_page_error(self):
        mock_client = MagicMock()
        mock_client.post.side_effect = Exception("Network error")

        result = fetch_novel_food_page(mock_client, page=0)
        assert result is None


class TestNovelFoodSaveResults:
    """Tests for novel food saving."""

    def test_save_json(self, tmp_path):
        entries = [
            {"name": "Chia seeds", "status": "authorised", "category": "Seeds"}
        ]
        save_novel_food_results(entries, str(tmp_path))
        json_file = tmp_path / "novel_food_catalogue.json"
        assert json_file.exists()
        data = json.loads(json_file.read_text())
        assert data["total_entries"] == 1
        assert len(data["entries"]) == 1
        assert "fetched_at" in data


# ============================================================
# CLI Tests (argparse setup)
# ============================================================


class TestRasffCli:
    """Tests for RASFF CLI argument parsing."""

    def test_default_args(self):
        from fetch_rasff import main
        import fetch_rasff

        parser = argparse.ArgumentParser()
        # Verify the module can be imported and has main
        assert callable(fetch_rasff.main)

    def test_help_flag(self):
        """Verify --help exits cleanly (argparse configured correctly)."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "fetch_rasff.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "RASFF" in result.stdout
        assert "--output" in result.stdout
        assert "--verbose" in result.stdout
        assert "--delay" in result.stdout
        assert "--max-pages" in result.stdout
        assert "--category" in result.stdout


class TestHealthClaimsCli:
    """Tests for health claims CLI argument parsing."""

    def test_help_flag(self):
        """Verify --help exits cleanly."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "fetch_health_claims.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "health claims" in result.stdout
        assert "--output" in result.stdout
        assert "--verbose" in result.stdout
        assert "--delay" in result.stdout
        assert "--max-pages" in result.stdout
        assert "--status" in result.stdout


class TestNovelFoodCli:
    """Tests for novel food CLI argument parsing."""

    def test_help_flag(self):
        """Verify --help exits cleanly."""
        import subprocess

        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve().parent.parent / "fetch_novel_food.py"), "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "Novel Food" in result.stdout
        assert "--output" in result.stdout
        assert "--verbose" in result.stdout
        assert "--delay" in result.stdout
        assert "--max-pages" in result.stdout
