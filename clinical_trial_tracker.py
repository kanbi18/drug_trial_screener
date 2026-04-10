import yfinance as yf
import pandas as pd
import requests
import time

# yfinance industry keys for biotech & pharma sectors
drug_company_sectors = [
    "biotechnology",
    "drug-manufacturers-general",
    "drug-manufacturers-specialty-generic"
]

def get_public_biotech_list():
    """Fetch top companies from each drug/biotech sector via yfinance.
    Returns a deduplicated DataFrame with the ticker symbol as a column."""
    complete_drug_companies = []

    for sector_name in drug_company_sectors:
        print(f"Fetching companies for sector: {sector_name}...")
        try:
            drug_sector = yf.Industry(sector_name)
            top_sector_companies = drug_sector.top_companies

            if top_sector_companies is not None and not top_sector_companies.empty:
                complete_drug_companies.append(top_sector_companies)
                print(f"  Found {len(top_sector_companies)} companies.")
            else:
                print(f"  No data returned for {sector_name}.")

        except Exception as e:
            print(f"  Error accessing {sector_name}: {e}")

    if not complete_drug_companies:
        return pd.DataFrame()

    # Combine all sectors; the ticker is the index, so deduplicate on it
    combined = pd.concat(complete_drug_companies)
    combined = combined[~combined.index.duplicated(keep='first')]

    # Promote the ticker index to a regular 'symbol' column for downstream use
    combined = combined.reset_index(names='symbol')
    return combined

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
    # --- Step 1: Build the company list from yfinance ---
    biotech_pharma_df = get_public_biotech_list()

    if biotech_pharma_df.empty:
        print("No companies found. Exiting.")
        return

    # --- Step 2: Filter by market cap if requested ---
    if max_market_cap_in_billions is not None:
        threshold = max_market_cap_in_billions * 1e9
        print(f"Fetching market caps to filter for <= ${max_market_cap_in_billions}B...")
        max_market_cap_in_billionss = {}
        for symbol in biotech_pharma_df['symbol']:
            try:
                info = yf.Ticker(symbol).fast_info
                max_market_cap_in_billionss[symbol] = info.get('marketCap', info.get('max_market_cap_in_billions', 0)) or 0
            except Exception:
                max_market_cap_in_billionss[symbol] = 0
        biotech_pharma_df['max_market_cap_in_billions'] = biotech_pharma_df['symbol'].map(max_market_cap_in_billionss)
        biotech_pharma_df = biotech_pharma_df[biotech_pharma_df['max_market_cap_in_billions'] <= threshold]
        print(f"  {len(biotech_pharma_df)} companies below ${max_market_cap_in_billions}B market cap.")

    if biotech_pharma_df.empty:
        print("No companies remain after filtering. Exiting.")
        return

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