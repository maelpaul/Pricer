"""
Options and Bonds Pricer
Main Streamlit application entrypoint.
"""

import streamlit as st

# ── PAGE CONFIG ──────────────────────────────────────────────
st.set_page_config(
    page_title="Options and Bonds Pricer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM CSS ───────────────────────────────────────────────
st.markdown("""
<style>
/* Import Google Font */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* Global font */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background-color: #fafafa;
    border-right: 1px solid #e5e5e5;
}

/* Metric cards styling */
[data-testid="stMetric"] {
    background-color: #ffffff;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 12px 16px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

[data-testid="stMetric"] label {
    font-size: 0.7rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    color: #666 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    color: #1a1a1a !important;
}

/* Section headers */
h4 {
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    color: #888 !important;
    margin-top: 1.5rem !important;
    margin-bottom: 0.8rem !important;
    border-bottom: none !important;
}

/* Expander styling */
[data-testid="stExpander"] {
    border: 1px solid #e8e8e8 !important;
    border-radius: 8px !important;
    margin-bottom: 8px !important;
    background-color: #ffffff !important;
}

[data-testid="stExpander"] summary {
    font-weight: 500 !important;
    font-size: 0.9rem !important;
}

/* DataFrame styling */
[data-testid="stDataFrame"] {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
}

/* Main area padding */
.main .block-container {
    padding-top: 1rem;
    padding-bottom: 2rem;
}

/* Logo area */
.header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 0.5rem;
}

.title {
    font-size: 0.9rem;
    font-weight: 700;
    color: #1a1a1a;
    margin: 0;
}

.badge {
    background-color: #fee;
    color: #c0392b;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid #f5c6cb;
    letter-spacing: 0.3px;
}

/* Slider label */
[data-testid="stSlider"] [data-testid="stMarkdownContainer"] {
    font-size: 0.85rem;
}

/* Number input compact */
[data-testid="stNumberInput"] {
    margin-bottom: -0.5rem;
}

/* Delta indicators in metrics */
[data-testid="stMetricDelta"] svg {
    display: inline;
}

/* Hide Streamlit branding but keep sidebar toggle */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {background: transparent !important;}
</style>
""", unsafe_allow_html=True)


# ── SIDEBAR HEADER ───────────────────────────────────────────
with st.sidebar:
    # Logo text-based
    st.markdown("""
    <div style="margin-bottom: 5px;">
        <span style="font-size: 1.4rem; font-weight: 700; color: #1a1a1a; font-family: 'Inter', sans-serif;">Pricer</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # Navigation
    page = st.selectbox(
        "Navigation",
        ["Options", "Bonds"],  # ["Turbo", "Discount Cert.", "Bonus Cert.", "Interview"],
        label_visibility="collapsed",
    )

    st.markdown("---")


# ── PAGE ROUTING ─────────────────────────────────────────────
if page == "Options":
    from views.options import render_sidebar, render
    params = render_sidebar()
    render(params)

elif page == "Bonds":
    from views.bonds import render_sidebar, render
    params = render_sidebar()
    render(params)

# elif page == "Turbo":
#     from views.turbo import render_sidebar, render
#     params = render_sidebar()
#     render(params)
#
# elif page == "Discount Cert.":
#     from views.discount_cert import render_sidebar, render
#     params = render_sidebar()
#     render(params)
#
# elif page == "Bonus Cert.":
#     from views.bonus_cert import render_sidebar, render
#     params = render_sidebar()
#     render(params)
#
# elif page == "Interview":
#     from views.interview import render_sidebar, render
#     render_sidebar()
#     render()
