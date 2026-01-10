# templates/resume_templates.py

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Optional

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.shared import OxmlElement, qn


# -------------------------
# Data structures
# -------------------------

@dataclass
class ExperienceItem:
    title: str
    company: str
    start_date: str
    end_date: str
    location: str = ""
    bullets: List[str] = field(default_factory=list)


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
    location: str = ""
    email: str = ""
    phone: str = ""
    links: List[str] = field(default_factory=list)

    summary: str = ""
    skills: List[str] = field(default_factory=list)

    experience: List[ExperienceItem] = field(default_factory=list)
    education: List[EducationItem] = field(default_factory=list)

    certifications: List[str] = field(default_factory=list)
    projects: List[str] = field(default_factory=list)


# -------------------------
# Helper functions
# -------------------------

def _set_document_margins(doc: Document, top=0.6, bottom=0.6, left=0.7, right=0.7) -> None:
    section = doc.sections[0]
    section.top_margin = Inches(top)
    section.bottom_margin = Inches(bottom)
    section.left_margin = Inches(left)
    section.right_margin = Inches(right)


def _add_horizontal_rule(paragraph) -> None:
    """Adds a subtle horizontal line beneath a paragraph (Word-compatible)."""
    p = paragraph._p  # noqa
    pPr = p.get_or_add_pPr()
    pBdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "2")
    bottom.set(qn("w:color"), "BFBFBF")
    pBdr.append(bottom)
    pPr.append(pBdr)


def _add_heading(doc: Document, text: str) -> None:
    p = doc.add_paragraph()
    run = p.add_run(text.upper())
    run.bold = True
    run.font.size = Pt(10.5)
    run.font.color.rgb = RGBColor(60, 60, 60)
    _add_horizontal_rule(p)


def _add_kv_line(doc: Document, left: str, right: str) -> None:
    table = doc.add_table(rows=1, cols=2)
    table.autofit = True
    row = table.rows[0]
    row.cells[0].text = left
    row.cells[1].text = right
    row.cells[0].paragraphs[0].runs[0].bold = True
    row.cells[1].paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.RIGHT


def _safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _save_doc(doc: Document, out_dir: str, filename: str) -> str:
    _safe_mkdir(out_dir)
    out_path = os.path.join(out_dir, filename)
    doc.save(out_path)
    return out_path


# -------------------------
# Template Renderer
# -------------------------

