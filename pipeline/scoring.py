"""Trial readiness scoring module.

Computes:
  - base_rate: historical phase-to-approval probability (0.0–1.0)
  - readiness_score: weighted composite score (0–100)
  - readiness_rationale: human-readable explanation of top contributing factors
"""

import re

# ---------------------------------------------------------------------------
# Historical base rates: probability of eventual FDA approval given current phase.
# Source: BIO/Informa Clinical Development Success Rates 2011–2020.
# ---------------------------------------------------------------------------
PHASE_BASE_RATES = {
    "PHASE1": 0.08,
    "PHASE2": 0.15,
    "PHASE3": 0.58,
    "PHASE4": 0.90,   # Already approved; post-marketing study
    "NA": 0.05,        # Early / unknown phase
}

# ---------------------------------------------------------------------------
# Therapeutic area modifiers (additive adjustment to base rate).
# Positive = historically higher success; negative = historically harder.
# ---------------------------------------------------------------------------
THERAPEUTIC_AREA_KEYWORDS = {
    "oncology": {
        "keywords": ["cancer", "tumor", "tumour", "carcinoma", "lymphoma", "leukemia",
                      "melanoma", "sarcoma", "glioblastoma", "myeloma", "neoplasm",
                      "oncology", "metastatic"],
        "modifier": -0.03,
        "label": "Oncology",
    },
    "rare_disease": {
        "keywords": ["orphan", "rare disease", "ultra-rare", "duchenne", "huntington",
                      "sickle cell", "cystic fibrosis", "spinal muscular atrophy",
                      "hemophilia", "fabry", "gaucher", "pompe"],
        "modifier": 0.05,
        "label": "Rare / Orphan Disease",
    },
    "cns": {
        "keywords": ["alzheimer", "parkinson", "depression", "schizophrenia", "epilepsy",
                      "migraine", "neuropathic", "multiple sclerosis", "als",
                      "amyotrophic", "bipolar", "anxiety", "adhd", "autism",
                      "neurodegenerat", "dementia", "cerebellar", "ataxia"],
        "modifier": -0.04,
        "label": "CNS / Neurology",
    },
    "infectious": {
        "keywords": ["hiv", "hepatitis", "influenza", "covid", "sars", "tuberculosis",
                      "malaria", "antibiotic", "antiviral", "antifungal", "infection",
                      "vaccine", "pneumonia", "sepsis"],
        "modifier": 0.02,
        "label": "Infectious Disease",
    },
    "cardiovascular": {
        "keywords": ["cardiovascular", "heart failure", "hypertension", "atherosclerosis",
                      "atrial fibrillation", "stroke", "thrombosis", "cholesterol",
                      "triglyceride", "cardiac"],
        "modifier": -0.02,
        "label": "Cardiovascular",
    },
    "metabolic": {
        "keywords": ["diabetes", "obesity", "metabolic", "nafld", "nash", "lipodystrophy",
                      "hyperlipidemia", "thyroid"],
        "modifier": 0.00,
        "label": "Metabolic / Endocrine",
    },
    "autoimmune": {
        "keywords": ["autoimmune", "rheumatoid", "lupus", "psoriasis", "crohn",
                      "ulcerative colitis", "inflammatory bowel", "eczema", "dermatitis",
                      "ankylosing"],
        "modifier": 0.01,
        "label": "Autoimmune / Inflammatory",
    },
}

# ---------------------------------------------------------------------------
# Readiness score weights (must sum to 1.0)
# ---------------------------------------------------------------------------
WEIGHTS = {
    "phase_base_rate": 0.30,
    "therapeutic_area": 0.15,
    "recruitment_status": 0.10,
    "enrollment_size": 0.10,
    "fda_approvals": 0.15,
    "market_cap_tier": 0.10,
    "multi_site": 0.10,
}


def get_base_rate(phase_str):
    """Return historical probability of FDA approval given the trial's current phase.

    Args:
        phase_str: Phase string as returned by ClinicalTrials.gov,
                   e.g. "PHASE2", "PHASE1, PHASE2", "PHASE3".

    Returns:
        float between 0.0 and 1.0.
    """
    if not phase_str:
        return PHASE_BASE_RATES["NA"]

    # If multiple phases listed (e.g. "PHASE1, PHASE2"), take the highest.
    phases = [p.strip().upper() for p in phase_str.replace(",", " ").split()]
    best = max(
        (PHASE_BASE_RATES.get(p, PHASE_BASE_RATES["NA"]) for p in phases),
        default=PHASE_BASE_RATES["NA"],
    )
    return best


def detect_therapeutic_area(title, conditions):
    """Detect therapeutic area from trial title and conditions list.

    Args:
        title: Trial brief title (str).
        conditions: List of condition strings from ClinicalTrials.gov.

    Returns:
        Tuple of (area_label: str, modifier: float).
        Returns ("General", 0.0) if no specific area matched.
    """
    text = " ".join([title or ""] + (conditions or [])).lower()

    for area_info in THERAPEUTIC_AREA_KEYWORDS.values():
        for kw in area_info["keywords"]:
            if kw in text:
                return area_info["label"], area_info["modifier"]

    return "General", 0.0


