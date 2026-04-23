# Biotech Pipeline Research (Go)

Clinical trial screening tool for identifying promising biotech/pharma companies with active trials, scoring trial readiness, and exporting structured CSV outputs.

## Quick Start

```bash
# Set your FMP API key
export FMP_API_KEY="your_key_here"

# Run the main pipeline
go run . --cap 10

# Run with phase filter and company table
go run . --cap 10 --phase 2,3 --company-info

# Skip scoring for faster runs
go run . --cap 10 --skip-scoring

# Run tests
go test ./...
```

## Project Layout

```text
research/
├── go.mod
├── main.go                              # Main CLI entrypoint
├── cmd/
│   └── clinical_trial_tracker/
│       └── main.go                      # Legacy tracker-style entrypoint
├── internal/
│   └── app/
│       ├── app.go                       # Args parsing + pipeline orchestration
│       └── app_test.go
├── pipeline/
│   ├── types.go
│   ├── stock_screener.go                # FMP stock screener
│   ├── stock_screener_test.go
│   ├── clinical_trials.go               # ClinicalTrials.gov fetching
│   ├── clinical_trials_test.go
│   ├── trial_readiness_scoring.go       # Readiness score + rationale
│   ├── trial_readiness_scoring_test.go
│   ├── company_metadata.go              # OpenFDA metadata
│   ├── company_metadata_test.go
│   ├── pipeline_exporter.go             # CSV exporters
│   ├── pipeline_exporter_test.go
│   ├── trial_success_predictor.go       # ML stub (not implemented)
│   └── trial_success_predictor_test.go
└── data/                                # Generated CSV outputs
```

## CLI Flags

- `--cap BILLIONS`: market cap limit in billions
- `--phase PHASES`: comma-separated phases (`1,2,3`) or `all`
- `--output-dir DIR`: output directory (default `./data`)
- `--skip-scoring`: skip readiness scoring
- `--company-info`: export company metadata table
- `--format csv`: currently only CSV is supported

## APIs

- Financial Modeling Prep: stock screening + company metadata (`FMP_API_KEY` required)
- ClinicalTrials.gov v2: trial data (no API key)
- OpenFDA Drug API: FDA approval count (no API key)

## Output Files

- Trials: `trials_cap_<cap>_<date>.csv` or `trials_all_<date>.csv`
- Company info: `company_info_<date>.csv`
- Company universe: `companies_universe.csv`
