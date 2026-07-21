"""
Job & Internship Hunter — Streamlit UI Shell
Step 1: Streamlit UI shell — DONE
Step 2: Resume upload + skill extraction (pdfplumber + Gemini) — DONE
Step 3: Country/role/target-company form inputs wired to the pipeline — DONE
Step 4: Run button connected to agent_pipeline.py — DONE
Step 5: Job cards show why_matched + missing_skills (v2 career coaching) — DONE
Step 6: Aggregate "skills to focus on" panel across all matched jobs — DONE
Step 7: Grounded strength/gap insight line (pure logic, no extra API call) — DONE
Step 8: Removed target-company selector (Adzuna rarely surfaces them) — DONE

Run with: streamlit run app.py
"""

import streamlit as st
from collections import Counter
from resume_parser import parse_resume
from agent_pipeline import run_pipeline

# ---------------------------------------------------------------------------
# Static reference data
# ---------------------------------------------------------------------------
COUNTRY_NAME_TO_CODE = {
    "India": "in",
    "US": "us",
    "UK": "gb",
    "Germany": "de",
}
COUNTRIES = list(COUNTRY_NAME_TO_CODE.keys())

# Fallback skills used only if no resume has been parsed yet
DEFAULT_CORE_SKILLS = ["Python", "API", "LangChain", "LangGraph", "CrewAI"]
DEFAULT_TARGET_SKILLS = ["SQL", "ML", "TensorFlow",
                         "PyTorch", "scikit-learn", "Flask", "FastAPI"]

st.set_page_config(page_title="Job & Internship Hunter",
                   page_icon="🎯", layout="wide")

if "resume_data" not in st.session_state:
    st.session_state.resume_data = None
if "results" not in st.session_state:
    st.session_state.results = None
if "run_error" not in st.session_state:
    st.session_state.run_error = None

st.title("🎯 Job & Internship Hunter")
st.caption(
    "AI/ML-powered job matching — multi-agent pipeline with LangGraph + Gemini")

