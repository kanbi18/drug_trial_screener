"""Export module — writes pipeline results to output formats.

Currently supports CSV. Interface is designed to be extended with
additional formats (e.g. Obsidian markdown) in the future.
"""

import os
from datetime import date

import pandas as pd


TRIAL_COLUMNS = [
    "ticker",
    "company",
    "nct_id",
    "title",
    "phase",
    "status",
    "therapeutic_area",
    "enrollment_count",
    "is_multi_site",
    "start_date",
    "base_rate",
    "readiness_score",
    "readiness_rationale",
    "analyst_estimate",
]

COMPANY_COLUMNS = [
    "ticker",
    "company_name",
    "market_cap",
    "sector",
    "industry",
    "exchange",
    "fda_approved_drugs_count",
    "active_trial_count",
    "avg_readiness_score",
]


def export_trials_csv(trial_rows, output_dir, filename=None, max_cap_label=None):
    """Export trial results to CSV.

    Args:
        trial_rows: List of trial dicts matching TRIAL_COLUMNS keys.
        output_dir: Directory to write the file into.
        filename: Explicit filename. If None, auto-generated from max_cap_label.
        max_cap_label: Market cap label for auto-naming (e.g. "10B").

    Returns:
        Path to the written file.
    """
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        today = date.today().strftime("%Y-%m-%d")
        if max_cap_label:
            filename = f"biotech_pipeline_{max_cap_label}_cap_{today}.csv"
        else:
            filename = f"master_biotech_pipeline_{today}.csv"

    df = pd.DataFrame(trial_rows)
    # Ensure all expected columns exist, in order
    for col in TRIAL_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[TRIAL_COLUMNS]

    path = os.path.join(output_dir, filename)
    df.to_csv(path, index=False)
    print(f"Trials CSV written: {path} ({len(df)} rows)")
    return path


def export_companies_csv(companies_df, output_dir, filename=None):
    """Export company info table to CSV.

    Args:
        companies_df: DataFrame with COMPANY_COLUMNS.
        output_dir: Directory to write the file into.
        filename: Explicit filename. If None, auto-generated.

    Returns:
        Path to the written file.
    """
    os.makedirs(output_dir, exist_ok=True)

    if filename is None:
        today = date.today().strftime("%Y-%m-%d")
        filename = f"company_info_{today}.csv"

    for col in COMPANY_COLUMNS:
        if col not in companies_df.columns:
            companies_df[col] = None

    path = os.path.join(output_dir, filename)
    companies_df[COMPANY_COLUMNS].to_csv(path, index=False)
    print(f"Company CSV written: {path} ({len(companies_df)} rows)")
    return path


def export_company_list_csv(companies_df, output_dir, filename="company_universe.csv"):
    """Export the raw screener company list (for reference / debugging).

    Args:
        companies_df: DataFrame from screener.
        output_dir: Directory to write the file into.
        filename: Output filename.

    Returns:
        Path to the written file.
    """
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, filename)
    companies_df.to_csv(path, index=False)
    print(f"Company list written: {path} ({len(companies_df)} rows)")
    return path
