import json
import re

JOBS_FILE = "jobs.json"

# Skills you currently have hands-on experience with
CORE_SKILLS = [
    "python",
    "api",
    "rest api",
    "git",
    "github",
    "json",
    "langchain",
    "langgraph",
    "crewai",
    "agentic ai",
]

# Skills you're actively learning but don't have hands-on experience with yet —
# tracked separately so you can see demand for skills you're about to build
TARGET_SKILLS = [
    "sql",
    "machine learning",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "flask",
    "fastapi",
]

SKILLS = CORE_SKILLS + TARGET_SKILLS


def load_jobs(filepath=JOBS_FILE):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def score_job(job, skills, core_skills=None, target_skills=None):
    """Return (score, matched_core, matched_target) based on keyword hits
    in the job title + description. core_skills/target_skills default to
    the module-level lists if not provided (keeps CLI usage unchanged)."""
    core_skills = core_skills if core_skills is not None else CORE_SKILLS
    target_skills = target_skills if target_skills is not None else TARGET_SKILLS

    text = f"{job.get('title', '')} {job.get('description', '')}".lower()
    matched = [
        skill for skill in skills
        if re.search(r"\b" + re.escape(skill.lower()) + r"\b", text)
    ]
    matched_core = [s for s in matched if s in core_skills]
    matched_target = [s for s in matched if s in target_skills]
    return len(matched), matched_core, matched_target


def rank_jobs(jobs, skills, core_skills=None, target_skills=None):
    scored = []
    for job in jobs:
        score, matched_core, matched_target = score_job(
            job, skills, core_skills, target_skills)
        scored.append({
            **job,
            "match_score": score,
            "matched_core": matched_core,
            "matched_target": matched_target,
        })

    return sorted(scored, key=lambda j: j["match_score"], reverse=True)


def print_ranked(ranked, top_n=10):
    print(f"Top {min(top_n, len(ranked))} matches:\n")
    for i, job in enumerate(ranked[:top_n], start=1):
        print(f"{i}. {job['title']} — {job['company']}")
        print(f"   Location: {job['location']}")
        print(f"   Match score: {job['match_score']}")
        print(
            f"   Core skills matched: {', '.join(job['matched_core']) or 'none'}")
        print(
            f"   Target skills matched: {', '.join(job['matched_target']) or 'none'}")
        print(f"   Link: {job['url']}\n")


if __name__ == "__main__":
    jobs = load_jobs()
    ranked = rank_jobs(jobs, SKILLS)
    print_ranked(ranked)