# ---------------------------------------------------------------------------
# Sidebar — search form
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Search Settings")

    selected_countries = st.multiselect(
        "Countries", options=COUNTRIES, default=COUNTRIES
    )

    role_query = st.text_input("Role / keywords", value="AI ML Intern")

    st.divider()

    st.subheader("Resume")
    resume_file = st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        help="We'll extract your skills, experience, education, and projects.",
    )

    if resume_file is not None:
        if st.button("📄 Parse Resume", use_container_width=True):
            with st.spinner("Reading your resume..."):
                st.session_state.resume_data = parse_resume(resume_file)
            if st.session_state.resume_data and st.session_state.resume_data.get("skills"):
                st.success("Resume parsed!")
            else:
                st.warning(
                    "Resume uploaded, but we couldn't extract skills from it. You can still run a search using default skills.")

    st.divider()
    run_clicked = st.button(
        "🚀 Run Search", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Run the pipeline when the button is clicked
# ---------------------------------------------------------------------------
if run_clicked:
    if not selected_countries:
        st.session_state.run_error = "Please select at least one country before running a search."
        st.session_state.results = None
    else:
        country_codes = [COUNTRY_NAME_TO_CODE[c] for c in selected_countries]

        # Use resume-extracted skills if available, otherwise fall back to defaults
        if st.session_state.resume_data and st.session_state.resume_data.get("skills"):
            resume_skills = [s.lower()
                             for s in st.session_state.resume_data["skills"]]
            core_skills = resume_skills
            target_skills = []  # everything from the resume counts as "have it"
            skills = resume_skills
        else:
            core_skills = [s.lower() for s in DEFAULT_CORE_SKILLS]
            target_skills = [s.lower() for s in DEFAULT_TARGET_SKILLS]
            skills = core_skills + target_skills

        with st.spinner("Searching for jobs, matching against your skills, and writing summaries... this can take a minute."):
            try:
                results = run_pipeline(
                    countries=country_codes,
                    what=role_query,
                    where="",
                    skills=skills,
                    core_skills=core_skills,
                    target_skills=target_skills,
                )
                st.session_state.results = results
                st.session_state.run_error = None
            except Exception as e:
                st.session_state.results = None
                error_text = str(e).lower()
                if "quota" in error_text or "429" in error_text or "resourceexhausted" in error_text:
                    st.session_state.run_error = (
                        "We've hit today's limit on AI summaries. "
                        "Please try again later, or check back tomorrow."
                    )
                else:
                    st.session_state.run_error = (
                        "Something went wrong while searching for jobs. Please try again in a bit."
                    )
                print(f"[app] Pipeline error: {e}")

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Results")

    if st.session_state.run_error:
        st.error(st.session_state.run_error)
    elif st.session_state.results:
        for job in st.session_state.results:
            with st.container(border=True):
                header_col, badge_col = st.columns([4, 1])
                with header_col:
                    st.markdown(f"**{job['title']}** — {job['company']}")
                    st.caption(job["location"])
                with badge_col:
                    st.metric("Match", job["match_score"])

                st.write(job["summary"])

                # Why this matched (v2)
                if job.get("why_matched"):
                    st.markdown(
                        f"✅ **Why this matched:** {job['why_matched']}")

                # Missing skills, shown as tags (v2)
                missing = job.get("missing_skills") or []
                if missing:
                    tags_html = " ".join(
                        f'<span style="background-color:#3a2f1a; color:#f5c66b; '
                        f'padding:2px 10px; border-radius:12px; font-size:0.85em; '
                        f'margin-right:6px;">{skill}</span>'
                        for skill in missing
                    )
                    st.markdown(
                        f"📌 **Skills to grow:** {tags_html}", unsafe_allow_html=True)

                st.markdown(f"[View listing]({job['url']})")
    else:
        st.write(
            "Set your filters in the sidebar and click **Run Search** to see results here.")

with col2:
    st.subheader("Your Skills")

    if st.session_state.resume_data and st.session_state.resume_data.get("skills"):
        data = st.session_state.resume_data

        st.markdown("**Skills:**")
        st.write(", ".join(data["skills"]))

        if data.get("experience"):
            st.markdown("**Experience:**")
            for exp in data["experience"]:
                st.write(
                    f"- {exp.get('title', '')} @ {exp.get('company', '')} ({exp.get('duration', '')})")

        if data.get("education"):
            st.markdown("**Education:**")
            for edu in data["education"]:
                st.write(
                    f"- {edu.get('degree', '')}, {edu.get('institution', '')} ({edu.get('year', '')})")

        if data.get("projects"):
            st.markdown("**Projects:**")
            for proj in data["projects"]:
                st.write(
                    f"- {proj.get('name', '')}: {proj.get('description', '')}")
    else:
        st.markdown("**Core (hands-on):**")
        st.write(", ".join(DEFAULT_CORE_SKILLS))
        st.markdown("**Target (learning):**")
        st.write(", ".join(DEFAULT_TARGET_SKILLS))
        st.caption(
            "⬆️ Upload and parse a resume to replace this with your actual data.")

    # -----------------------------------------------------------------
    # Aggregate "Skills to focus on" panel (v2) — built from missing_skills
    # across all matched jobs in the current results, no extra API call.
    # -----------------------------------------------------------------
    if st.session_state.results:
        # --- Tally what's MISSING across all matched jobs ---
        all_missing = []
        for job in st.session_state.results:
            all_missing.extend(job.get("missing_skills") or [])

        missing_display_form = {}
        missing_counts = Counter()
        for skill in all_missing:
            key = skill.strip().lower()
            if not key:
                continue
            missing_counts[key] += 1
            missing_display_form.setdefault(key, skill.strip())

        ranked_missing = missing_counts.most_common()

        # --- Tally what you're STRONG on: skills that actually matched,
        # across all jobs (matched_core + matched_target) ---
        all_matched = []
        for job in st.session_state.results:
            all_matched.extend(job.get("matched_core") or [])
            all_matched.extend(job.get("matched_target") or [])

        matched_display_form = {}
        matched_counts = Counter()
        for skill in all_matched:
            key = skill.strip().lower()
            if not key:
                continue
            matched_counts[key] += 1
            matched_display_form.setdefault(key, skill.strip())

        ranked_matched = matched_counts.most_common()

        if ranked_missing or ranked_matched:
            st.divider()
            st.subheader("📈 Skills to Focus On")
            st.caption(
                "Based on gaps found across all your current job matches.")

            # --- Grounded one-line insight (pure logic, no extra API call) ---
            top_strengths = [matched_display_form[k]
                             for k, _ in ranked_matched[:2]]
            top_gaps = [missing_display_form[k] for k, _ in ranked_missing[:2]]

            if top_strengths and top_gaps:
                insight = (
                    f"💡 Your resume is strong on **{' and '.join(top_strengths)}** — "
                    f"most of your matches are being held back by **{' and '.join(top_gaps)}**."
                )
            elif top_strengths and not top_gaps:
                insight = (
                    f"💡 Your resume is strong on **{' and '.join(top_strengths)}**, "
                    f"and no major skill gaps showed up across these matches."
                )
            elif top_gaps and not top_strengths:
                insight = (
                    f"💡 Across these matches, the biggest gaps are "
                    f"**{' and '.join(top_gaps)}**."
                )
            else:
                insight = None

            if insight:
                st.markdown(insight)

            # --- Tags for the full missing-skills list ---
            if ranked_missing:
                tags_html = " ".join(
                    f'<span style="background-color:#1a2f3a; color:#6bc6f5; '
                    f'padding:3px 12px; border-radius:12px; font-size:0.9em; '
                    f'margin-right:6px; margin-bottom:6px; display:inline-block;">'
                    f'{missing_display_form[key]}'
                    + (f' ({count})' if count > 1 else '')
                    + '</span>'
                    for key, count in ranked_missing
                )
                st.markdown(tags_html, unsafe_allow_html=True)
