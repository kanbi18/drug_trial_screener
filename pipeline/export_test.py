"""Tests for pipeline.export module."""

import os
import pytest
import pandas as pd
from pipeline.export import (
    export_trials_csv,
    export_companies_csv,
    export_company_list_csv,
    TRIAL_COLUMNS,
    COMPANY_COLUMNS,
)


@pytest.fixture
def tmp_output(tmp_path):
    return str(tmp_path)


# ── TRIAL_COLUMNS / COMPANY_COLUMNS constants ─────────────────────────────

class TestConstants:
    def test_trial_columns_count(self):
        assert len(TRIAL_COLUMNS) == 14

    def test_company_columns_count(self):
        assert len(COMPANY_COLUMNS) == 9

    def test_trial_columns_no_duplicates(self):
        assert len(TRIAL_COLUMNS) == len(set(TRIAL_COLUMNS))

    def test_company_columns_no_duplicates(self):
        assert len(COMPANY_COLUMNS) == len(set(COMPANY_COLUMNS))


# ── export_trials_csv ──────────────────────────────────────────────────────

class TestExportTrialsCsv:
    def test_creates_file(self, tmp_output):
        rows = [{"ticker": "ABC", "company": "Abc", "nct_id": "NCT001",
                 "title": "Trial", "phase": "PHASE2", "status": "RECRUITING"}]
        path = export_trials_csv(rows, tmp_output, filename="test.csv")
        assert os.path.isfile(path)

    def test_correct_columns(self, tmp_output):
        rows = [{"ticker": "X", "nct_id": "NCT001"}]
        path = export_trials_csv(rows, tmp_output, filename="test.csv")
        df = pd.read_csv(path)
        assert list(df.columns) == TRIAL_COLUMNS

    def test_fills_missing_columns_with_none(self, tmp_output):
        rows = [{"ticker": "X"}]
        path = export_trials_csv(rows, tmp_output, filename="test.csv")
        df = pd.read_csv(path)
        assert len(df) == 1
        assert df.iloc[0]["ticker"] == "X"
        assert pd.isna(df.iloc[0]["nct_id"])

    def test_auto_filename_with_cap_label(self, tmp_output):
        rows = [{"ticker": "X"}]
        path = export_trials_csv(rows, tmp_output, max_cap_label="10B")
        filename = os.path.basename(path)
        assert "10B" in filename
        assert filename.endswith(".csv")

    def test_auto_filename_without_cap_label(self, tmp_output):
        rows = [{"ticker": "X"}]
        path = export_trials_csv(rows, tmp_output)
        filename = os.path.basename(path)
        assert "master_biotech_pipeline" in filename

    def test_empty_rows(self, tmp_output):
        path = export_trials_csv([], tmp_output, filename="empty.csv")
        df = pd.read_csv(path)
        assert len(df) == 0
        assert list(df.columns) == TRIAL_COLUMNS

    def test_creates_output_dir(self, tmp_path):
        nested = str(tmp_path / "a" / "b" / "c")
        path = export_trials_csv([{"ticker": "X"}], nested, filename="test.csv")
        assert os.path.isfile(path)


# ── export_companies_csv ───────────────────────────────────────────────────

class TestExportCompaniesCsv:
    def test_creates_file(self, tmp_output):
        df = pd.DataFrame([{"ticker": "ABC", "company_name": "Abc"}])
        path = export_companies_csv(df, tmp_output, filename="co.csv")
        assert os.path.isfile(path)

    def test_correct_columns(self, tmp_output):
        df = pd.DataFrame([{"ticker": "X"}])
        path = export_companies_csv(df, tmp_output, filename="co.csv")
        result = pd.read_csv(path)
        assert list(result.columns) == COMPANY_COLUMNS

    def test_auto_filename(self, tmp_output):
        df = pd.DataFrame([{"ticker": "X"}])
        path = export_companies_csv(df, tmp_output)
        filename = os.path.basename(path)
        assert "company_info" in filename
        assert filename.endswith(".csv")


# ── export_company_list_csv ────────────────────────────────────────────────

class TestExportCompanyListCsv:
    def test_creates_file(self, tmp_output):
        df = pd.DataFrame([{"symbol": "ABC", "name": "ABC Inc."}])
        path = export_company_list_csv(df, tmp_output)
        assert os.path.isfile(path)
        assert os.path.basename(path) == "company_universe.csv"

    def test_preserves_all_columns(self, tmp_output):
        df = pd.DataFrame([{"symbol": "X", "name": "X", "marketCap": 1e9}])
        path = export_company_list_csv(df, tmp_output)
        result = pd.read_csv(path)
        assert "symbol" in result.columns
        assert "marketCap" in result.columns

    def test_custom_filename(self, tmp_output):
        df = pd.DataFrame([{"symbol": "X"}])
        path = export_company_list_csv(df, tmp_output, filename="custom.csv")
        assert os.path.basename(path) == "custom.csv"
