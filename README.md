# Resume Builder AI™ — by DOKA CHARLES DANIEL

AI-powered Resume + Cover Letter Builder built with **Streamlit**, **python-docx**, and **Hugging Face** models.  
Generate ATS-friendly resumes, tailored cover letters, and an ATS optimization score — then export to **DOCX**.

**Live/Hosting:** Streamlit Cloud  
**Author:** DOKA CHARLES DANIEL  
**Support:** charlesdanieldoka@gmail.com  
**Repository:** https://github.com/Charles-12345/resume_builder_ai_powered

---

## ✨ Features

### 📄 Resume Builder
- Collect structured profile information (contacts, links, skills, experience, education)
- Generate an AI-written professional summary
- Add multiple experience and education entries
- Optional sections: certifications, projects
- Export to DOCX with multiple templates:
  - `modern`
  - `executive`
  - `creative`
  - `technical`

### ✉️ Cover Letter Generator
- Generate tailored cover letters based on:
  - Target role + company
  - Skills + achievements
  - Motivation + job description (optional)
- Export cover letter to DOCX

### ✅ ATS Optimization Checker
- Compare resume text vs job description
- Returns:
  - Score /100
  - Matched keywords
  - Missing keywords
  - Improvement notes

### 📊 Admin Dashboard (optional)
- Basic usage tracking (events)
- Downloads, resume generation counts, etc.
- Requires `ADMIN_PASSWORD`

### 🔒 Monetization (optional “Paywall Gate”)
- Gate downloads behind a simple unlock mechanism
- Payment link button + unlock code flow
- Controlled via environment variables / Streamlit Secrets

---

## 🧱 Project Structure

```text
resume_builder_ai_powered/
├─ app.py                          # Main Streamlit app
├─ models/
│  ├─ __init__.py
│  ├─ resume_generator_enhanced.py # Resume generation logic
│  └─ cover_letter_enhanced.py     # Cover letter generation logic
├─ app_templates/
│  ├─ __init__.py
│  └─ resume_templates.py          # DOCX rendering + templates
├─ utils/
│  ├─ __init__.py
│  ├─ branding.py                  # Branding + UI helpers
│  └─ analytics.py                 # Logging + DB events (optional)
├─ generated_documents/            # Output folder (auto-created)
└─ requirements.txt
