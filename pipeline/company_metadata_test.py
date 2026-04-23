"""Tests for pipeline.company_info module."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from pipeline.company_metadata import get_fda_approval_count, build_company_table


# ── get_fda_approval_count ─────────────────────────────────────────────────

class TestGetFdaApprovalCount:
    @patch("pipeline.company_metadata.requests.get")
    def test_returns_total_count(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "meta": {"results": {"total": 42}},
            "results": [],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert get_fda_approval_count("Pfizer") == 42

    @patch("pipeline.company_metadata.requests.get")
    def test_returns_zero_on_no_results(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "meta": {"results": {"total": 0}},
            "results": [],
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert get_fda_approval_count("Unknown Company") == 0

    @patch("pipeline.company_metadata.requests.get")
    def test_returns_zero_on_error(self, mock_get):
        mock_get.side_effect = ConnectionError("timeout")
        assert get_fda_approval_count("TestCo") == 0

    @patch("pipeline.company_metadata.requests.get")
    def test_returns_zero_on_malformed_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        assert get_fda_approval_count("TestCo") == 0


# ── build_company_table ────────────────────────────────────────────────────

class TestBuildCompanyTable:
    @patch("pipeline.company_metadata.get_fda_approval_count", return_value=5)
    def test_basic_table_structure(self, mock_fda):
        companies_df = pd.DataFrame([{
            "symbol": "ABCD",
            "name": "Abcd Therapeutics, Inc.",
            "marketCap": 3e9,
            "sector": "Healthcare",
            "industry": "Biotechnology",
            "exchange": "NASDAQ",
        }])

        result = build_company_table(companies_df)

        assert len(result) == 1
        row = result.iloc[0]
        assert row["ticker"] == "ABCD"
        assert row["company_name"] == "Abcd"
        assert row["market_cap"] == 3e9
        assert row["fda_approved_drugs_count"] == 5
        assert row["active_trial_count"] == 0
        assert row["avg_readiness_score"] is None

    @patch("pipeline.company_metadata.get_fda_approval_count", return_value=2)
    def test_with_trial_results(self, mock_fda):
        companies_df = pd.DataFrame([{
            "symbol": "XYZ",
            "name": "XYZ Corp.",
            "marketCap": 1e9,
            "sector": "Healthcare",
            "industry": "Biotechnology",
            "exchange": "NYSE",
        }])

        trials = [
            {"ticker": "XYZ", "readiness_score": 60},
            {"ticker": "XYZ", "readiness_score": 80},
        ]

        result = build_company_table(companies_df, trial_results=trials)
        row = result.iloc[0]
        assert row["active_trial_count"] == 2
        assert row["avg_readiness_score"] == 70.0

    @patch("pipeline.company_metadata.get_fda_approval_count", return_value=0)
    def test_trials_with_none_scores(self, mock_fda):
        companies_df = pd.DataFrame([{
            "symbol": "AAA",
            "name": "AAA Inc.",
            "marketCap": 500e6,
            "sector": "Healthcare",
            "industry": "Biotechnology",
            "exchange": "NASDAQ",
        }])

        trials = [
            {"ticker": "AAA", "readiness_score": None},
            {"ticker": "AAA", "readiness_score": 50},
        ]

        result = build_company_table(companies_df, trial_results=trials)
        row = result.iloc[0]
        assert row["active_trial_count"] == 2
        assert row["avg_readiness_score"] == 50.0

    @patch("pipeline.company_metadata.get_fda_approval_count", return_value=0)
    def test_expected_columns(self, mock_fda):
        companies_df = pd.DataFrame([{
            "symbol": "T", "name": "T", "marketCap": 1e9,
            "sector": "Healthcare", "industry": "Biotechnology", "exchange": "NYSE",
        }])

        result = build_company_table(companies_df)
        expected_cols = [
            "ticker", "company_name", "market_cap", "sector", "industry",
            "exchange", "fda_approved_drugs_count", "active_trial_count",
            "avg_readiness_score",
        ]
        assert list(result.columns) == expected_cols
