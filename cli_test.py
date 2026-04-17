"""Tests for cli.py — argument parsing and phase filtering."""

import pytest
from cli import parse_args, filter_trials_by_phase


# ── parse_args ─────────────────────────────────────────────────────────────

class TestParseArgs:
    def test_defaults(self):
        args = parse_args([])
        assert args.cap is None
        assert args.phase == "all"
        assert args.output_dir == "./data"
        assert args.skip_scoring is False
        assert args.company_info is False
        assert args.format == "csv"

    def test_cap_flag(self):
        args = parse_args(["--cap", "10"])
        assert args.cap == 10.0

    def test_cap_float(self):
        args = parse_args(["--cap", "5.5"])
        assert args.cap == 5.5

    def test_phase_flag(self):
        args = parse_args(["--phase", "2,3"])
        assert args.phase == "2,3"

    def test_output_dir_flag(self):
        args = parse_args(["--output-dir", "/tmp/out"])
        assert args.output_dir == "/tmp/out"

    def test_skip_scoring(self):
        args = parse_args(["--skip-scoring"])
        assert args.skip_scoring is True

    def test_company_info(self):
        args = parse_args(["--company-info"])
        assert args.company_info is True

    def test_all_flags(self):
        args = parse_args([
            "--cap", "10",
            "--phase", "3",
            "--output-dir", "/tmp",
            "--skip-scoring",
            "--company-info",
            "--format", "csv",
        ])
        assert args.cap == 10.0
        assert args.phase == "3"
        assert args.output_dir == "/tmp"
        assert args.skip_scoring is True
        assert args.company_info is True


# ── filter_trials_by_phase ─────────────────────────────────────────────────

class TestFilterTrialsByPhase:
    SAMPLE_TRIALS = [
        {"nct_id": "NCT001", "phase": "PHASE1"},
        {"nct_id": "NCT002", "phase": "PHASE2"},
        {"nct_id": "NCT003", "phase": "PHASE3"},
        {"nct_id": "NCT004", "phase": "PHASE1, PHASE2"},
        {"nct_id": "NCT005", "phase": ""},
        {"nct_id": "NCT006", "phase": None},
    ]

    def test_all_returns_everything(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "all")
        assert len(result) == len(self.SAMPLE_TRIALS)

    def test_single_phase(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "2")
        nct_ids = {t["nct_id"] for t in result}
        assert "NCT002" in nct_ids
        assert "NCT004" in nct_ids  # "PHASE1, PHASE2" includes PHASE2
        assert "NCT001" not in nct_ids

    def test_multiple_phases(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "2,3")
        nct_ids = {t["nct_id"] for t in result}
        assert "NCT002" in nct_ids
        assert "NCT003" in nct_ids
        assert "NCT004" in nct_ids

    def test_phase_1_only(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "1")
        nct_ids = {t["nct_id"] for t in result}
        assert "NCT001" in nct_ids
        assert "NCT004" in nct_ids
        assert "NCT002" not in nct_ids

    def test_empty_phase_excluded(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "3")
        nct_ids = {t["nct_id"] for t in result}
        assert "NCT005" not in nct_ids
        assert "NCT006" not in nct_ids

    def test_empty_string_returns_all(self):
        result = filter_trials_by_phase(self.SAMPLE_TRIALS, "")
        assert len(result) == len(self.SAMPLE_TRIALS)
