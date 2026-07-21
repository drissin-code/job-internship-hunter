import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRIES = ["in", "us", "gb", "de"]  # India, USA, UK, Germany
WHAT = "python developer"
WHERE = ""  # leave blank to search the whole country
RESULTS_PER_PAGE = 30  # higher, since we're filtering afterward
OUTPUT_FILE = "jobs.json"


def fetch_jobs(countries=None, what=None, where=None):
    """Fetch jobs from Adzuna across multiple countries and return a list of structured job dicts.
    Falls back to the module-level defaults if no arguments are passed (keeps CLI usage unchanged)."""
    countries = countries if countries is not None else COUNTRIES
    what = what if what is not None else WHAT
    where = where if where is not None else WHERE

    all_jobs = []

    for country in countries:
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": APP_ID,
            "app_key": APP_KEY,
            "results_per_page": RESULTS_PER_PAGE,
            "what": what,
            "content-type": "application/json",
        }
        if where:
            params["where"] = where

        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Error fetching from {country}: {response.status_code}")
            print(response.text)
            continue

        data = response.json()
        raw_jobs = data.get("results", [])

        for job in raw_jobs:
            all_jobs.append({
                "id": job.get("id"),
                "title": job.get("title", "N/A"),
                "company": job.get("company", {}).get("display_name", "N/A"),
                "location": job.get("location", {}).get("display_name", "N/A"),
                "country": country,
                "description": job.get("description", ""),
                "salary_min": job.get("salary_min"),
                "salary_max": job.get("salary_max"),
                "url": job.get("redirect_url", "N/A"),
                "fetched_at": datetime.now().isoformat(),
            })

        print(f"  {country.upper()}: fetched {len(raw_jobs)} job(s)")

    return all_jobs


def save_jobs(jobs, filepath=OUTPUT_FILE):
    """Save jobs to a JSON file, merging with existing entries and deduping by id."""
    existing = []
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            existing = json.load(f)

    existing_ids = {job["id"] for job in existing}
    new_jobs = [job for job in jobs if job["id"] not in existing_ids]

    combined = existing + new_jobs

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(combined, f, indent=2, ensure_ascii=False)

    print(
        f"Saved {len(new_jobs)} new job(s). Total in {filepath}: {len(combined)}")


if __name__ == "__main__":
    print(f"Fetching '{WHAT}' jobs across: {', '.join(COUNTRIES)}\n")
    jobs = fetch_jobs()
    print(f"\nFetched {len(jobs)} job(s) total.\n")
    save_jobs(jobs)
