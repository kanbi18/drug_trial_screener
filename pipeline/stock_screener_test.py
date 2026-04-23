"""Tests for pipeline.screener module."""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from pipeline.stock_screener import get_public_biotech_list, FMP_INDUSTRIES, FMP_SCREENER_URL


class TestGetPublicBiotechList:
    @patch("pipeline.stock_screener.FMP_API_KEY", "")
    def test_raises_without_api_key(self):
        with pytest.raises(RuntimeError, match="FMP_API_KEY"):
            get_public_biotech_list()

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_returns_dataframe_with_correct_columns(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {
                "symbol": "ABCD",
                "companyName": "ABCD Inc.",
                "marketCap": 5_000_000_000,
                "sector": "Healthcare",
                "industry": "Biotechnology",
                "exchange": "NASDAQ",
            }
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        df = get_public_biotech_list()
        assert list(df.columns) == ["symbol", "name", "marketCap", "sector", "industry", "exchange"]
        assert len(df) >= 1

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_deduplicates_by_symbol(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = [
            {"symbol": "DUP", "companyName": "Dup Inc.", "marketCap": 1e9,
             "sector": "Healthcare", "industry": "Biotechnology", "exchange": "NYSE"},
        ]
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        df = get_public_biotech_list()
        # Called 3 times (one per industry), all return same symbol
        assert df["symbol"].nunique() == 1
        assert len(df) == 1

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_empty_response(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        df = get_public_biotech_list()
        assert df.empty
        assert list(df.columns) == ["symbol", "name", "marketCap", "sector", "industry", "exchange"]

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_market_cap_filter_passed(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        get_public_biotech_list(max_market_cap=10e9)

        for call in mock_get.call_args_list:
            params = call[1]["params"]
            assert params["marketCapLowerThan"] == int(10e9)

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_no_market_cap_filter_when_none(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        get_public_biotech_list(max_market_cap=None)

        for call in mock_get.call_args_list:
            params = call[1]["params"]
            assert "marketCapLowerThan" not in params

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_queries_all_three_industries(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        get_public_biotech_list()
        assert mock_get.call_count == len(FMP_INDUSTRIES)

        queried_industries = [
            call[1]["params"]["industry"] for call in mock_get.call_args_list
        ]
        assert queried_industries == FMP_INDUSTRIES

    @patch("pipeline.stock_screener.requests.get")
    @patch("pipeline.stock_screener.FMP_API_KEY", "test_key")
    def test_custom_exchanges(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = []
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        get_public_biotech_list(exchanges="NASDAQ")

        for call in mock_get.call_args_list:
            assert call[1]["params"]["exchange"] == "NASDAQ"
