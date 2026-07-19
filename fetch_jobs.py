import os
import requests
from dotenv import load_dotenv

# Load API credentials from .env
load_dotenv()

APP_ID = os.getenv("ADZUNA_APP_ID")
APP_KEY = os.getenv("ADZUNA_APP_KEY")

# Adzuna API config
COUNTRY = "in"  # country code, e.g. "in" for India, "gb" for UK, "us" for USA
WHAT = "software engineer"  # job title/keywords to search
WHERE = "kerala"  # location to search in
RESULTS_PER_PAGE = 10


def fetch_jobs():
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
        return

    data = response.json()
    jobs = data.get("results", [])

    print(f"Found {len(jobs)} jobs for '{WHAT}' in '{WHERE}'\n")

    for i, job in enumerate(jobs, start=1):
        title = job.get("title", "N/A")
        company = job.get("company", {}).get("display_name", "N/A")
        location = job.get("location", {}).get("display_name", "N/A")
        url = job.get("redirect_url", "N/A")

        print(f"{i}. {title}")
        print(f"   Company: {company}")
        print(f"   Location: {location}")
        print(f"   Link: {url}\n")


if __name__ == "__main__":
    fetch_jobs()
