"""Clinical trials module — fetches and parses trial data from ClinicalTrials.gov v2 API."""

import time

import requests

CLINICAL_TRIALS_URL = "https://clinicaltrials.gov/api/v2/studies"

# Delay between requests to respect ClinicalTrials.gov rate limits
REQUEST_DELAY = 0.5


def clean_company_name(name):
    """Strip common corporate suffixes for better search matching."""
    for suffix in [", Inc.", " Inc.", " Corp.", " PLC", " Ltd.", " Incorporated",
                   " International", " Holdings", " Therapeutics", " Biosciences"]:
        name = name.replace(suffix, "")
    return name.strip()


def fetch_trials(company_name, statuses=None, page_size=50):
    """Query ClinicalTrials.gov for trials sponsored by the given company.

    Args:
        company_name: Sponsor name to search for.
        statuses: List of trial statuses to filter. Defaults to
                  ["RECRUITING", "NOT_YET_RECRUITING"].
        page_size: Max results per request.

    Returns:
        List of parsed trial dicts with keys:
            nct_id, title, phase, status, conditions, enrollment_count,
            locations_count, start_date, has_results
    """
    if statuses is None:
        statuses = ["RECRUITING", "NOT_YET_RECRUITING"]

    params = {
        "query.spons": company_name,
        "filter.overallStatus": "|".join(statuses),
        "pageSize": page_size,
        "format": "json",
    }
    try:
        response = requests.get(CLINICAL_TRIALS_URL, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"  Error fetching trials for {company_name}: {e}")
        return []

    parsed = []
    for study in data.get("studies", []):
        protocol = study.get("protocolSection", {})
        id_module = protocol.get("identificationModule", {})
        design_module = protocol.get("designModule", {})
        status_module = protocol.get("statusModule", {})
        conditions_module = protocol.get("conditionsModule", {})
        contacts_module = protocol.get("contactsLocationsModule", {})

        enrollment_info = design_module.get("enrollmentInfo", {})
        locations = contacts_module.get("locations", [])
        start_date_struct = status_module.get("startDateStruct", {})

        parsed.append({
            "nct_id": id_module.get("nctId"),
            "title": id_module.get("briefTitle"),
            "phase": ", ".join(design_module.get("phases", [])),
            "status": status_module.get("overallStatus"),
            "conditions": conditions_module.get("conditions", []),
            "enrollment_count": enrollment_info.get("count"),
            "locations_count": len(locations) if locations else 0,
            "start_date": start_date_struct.get("date"),
            "has_results": study.get("hasResults", False),
        })

    return parsed


def fetch_all_trials(companies_df, statuses=None):
    """Fetch trials for every company in the DataFrame.

    Args:
        companies_df: DataFrame with at least 'symbol' and 'name' columns.
        statuses: Optional list of trial statuses to filter.

    Returns:
        List of dicts, each representing one trial row with company info attached.
    """
    all_results = []
    for _, row in companies_df.iterrows():
        clean_name = clean_company_name(row["name"])
        print(f"Searching trials for: {clean_name}...")

        trials = fetch_trials(clean_name, statuses=statuses)
        for trial in trials:
            trial["ticker"] = row["symbol"]
            trial["company"] = clean_name
            all_results.append(trial)

        time.sleep(REQUEST_DELAY)

    return all_results
