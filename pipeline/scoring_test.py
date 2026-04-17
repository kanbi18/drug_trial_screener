"""Tests for pipeline.scoring module."""

import pytest
from pipeline.scoring import (
    PHASE_BASE_RATES,
    WEIGHTS,
    get_base_rate,
    detect_therapeutic_area,
    calculate_readiness_score,
    _score_phase,
    _score_therapeutic_area,
    _score_recruitment,
    _score_enrollment,
    _score_fda_approvals,
    _score_market_cap,
    _score_multi_site,
)


# ── get_base_rate ──────────────────────────────────────────────────────────

class TestGetBaseRate:
    def test_phase1(self):
        assert get_base_rate("PHASE1") == 0.08

    def test_phase2(self):
        assert get_base_rate("PHASE2") == 0.15

    def test_phase3(self):
        assert get_base_rate("PHASE3") == 0.58

    def test_phase4(self):
        assert get_base_rate("PHASE4") == 0.90

    def test_none_returns_na(self):
        assert get_base_rate(None) == PHASE_BASE_RATES["NA"]

    def test_empty_string_returns_na(self):
        assert get_base_rate("") == PHASE_BASE_RATES["NA"]

    def test_multi_phase_takes_highest(self):
        # "PHASE1, PHASE2" → should return PHASE2 rate (0.15)
        assert get_base_rate("PHASE1, PHASE2") == 0.15

    def test_multi_phase_3_and_4(self):
        assert get_base_rate("PHASE3, PHASE4") == 0.90

    def test_unknown_phase_returns_na(self):
        assert get_base_rate("EARLY_PHASE1") == PHASE_BASE_RATES["NA"]

    def test_case_insensitive_via_upper(self):
        # Input is uppercased internally
        assert get_base_rate("phase2") == 0.15


# ── detect_therapeutic_area ────────────────────────────────────────────────

class TestDetectTherapeuticArea:
    def test_oncology_from_title(self):
        area, mod = detect_therapeutic_area("Study of Drug X in Breast Cancer", [])
        assert area == "Oncology"
        assert mod == -0.03

    def test_oncology_from_conditions(self):
        area, mod = detect_therapeutic_area("A Phase II Study", ["Melanoma"])
        assert area == "Oncology"
        assert mod == -0.03

    def test_cns_alzheimer(self):
        area, mod = detect_therapeutic_area("Treatment of Alzheimer Disease", ["Alzheimer Disease"])
        assert area == "CNS / Neurology"
        assert mod == -0.04

    def test_cns_depression(self):
        area, mod = detect_therapeutic_area("Depression Treatment Trial", [])
        assert area == "CNS / Neurology"

    def test_rare_disease(self):
        area, mod = detect_therapeutic_area("Duchenne Muscular Dystrophy", ["Duchenne"])
        assert area == "Rare / Orphan Disease"
        assert mod == 0.05

    def test_infectious(self):
        area, mod = detect_therapeutic_area("HIV Vaccine Study", ["HIV"])
        assert area == "Infectious Disease"
        assert mod == 0.02

    def test_cardiovascular(self):
        area, mod = detect_therapeutic_area("Heart Failure Trial", [])
        assert area == "Cardiovascular"
        assert mod == -0.02

    def test_metabolic(self):
        area, mod = detect_therapeutic_area("Obesity Drug Study", ["Obesity"])
        assert area == "Metabolic / Endocrine"
        assert mod == 0.00

    def test_autoimmune(self):
        area, mod = detect_therapeutic_area("Rheumatoid Arthritis", ["Rheumatoid Arthritis"])
        assert area == "Autoimmune / Inflammatory"
        assert mod == 0.01

    def test_general_no_match(self):
        area, mod = detect_therapeutic_area("A Study of Something", ["Condition X"])
        assert area == "General"
        assert mod == 0.0

    def test_none_title(self):
        area, mod = detect_therapeutic_area(None, None)
        assert area == "General"
        assert mod == 0.0

    def test_empty_inputs(self):
        area, mod = detect_therapeutic_area("", [])
        assert area == "General"
        assert mod == 0.0


# ── Sub-score functions ────────────────────────────────────────────────────

class TestScorePhase:
    def test_zero(self):
        assert _score_phase(0.0) == 0

    def test_one(self):
        assert _score_phase(1.0) == 100

    def test_mid(self):
        assert abs(_score_phase(0.58) - 58.0) < 1e-9

    def test_clamp_above(self):
        assert _score_phase(1.5) == 100

    def test_clamp_below(self):
        assert _score_phase(-0.1) == 0


class TestScoreTherapeuticArea:
    def test_neutral(self):
        assert _score_therapeutic_area(0.0) == 50

    def test_positive_modifier(self):
        assert _score_therapeutic_area(0.05) == 75

    def test_negative_modifier(self):
        assert _score_therapeutic_area(-0.04) == 30

    def test_clamp_above(self):
        assert _score_therapeutic_area(0.20) == 100

    def test_clamp_below(self):
        assert _score_therapeutic_area(-0.20) == 0


