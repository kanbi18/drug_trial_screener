# Biotech Pipeline Research

Clinical trial screening tool for identifying promising biotech/pharma companies with active trials, scoring trial readiness, and exporting structured results.

## Quick Start

```bash
# Set your FMP API key
export FMP_API_KEY="your_key_here"

# Run with $10B market cap filter
python cli.py --cap 10

# Run with phase filter and company info table
python cli.py --cap 10 --phase 2,3 --company-info

# Skip scoring for a faster run
python cli.py --cap 10 --skip-scoring

# See all options
python cli.py --help
```

## Pipeline Steps

### 1. Stock Screening (`pipeline/screener.py`)
**API:** Financial Modeling Prep (FMP)  
- Industries: Biotechnology, Drug Manufacturers (General & Specialty)
- Exchanges: NYSE, NASDAQ, AMEX
- Market cap filter: configurable via `--cap` flag
- Output: company universe list (symbol, name, marketCap, sector, industry, exchange)

### 2. Clinical Trial Fetching (`pipeline/trials.py`)
**API:** ClinicalTrials.gov v2  
- Statuses: RECRUITING, NOT_YET_RECRUITING
- Max 50 trials per company
- Enriched fields: enrollment count, conditions, locations count, start date, has results
- Phase filtering via `--phase` flag (e.g. `--phase 2,3`)

### 3. Trial Readiness Scoring (`pipeline/scoring.py`)
Each trial gets three scores:

| Column | Type | Description |
|---|---|---|
| `base_rate` | float 0.0–1.0 | Historical phase-to-approval probability (BIO/Informa data) |
| `readiness_score` | int 0–100 | Weighted composite of all factors below |
| `analyst_estimate` | float 0.0–1.0 | Manual column — user fills in from personal research |

**Readiness score factors:**

| Factor | Weight | Source |
|---|---|---|
| Phase base rate | 30% | Historical success rates |
| Therapeutic area | 15% | Keyword detection from trial title/conditions |
| Recruitment status | 10% | ClinicalTrials.gov |
| Enrollment size | 10% | ClinicalTrials.gov |
| Company FDA approvals | 15% | OpenFDA API |
| Company market cap tier | 10% | FMP |
| Multi-site trial | 10% | ClinicalTrials.gov location count |

Auto-generates `readiness_rationale` summarizing top 3 contributing factors.

### 4. ML Model — Stub (`pipeline/ml_model.py`)
Documented interface for a future gradient-boosted classifier (XGBoost/LightGBM) trained on historical trial outcomes. **Not called in the pipeline yet.** See module docstring for architecture, training data schema, feature engineering notes, and implementation checklist.

### 5. Company Info Table (`pipeline/company_info.py`)
**API:** OpenFDA Drug API (free, no key)  
Separate table (joined on ticker), generated with `--company-info` flag:

| Column | Source |
|---|---|
| ticker, company_name, market_cap, sector, industry, exchange | FMP |
| fda_approved_drugs_count | OpenFDA |
| active_trial_count | Aggregated from trials |
| avg_readiness_score | Aggregated from scoring |

### 6. Export (`pipeline/export.py`)
- **CSV:** ✅ Implemented — auto-dated filenames to `data/`
- **Obsidian markdown:** Planned — export interface is extensible for future formats

## Trial Table Schema (14 columns)

| Column | Type | Source |
|---|---|---|
| ticker | str | FMP |
| company | str | FMP |
| nct_id | str | ClinicalTrials.gov |
| title | str | ClinicalTrials.gov |
| phase | str | ClinicalTrials.gov |
| status | str | ClinicalTrials.gov |
| therapeutic_area | str | Auto-detected from conditions |
| enrollment_count | int | ClinicalTrials.gov |
| is_multi_site | bool | ClinicalTrials.gov |
| start_date | str | ClinicalTrials.gov |
| base_rate | float | Historical lookup |
| readiness_score | int 0–100 | Weighted composite |
| readiness_rationale | str | Auto-generated |
| analyst_estimate | float | Manual (empty on export) |

## CLI Flags

| Flag | Default | Description |
|---|---|---|
| `--cap BILLIONS` | None | Market cap limit in billions |
| `--phase PHASES` | all | Comma-separated phases: `1,2,3` or `all` |
| `--output-dir DIR` | `./data` | Output directory |
| `--skip-scoring` | off | Skip scoring (faster, no OpenFDA calls) |
| `--company-info` | off | Generate separate company info table |
| `--format FORMAT` | csv | Output format (extensible) |

## APIs

| API | Purpose | Auth | Rate Limit |
|---|---|---|---|
| Financial Modeling Prep | Stock screening, company data | `FMP_API_KEY` env var | Tier-dependent |
| ClinicalTrials.gov v2 | Trial data + enrichment | None | ~3 req/sec |
| OpenFDA Drug API | FDA approval count per company | None | 240 req/min |

## Project Structure

```
research/
├── cli.py                          # CLI entry point (argparse)
├── cli_test.py                     # CLI tests
├── pipeline/
│   ├── __init__.py
│   ├── screener.py                 # FMP stock screener
│   ├── trials.py                   # ClinicalTrials.gov fetching
│   ├── scoring.py                  # Readiness score + base rate
│   ├── ml_model.py                 # ML prediction (stub, documented)
│   ├── company_info.py             # Company metadata + OpenFDA
│   └── export.py                   # CSV export (extensible)
├── data/                           # Generated output files
└── README.md
```

## Environment Setup
- Python 3.10+
- Dependencies: `pandas`, `requests`
- **Required:** `FMP_API_KEY` environment variable