def _score_phase(base_rate):
    """Normalize base_rate (0.0–1.0) to a 0–100 sub-score."""
    return min(100, max(0, base_rate * 100))


def _score_therapeutic_area(modifier):
    """Convert area modifier to a 0–100 sub-score (50 = neutral)."""
    return min(100, max(0, 50 + modifier * 500))


def _score_recruitment(status):
    """Score recruitment status: actively recruiting is stronger signal."""
    mapping = {
        "RECRUITING": 80,
        "NOT_YET_RECRUITING": 50,
        "ACTIVE_NOT_RECRUITING": 40,
        "ENROLLING_BY_INVITATION": 60,
    }
    return mapping.get(status, 30)


def _score_enrollment(enrollment_count):
    """Larger enrollment → more robust trial. Scored on log scale."""
    if not enrollment_count or enrollment_count <= 0:
        return 30  # unknown / missing data
    if enrollment_count < 50:
        return 35
    if enrollment_count < 200:
        return 50
    if enrollment_count < 1000:
        return 70
    return 85


def _score_fda_approvals(approval_count):
    """More prior FDA approvals → stronger company track record."""
    if approval_count is None:
        return 40  # unknown
    if approval_count == 0:
        return 25
    if approval_count <= 2:
        return 50
    if approval_count <= 10:
        return 70
    return 90


def _score_market_cap(market_cap):
    """Larger cap → more resources. Mid-cap biotech gets slight boost for agility."""
    if not market_cap or market_cap <= 0:
        return 30
    cap_b = market_cap / 1e9
    if cap_b < 0.5:
        return 25   # micro-cap, higher risk
    if cap_b < 2:
        return 45   # small-cap
    if cap_b < 10:
        return 65   # mid-cap sweet spot
    if cap_b < 50:
        return 60   # large-cap
    return 55       # mega-cap pharma (slower, but safer)


def _score_multi_site(locations_count):
    """Multi-site trials are generally more robust."""
    if locations_count is None or locations_count <= 0:
        return 30
    if locations_count == 1:
        return 40
    if locations_count <= 10:
        return 60
    if locations_count <= 50:
        return 75
    return 85


def calculate_readiness_score(trial, company_data=None):
    """Compute a composite trial readiness score (0–100) with rationale.

    Args:
        trial: Dict with keys from trials.fetch_trials output:
            nct_id, title, phase, status, conditions, enrollment_count,
            locations_count, start_date, has_results.
        company_data: Optional dict with keys:
            market_cap (float), fda_approval_count (int or None).

    Returns:
        Tuple of (readiness_score: int, base_rate: float, therapeutic_area: str,
                  readiness_rationale: str).
    """
    company_data = company_data or {}

    # --- Individual sub-scores ---
    base_rate = get_base_rate(trial.get("phase"))
    area_label, area_modifier = detect_therapeutic_area(
        trial.get("title"), trial.get("conditions")
    )

    sub_scores = {
        "phase_base_rate": (_score_phase(base_rate), f"Phase base rate {base_rate:.0%}"),
        "therapeutic_area": (
            _score_therapeutic_area(area_modifier),
            f"{area_label} area ({area_modifier:+.0%})",
        ),
        "recruitment_status": (
            _score_recruitment(trial.get("status")),
            f"Status: {trial.get('status', 'unknown')}",
        ),
        "enrollment_size": (
            _score_enrollment(trial.get("enrollment_count")),
            f"Enrollment: {trial.get('enrollment_count', 'N/A')}",
        ),
        "fda_approvals": (
            _score_fda_approvals(company_data.get("fda_approval_count")),
            f"Prior FDA approvals: {company_data.get('fda_approval_count', 'N/A')}",
        ),
        "market_cap_tier": (
            _score_market_cap(company_data.get("market_cap")),
            f"Market cap tier",
        ),
        "multi_site": (
            _score_multi_site(trial.get("locations_count")),
            f"Sites: {trial.get('locations_count', 'N/A')}",
        ),
    }

    # --- Weighted composite ---
    total = sum(
        sub_scores[key][0] * WEIGHTS[key] for key in WEIGHTS
    )
    readiness_score = int(round(total))

    # --- Rationale: top 3 contributing factors by weighted score ---
    ranked = sorted(
        ((key, sub_scores[key][0] * WEIGHTS[key], sub_scores[key][1]) for key in WEIGHTS),
        key=lambda x: x[1],
        reverse=True,
    )
    top3 = [desc for _, _, desc in ranked[:3]]
    rationale = "; ".join(top3)

    return readiness_score, base_rate, area_label, rationale
