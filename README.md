# Job & Internship Hunter

An AI-powered, multi-agent job search assistant that takes your resume, searches job listings across multiple countries, ranks them against your actual skills, and generates plain-English summaries — so you spend less time scrolling job boards and more time applying to roles that actually fit.

## The Problem

Job hunting means manually checking dozens of job boards across different countries, reading through hundreds of listings, and trying to figure out which ones are worth your time. It's repetitive and easy to miss good opportunities buried in noise.

## What It Does

This tool automates that process end-to-end, from resume to ranked results, orchestrated as a multi-agent pipeline built with LangGraph and wrapped in a Streamlit interface:

1. **Resume Parser** — extracts skills, experience, education, and projects from an uploaded PDF resume using `pdfplumber` for text extraction and Gemini for structured extraction, so you don't have to hardcode your own skill list
2. **Search Agent** — queries the [Adzuna API](https://developer.adzuna.com/) across multiple countries (India, US, UK, Germany) for relevant job listings, and flags any postings from target companies you specify
3. **Match Agent** — scores every listing against your skills profile (extracted from your resume, or a configurable default), and ranks the top matches
4. **Summarizer Agent** — uses Google's Gemini API to write a short, plain-English summary of each top match, so you can decide at a glance whether it's worth reading further

Results are persisted to `jobs.json` with automatic deduplication, so re-running the tool only adds genuinely new listings.

## Tech Stack

- Python 3.14
- Streamlit — user interface
- LangGraph — multi-agent orchestration
- Google Gemini API (via `langchain-google-genai` and `google-generativeai`) — resume extraction + summarization
- Adzuna API — job listing data source
- pdfplumber — PDF text extraction
- python-dotenv — secure credential management

## Architecture
[Resume Parser] → [Search Agent] → [Match Agent] → [Summarizer Agent] → Ranked, Summarized Results

Each agent is a standalone, testable function wired into a LangGraph `StateGraph`. This means each stage can be run, tested, and debugged independently before being composed into the full pipeline — see `resume_parser.py`, `fetch_jobs.py`, `match_jobs.py`, and `agent_pipeline.py`.

The pipeline is built to degrade gracefully: if the Gemini API is unavailable or rate-limited mid-run, the Summarizer Agent falls back to a plain-text summary instead of crashing the whole search, and the UI surfaces a clear, non-technical message instead of a stack trace.

## Setup

1. Clone the repo and create a virtual environment:
   python -m venv venv
venv\Scripts\Activate.ps1 # Windows
2. Install dependencies:
pip install -r requirements.txt
3. Create a `.env` file in the project root:
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
GEMINI_API_KEY=your_gemini_api_key
Get free Adzuna credentials at [developer.adzuna.com](https://developer.adzuna.com/), and a free Gemini API key at [Google AI Studio](https://aistudio.google.com/).

## Usage

**Streamlit app (recommended):**
streamlit run app.py

Upload your resume, set your search filters (countries, role, target companies) in the sidebar, click **Parse Resume** to extract your skills, then **Run Search** to get ranked, summarized job matches.

**Command line (no UI):**
python agent_pipeline.py


Or run individual stages:

python fetch_jobs.py # fetch and save listings only
python match_jobs.py # rank already-saved listings against default skills
## Customization

- **Skills:** if not using resume upload, edit `CORE_SKILLS` and `TARGET_SKILLS` in `match_jobs.py` to reflect your own profile
- **Search scope:** edit `COUNTRIES` and `WHAT` in `fetch_jobs.py`, or set them directly from the Streamlit sidebar
- **Target companies:** edit `TARGET_COMPANIES` in `fetch_jobs.py`, or set them from the sidebar

## Known Limitations

- Adzuna aggregates from job boards, not every company's own careers page — large MNCs (e.g. NVIDIA, Salesforce) that post primarily on their own sites may not appear
- **Gemini's free tier has daily and per-minute rate limits that are easy to hit during active development or testing.** When the quota is exceeded, resume parsing returns an empty skills list (with a clear warning in the UI) and job summaries fall back to plain text — the app stays usable, but the AI-generated content is temporarily degraded until quota resets
- No UAE/Dubai coverage — Adzuna doesn't support that region
- Resume parsing works best with text-based PDFs; scanned/image-only resumes won't extract correctly since `pdfplumber` reads text layers, not images

## What's Next

- **Missing-skills gap analysis** — for each job match, explicitly call out which required skills are missing from the resume, not just a match score
- **Aggregate skill recommendations** — across all matched jobs, surface the 2-3 skills that would unlock the most additional opportunities
- **Strengths/weaknesses analysis** — a standalone resume review, independent of any specific job posting
- **Deployment** — host on Streamlit Community Cloud so the app is usable via a link, not just localhost
- **Direct scraping/integration** for target companies not covered by Adzuna

---

Built by [Drissin](https://github.com/drissin-code) as part of an AI/ML learning project — exploring agentic AI design (multi-agent orchestration, tool use, graceful fallback handling, context engineering) alongside practical job-search tooling.
