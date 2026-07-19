# Job & Internship Hunter

An AI-powered, multi-agent job search assistant that searches job listings across multiple countries, ranks them against your actual skills, and generates plain-English summaries — so you spend less time scrolling job boards and more time applying to roles that actually fit.

## The Problem

Job hunting means manually checking dozens of job boards across different countries, reading through hundreds of listings, and trying to figure out which ones are worth your time. It's repetitive and easy to miss good opportunities buried in noise.

## What It Does

This tool automates that process in three stages, orchestrated as a multi-agent pipeline built with **LangGraph**:

1. **Search Agent** — queries the [Adzuna API](https://developer.adzuna.com/) across multiple countries (India, US, UK, Germany) for relevant job listings, and flags any postings from target companies
2. **Match Agent** — scores every listing against a configurable skills profile (core skills vs. skills you're actively learning), and ranks the top matches
3. **Summarizer Agent** — uses Google's Gemini API to write a short, plain-English summary of each top match, so you can decide at a glance whether it's worth reading further

Results are persisted to `jobs.json` with automatic deduplication, so re-running the tool only adds genuinely new listings.

## Tech Stack

- **Python 3.14**
- **LangGraph** — multi-agent orchestration
- **Google Gemini API** (via `langchain-google-genai`) — summarization
- **Adzuna API** — job listing data source
- **python-dotenv** — secure credential management

## Architecture
[Search Agent] → [Match Agent] → [Summarizer Agent] → Ranked, Summarized Results
Each agent is a standalone, testable function wired into a LangGraph `StateGraph`. This means each stage can be run, tested, and debugged independently before being composed into the full pipeline — see `fetch_jobs.py`, `match_jobs.py`, and `agent_pipeline.py`.

## Setup

1. Clone the repo and create a virtual environment:
```bash
   python -m venv venv
   venv\Scripts\Activate.ps1   # Windows
```

2. Install dependencies:
```bash
   pip install -r requirements.txt
```

3. Create a `.env` file in the project root:
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GEMINI_API_KEY=your_gemini_api_key
Get free Adzuna credentials at [developer.adzuna.com](https://developer.adzuna.com/), and a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).

## Usage

Run the full pipeline:
```bash
python agent_pipeline.py
```

Or run individual stages:
```bash
python fetch_jobs.py    # fetch and save listings only
python match_jobs.py    # rank already-saved listings against your skills
```

## Customization

- **Skills:** edit `CORE_SKILLS` and `TARGET_SKILLS` in `match_jobs.py` to reflect your own profile
- **Search scope:** edit `COUNTRIES` and `WHAT` in `fetch_jobs.py` to change which countries/roles are searched
- **Target companies:** edit `TARGET_COMPANIES` in `fetch_jobs.py`

## Known Limitations

- Adzuna aggregates from job boards, not every company's own careers page — large MNCs (e.g. NVIDIA, Salesforce) that post primarily on their own sites may not appear
- Gemini's free tier has daily/per-minute rate limits; the Summarizer Agent falls back to a plain-text summary if the quota is exceeded, rather than failing the whole pipeline
- No UAE/Dubai coverage — Adzuna doesn't support that region

## What's Next

- Resume upload support (parse skills automatically instead of hardcoding them)
- Streamlit UI for non-technical use
- Direct scraping/integration for target companies not covered by Adzuna

---

Built by [Drissin](https://github.com/drissin-code) as part of an AI/ML portfolio.