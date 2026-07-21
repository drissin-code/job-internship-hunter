import os
import json
import re
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, List, Dict, Optional

from fetch_jobs import fetch_jobs, save_jobs
from match_jobs import rank_jobs, SKILLS, CORE_SKILLS, TARGET_SKILLS

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOP_N = 2  # how many top matches to summarize


class PipelineState(TypedDict):
    # Inputs (set before invoking the graph)
    countries: List[str]
    what: str
    where: str
    skills: List[str]
    core_skills: List[str]
    target_skills: List[str]

    # Outputs (filled in by the pipeline as it runs)
    jobs: List[Dict]
    ranked: List[Dict]
    summaries: List[Dict]


# ---- Node 1: Search ----
def search_node(state: PipelineState) -> PipelineState:
    print("[Search Agent] Fetching jobs from Adzuna...")
    jobs = fetch_jobs(
        countries=state.get("countries"),
        what=state.get("what"),
        where=state.get("where"),
    )
    save_jobs(jobs)
    return {**state, "jobs": jobs}


# ---- Node 2: Match/Filter ----
def match_node(state: PipelineState) -> PipelineState:
    print("[Match Agent] Scoring jobs against your skills...")
    skills = state.get("skills") or SKILLS
    core_skills = state.get("core_skills") or CORE_SKILLS
    target_skills = state.get("target_skills") or TARGET_SKILLS

    ranked = rank_jobs(state["jobs"], skills, core_skills, target_skills)
    top_matches = ranked[:TOP_N]
    return {**state, "ranked": top_matches}


# ---- Helper: extract plain text from a Gemini response ----
def _extract_text(response) -> str:
    if isinstance(response.content, list):
        # Newer Gemini models return content as a list of structured
        # blocks (e.g. {"type": "text", "text": "..."}) rather than
        # a plain string — pull just the text out of those blocks.
        return "".join(
            block.get("text", "") for block in response.content
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    return (response.content or "").strip()


# ---- Helper: defensively parse JSON out of a Gemini response ----
def _parse_job_json(raw_text: str) -> Optional[Dict]:
    """
    Gemini sometimes wraps JSON in ```json fences, adds stray text before/after,
    or occasionally returns slightly malformed JSON. This tries a few fallbacks
    before giving up, same pattern as resume_parser.py.
    """
    if not raw_text:
        return None

    text = raw_text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find the first {...} block in the text and parse just that
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    return None


# ---- Node 3: Summarize (now with why_matched + missing_skills) ----
def summarize_node(state: PipelineState) -> PipelineState:
    print("[Summarizer Agent] Writing summaries for top matches...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-3.1-flash-lite",
        google_api_key=GEMINI_API_KEY,
        request_timeout=30,  # don't let a single call hang forever
    )

    user_skills = state.get("skills") or SKILLS

    summaries = []
    total = len(state["ranked"])
    for i, job in enumerate(state["ranked"]):
        prompt = (
            "You are a job-matching assistant for a student job hunter. "
            "Given a job listing and the candidate's current skills, respond with "
            "ONLY a raw JSON object (no markdown fences, no extra text) with exactly "
            "these three keys:\n"
            '  "summary": a plain 2-sentence summary of the job, concrete and no fluff.\n'
            '  "why_matched": 1 short sentence explaining specifically which of the '
            "candidate's skills line up with this job, referencing the candidate's "
            "actual skills, not generic praise.\n"
            '  "missing_skills": a JSON array of specific skills/technologies this job '
            "wants that are NOT in the candidate's current skill list. Use short skill "
            "names (e.g. \"Docker\", \"SQL\"), not full sentences. Empty array if none.\n\n"
            f"Candidate's current skills: {', '.join(user_skills)}\n\n"
            f"Job Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Description: {job['description'][:800]}"
        )

        # Fallback values used if the call or parsing fails
        summary_text = f"{job['title']} at {job['company']} in {job['location']}. (AI summary unavailable — quota limit reached.)"
        why_matched_text = "Matched based on overlapping skills (details unavailable)."
        missing_skills_list: List[str] = []

        print(f"  -> Calling Gemini for job {i+1}/{total}: {job['title']}")
        try:
            response = llm.invoke(prompt)
            print(f"  <- Got response for job {i+1}/{total}")

            raw_text = _extract_text(response)
            parsed = _parse_job_json(raw_text)

            if parsed is None:
                raise ValueError("Could not parse JSON from model response")

            summary_text = str(parsed.get("summary") or summary_text).strip()
            why_matched_text = str(parsed.get(
                "why_matched") or why_matched_text).strip()

            raw_missing = parsed.get("missing_skills")
            if isinstance(raw_missing, list):
                missing_skills_list = [str(s).strip()
                                       for s in raw_missing if str(s).strip()]
            # if it's not a list (model mistake), just keep the empty fallback

            if not summary_text:
                raise ValueError("Empty summary returned")

        except Exception as e:
            print(
                f"  Warning: summary failed for '{job['title']}' ({e.__class__.__name__}: {e}) — using fallback")

        summaries.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "match_score": job["match_score"],
            "matched_core": job.get("matched_core", []),
            "matched_target": job.get("matched_target", []),
            "url": job["url"],
            "summary": summary_text,
            "why_matched": why_matched_text,
            "missing_skills": missing_skills_list,
        })

        if i < total - 1:
            # brief pause between calls to respect free-tier rate limits
            time.sleep(5)

    return {**state, "summaries": summaries}


def build_graph():
    graph = StateGraph(PipelineState)
    graph.add_node("search", search_node)
    graph.add_node("match", match_node)
    graph.add_node("summarize", summarize_node)

    graph.set_entry_point("search")
    graph.add_edge("search", "match")
    graph.add_edge("match", "summarize")
    graph.add_edge("summarize", END)

    return graph.compile()


def run_pipeline(
    countries: Optional[List[str]] = None,
    what: Optional[str] = None,
    where: Optional[str] = None,
    skills: Optional[List[str]] = None,
    core_skills: Optional[List[str]] = None,
    target_skills: Optional[List[str]] = None,
) -> List[Dict]:
    """
    Convenience entry point for app.py. Builds the graph, runs it with the
    given inputs, and returns the final list of summarized job matches.
    Any argument left as None falls back to the defaults baked into
    fetch_jobs.py / match_jobs.py.
    """
    app = build_graph()
    initial_state: PipelineState = {
        "countries": countries,
        "what": what,
        "where": where,
        "skills": skills,
        "core_skills": core_skills,
        "target_skills": target_skills,
        "jobs": [],
        "ranked": [],
        "summaries": [],
    }
    result = app.invoke(initial_state)
    return result["summaries"]


def print_results(summaries):
    print(f"\n{'='*60}")
    print(f"Top {len(summaries)} Job Matches")
    print(f"{'='*60}\n")
    for i, job in enumerate(summaries, start=1):
        print(f"{i}. {job['title']} — {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Match score: {job['match_score']}")
        print(f"   Summary: {job['summary']}")
        print(f"   Why matched: {job['why_matched']}")
        if job['missing_skills']:
            print(f"   Missing skills: {', '.join(job['missing_skills'])}")
        print(f"   Link: {job['url']}\n")


if __name__ == "__main__":
    summaries = run_pipeline()
    print_results(summaries)
