"""
Job & Internship Hunter — Streamlit UI Shell
Step 1 of 4 in the "works for anyone" build:
  1. [THIS FILE] Streamlit UI shell (hardcoded values, visually testable)
  2. Wire in resume upload + skill extraction (pdfplumber + Gemini)
  3. Wire in country/role/target-company form inputs (replace hardcoded lists)
  4. Connect "Run" button to agent_pipeline.py

Run with: streamlit run app.py
"""

import streamlit as st

# ---------------------------------------------------------------------------
# TEMP hardcoded values — these mirror the constants currently living in
# fetch_jobs.py / match_jobs.py. In Step 3 these will be replaced by the
# values collected from the sidebar form instead of being imported as-is.
# ---------------------------------------------------------------------------
COUNTRIES = ["India", "US", "UK", "Germany"]
TARGET_COMPANIES = ["NVIDIA", "TCS", "Infosys", "Cognizant", "Okta", "Salesforce"]
CORE_SKILLS = ["Python", "API", "LangChain", "LangGraph", "CrewAI"]
TARGET_SKILLS = ["SQL", "ML", "TensorFlow", "PyTorch", "scikit-learn", "Flask", "FastAPI"]

# Fake results so the page has something to render before agent_pipeline.py
# is wired in (Step 4). Shape matches what the Summarizer Agent produces.
MOCK_RESULTS = [
    {
        "title": "AI/ML Intern",
        "company": "Acme Analytics",
        "location": "Bengaluru, India",
        "match_score": 82,
        "summary": "Strong fit — asks for Python and API experience which you have hands-on. "
                    "SQL and scikit-learn listed as nice-to-have.",
        "url": "https://example.com/job/1",
        "is_target_company": False,
    },
    {
        "title": "Machine Learning Engineer (New Grad)",
        "company": "NVIDIA",
        "location": "Remote",
        "match_score": 65,
        "summary": "Target company match! Heavier on PyTorch/TensorFlow than your current "
                    "hands-on skills, but LangGraph experience is a plus for their agent tooling team.",
        "url": "https://example.com/job/2",
        "is_target_company": True,
    },
]

st.set_page_config(page_title="Job & Internship Hunter", page_icon="🎯", layout="wide")

st.title("🎯 Job & Internship Hunter")
st.caption("AI/ML-powered job matching — multi-agent pipeline with LangGraph + Gemini")

# ---------------------------------------------------------------------------
# Sidebar — search form (Step 3 will make these actually drive the pipeline)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Search Settings")

    selected_countries = st.multiselect(
        "Countries", options=COUNTRIES, default=COUNTRIES
    )

    role_query = st.text_input("Role / keywords", value="AI ML Intern")

    selected_targets = st.multiselect(
        "Target companies (flagged in results)",
        options=TARGET_COMPANIES,
        default=TARGET_COMPANIES,
    )

    st.divider()

    st.subheader("Resume")
    st.file_uploader(
        "Upload your resume (PDF)",
        type=["pdf"],
        help="Not wired up yet — Step 2 will extract skills via pdfplumber + Gemini.",
        disabled=True,
    )
    st.caption("⏳ Coming in Step 2: auto skill extraction from your resume.")

    st.divider()
    run_clicked = st.button("🚀 Run Search", type="primary", use_container_width=True)

# ---------------------------------------------------------------------------
# Main area
# ---------------------------------------------------------------------------
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Results")

    if run_clicked:
        # Step 4 will replace this block with a real call into agent_pipeline.py,
        # e.g. results = run_pipeline(countries=selected_countries, role=role_query, ...)
        st.info("Showing mock results — agent_pipeline.py is not connected yet (Step 4).")

        for job in MOCK_RESULTS:
            with st.container(border=True):
                header_col, badge_col = st.columns([4, 1])
                with header_col:
                    st.markdown(f"**{job['title']}** — {job['company']}")
                    st.caption(job["location"])
                with badge_col:
                    st.metric("Match", f"{job['match_score']}%")

                if job["is_target_company"]:
                    st.markdown("🎯 **Target company**")

                st.write(job["summary"])
                st.markdown(f"[View listing]({job['url']})")
    else:
        st.write("Set your filters in the sidebar and click **Run Search** to see results here.")

with col2:
    st.subheader("Your Skills")
    st.markdown("**Core (hands-on):**")
    st.write(", ".join(CORE_SKILLS))
    st.markdown("**Target (learning):**")
    st.write(", ".join(TARGET_SKILLS))
    st.caption("⏳ Coming in Step 2: this panel will populate from your uploaded resume instead of hardcoded lists.")