import os
import json
import requests
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

COUNTRY = "in"
WHAT = "software engineer"
WHERE = "kerala"
RESULTS_PER_PAGE = 10
OUTPUT_FILE = "jobs.json"


def fetch_jobs():
    """Fetch jobs from Adzuna and return a list of structured job dicts."""
    url = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}/search/1"
    params = {
        "app_id": APP_ID,
        "app_key": APP_KEY,
        "results_per_page": RESULTS_PER_PAGE,
        "what": WHAT,
        "where": WHERE,
        "content-type": "application/json",
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return []

    data = response.json()
    raw_jobs = data.get("results", [])

    jobs = []
    for job in raw_jobs:
        jobs.append({
            "id": job.get("id"),
            "title": job.get("title", "N/A"),
            "company": job.get("company", {}).get("display_name", "N/A"),
            "location": job.get("location", {}).get("display_name", "N/A"),
            "description": job.get("description", ""),
            "salary_min": job.get("salary_min"),
            "salary_max": job.get("salary_max"),
            "url": job.get("redirect_url", "N/A"),
            "fetched_at": datetime.now().isoformat(),
        })

    return jobs


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
    jobs = fetch_jobs()
    print(f"Fetched {len(jobs)} job(s) from Adzuna.\n")
    save_jobs(jobs)
