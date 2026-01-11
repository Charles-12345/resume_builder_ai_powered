import streamlit as st

APP_BRAND = "Resume Builder AI™ — by DOKA CHARLES DANIEL"
BRAND_LINE = "Generated with Resume Builder AI™ — by DOKA CHARLES DANIEL"

def apply_page_config() -> None:
    st.set_page_config(
        page_title=APP_BRAND,
        page_icon="📄",
        layout="wide",
        menu_items={
            "About": (
                "Resume Builder AI™\n\n"
                "Built by DOKA CHARLES DANIEL\n"
                "© 2026"
            )
        },
    )

def render_brand_sidebar() -> None:
    with st.sidebar:
        st.markdown("## 📄 Resume Builder AI™")
        st.caption("by **DOKA CHARLES DANIEL**")
        st.divider()

def render_brand_header() -> None:
    st.markdown(f"# 📄 {APP_BRAND}")
    st.caption("ATS-friendly resume + cover letter generator • DOCX export • ATS score checker")

def render_footer() -> None:
    st.markdown(
        """
        <style>
          .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background: white;
            border-top: 1px solid #eee;
            padding: 8px 16px;
            text-align: center;
            font-size: 12px;
            color: #666;
            z-index: 9999;
          }
        </style>
        <div class="footer">
          Resume Builder AI™ — by DOKA CHARLES DANIEL • © 2026
        </div>
        """,
        unsafe_allow_html=True,
    )
