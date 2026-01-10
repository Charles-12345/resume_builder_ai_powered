from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from datetime import date
from typing import Optional, Sequence

import streamlit as st
from docx import Document

# --- Your project modules ---
from models.resume_generator_enhanced import ResumeGeneratorEnhanced, CandidateProfile
from models.cover_letter_enhanced import CoverLetterGeneratorEnhanced, CoverLetterInput

# Import only what we KNOW exists (based on your tests)
from templates.resume_templates import ResumeTemplateRenderer


# -------------------------
# Local data models (robust)
# -------------------------
@dataclass
class ExperienceItem:
    title: str
    company: str
    start_date: str = ""
    end_date: str = ""
    location: str = ""
    bullets: list[str] = field(default_factory=list)


@dataclass
class EducationItem:
    degree: str
    institution: str
    year: str = ""
    details: str = ""


@dataclass
class ResumeData:
    full_name: str
    headline: str
    location: str
    email: str
    phone: str
    links: list[str]
    summary: str
    skills: list[str]
    experience: list[ExperienceItem]
    education: list[EducationItem]
    certifications: list[str] = field(default_factory=list)
    projects: list[str] = field(default_factory=list)


# -------------------------
# App config
# -------------------------
st.set_page_config(
    page_title="Resume Builder AI",
    page_icon="📄",
    layout="wide",
)

GENERATED_DIR = "generated_documents"


# -------------------------
# Utilities
# -------------------------
def ensure_generated_dir() -> None:
    os.makedirs(GENERATED_DIR, exist_ok=True)


def safe_filename(name: str) -> str:
    name = (name or "").strip().lower()
    name = re.sub(r"[^a-z0-9\-_\s]", "", name)
    name = re.sub(r"\s+", "_", name)
    return name or "document"


def build_cover_letter_docx(text: str, out_path: str) -> None:
    doc = Document()
    for para in text.split("\n\n"):
        p = para.strip()
        if p:
            doc.add_paragraph(p)
    doc.save(out_path)


@st.cache_resource
def get_resume_generator() -> ResumeGeneratorEnhanced:
    return ResumeGeneratorEnhanced()


@st.cache_resource
def get_cover_generator() -> CoverLetterGeneratorEnhanced:
    return CoverLetterGeneratorEnhanced()


@st.cache_resource
def get_template_renderer() -> ResumeTemplateRenderer:
    # Ensure output dir exists before renderer is created/cached
    ensure_generated_dir()
    return ResumeTemplateRenderer(output_dir=GENERATED_DIR)


def init_session_state() -> None:
    st.session_state.setdefault("experience", [])
    st.session_state.setdefault("education", [])
    st.session_state.setdefault("generated_resume_path", "")
    st.session_state.setdefault("generated_cover_path", "")
    st.session_state.setdefault("generated_summary", "")
    st.session_state.setdefault("generated_cover_letter", "")


# -------------------------
# Page: Home
# -------------------------
def page_home() -> None:
    st.title("📄 Resume Builder AI")
    st.write(
        """
This app helps you:
- Generate an ATS-friendly **summary**
- Build a structured resume and export to **DOCX**
- Generate a **cover letter** (and export to DOCX)
- Compute a practical **ATS optimization score**
"""
    )

    st.info("Tip: Start with `python -m streamlit run app.py` from the project root.")

    with st.expander("Project folders expected"):
        st.code(
            """resume_builder_ai_powered/
├─ app.py
├─ models/
│  ├─ __init__.py
│  ├─ resume_generator_enhanced.py
│  └─ cover_letter_enhanced.py
├─ templates/
│  ├─ __init__.py
│  └─ resume_templates.py
└─ generated_documents/""",
            language="text",
        )