class TestScoreRecruitment:
    def test_recruiting(self):
        assert _score_recruitment("RECRUITING") == 80

    def test_not_yet(self):
        assert _score_recruitment("NOT_YET_RECRUITING") == 50

    def test_active_not_recruiting(self):
        assert _score_recruitment("ACTIVE_NOT_RECRUITING") == 40

    def test_enrolling_by_invitation(self):
        assert _score_recruitment("ENROLLING_BY_INVITATION") == 60

    def test_unknown_status(self):
        assert _score_recruitment("SOMETHING_ELSE") == 30

    def test_none(self):
        assert _score_recruitment(None) == 30


class TestScoreEnrollment:
    def test_none(self):
        assert _score_enrollment(None) == 30

    def test_zero(self):
        assert _score_enrollment(0) == 30

    def test_negative(self):
        assert _score_enrollment(-5) == 30

    def test_small(self):
        assert _score_enrollment(10) == 35

    def test_medium(self):
        assert _score_enrollment(100) == 50

    def test_large(self):
        assert _score_enrollment(500) == 70

    def test_very_large(self):
        assert _score_enrollment(5000) == 85


class TestScoreFdaApprovals:
    def test_none(self):
        assert _score_fda_approvals(None) == 40

    def test_zero(self):
        assert _score_fda_approvals(0) == 25

    def test_few(self):
        assert _score_fda_approvals(2) == 50

    def test_moderate(self):
        assert _score_fda_approvals(5) == 70

    def test_many(self):
        assert _score_fda_approvals(15) == 90


class TestScoreMarketCap:
    def test_none(self):
        assert _score_market_cap(None) == 30

    def test_zero(self):
        assert _score_market_cap(0) == 30

    def test_micro(self):
        assert _score_market_cap(0.3e9) == 25

    def test_small(self):
        assert _score_market_cap(1e9) == 45

    def test_mid(self):
        assert _score_market_cap(5e9) == 65

    def test_large(self):
        assert _score_market_cap(20e9) == 60

    def test_mega(self):
        assert _score_market_cap(100e9) == 55


class TestScoreMultiSite:
    def test_none(self):
        assert _score_multi_site(None) == 30

    def test_zero(self):
        assert _score_multi_site(0) == 30

    def test_single(self):
        assert _score_multi_site(1) == 40

    def test_few(self):
        assert _score_multi_site(5) == 60

    def test_many(self):
        assert _score_multi_site(30) == 75

    def test_very_many(self):
        assert _score_multi_site(100) == 85


# ── Weights ────────────────────────────────────────────────────────────────

class TestWeights:
    def test_sum_to_one(self):
        assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9

    def test_all_positive(self):
        for key, val in WEIGHTS.items():
            assert val > 0, f"Weight {key} is not positive: {val}"


# ── calculate_readiness_score ──────────────────────────────────────────────

class TestCalculateReadinessScore:
    def _make_trial(self, **overrides):
        base = {
            "nct_id": "NCT00000001",
            "title": "A Study of Drug X",
            "phase": "PHASE2",
            "status": "RECRUITING",
            "conditions": ["Cancer"],
            "enrollment_count": 200,
            "locations_count": 5,
            "start_date": "2025-01-01",
            "has_results": False,
        }
        base.update(overrides)
        return base

    def test_returns_four_values(self):
        result = calculate_readiness_score(self._make_trial())
        assert len(result) == 4

    def test_score_in_range(self):
        score, _, _, _ = calculate_readiness_score(self._make_trial())
        assert 0 <= score <= 100

    def test_base_rate_matches_phase(self):
        _, base_rate, _, _ = calculate_readiness_score(
            self._make_trial(phase="PHASE3")
        )
        assert base_rate == 0.58

    def test_therapeutic_area_detected(self):
        _, _, area, _ = calculate_readiness_score(
            self._make_trial(title="Alzheimer Treatment", conditions=["Alzheimer"])
        )
        assert area == "CNS / Neurology"

    def test_rationale_non_empty(self):
        _, _, _, rationale = calculate_readiness_score(self._make_trial())
        assert len(rationale) > 0

    def test_rationale_has_semicolons(self):
        # Top-3 factors joined by "; "
        _, _, _, rationale = calculate_readiness_score(self._make_trial())
        assert ";" in rationale

    def test_company_data_affects_score(self):
        trial = self._make_trial()
        score_no_company, _, _, _ = calculate_readiness_score(trial)
        score_with_company, _, _, _ = calculate_readiness_score(
            trial, {"market_cap": 50e9, "fda_approval_count": 20}
        )
        # Strong company data should push score higher
        assert score_with_company >= score_no_company

    def test_phase3_scores_higher_than_phase1(self):
        s1, _, _, _ = calculate_readiness_score(self._make_trial(phase="PHASE1"))
        s3, _, _, _ = calculate_readiness_score(self._make_trial(phase="PHASE3"))
        assert s3 > s1

    def test_none_company_data_doesnt_crash(self):
        score, _, _, _ = calculate_readiness_score(self._make_trial(), None)
        assert 0 <= score <= 100

    def test_empty_trial_doesnt_crash(self):
        score, br, area, rationale = calculate_readiness_score({})
        assert 0 <= score <= 100
        assert br == PHASE_BASE_RATES["NA"]
        assert area == "General"
