import os
import pandas as pd
import requests
import time

FMP_API_KEY = os.environ.get("FMP_API_KEY", "")

# FMP industry names matching the old yfinance sectors
FMP_INDUSTRIES = [
    "Biotechnology",
    "Drug Manufacturers - General",
    "Drug Manufacturers - Specialty & Generic",
]


def get_public_biotech_list(max_market_cap=None):
    """Fetch the full universe of biotech/pharma companies via the FMP stock screener.
    Returns a DataFrame with columns: symbol, name, marketCap."""
    if not FMP_API_KEY:
        raise RuntimeError("FMP_API_KEY environment variable is not set.")

    all_companies = []
    for industry in FMP_INDUSTRIES:
        print(f"Fetching companies for industry: {industry}...")
        params = {
            "sector": "Healthcare",
            "industry": industry,
            "exchange": "NYSE,NASDAQ,AMEX",
            "apikey": FMP_API_KEY,
        }
        if max_market_cap is not None:
            params["marketCapLowerThan"] = int(max_market_cap)

        resp = requests.get(
            "https://financialmodelingprep.com/api/v3/stock-screener",
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        companies = resp.json()
        print(f"  Found {len(companies)} companies.")
        all_companies.extend(companies)

    if not all_companies:
        return pd.DataFrame()

    df = pd.DataFrame(all_companies)
    df = df.rename(columns={"companyName": "name"})
    df = df.drop_duplicates(subset="symbol", keep="first")
    return df[["symbol", "name", "marketCap"]]

# --- Helper to strip common corporate suffixes ---
def clean_company_name(name):
    for suffix in [", Inc.", " Inc.", " Corp.", " PLC", " Ltd.", " Incorporated"]:
        name = name.replace(suffix, "")
    return name.strip()


# --- Query ClinicalTrials.gov for active trials by sponsor ---
def fetch_trials(company_name):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.spons": company_name,
        "filter.overallStatus": "RECRUITING|NOT_YET_RECRUITING",
        "pageSize": 50,
        "format": "json"
    }
    try:
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("studies", [])
    except Exception as e:
        print(f"  Error fetching trials for {company_name}: {e}")
        return []


def generate_biotech_trials(max_market_cap_in_billions=None):
    """Generate a CSV of active clinical trials for biotech/pharma companies.

    Args:
        max_market_cap_in_billions: Optional maximum market cap in billions (e.g. 10 = $10B).
                    If provided, only companies below this threshold are included
                    and the output filename reflects the cap.
                    If None, all companies are included and the output is
                    master_biotech_pipeline_2026.csv.
    """
    # --- Step 1: Build the company list from FMP (market cap filter applied at query time) ---
    threshold = max_market_cap_in_billions * 1e9 if max_market_cap_in_billions else None
    biotech_pharma_df = get_public_biotech_list(max_market_cap=threshold)

    if biotech_pharma_df.empty:
        print("No companies found. Exiting.")
        return

    if max_market_cap_in_billions is not None:
        print(f"  {len(biotech_pharma_df)} companies at or below ${max_market_cap_in_billions}B market cap.")

    print(f"Total companies: {len(biotech_pharma_df)}")
    print(biotech_pharma_df[['symbol', 'name']].head())

    # Persist the company list
    biotech_pharma_df.to_csv("yfinance_drug_industry_list.csv", index=False)

    # --- Step 3: Iterate over every company and collect trial data ---
    all_results = []
    for _, row in biotech_pharma_df.iterrows():
        clean_name = clean_company_name(row['name'])

        print(f"Searching trials for: {clean_name}...")
        studies = fetch_trials(clean_name)

        for study in studies:
            protocol = study.get("protocolSection", {})
            all_results.append({
                "Ticker": row['symbol'],
                "Company": clean_name,
                "NCT_ID": protocol.get("identificationModule", {}).get("nctId"),
                "Title": protocol.get("identificationModule", {}).get("briefTitle"),
                "Phase": ", ".join(protocol.get("designModule", {}).get("phases", [])),
                "Status": protocol.get("statusModule", {}).get("overallStatus")
            })

        # Respect ClinicalTrials.gov rate limits
        time.sleep(0.5)

    # --- Step 4: Save the combined results ---
    final_df = pd.DataFrame(all_results)

    if max_market_cap_in_billions is not None:
        output_file = f"biotech_pipeline_{max_market_cap_in_billions}B_cap_2026.csv"
    else:
        output_file = "master_biotech_pipeline_2026.csv"

    final_df.to_csv(output_file, index=False)
    print(f"Done — {len(final_df)} trials saved to {output_file}")


if __name__ == "__main__":
    generate_biotech_trials(max_market_cap_in_billions=10)  # Example: filter for companies with market cap <= $10B