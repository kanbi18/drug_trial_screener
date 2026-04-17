"""Company information module — builds a separate company metadata table.

Integrates:
  - Financial Modeling Prep (FMP) for market data (already fetched by screener).
  - OpenFDA Drug API for historical FDA approval counts (free, no key needed).
"""

import requests


OPENFDA_DRUG_URL = "https://api.fda.gov/drug/drugsfda.json"


def get_fda_approval_count(company_name):
    """Query OpenFDA for the number of FDA-approved drug applications by sponsor.

    Args:
        company_name: Company/sponsor name (cleaned, without Inc./Corp. suffixes).

    Returns:
        int: Number of approved applications, or 0 on error / no results.
    """
    params = {
        "search": f'openfda.manufacturer_name:"{company_name}"',
        "limit": 1,
    }
    try:
        resp = requests.get(OPENFDA_DRUG_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        meta = data.get("meta", {}).get("results", {})
        return meta.get("total", 0)
    except Exception:
        return 0


def build_company_table(companies_df, trial_results=None):
    """Build a company-level metadata table.

    Args:
        companies_df: DataFrame from screener with columns:
            symbol, name, marketCap, sector, industry, exchange.
        trial_results: Optional list of trial dicts (with 'ticker' and
            'readiness_score' keys) used to compute aggregate stats.

    Returns:
        DataFrame with columns:
            ticker, company_name, market_cap, sector, industry, exchange,
            fda_approved_drugs_count, active_trial_count, avg_readiness_score.
    """
    from pipeline.trials import clean_company_name

    rows = []
    for _, company in companies_df.iterrows():
        ticker = company["symbol"]
        clean_name = clean_company_name(company["name"])

        print(f"  Fetching FDA data for {clean_name}...")
        fda_count = get_fda_approval_count(clean_name)

        # Aggregate trial-level data for this company
        active_count = 0
        avg_score = None
        if trial_results:
            company_trials = [t for t in trial_results if t.get("ticker") == ticker]
            active_count = len(company_trials)
            scores = [t["readiness_score"] for t in company_trials
                      if t.get("readiness_score") is not None]
            if scores:
                avg_score = round(sum(scores) / len(scores), 1)

        rows.append({
            "ticker": ticker,
            "company_name": clean_name,
            "market_cap": company.get("marketCap"),
            "sector": company.get("sector"),
            "industry": company.get("industry"),
            "exchange": company.get("exchange"),
            "fda_approved_drugs_count": fda_count,
            "active_trial_count": active_count,
            "avg_readiness_score": avg_score,
        })

    import pandas as pd
    return pd.DataFrame(rows)
