# models/cover_letter_enhanced.py

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from dotenv import load_dotenv

# Optional: Only needed if you want to call Hugging Face Inference API
try:
    import requests
except ImportError:  # pragma: no cover
    requests = None


# -------------------------
# Data models
# -------------------------

@dataclass
class CoverLetterInput:
    full_name: str
    target_role: str
    company_name: str
    years_experience: int
    key_skills: List[str] = field(default_factory=list)
    key_achievements: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    motivation: str = ""  # Why this role/company
    location: str = ""
    email: str = ""
    phone: str = ""
    date_line: str = ""  # Optional custom date line (e.g., "January 11, 2026")
    hiring_manager_name: str = ""  # Optional


@dataclass
class CoverLetterResult:
    cover_letter: str
    source: str  # "template" or "huggingface_api"


# -------------------------
# Main class
# -------------------------

class CoverLetterGeneratorEnhanced:
    """
    Enhanced cover letter helper:
      - generate_cover_letter(data, job_description=None, tone="professional")
    """

    def __init__(
        self,
        hf_token_env: str = "HUGGINGFACE_TOKEN",
        hf_model_env: str = "HF_COVERLETTER_MODEL",
        hf_api_url_env: str = "HF_API_URL_COVER",
        request_timeout: int = 30,
    ) -> None:
        load_dotenv()
        self.hf_token = os.getenv(hf_token_env, "").strip()
        self.hf_model = os.getenv(hf_model_env, "google/flan-t5-large").strip()
        self.hf_api_url = os.getenv(hf_api_url_env, "").strip()
        self.request_timeout = request_timeout

        self._whitespace_re = re.compile(r"\s+")

    def generate_cover_letter(
        self,
        data: CoverLetterInput,
        job_description: Optional[str] = None,
        tone: str = "professional",
        use_hf_api_if_available: bool = True,
    ) -> CoverLetterResult:
        """
        Generates an ATS-friendly cover letter.
        If HF token + requests exists and use_hf_api_if_available=True, it attempts the HF API.
        Otherwise falls back to a strong template-based cover letter.
        """
        template_letter = self._generate_cover_letter_template(data, job_description, tone)

        if not use_hf_api_if_available:
            return CoverLetterResult(cover_letter=template_letter, source="template")

        if not self.hf_token or requests is None:
            return CoverLetterResult(cover_letter=template_letter, source="template")

        try:
            api_letter = self._generate_cover_letter_hf_api(data, job_description, tone)
            if api_letter and len(api_letter.strip()) >= 200:
                return CoverLetterResult(cover_letter=api_letter.strip(), source="huggingface_api")
            return CoverLetterResult(cover_letter=template_letter, source="template")
        except Exception:
            return CoverLetterResult(cover_letter=template_letter, source="template")

    # -------------------------
    # Internal Helpers
    # -------------------------

    def _generate_cover_letter_template(
        self,
        data: CoverLetterInput,
        job_description: Optional[str],
        tone: str,
    ) -> str:
        # Header block (optional)
        header_lines = []
        if data.date_line:
            header_lines.append(data.date_line)
        if data.location:
            header_lines.append(data.location)
        if data.email:
            header_lines.append(data.email)
        if data.phone:
            header_lines.append(data.phone)

        header = "\n".join(header_lines).strip()
        if header:
            header += "\n\n"

        salutation = "Dear Hiring Manager,"
        if data.hiring_manager_name.strip():
            salutation = f"Dear {data.hiring_manager_name.strip()},"

        # Body content
        skills = ", ".join(data.key_skills[:10]).strip()
        tools = ", ".join(data.tools[:8]).strip()

        # Achievements: pick up to 2
        ach = ""
        if data.key_achievements:
            if len(data.key_achievements) == 1:
                ach = f"One highlight includes {data.key_achievements[0].rstrip('.') }."
            else:
                ach = (
                    f"Key highlights include {data.key_achievements[0].rstrip('.') } "
                    f"and {data.key_achievements[1].rstrip('.') }."
                )

        motivation = data.motivation.strip()
        if not motivation:
            motivation = f"I’m excited about the opportunity to contribute to {data.company_name} in this role."

        # Light customization based on tone
        tone_line = ""
        if tone.lower() in {"warm", "friendly"}:
            tone_line = "I’d welcome the chance to bring my energy and commitment to your team."
        elif tone.lower() in {"confident", "assertive"}:
            tone_line = "I am confident I can deliver immediate value and measurable outcomes in this position."
        else:
            tone_line = "I would welcome the opportunity to support your team and deliver measurable results."

        # Optional JD hint: add a short phrase if JD exists
        jd_hint = ""
        if job_description and len(job_description.strip()) > 40:
            jd_hint = (
                " I have reviewed the role requirements and can align my experience to the key priorities outlined."
            )

        body = f"""{salutation}

I am writing to apply for the {data.target_role} position at {data.company_name}.{jd_hint} With {data.years_experience}+ years of experience, I have developed strong capabilities in {skills or "delivering high-quality results"}{("." if skills else ".")}

{motivation}

In previous roles, I have consistently supported performance and outcomes through quality delivery, collaboration, and data-informed decision-making. {ach}{" " if ach else ""}{("I am proficient with tools such as " + tools + ".") if tools else ""}

{tone_line} Thank you for considering my application. I look forward to the possibility of discussing how my experience and skills can support {data.company_name}.

Sincerely,
{data.full_name}
"""
        return self._cleanup_spaces_preserve_paragraphs(body)

    def _generate_cover_letter_hf_api(
        self,
        data: CoverLetterInput,
        job_description: Optional[str],
        tone: str,
    ) -> str:
        if requests is None:
            raise RuntimeError("requests is not installed.")

        api_url = self.hf_api_url or f"https://api-inference.huggingface.co/models/{self.hf_model}"

        prompt = self._build_cover_letter_prompt(data, job_description, tone)

        headers = {"Authorization": f"Bearer {self.hf_token}"}
        payload = {
            "inputs": prompt,
            "parameters": {"max_new_tokens": 450, "temperature": 0.5},
        }

        resp = requests.post(api_url, headers=headers, json=payload, timeout=self.request_timeout)
        resp.raise_for_status()
        output = resp.json()

        if isinstance(output, list) and output and isinstance(output[0], dict):
            text = output[0].get("generated_text") or output[0].get("summary_text") or ""
            return text
        if isinstance(output, dict) and "error" in output:
            raise RuntimeError(output["error"])
        return ""

    def _build_cover_letter_prompt(
        self,
        data: CoverLetterInput,
        job_description: Optional[str],
        tone: str,
    ) -> str:
        skills = ", ".join(data.key_skills[:12])
        tools = ", ".join(data.tools[:10])
        achievements = "; ".join(data.key_achievements[:3])

        jd = job_description.strip() if job_description else ""

        prompt = (
            "Write a one-page, ATS-friendly cover letter.\n"
            f"Tone: {tone}\n"
            f"Applicant name: {data.full_name}\n"
            f"Target role: {data.target_role}\n"
            f"Company: {data.company_name}\n"
            f"Years of experience: {data.years_experience}\n"
            f"Key skills: {skills}\n"
            f"Tools: {tools}\n"
            f"Key achievements: {achievements}\n"
            f"Motivation: {data.motivation}\n"
        )
        if jd:
            prompt += f"Job description:\n{jd}\n"
        prompt += (
            "Use 4–6 short paragraphs. Avoid bullet points. "
            "Include a polite closing and signature with the applicant name. "
            "Return only the cover letter text."
        )
        return prompt

    def _cleanup_spaces_preserve_paragraphs(self, text: str) -> str:
        # Normalize whitespace inside lines but keep paragraph breaks
        lines = [self._whitespace_re.sub(" ", line).strip() for line in text.splitlines()]
        # Keep blank lines
        cleaned = "\n".join(lines)
        # Reduce 3+ newlines to 2
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned).strip()
        return cleaned


