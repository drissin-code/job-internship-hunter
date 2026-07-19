import os
import time
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import TypedDict, List, Dict

from fetch_jobs import fetch_jobs, flag_target_companies, save_jobs
from match_jobs import rank_jobs, SKILLS

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TOP_N = 5  # how many top matches to summarize


class PipelineState(TypedDict):
    jobs: List[Dict]
    ranked: List[Dict]
    summaries: List[Dict]


# ---- Node 1: Search ----
def search_node(state: PipelineState) -> PipelineState:
    print("[Search Agent] Fetching jobs from Adzuna...")
    jobs = fetch_jobs()
    jobs = flag_target_companies(jobs, [
        "nvidia", "tcs", "tata consultancy", "infosys", "cognizant", "okta", "salesforce",
    ])
    save_jobs(jobs)
    return {"jobs": jobs, "ranked": [], "summaries": []}


# ---- Node 2: Match/Filter ----
def match_node(state: PipelineState) -> PipelineState:
    print("[Match Agent] Scoring jobs against your skills...")
    ranked = rank_jobs(state["jobs"], SKILLS)
    top_matches = ranked[:TOP_N]
    return {**state, "ranked": top_matches}


# ---- Node 3: Summarize ----
def summarize_node(state: PipelineState) -> PipelineState:
    print("[Summarizer Agent] Writing summaries for top matches...")
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

    summaries = []
    for i, job in enumerate(state["ranked"]):
        prompt = (
            f"Summarize this job listing in 2 short sentences for a student "
            f"job-hunting assistant. Be concrete and plain, no fluff.\n\n"
            f"Title: {job['title']}\n"
            f"Company: {job['company']}\n"
            f"Location: {job['location']}\n"
            f"Description: {job['description'][:800]}"
        )
        try:
            response = llm.invoke(prompt)
            summary_text = response.content
        except Exception as e:
            print(
                f"  Warning: summary failed for '{job['title']}' ({e.__class__.__name__}) — using fallback")
            summary_text = f"{job['title']} at {job['company']} in {job['location']}. (AI summary unavailable — quota limit reached.)"

        summaries.append({
            "title": job["title"],
            "company": job["company"],
            "location": job["location"],
            "match_score": job["match_score"],
            "url": job["url"],
            "summary": summary_text,
        })

        if i < len(state["ranked"]) - 1:
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


def print_results(summaries):
    print(f"\n{'='*60}")
    print(f"Top {len(summaries)} Job Matches")
    print(f"{'='*60}\n")
    for i, job in enumerate(summaries, start=1):
        print(f"{i}. {job['title']} — {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Match score: {job['match_score']}")
        print(f"   Summary: {job['summary']}")
        print(f"   Link: {job['url']}\n")


if __name__ == "__main__":
    app = build_graph()
    result = app.invoke({"jobs": [], "ranked": [], "summaries": []})
    print_results(result["summaries"])
