# models/resume_generator_enhanced.py

from __future__ import annotations

import os
import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from collections import Counter

from dotenv import load_dotenv

# Optional: Only needed if you want to call Hugging Face Inference API
try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


# -------------------------
# Data models (optional, but clean)
# -------------------------

@dataclass
class CandidateProfile:
    full_name: str
    title: str
    years_experience: int
    core_skills: List[str]
    industries: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    location: str = ""
    email: str = ""
    phone: str = ""
    links: List[str] = field(default_factory=list)


@dataclass
class SummaryResult:
    summary: str
    source: str  # "template" or "huggingface_api"


@dataclass
class ATSScoreResult:
    score: int  # 0-100
    matched_keywords: List[str]
    missing_keywords: List[str]
    notes: List[str]


# -------------------------
# Main class
# -------------------------

class ResumeGeneratorEnhanced:
    """
    Enhanced resume helper:
      - generate_summary(profile, job_description=None, target_title=None)
      - ats_optimization_score(resume_text, job_description)
    """

    def __init__(
        self,
        hf_token_env: str = "HUGGINGFACE_TOKEN",
        hf_model_env: str = "HF_SUMMARY_MODEL",
        hf_api_url_env: str = "HF_API_URL",
        request_timeout: int = 30,
    ) -> None:
        load_dotenv()
        self.hf_token = os.getenv(hf_token_env, "").strip()
        self.hf_model = os.getenv(hf_model_env, "google/flan-t5-large").strip()
        # Default HF Inference API endpoint; can override via env
        self.hf_api_url = os.getenv(hf_api_url_env, "").strip()
        self.request_timeout = request_timeout

        # Pre-compile some regex patterns
        self._whitespace_re = re.compile(r"\s+")
        self._word_re = re.compile(r"[A-Za-z][A-Za-z\-\+\.]{1,}")

    # -------------------------
    # Public Methods
    # -------------------------

    def generate_summary(
        self,
        profile: CandidateProfile,
        job_description: Optional[str] = None,
        target_title: Optional[str] = None,
        use_hf_api_if_available: bool = True,
    ) -> SummaryResult:
        """
        Generates a professional summary.
        If HF token + requests exists and use_hf_api_if_available=True, it attempts the HF API.
        Otherwise falls back to a high-quality template-based summary.
        """

        # Always build a strong fallback
        template_summary = self._generate_summary_template(profile, target_title, job_description)

        if not use_hf_api_if_available:
            return SummaryResult(summary=template_summary, source="template")

        if not self.hf_token or requests is None:
            return SummaryResult(summary=template_summary, source="template")

        # Try HF Inference API (safe, with fallback)
        try:
            api_summary = self._generate_summary_hf_api(profile, job_description, target_title)
            if api_summary and len(api_summary.strip()) >= 40:
                return SummaryResult(summary=api_summary.strip(), source="huggingface_api")
            return SummaryResult(summary=template_summary, source="template")
        except Exception:
            return SummaryResult(summary=template_summary, source="template")

    def ats_optimization_score(self, resume_text: str, job_description: str) -> ATSScoreResult:
        """
        Returns a practical ATS score (0-100) based on keyword match + basic formatting checks.
        This is a heuristic score (useful for improvement), not a “true ATS vendor score”.
        """
        resume_text_clean = self._normalize_text(resume_text)
        jd_clean = self._normalize_text(job_description)

        resume_keywords = self._extract_keywords(resume_text_clean)
        jd_keywords = self._extract_keywords(jd_clean)

        if not jd_keywords:
            return ATSScoreResult(
                score=0,
                matched_keywords=[],
                missing_keywords=[],
                notes=["Job description is empty or not readable; cannot compute ATS match."],
            )

        matched = sorted(set(resume_keywords).intersection(set(jd_keywords)))
        missing = sorted(set(jd_keywords).difference(set(resume_keywords)))

        # Keyword match ratio
        match_ratio = len(matched) / max(1, len(set(jd_keywords)))

        # Base score from keyword overlap (up to 70)
        score = int(round(70 * match_ratio))

        notes: List[str] = []

        # Formatting / structure heuristics (up to 30)
        structure_points = 0

        # Encourage common sections
        section_checks = {
            "experience": bool(re.search(r"\bexperience\b|\bemployment\b|\bwork history\b", resume_text_clean)),
            "education": bool(re.search(r"\beducation\b|\bqualifications\b", resume_text_clean)),
            "skills": bool(re.search(r"\bskills\b|\bcompetencies\b|\bcore skills\b", resume_text_clean)),
        }
        missing_sections = [k for k, ok in section_checks.items() if not ok]
        if missing_sections:
            notes.append(f"Missing common section headings: {', '.join(missing_sections)}.")
        else:
            structure_points += 10

        # Penalize super-long lines (ATS can struggle with odd formatting)
        long_lines = self._count_long_lines(resume_text, threshold=120)
        if long_lines == 0:
            structure_points += 8
        else:
            notes.append(f"Found {long_lines} very long lines (>120 chars). Consider wrapping text.")

        # Penalize excessive symbols that sometimes indicate tables/graphics
        symbol_density = self._symbol_density(resume_text)
        if symbol_density < 0.06:
            structure_points += 6
        else:
            notes.append("High symbol density detected. Avoid heavy tables/graphics for ATS-friendly resumes.")

        # Reward reasonable length
        word_count = len(self._word_re.findall(resume_text))
        if 250 <= word_count <= 950:
            structure_points += 6
        else:
            notes.append(f"Resume word count is {word_count}. Typical ranges are ~250–950 depending on seniority.")

        score = min(100, score + structure_points)

        # Choose top missing keywords to focus on
        missing_top = missing[:20]

        return ATSScoreResult(
            score=score,
            matched_keywords=matched[:30],
            missing_keywords=missing_top,
            notes=notes or ["Looks reasonably ATS-friendly. Improve by adding missing key terms naturally."],
        )

    # -------------------------
    # Internal Helpers
    # -------------------------

    def _generate_summary_template(
        self,
        profile: CandidateProfile,
        target_title: Optional[str],
        job_description: Optional[str],
    ) -> str:
        title = target_title.strip() if target_title else profile.title.strip()

        core_skills = ", ".join(profile.core_skills[:8]).strip()
        tools = ", ".join(profile.tools[:6]).strip()
        industries = ", ".join(profile.industries[:4]).strip()

        achievement_line = ""
        if profile.achievements:
            # Keep it short and punchy
            achievement_line = f" Proven track record including: {profile.achievements[0].rstrip('.') }."

        jd_hint = ""
        if job_description:
            jd_keywords = self._extract_keywords(self._normalize_text(job_description))
            jd_hint_terms = [k for k in jd_keywords if k.lower() not in {s.lower() for s in profile.core_skills}]
            jd_hint_terms = jd_hint_terms[:4]
            if jd_hint_terms:
                jd_hint = f" Experienced in {', '.join(jd_hint_terms)}."

        parts = [
            f"{title} with {profile.years_experience}+ years of experience delivering measurable results.",
            f"Skilled in {core_skills}." if core_skills else "",
            f"Tools: {tools}." if tools else "",
            f"Industry exposure: {industries}." if industries else "",
            achievement_line,
            jd_hint,
            "Strong communicator with a focus on quality, timeliness, and stakeholder collaboration.",
        ]
        summary = " ".join([p for p in parts if p]).strip()
        summary = self._cleanup_spaces(summary)
        return summary

    def _generate_summary_hf_api(
        self,
        profile: CandidateProfile,
        job_description: Optional[str],
        target_title: Optional[str],
    ) -> str:
        """
        Calls Hugging Face Inference API.
        Works best with text2text-generation style models (e.g., flan-t5).
        """
        if requests is None:
            raise RuntimeError("requests is not installed.")

        # If user set a full API URL, use it; otherwise build from model
        api_url = self.hf_api_url or f"https://api-inference.huggingface.co/models/{self.hf_model}"

        title = target_title or profile.title
        prompt = self._build_summary_prompt(profile, title, job_description)

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 140, "temperature": 0.4},
        }

        resp = requests.post(api_url, headers=headers, json=payload, timeout=self.request_timeout)
        resp.raise_for_status()
        data = resp.json()

        # HF can return list[dict] or dict depending on model/status
        if isinstance(data, list) and data and isinstance(data[0], dict):
            # Some models return "generated_text"
            text = data[0].get("generated_text") or data[0].get("summary_text") or ""
            return text
        if isinstance(data, dict):
            # errors or alternate structures
            if "error" in data:
                raise RuntimeError(data["error"])
        return ""

    def _build_summary_prompt(
        self,
        profile: CandidateProfile,
        title: str,
        job_description: Optional[str],
    ) -> str:
        skills = ", ".join(profile.core_skills[:12])
        tools = ", ".join(profile.tools[:10])
        achievements = "; ".join(profile.achievements[:3])

        jd = job_description.strip() if job_description else ""

        prompt = (
            "Write a concise, ATS-friendly professional summary (3–4 sentences) for a resume.\n"
            f"Target role title: {title}\n"
            f"Years of experience: {profile.years_experience}\n"
            f"Core skills: {skills}\n"
            f"Tools: {tools}\n"
            f"Key achievements: {achievements}\n"
        )
        if jd:
            prompt += f"Job description context:\n{jd}\n"
        prompt += "Return only the summary text."
        return prompt

    def _normalize_text(self, text: str) -> str:
        text = text.lower()
        text = text.replace("\u2019", "'").replace("\u2013", "-").replace("\u2014", "-")
        text = self._whitespace_re.sub(" ", text)
        return text.strip()

    def _cleanup_spaces(self, text: str) -> str:
        return self._whitespace_re.sub(" ", text).strip()

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract “keywords” (simple heuristic):
        - words length >= 3
        - remove very common stopwords
        - keep tokens that look like skills/tools/terms
        """
        stop = {
            "and","the","for","with","from","that","this","have","has","had","are","was","were","been",
            "to","of","in","on","at","as","by","or","an","a","it","is","be","will","can","may",
            "your","you","we","our","their","they","them","i","my","me","us",
            "role","job","work","team","ability","skills","experience","years","including",
        }

        tokens = [t.lower() for t in self._word_re.findall(text)]
        tokens = [t for t in tokens if len(t) >= 3 and t not in stop]

        # Keep top terms by frequency to avoid noise
        counts = Counter(tokens)
        # return up to 80 unique keywords by freq
        return [w for w, _ in counts.most_common(80)]

    def _count_long_lines(self, text: str, threshold: int = 120) -> int:
        lines = text.splitlines()
        return sum(1 for line in lines if len(line) > threshold)

    def _symbol_density(self, text: str) -> float:
        if not text:
            return 0.0
        symbols = sum(1 for ch in text if not ch.isalnum() and not ch.isspace())
        return symbols / max(1, len(text))


# -------------------------
# Quick manual test runner
# -------------------------
if __name__ == "__main__":
    generator = ResumeGeneratorEnhanced()

    profile = CandidateProfile(
        full_name="Charles Example",
        title="Monitoring, Evaluation, and Learning (MEL) Manager",
        years_experience=8,
        core_skills=["M&E", "Data Analysis", "Power BI", "SQL", "KoboToolbox", "Reporting", "Data Quality Assurance"],
        industries=["Humanitarian", "Development"],
        achievements=["Led a multi-state monitoring system improving reporting timeliness by 35%"],
        tools=["Excel", "Power BI", "Python", "KoboToolbox", "SQL"],
        location="Juba, South Sudan",
        email="charles@example.com",
    )

    jd = """
    We are seeking an M&E Manager with strong quantitative skills, experience with Power BI dashboards,
    SQL data pipelines, and survey tools (ODK/Kobo). Responsibilities include indicator tracking,
    data quality audits, donor reporting, and learning agenda facilitation.
    """

    summary = generator.generate_summary(profile, job_description=jd, target_title="M&E Manager")
    print("\nSUMMARY SOURCE:", summary.source)
    print(summary.summary)

    resume_text = f"""
    EXPERIENCE
    MEL Manager with extensive experience in indicator tracking, donor reporting, data quality audits.
    Skilled in Power BI, SQL, and KoboToolbox. Built dashboards and automated reporting pipelines.

    EDUCATION
    MSc Data Science

    SKILLS
    Power BI, SQL, Python, Data Quality Assurance, Reporting, Survey Design, KoboToolbox
    """
    score = generator.ats_optimization_score(resume_text, jd)
    print("\nATS SCORE:", score.score)
    print("Matched keywords (sample):", score.matched_keywords[:10])
    print("Missing keywords (sample):", score.missing_keywords[:10])
    print("Notes:", score.notes)