class ResumeTemplateRenderer:
    def __init__(self, output_dir: str = "generated_documents") -> None:
        self.output_dir = output_dir

    # ---------- Template: Modern ----------
    def render_modern(self, data: ResumeData, filename: str = "resume_modern.docx") -> str:
        doc = Document()
        _set_document_margins(doc)

        # Header
        name_p = doc.add_paragraph()
        name_run = name_p.add_run(data.full_name)
        name_run.bold = True
        name_run.font.size = Pt(22)

        headline_p = doc.add_paragraph()
        headline_run = headline_p.add_run(data.headline)
        headline_run.font.size = Pt(11.5)
        headline_run.font.color.rgb = RGBColor(70, 70, 70)

        contact = " | ".join([x for x in [data.location, data.email, data.phone] if x])
        if data.links:
            contact = " | ".join([contact] + data.links) if contact else " | ".join(data.links)

        if contact:
            c_p = doc.add_paragraph(contact)
            c_p.runs[0].font.size = Pt(9.5)
            c_p.runs[0].font.color.rgb = RGBColor(90, 90, 90)

        doc.add_paragraph()  # spacing

        # Summary
        if data.summary.strip():
            _add_heading(doc, "Summary")
            s = doc.add_paragraph(data.summary.strip())
            s.runs[0].font.size = Pt(10.5)

        # Skills
        if data.skills:
            _add_heading(doc, "Core Skills")
            sk = doc.add_paragraph(", ".join(data.skills))
            sk.runs[0].font.size = Pt(10.5)

        # Experience
        if data.experience:
            _add_heading(doc, "Experience")
            for item in data.experience:
                _add_kv_line(
                    doc,
                    f"{item.title} — {item.company}",
                    f"{item.start_date} – {item.end_date}",
                )
                if item.location:
                    loc_p = doc.add_paragraph(item.location)
                    loc_p.runs[0].italic = True
                    loc_p.runs[0].font.size = Pt(9.5)

                for b in item.bullets:
                    bp = doc.add_paragraph(b, style=None)
                    bp.style = doc.styles["List Bullet"]
                    bp.runs[0].font.size = Pt(10.5)
                doc.add_paragraph()

        # Education
        if data.education:
            _add_heading(doc, "Education")
            for ed in data.education:
                line = f"{ed.degree} — {ed.institution}"
                if ed.year:
                    line += f" ({ed.year})"
                p = doc.add_paragraph(line)
                p.runs[0].bold = True
                p.runs[0].font.size = Pt(10.5)
                if ed.details:
                    d = doc.add_paragraph(ed.details)
                    d.runs[0].font.size = Pt(10.5)

        # Optional sections
        self._append_optional_sections(doc, data)

        return _save_doc(doc, self.output_dir, filename)

    # ---------- Template: Executive ----------
    def render_executive(self, data: ResumeData, filename: str = "resume_executive.docx") -> str:
        doc = Document()
        _set_document_margins(doc, top=0.8, bottom=0.8, left=0.9, right=0.9)

        # Centered header
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(data.full_name)
        r.bold = True
        r.font.size = Pt(20)

        p2 = doc.add_paragraph()
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r2 = p2.add_run(data.headline)
        r2.font.size = Pt(11.5)
        r2.font.color.rgb = RGBColor(70, 70, 70)

        contact = " • ".join([x for x in [data.location, data.email, data.phone] if x])
        if data.links:
            contact = " • ".join([contact] + data.links) if contact else " • ".join(data.links)

        if contact:
            p3 = doc.add_paragraph()
            p3.alignment = WD_ALIGN_PARAGRAPH.CENTER
            r3 = p3.add_run(contact)
            r3.font.size = Pt(9.5)
            r3.font.color.rgb = RGBColor(90, 90, 90)

        doc.add_paragraph()

        # Executive summary (slightly longer)
        if data.summary.strip():
            _add_heading(doc, "Executive Profile")
            s = doc.add_paragraph(data.summary.strip())
            s.runs[0].font.size = Pt(11)

        # Key competencies in 2 columns (table)
        if data.skills:
            _add_heading(doc, "Key Competencies")
            table = doc.add_table(rows=1, cols=2)
            left = table.rows[0].cells[0].paragraphs[0]
            right = table.rows[0].cells[1].paragraphs[0]

            half = (len(data.skills) + 1) // 2
            for i, sk in enumerate(data.skills):
                target = left if i < half else right
                pr = target.add_run(f"• {sk}\n")
                pr.font.size = Pt(10.5)

        # Experience (focus on impact)
        if data.experience:
            _add_heading(doc, "Professional Experience")
            for item in data.experience:
                title_line = f"{item.title}, {item.company}"
                dates = f"{item.start_date} – {item.end_date}"
                _add_kv_line(doc, title_line, dates)
                if item.location:
                    lp = doc.add_paragraph(item.location)
                    lp.runs[0].italic = True
                    lp.runs[0].font.size = Pt(9.5)

                # Bullets (keep 3–5 ideally)
                for b in item.bullets[:6]:
                    bp = doc.add_paragraph(b)
                    bp.style = doc.styles["List Bullet"]
                    bp.runs[0].font.size = Pt(10.5)
                doc.add_paragraph()

        # Education
        if data.education:
            _add_heading(doc, "Education")
            for ed in data.education:
                line = f"{ed.degree} — {ed.institution}"
                if ed.year:
                    line += f" ({ed.year})"
                p = doc.add_paragraph(line)
                p.runs[0].bold = True
                p.runs[0].font.size = Pt(10.5)
                if ed.details:
                    d = doc.add_paragraph(ed.details)
                    d.runs[0].font.size = Pt(10.5)

        self._append_optional_sections(doc, data)

        return _save_doc(doc, self.output_dir, filename)

    # ---------- Template: Creative ----------
    def render_creative(self, data: ResumeData, filename: str = "resume_creative.docx") -> str:
        doc = Document()
        _set_document_margins(doc)

        # Bold name + colored headline effect (still ATS-friendly: no shapes)
        name = doc.add_paragraph()
        run = name.add_run(data.full_name)
        run.bold = True
        run.font.size = Pt(24)

        hl = doc.add_paragraph()
        r2 = hl.add_run(data.headline)
        r2.font.size = Pt(12)
        r2.font.color.rgb = RGBColor(40, 90, 140)

        contact = " | ".join([x for x in [data.location, data.email, data.phone] if x])
        if data.links:
            contact = " | ".join([contact] + data.links) if contact else " | ".join(data.links)

        if contact:
            cp = doc.add_paragraph(contact)
            cp.runs[0].font.size = Pt(9.5)

        doc.add_paragraph()

        # Split layout using a table: left = skills, right = main content
        layout = doc.add_table(rows=1, cols=2)
        left_cell = layout.rows[0].cells[0]
        right_cell = layout.rows[0].cells[1]

        # Left: Skills blocks
        if data.skills:
            p = left_cell.add_paragraph()
            rr = p.add_run("SKILLS")
            rr.bold = True
            rr.font.size = Pt(10.5)
            for sk in data.skills:
                sp = left_cell.add_paragraph(f"• {sk}")
                sp.runs[0].font.size = Pt(10)

        if data.certifications:
            p = left_cell.add_paragraph()
            rr = p.add_run("CERTIFICATIONS")
            rr.bold = True
            rr.font.size = Pt(10.5)
            for c in data.certifications:
                sp = left_cell.add_paragraph(f"• {c}")
                sp.runs[0].font.size = Pt(10)

        # Right: Summary + Experience + Education
        if data.summary.strip():
            p = right_cell.add_paragraph()
            rr = p.add_run("SUMMARY")
            rr.bold = True
            rr.font.size = Pt(10.5)
            sp = right_cell.add_paragraph(data.summary.strip())
            sp.runs[0].font.size = Pt(10.5)

        if data.experience:
            p = right_cell.add_paragraph()
            rr = p.add_run("EXPERIENCE")
            rr.bold = True
            rr.font.size = Pt(10.5)

            for item in data.experience:
                t = right_cell.add_paragraph(f"{item.title} — {item.company}")
                t.runs[0].bold = True
                t.runs[0].font.size = Pt(10.5)

                d = right_cell.add_paragraph(f"{item.start_date} – {item.end_date}" + (f" | {item.location}" if item.location else ""))
                d.runs[0].italic = True
                d.runs[0].font.size = Pt(9.5)

                for b in item.bullets:
                    bp = right_cell.add_paragraph(f"• {b}")
                    bp.runs[0].font.size = Pt(10.5)

        if data.education:
            p = right_cell.add_paragraph()
            rr = p.add_run("EDUCATION")
            rr.bold = True
            rr.font.size = Pt(10.5)

            for ed in data.education:
                line = f"{ed.degree} — {ed.institution}"
                if ed.year:
                    line += f" ({ed.year})"
                ep = right_cell.add_paragraph(line)
                ep.runs[0].bold = True
                ep.runs[0].font.size = Pt(10.5)
                if ed.details:
                    dp = right_cell.add_paragraph(ed.details)
                    dp.runs[0].font.size = Pt(10.5)

        if data.projects:
            p = right_cell.add_paragraph()
            rr = p.add_run("PROJECTS")
            rr.bold = True
            rr.font.size = Pt(10.5)
            for prj in data.projects:
                prjp = right_cell.add_paragraph(f"• {prj}")
                prjp.runs[0].font.size = Pt(10.5)

        return _save_doc(doc, self.output_dir, filename)

    # ---------- Template: Technical ----------
    def render_technical(self, data: ResumeData, filename: str = "resume_technical.docx") -> str:
        doc = Document()
        _set_document_margins(doc)

        # Compact header
        p = doc.add_paragraph()
        r = p.add_run(data.full_name)
        r.bold = True
        r.font.size = Pt(18)

        h = doc.add_paragraph(data.headline)
        h.runs[0].font.size = Pt(11)

        contact = " | ".join([x for x in [data.location, data.email, data.phone] if x])
        if data.links:
            contact = " | ".join([contact] + data.links) if contact else " | ".join(data.links)
        if contact:
            c = doc.add_paragraph(contact)
            c.runs[0].font.size = Pt(9.5)

        doc.add_paragraph()

        # Technical summary (brief)
        if data.summary.strip():
            _add_heading(doc, "Professional Summary")
            s = doc.add_paragraph(data.summary.strip())
            s.runs[0].font.size = Pt(10.5)

        # Skills categorized: quick heuristic split
        if data.skills:
            _add_heading(doc, "Technical Skills")
            # simple layout with 2 columns table
            table = doc.add_table(rows=1, cols=2)
            left = table.rows[0].cells[0]
            right = table.rows[0].cells[1]

            half = (len(data.skills) + 1) // 2
            for i, sk in enumerate(data.skills):
                cell = left if i < half else right
                p = cell.add_paragraph(f"• {sk}")
                p.runs[0].font.size = Pt(10.5)

        # Experience with emphasis on tools/results
        if data.experience:
            _add_heading(doc, "Experience")
            for item in data.experience:
                _add_kv_line(doc, f"{item.title} — {item.company}", f"{item.start_date} – {item.end_date}")
                if item.location:
                    lp = doc.add_paragraph(item.location)
                    lp.runs[0].italic = True
                    lp.runs[0].font.size = Pt(9.5)
                for b in item.bullets:
                    bp = doc.add_paragraph(b)
                    bp.style = doc.styles["List Bullet"]
                    bp.runs[0].font.size = Pt(10.5)

        # Education
        if data.education:
            _add_heading(doc, "Education")
            for ed in data.education:
                line = f"{ed.degree} — {ed.institution}"
                if ed.year:
                    line += f" ({ed.year})"
                p = doc.add_paragraph(line)
                p.runs[0].bold = True
                p.runs[0].font.size = Pt(10.5)
                if ed.details:
                    d = doc.add_paragraph(ed.details)
                    d.runs[0].font.size = Pt(10.5)

        self._append_optional_sections(doc, data)

        return _save_doc(doc, self.output_dir, filename)

    # ---------- Optional sections appended to templates ----------
    def _append_optional_sections(self, doc: Document, data: ResumeData) -> None:
        if data.certifications:
            _add_heading(doc, "Certifications")
            for c in data.certifications:
                p = doc.add_paragraph(c)
                p.style = doc.styles["List Bullet"]
                p.runs[0].font.size = Pt(10.5)

        if data.projects:
            _add_heading(doc, "Projects")
            for prj in data.projects:
                p = doc.add_paragraph(prj)
                p.style = doc.styles["List Bullet"]
                p.runs[0].font.size = Pt(10.5)


