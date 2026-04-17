"""Tests for pipeline.trials module."""

import pytest
from unittest.mock import patch, MagicMock
from pipeline.trials import clean_company_name, fetch_trials, fetch_all_trials
import pandas as pd


# ── clean_company_name ─────────────────────────────────────────────────────

class TestCleanCompanyName:
    def test_strip_inc_with_comma(self):
        assert clean_company_name("Vertex Pharmaceuticals, Inc.") == "Vertex Pharmaceuticals"

    def test_strip_inc(self):
        assert clean_company_name("Vertex Pharmaceuticals Inc.") == "Vertex Pharmaceuticals"

    def test_strip_corp(self):
        assert clean_company_name("Pfizer Corp.") == "Pfizer"

    def test_strip_plc(self):
        assert clean_company_name("AstraZeneca PLC") == "AstraZeneca"

    def test_strip_ltd(self):
        assert clean_company_name("BioNTech Ltd.") == "BioNTech"

    def test_strip_incorporated(self):
        assert clean_company_name("Amgen Incorporated") == "Amgen"

    def test_strip_international(self):
        assert clean_company_name("Teva International") == "Teva"

    def test_strip_holdings(self):
        assert clean_company_name("Royalty Pharma Holdings") == "Royalty Pharma"

    def test_strip_therapeutics(self):
        assert clean_company_name("Axsome Therapeutics") == "Axsome"

    def test_strip_biosciences(self):
        assert clean_company_name("Sarepta Biosciences") == "Sarepta"

    def test_multiple_suffixes(self):
        assert clean_company_name("Acme Therapeutics, Inc.") == "Acme"

    def test_no_suffix(self):
        assert clean_company_name("Moderna") == "Moderna"

    def test_empty_string(self):
        assert clean_company_name("") == ""

    def test_whitespace_stripped(self):
        assert clean_company_name("  Pfizer Corp.  ") == "Pfizer"


# ── fetch_trials ───────────────────────────────────────────────────────────

SAMPLE_API_RESPONSE = {
    "studies": [
        {
            "hasResults": False,
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Phase II Cancer Study",
                },
                "designModule": {
                    "phases": ["PHASE2"],
                    "enrollmentInfo": {"count": 150},
                },
                "statusModule": {
                    "overallStatus": "RECRUITING",
                    "startDateStruct": {"date": "2025-03-01"},
                },
                "conditionsModule": {
                    "conditions": ["Breast Cancer"],
                },
                "contactsLocationsModule": {
                    "locations": [{"facility": "Site A"}, {"facility": "Site B"}],
                },
            },
        }
    ]
}


class TestFetchTrials:
    @patch("pipeline.trials.requests.get")
    def test_parses_single_study(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = SAMPLE_API_RESPONSE
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = fetch_trials("TestCo")
        assert len(results) == 1

        trial = results[0]
        assert trial["nct_id"] == "NCT12345678"
        assert trial["title"] == "Phase II Cancer Study"
        assert trial["phase"] == "PHASE2"
        assert trial["status"] == "RECRUITING"
        assert trial["conditions"] == ["Breast Cancer"]
        assert trial["enrollment_count"] == 150
        assert trial["locations_count"] == 2
        assert trial["start_date"] == "2025-03-01"
        assert trial["has_results"] is False

    @patch("pipeline.trials.requests.get")
    def test_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"studies": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = fetch_trials("Unknown Corp")
        assert results == []

    @patch("pipeline.trials.requests.get")
    def test_network_error_returns_empty(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        results = fetch_trials("TestCo")
        assert results == []

    @patch("pipeline.trials.requests.get")
    def test_custom_statuses(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"studies": []}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        fetch_trials("TestCo", statuses=["RECRUITING", "ACTIVE_NOT_RECRUITING"])

        call_params = mock_get.call_args[1]["params"]
        assert "RECRUITING|ACTIVE_NOT_RECRUITING" == call_params["filter.overallStatus"]

    @patch("pipeline.trials.requests.get")
    def test_missing_optional_fields(self, mock_get):
        minimal_study = {
            "studies": [{
                "hasResults": True,
                "protocolSection": {
                    "identificationModule": {"nctId": "NCT99999999"},
                    "designModule": {},
                    "statusModule": {},
                    "conditionsModule": {},
                    "contactsLocationsModule": {},
                },
            }]
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = minimal_study
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        results = fetch_trials("TestCo")
        assert len(results) == 1
        trial = results[0]
        assert trial["nct_id"] == "NCT99999999"
        assert trial["title"] is None
        assert trial["phase"] == ""
        assert trial["conditions"] == []
        assert trial["enrollment_count"] is None
        assert trial["locations_count"] == 0
        assert trial["start_date"] is None
        assert trial["has_results"] is True


# ── fetch_all_trials ───────────────────────────────────────────────────────

class TestFetchAllTrials:
    @patch("pipeline.trials.time.sleep")
    @patch("pipeline.trials.fetch_trials")
    def test_attaches_ticker_and_company(self, mock_fetch, mock_sleep):
        mock_fetch.return_value = [
            {"nct_id": "NCT001", "title": "Trial 1", "phase": "PHASE2",
             "status": "RECRUITING", "conditions": [], "enrollment_count": 50,
             "locations_count": 1, "start_date": None, "has_results": False},
        ]
        df = pd.DataFrame([
            {"symbol": "ABCD", "name": "Abcd Therapeutics, Inc."},
        ])

        results = fetch_all_trials(df)
        assert len(results) == 1
        assert results[0]["ticker"] == "ABCD"
        assert results[0]["company"] == "Abcd"

    @patch("pipeline.trials.time.sleep")
    @patch("pipeline.trials.fetch_trials")
    def test_multiple_companies(self, mock_fetch, mock_sleep):
        mock_fetch.side_effect = [
            [{"nct_id": "NCT001", "title": "T1", "phase": "PHASE1",
              "status": "RECRUITING", "conditions": [], "enrollment_count": 10,
              "locations_count": 1, "start_date": None, "has_results": False}],
            [],  # second company has no trials
        ]
        df = pd.DataFrame([
            {"symbol": "AAA", "name": "AAA Inc."},
            {"symbol": "BBB", "name": "BBB Corp."},
        ])

        results = fetch_all_trials(df)
        assert len(results) == 1
        assert results[0]["ticker"] == "AAA"

    @patch("pipeline.trials.time.sleep")
    @patch("pipeline.trials.fetch_trials")
    def test_respects_rate_limit(self, mock_fetch, mock_sleep):
        mock_fetch.return_value = []
        df = pd.DataFrame([
            {"symbol": "X", "name": "X"},
            {"symbol": "Y", "name": "Y"},
        ])
        fetch_all_trials(df)
        assert mock_sleep.call_count == 2
