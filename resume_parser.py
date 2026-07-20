"""
resume_parser.py
Extracts raw text from an uploaded resume PDF, then uses Gemini to pull out
structured data: skills, experience, education, and projects.
"""

import json
import os
import pdfplumber
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Reuses the same Gemini setup pattern as agent_pipeline.py
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-3.1-flash-lite")

EXTRACTION_PROMPT = """You are a resume parser. Read the resume text below and
extract structured information. Respond ONLY with valid JSON, no markdown
fences, no preamble. Use this exact schema:

{
  "skills": ["skill1", "skill2", ...],
  "experience": [
    {"title": "...", "company": "...", "duration": "...", "summary": "..."}
  ],
  "education": [
    {"degree": "...", "institution": "...", "year": "..."}
  ],
  "projects": [
    {"name": "...", "description": "...", "tech_used": ["..."]}
  ]
}

If a section is missing from the resume, return an empty list for it.
Do not invent information that isn't in the resume text.

Resume text:
---
RESUME_TEXT_PLACEHOLDER
---
"""


def extract_text_from_pdf(uploaded_file) -> str:
    """
    Takes a Streamlit UploadedFile object and returns the raw extracted text.
    """
    text_chunks = []
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)
    return "\n".join(text_chunks)


def extract_structured_data(resume_text: str) -> dict:
    """
    Sends resume text to Gemini and returns structured skills/experience/
    education/projects as a dict. Falls back to an empty structure if the
    API call fails or returns something unparsable.
    """
    fallback = {"skills": [], "experience": [],
                "education": [], "projects": []}

    if not resume_text.strip():
        return fallback

    prompt = EXTRACTION_PROMPT.replace("RESUME_TEXT_PLACEHOLDER", resume_text)

    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Gemini sometimes wraps JSON in ```json fences despite instructions —
        # strip them defensively.
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)

        # Make sure all expected keys exist even if Gemini omits one
        for key in fallback:
            data.setdefault(key, [])

        return data

    except Exception as e:
        print(f"[resume_parser] Extraction failed, using fallback: {e}")
        return fallback


def parse_resume(uploaded_file) -> dict:
    """
    Convenience wrapper: PDF -> raw text -> structured data.
    This is the one function app.py needs to call.
    """
    text = extract_text_from_pdf(uploaded_file)
    return extract_structured_data(text)