# -------------------------
# Quick manual test runner
# -------------------------
if __name__ == "__main__":
    generator = CoverLetterGeneratorEnhanced()

    data = CoverLetterInput(
        full_name="Charles Example",
        target_role="M&E Manager",
        company_name="Example NGO",
        years_experience=8,
        key_skills=["Monitoring & Evaluation", "Power BI", "SQL", "KoboToolbox", "Reporting", "Data Quality Assurance"],
        key_achievements=[
            "improved reporting timeliness by 35% through automation and dashboarding",
            "led routine data quality audits across multiple field sites",
        ],
        tools=["Excel", "Power BI", "Python", "KoboToolbox", "SQL"],
        motivation="I am motivated by your focus on evidence-driven programming and strong learning culture.",
        location="Juba, South Sudan",
        email="charles@example.com",
        phone="+211-000-000-000",
        date_line="January 11, 2026",
    )

    jd = """
    We are looking for an M&E Manager with experience in Power BI dashboarding, SQL analytics, and survey systems (ODK/Kobo).
    The role supports indicator tracking, donor reporting, and learning events to improve program performance.
    """

    result = generator.generate_cover_letter(data, job_description=jd, tone="professional")
    print("\nCOVER LETTER SOURCE:", result.source)
    print(result.cover_letter)