# -------------------------
# Quick test runner
# -------------------------
if __name__ == "__main__":
    sample = ResumeData(
        full_name="Charles Example",
        headline="Monitoring, Evaluation & Learning (MEL) Manager | Data Analyst | Power BI | SQL | Python",
        location="Juba, South Sudan",
        email="charles@example.com",
        phone="+211-000-000-000",
        links=["linkedin.com/in/charles-example", "github.com/charles-example"],
        summary=(
            "MEL professional with 8+ years of experience building monitoring systems, improving data quality, "
            "and producing donor-ready reports. Strong in Power BI, SQL, and survey systems (Kobo/ODK), "
            "with a focus on actionable insights and learning."
        ),
        skills=[
            "Monitoring & Evaluation", "Indicator Tracking", "Power BI Dashboards", "SQL", "Python",
            "KoboToolbox / ODK", "Data Quality Audits", "Donor Reporting", "Data Visualization", "Data Management"
        ],
        experience=[
            ExperienceItem(
                title="Field MEL Manager",
                company="Example NGO",
                start_date="2023",
                end_date="Present",
                location="South Sudan",
                bullets=[
                    "Designed and maintained indicator tracking system; improved reporting timeliness by 35%.",
                    "Built Power BI dashboards for program performance and donor reporting.",
                    "Led routine data quality audits and coached field teams on data standards.",
                ],
            ),
            ExperienceItem(
                title="Database Manager",
                company="Example INGO",
                start_date="2019",
                end_date="2023",
                location="South Sudan",
                bullets=[
                    "Developed SQL queries and automated reporting outputs for weekly/monthly reporting cycles.",
                    "Managed KoboToolbox forms and data pipelines; ensured clean, analysis-ready datasets.",
                ],
            ),
        ],
        education=[
            EducationItem(degree="MSc Data Science", institution="Guglielmo Marconi University", year="2024"),
            EducationItem(degree="BA (or BSc) — Relevant Field", institution="Your University", year="2016"),
        ],
        certifications=["Power BI (Intermediate/Advanced)", "KoboToolbox/XLSForm (Advanced)"],
        projects=["Built automated reporting pipeline integrating Kobo exports → SQL → Power BI dashboards."],
    )

    renderer = ResumeTemplateRenderer(output_dir="generated_documents")

    paths = []
    paths.append(renderer.render_modern(sample))
    paths.append(renderer.render_executive(sample))
    paths.append(renderer.render_creative(sample))
    paths.append(renderer.render_technical(sample))

    print("Generated DOCX files:")
    for p in paths:
        print(" -", p)
