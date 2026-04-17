"""Stock screener module — fetches biotech/pharma companies via Financial Modeling Prep API."""

import os

import pandas as pd
import requests

FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

FMP_INDUSTRIES = [
    "Biotechnology",
    "Drug Manufacturers - General",
    "Drug Manufacturers - Specialty & Generic",
]

FMP_SCREENER_URL = "https://financialmodelingprep.com/api/v3/stock-screener"


def get_public_biotech_list(max_market_cap=None, exchanges="NYSE,NASDAQ,AMEX"):
    """Fetch the universe of biotech/pharma companies via FMP stock screener.

    Args:
        max_market_cap: Maximum market cap in raw dollars (e.g. 10e9 for $10B).
                        None means no upper limit.
        exchanges: Comma-separated exchange list.

    Returns:
        DataFrame with columns: symbol, name, marketCap, sector, industry, exchange.
    """
    if not FMP_API_KEY:
        raise RuntimeError("FMP_API_KEY environment variable is not set.")

    all_companies = []
    for industry in FMP_INDUSTRIES:
        print(f"Fetching companies for industry: {industry}...")
        params = {
            "sector": "Healthcare",
            "industry": industry,
            "exchange": exchanges,
            "apikey": FMP_API_KEY,
        }
        if max_market_cap is not None:
            params["marketCapLowerThan"] = int(max_market_cap)

        resp = requests.get(FMP_SCREENER_URL, params=params, timeout=15)
        resp.raise_for_status()
        companies = resp.json()
        print(f"  Found {len(companies)} companies.")
        all_companies.extend(companies)

    if not all_companies:
        return pd.DataFrame(columns=["symbol", "name", "marketCap", "sector", "industry", "exchange"])

    df = pd.DataFrame(all_companies)
    df = df.rename(columns={"companyName": "name"})
    df = df.drop_duplicates(subset="symbol", keep="first")

    keep_cols = ["symbol", "name", "marketCap", "sector", "industry", "exchange"]
    for col in keep_cols:
        if col not in df.columns:
            df[col] = None
    return df[keep_cols]
