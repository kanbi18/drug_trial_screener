#!/usr/bin/env python3
"""CLI entry point for the biotech clinical trial pipeline.

Usage examples:
    python cli.py --cap 10
    python cli.py --cap 10 --phase 2,3 --company-info
    python cli.py --output-dir ./data --format csv
    python cli.py --help
"""

import argparse
import sys

import pandas as pd

from pipeline.stock_screener import get_public_biotech_list
from pipeline.clinical_trials import fetch_all_trials, clean_company_name
from pipeline.trial_readiness_scoring import calculate_readiness_score
from pipeline.company_metadata import build_company_table, get_fda_approval_count
from pipeline.pipeline_exporter import (
    export_trials_csv,
    export_companies_csv,
    export_company_list_csv,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Biotech clinical trial pipeline — screen companies, "
                    "fetch trials, score readiness, and export results.",
    )
    parser.add_argument(
        "--cap",
        type=float,
        default=None,
        metavar="BILLIONS",
        help="Maximum market cap in billions (e.g. 10 = $10B). "
             "Default: no limit (all companies).",
    )
    parser.add_argument(
        "--phase",
        type=str,
        default="all",
        metavar="PHASES",
        help="Comma-separated trial phases to include: 1,2,3 or 'all'. "
             "Default: all.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data",
        metavar="DIR",
        help="Output directory for generated files. Default: ./data",
    )
    parser.add_argument(
        "--skip-scoring",
        action="store_true",
        help="Skip readiness score calculation (faster, fewer API calls).",
    )
    parser.add_argument(
        "--company-info",
        action="store_true",
        help="Also generate a separate company info table.",
    )
    parser.add_argument(
        "--format",
        type=str,
        default="csv",
        choices=["csv"],
        help="Output format. Default: csv. (Extensible for future formats.)",
    )
    return parser.parse_args(argv)


def filter_trials_by_phase(trials, phase_arg):
    """Filter trial list to only include specified phases.

    Args:
        trials: List of trial dicts with 'phase' key.
        phase_arg: "all" or comma-separated phase numbers like "2,3".

    Returns:
        Filtered list of trial dicts.
    """
    if phase_arg == "all":
        return trials

    wanted = set()
    for p in phase_arg.split(","):
        p = p.strip()
        if p:
            wanted.add(f"PHASE{p}")

    if not wanted:
        return trials

    filtered = []
    for trial in trials:
        trial_phases = {
            ph.strip().upper()
            for ph in (trial.get("phase") or "").replace(",", " ").split()
        }
        if trial_phases & wanted:
            filtered.append(trial)

    return filtered


def run_pipeline(args):
    # --- Step 1: Screen companies ---
    print("=" * 60)
    print("STEP 1: Screening biotech/pharma companies")
    print("=" * 60)

    threshold = args.cap * 1e9 if args.cap else None
    companies_df = get_public_biotech_list(max_market_cap=threshold)

    if companies_df.empty:
        print("No companies found. Exiting.")
        return

    # Format cap as e.g. "10B" (int) or "2.5B" (float), used in output filenames
    cap_label = f"{int(args.cap)}B" if args.cap and args.cap == int(args.cap) else (
        f"{args.cap}B" if args.cap else None
    )

    print(f"  Found {len(companies_df)} companies.")
    export_company_list_csv(companies_df, args.output_dir)

    # --- Step 2: Fetch clinical trials ---
    print()
    print("=" * 60)
    print("STEP 2: Fetching clinical trials from ClinicalTrials.gov")
    print("=" * 60)

    raw_trials = fetch_all_trials(companies_df)
    print(f"  Fetched {len(raw_trials)} raw trials.")

    # --- Phase filter ---
    trials = filter_trials_by_phase(raw_trials, args.phase)
    if args.phase != "all":
        print(f"  After phase filter ({args.phase}): {len(trials)} trials.")

    # --- Step 3: Score trials ---
    if not args.skip_scoring:
        print()
        print("=" * 60)
        print("STEP 3: Scoring trial readiness")
        print("=" * 60)

        # Pre-fetch FDA approval counts for each company (batch)
        fda_cache = {}
        for _, company in companies_df.iterrows():
            clean_name = clean_company_name(company["name"])
            if clean_name not in fda_cache:
                fda_cache[clean_name] = get_fda_approval_count(clean_name)

        for trial in trials:
            company_data = {
                "market_cap": companies_df.loc[
                    companies_df["symbol"] == trial["ticker"], "marketCap"
                ].iloc[0] if trial["ticker"] in companies_df["symbol"].values else None,
                "fda_approval_count": fda_cache.get(trial.get("company"), 0),
            }

            score, base_rate, area, rationale = calculate_readiness_score(
                trial, company_data
            )
            trial["readiness_score"] = score
            trial["base_rate"] = round(base_rate, 3)
            trial["therapeutic_area"] = area
            trial["readiness_rationale"] = rationale
            trial["is_multi_site"] = (trial.get("locations_count", 0) or 0) > 1

        print(f"  Scored {len(trials)} trials.")
    else:
        print("\n  Skipping scoring (--skip-scoring).")
        for trial in trials:
            trial["readiness_score"] = None
            trial["base_rate"] = None
            trial["therapeutic_area"] = None
            trial["readiness_rationale"] = None
            trial["is_multi_site"] = (trial.get("locations_count", 0) or 0) > 1

    # analyst_estimate is always empty on export (manual fill later)
    for trial in trials:
        trial["analyst_estimate"] = None

    # --- Step 4: Export trials ---
    print()
    print("=" * 60)
    print("STEP 4: Exporting results")
    print("=" * 60)

    export_trials_csv(trials, args.output_dir, max_cap_label=cap_label)

    # --- Step 5 (optional): Company info table ---
    if args.company_info:
        print()
        print("=" * 60)
        print("STEP 5: Building company info table")
        print("=" * 60)

        company_table = build_company_table(companies_df, trial_results=trials)
        export_companies_csv(company_table, args.output_dir)

    print()
    print("=" * 60)
    print("DONE")
    print("=" * 60)


def main():
    args = parse_args()
    run_pipeline(args)


if __name__ == "__main__":
    main()