# -------------------------
# Page: Resume Builder
# -------------------------
def page_resume_builder() -> None:
    st.title("🧱 Resume Builder")

    resume_gen = get_resume_generator()
    renderer = get_template_renderer()

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.subheader("1) Personal Details")
        full_name = st.text_input("Full name", value="Charles Example")
        title = st.text_input("Target title / headline role", value="Monitoring, Evaluation & Learning (MEL) Manager")

        years_exp = st.number_input("Years of experience", min_value=0, max_value=60, value=8, step=1)
        years_exp_int = int(years_exp)

        location = st.text_input("Location", value="Juba, South Sudan")
        email = st.text_input("Email", value="charles@example.com")
        phone = st.text_input("Phone", value="+211-000-000-000")

        links_raw = st.text_area(
            "Links (one per line)",
            value="linkedin.com/in/your-profile\ngithub.com/your-profile",
        )
        links = [x.strip() for x in links_raw.splitlines() if x.strip()]

        st.subheader("2) Skills & Tools")
        core_skills_raw = st.text_area(
            "Core skills (comma-separated)",
            value="M&E, Data Analysis, Power BI, SQL, KoboToolbox, Reporting, Data Quality Assurance",
        )
        tools_raw = st.text_area("Tools (comma-separated)", value="Excel, Power BI, Python, KoboToolbox, SQL")
        industries_raw = st.text_area("Industries (comma-separated)", value="Humanitarian, Development")
        achievements_raw = st.text_area(
            "Top achievements (one per line)",
            value="Improved reporting timeliness by 35% through automation and dashboarding\nLed routine data quality audits across multiple sites",
        )

        core_skills = [x.strip() for x in core_skills_raw.split(",") if x.strip()]
        tools = [x.strip() for x in tools_raw.split(",") if x.strip()]
        industries = [x.strip() for x in industries_raw.split(",") if x.strip()]
        achievements = [x.strip() for x in achievements_raw.splitlines() if x.strip()]

        st.subheader("3) Summary")
        job_desc = st.text_area("Optional: Job Description (helps summary + ATS)", value="", height=140)
        target_title = st.text_input("Optional: Target title for summary", value=title)

        if st.button("✨ Generate Summary", type="primary"):
            profile = CandidateProfile(
                full_name=full_name,
                title=title,
                years_experience=years_exp_int,
                core_skills=core_skills,
                industries=industries,
                achievements=achievements,
                tools=tools,
                location=location,
                email=email,
                phone=phone,
                links=links,
            )
            result = resume_gen.generate_summary(
                profile=profile,
                job_description=job_desc.strip() or None,
                target_title=target_title.strip() or None,
            )
            st.session_state.generated_summary = result.summary
            st.success(f"Summary generated (source: {result.source}).")

        summary_text = st.text_area(
            "Summary (editable)",
            value=st.session_state.generated_summary,
            height=160,
        )

    with col_right:
        st.subheader("4) Experience (Add multiple)")

        # Use a form for cleaner Streamlit rerun behavior
        with st.form("experience_form", clear_on_submit=True):
            ex_title = st.text_input("Role title")
            ex_company = st.text_input("Organization")
            ex_start = st.text_input("Start date", value="2023")
            ex_end = st.text_input("End date", value="Present")
            ex_loc = st.text_input("Location (optional)", value="South Sudan")
            ex_bullets_raw = st.text_area(
                "Bullets (one per line)",
                value="Built dashboards for program performance and donor reporting\nLed routine data quality audits and coached teams on standards",
                height=120,
            )
            add_ex = st.form_submit_button("Add Experience")

        if add_ex:
            if not ex_title.strip() or not ex_company.strip():
                st.error("Please provide at least a Role title and Organization.")
            else:
                bullets = [b.strip() for b in ex_bullets_raw.splitlines() if b.strip()]
                st.session_state.experience.append(
                    ExperienceItem(
                        title=ex_title.strip(),
                        company=ex_company.strip(),
                        start_date=ex_start.strip(),
                        end_date=ex_end.strip(),
                        location=ex_loc.strip(),
                        bullets=bullets,
                    )
                )
                st.success("Experience added.")
                st.rerun()

        if st.session_state.experience:
            st.write("**Current Experience Items:**")
            for i, item in enumerate(st.session_state.experience):
                with st.expander(f"{i+1}. {item.title} — {item.company}", expanded=False):
                    st.write(f"**Dates:** {item.start_date} – {item.end_date}")
                    if item.location:
                        st.write(f"**Location:** {item.location}")
                    st.write("**Bullets:**")
                    for b in item.bullets:
                        st.write(f"- {b}")

                    if st.button(f"Remove Experience #{i+1}", key=f"rm_ex_{i}"):
                        st.session_state.experience.pop(i)
                        st.warning("Removed.")
                        st.rerun()
        else:
            st.info("No experience items yet. Add at least one for a strong resume.")

        st.subheader("5) Education (Add multiple)")

        with st.form("education_form", clear_on_submit=True):
            ed_degree = st.text_input("Degree", value="MSc Data Science")
            ed_inst = st.text_input("Institution", value="Guglielmo Marconi University")
            ed_year = st.text_input("Year (optional)", value="2024")
            ed_details = st.text_input("Details (optional)", value="")
            add_ed = st.form_submit_button("Add Education")

        if add_ed:
            if not ed_degree.strip() or not ed_inst.strip():
                st.error("Please provide at least Degree and Institution.")
            else:
                st.session_state.education.append(
                    EducationItem(
                        degree=ed_degree.strip(),
                        institution=ed_inst.strip(),
                        year=ed_year.strip(),
                        details=ed_details.strip(),
                    )
                )
                st.success("Education added.")
                st.rerun()

        if st.session_state.education:
            for i, ed in enumerate(st.session_state.education):
                with st.expander(f"{i+1}. {ed.degree} — {ed.institution}", expanded=False):
                    if ed.year:
                        st.write(f"**Year:** {ed.year}")
                    if ed.details:
                        st.write(f"**Details:** {ed.details}")
                    if st.button(f"Remove Education #{i+1}", key=f"rm_ed_{i}"):
                        st.session_state.education.pop(i)
                        st.warning("Removed.")
                        st.rerun()
        else:
            st.info("No education items yet.")

        st.subheader("6) Optional sections")
        certs_raw = st.text_area("Certifications (one per line)", value="", height=90)
        projects_raw = st.text_area("Projects (one per line)", value="", height=90)

        certifications = [x.strip() for x in certs_raw.splitlines() if x.strip()]
        projects = [x.strip() for x in projects_raw.splitlines() if x.strip()]

        st.subheader("7) Export Resume to DOCX")
        template = st.selectbox(
            "Choose template",
            ["modern", "executive", "creative", "technical"],
            index=0,
        )

        export_name = safe_filename(full_name)
        out_filename = f"{export_name}_resume_{template}.docx"

        if st.button("📥 Generate Resume DOCX", type="primary"):
            data = ResumeData(
                full_name=full_name,
                headline=title,
                location=location,
                email=email,
                phone=phone,
                links=links,
                summary=summary_text.strip(),
                skills=core_skills,
                experience=st.session_state.experience,
                education=st.session_state.education,
                certifications=certifications,
                projects=projects,
            )

            # Your renderer must implement these methods; if not, rename accordingly.
            if template == "modern":
                path = renderer.render_modern(data, filename=out_filename)
            elif template == "executive":
                path = renderer.render_executive(data, filename=out_filename)
            elif template == "creative":
                path = renderer.render_creative(data, filename=out_filename)
            else:
                path = renderer.render_technical(data, filename=out_filename)

            st.session_state.generated_resume_path = path
            st.success(f"Resume generated: {path}")

        if st.session_state.generated_resume_path and os.path.exists(st.session_state.generated_resume_path):
            with open(st.session_state.generated_resume_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Resume DOCX",
                    data=f.read(),
                    file_name=os.path.basename(st.session_state.generated_resume_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )


# -------------------------
# Page: Cover Letter
# -------------------------
def page_cover_letter() -> None:
    st.title("✉️ Cover Letter Generator")

    cover_gen = get_cover_generator()

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Inputs")
        full_name = st.text_input("Full name", value="Charles Example", key="cl_name")
        company = st.text_input("Company name", value="Example NGO", key="cl_company")
        role = st.text_input("Target role", value="M&E Manager", key="cl_role")
        years = st.number_input("Years of experience", min_value=0, max_value=60, value=8, step=1, key="cl_years")
        years_int = int(years)

        location = st.text_input("Location (optional)", value="Juba, South Sudan", key="cl_loc")
        email = st.text_input("Email (optional)", value="charles@example.com", key="cl_email")
        phone = st.text_input("Phone (optional)", value="+211-000-000-000", key="cl_phone")
        hiring_manager = st.text_input("Hiring manager name (optional)", value="", key="cl_hm")

        skills_raw = st.text_area(
            "Key skills (comma-separated)",
            value="Monitoring & Evaluation, Power BI, SQL, KoboToolbox, Reporting, Data Quality Assurance",
            key="cl_skills",
        )
        tools_raw = st.text_area(
            "Tools (comma-separated)",
            value="Excel, Power BI, Python, KoboToolbox, SQL",
            key="cl_tools",
        )
        achievements_raw = st.text_area(
            "Achievements (one per line)",
            value="Improved reporting timeliness by 35% through automation and dashboarding\nLed routine data quality audits across multiple sites",
            key="cl_ach",
            height=120,
        )
        motivation = st.text_area(
            "Motivation (why this role/company)",
            value="I am motivated by your focus on evidence-driven programming and strong learning culture.",
            key="cl_motivation",
            height=90,
        )
        jd = st.text_area("Optional: Job Description", value="", key="cl_jd", height=140)

        tone = st.selectbox("Tone", ["professional", "warm", "confident"], index=0, key="cl_tone")

        if st.button("🪄 Generate Cover Letter", type="primary"):
            data = CoverLetterInput(
                full_name=full_name,
                target_role=role,
                company_name=company,
                years_experience=years_int,
                key_skills=[x.strip() for x in skills_raw.split(",") if x.strip()],
                key_achievements=[x.strip() for x in achievements_raw.splitlines() if x.strip()],
                tools=[x.strip() for x in tools_raw.split(",") if x.strip()],
                motivation=motivation.strip(),
                location=location.strip(),
                email=email.strip(),
                phone=phone.strip(),
                date_line=date.today().strftime("%B %d, %Y"),
                hiring_manager_name=hiring_manager.strip(),
            )

            result = cover_gen.generate_cover_letter(
                data=data,
                job_description=jd.strip() or None,
                tone=tone,
            )
            st.session_state.generated_cover_letter = result.cover_letter
            st.success(f"Cover letter generated (source: {result.source}).")

    with col2:
        st.subheader("Output (editable)")
        cover_text = st.text_area(
            "Cover letter text",
            value=st.session_state.generated_cover_letter,
            height=520,
        )

        if st.button("📄 Export Cover Letter to DOCX"):
            ensure_generated_dir()
            filename = f"{safe_filename(full_name)}_cover_letter.docx"
            out_path = os.path.join(GENERATED_DIR, filename)
            build_cover_letter_docx(cover_text.strip(), out_path)
            st.session_state.generated_cover_path = out_path
            st.success(f"Cover letter saved: {out_path}")

        if st.session_state.generated_cover_path and os.path.exists(st.session_state.generated_cover_path):
            with open(st.session_state.generated_cover_path, "rb") as f:
                st.download_button(
                    label="⬇️ Download Cover Letter DOCX",
                    data=f.read(),
                    file_name=os.path.basename(st.session_state.generated_cover_path),
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )


# -------------------------
# Page: ATS Checker
# -------------------------
def page_ats_checker() -> None:
    st.title("✅ ATS Optimization Checker")

    resume_gen = get_resume_generator()

    col1, col2 = st.columns(2)

    with col1:
        resume_text = st.text_area("Paste resume text", height=320)
    with col2:
        jd_text = st.text_area("Paste job description", height=320)

    if st.button("Calculate ATS Score", type="primary"):
        if not resume_text.strip() or not jd_text.strip():
            st.error("Please provide both resume text and job description.")
            return

        result = resume_gen.ats_optimization_score(resume_text, jd_text)
        st.metric("ATS Optimization Score", f"{result.score}/100")

        st.subheader("Matched keywords (sample)")
        st.write(", ".join(result.matched_keywords) if result.matched_keywords else "None found")

        st.subheader("Missing keywords to consider")
        st.write(", ".join(result.missing_keywords) if result.missing_keywords else "None")

        st.subheader("Notes")
        for n in result.notes:
            st.write(f"- {n}")


# -------------------------
# Routing
# -------------------------
def main() -> None:
    init_session_state()

    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to",
        ["Home", "Resume Builder", "Cover Letter", "ATS Checker"],
        index=0,
    )

    if page == "Home":
        page_home()
    elif page == "Resume Builder":
        page_resume_builder()
    elif page == "Cover Letter":
        page_cover_letter()
    else:
        page_ats_checker()


if __name__ == "__main__":
    main()
