import streamlit as st


def inject_css(theme="dark"):
    dark = theme == "dark"
    if dark:
        vars_ = """
        --bg:#07111f; --surface:#0d1726; --surface2:#111f31; --surface3:#16263a;
        --ink:#f5f7fb; --muted:#a9b6c7; --subtle:#7f90a5; --line:#24354a;
        --accent:#35d6a0; --accent2:#7cf0c5; --accent-bg:#0d3a30;
        --danger:#ff7b8a; --warning:#ffc76b; --info:#79b8ff;
        --shadow:0 18px 55px rgba(0,0,0,.28); --hero:#081421;
        """
    else:
        vars_ = """
        --bg:#f5f7fb; --surface:#ffffff; --surface2:#f8fafc; --surface3:#eef3f7;
        --ink:#101828; --muted:#475467; --subtle:#667085; --line:#d9e0e8;
        --accent:#087a52; --accent2:#12b981; --accent-bg:#e8f8f1;
        --danger:#b42318; --warning:#b54708; --info:#175cd3;
        --shadow:0 16px 45px rgba(16,24,40,.08); --hero:#081421;
        """

    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
    :root {{ {vars_} }}

    html, body, [class*="css"], [data-testid="stAppViewContainer"] {{
        font-family:'DM Sans',sans-serif !important;
    }}
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
        background:var(--bg) !important;
        color:var(--ink) !important;
    }}
    .main .block-container {{ max-width:1480px; padding-top:2rem; padding-bottom:4rem; }}
    h1,h2,h3,h4,h5,h6,p,span,label,li,small {{ color:var(--ink); }}
    p, .stMarkdown, .stCaption {{ color:var(--muted); }}
    .stCaption {{ color:var(--subtle) !important; }}

    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background:linear-gradient(180deg,#07111f 0%,#0b1726 100%) !important;
        border-right:1px solid #1d2c40 !important;
    }}
    section[data-testid="stSidebar"] * {{ color:#eaf1f8 !important; }}
    section[data-testid="stSidebar"] .stButton>button {{
        background:transparent !important; border:1px solid transparent !important;
        color:#dbe6f0 !important; border-radius:13px !important; min-height:43px;
        text-align:left !important; padding:0 14px !important; transition:.18s ease;
    }}
    section[data-testid="stSidebar"] .stButton>button:hover {{
        background:#142338 !important; border-color:#20344c !important; transform:translateX(2px);
    }}
    section[data-testid="stSidebar"] .stDivider {{ border-color:#203247 !important; }}

    /* Brand */
    .brand-row {{ display:flex; align-items:center; gap:12px; margin:3px 0 22px; }}
    .brand-mark {{ width:42px; height:42px; border-radius:14px; display:grid; place-items:center;
        background:linear-gradient(135deg,#35d6a0,#0d8f68); box-shadow:0 10px 25px rgba(53,214,160,.18); font-size:21px; }}
    .brand-name {{ font-family:'Manrope'; font-size:18px; font-weight:800; color:#fff; line-height:1; }}
    .brand-sub {{ font-size:11px; color:#91a3b8 !important; margin-top:4px; }}

    /* Hero */
    .hero {{ position:relative; overflow:hidden; border:1px solid rgba(255,255,255,.08); border-radius:30px;
        padding:46px 48px; margin:0 0 26px; background:linear-gradient(120deg,#07111f 0%,#0b2231 52%,#075c49 100%);
        box-shadow:0 24px 70px rgba(5,15,28,.20); color:#fff; }}
    .hero:before {{ content:''; position:absolute; width:420px; height:420px; border-radius:50%; right:-120px; top:-210px;
        background:radial-gradient(circle,rgba(53,214,160,.22),rgba(53,214,160,0) 68%); }}
    .hero:after {{ content:''; position:absolute; width:210px; height:210px; border-radius:50%; left:45%; bottom:-160px;
        background:rgba(255,255,255,.035); }}
    .hero > * {{ position:relative; z-index:1; }}
    .hero .eyebrow {{ font-size:11px; letter-spacing:1.7px; font-weight:800; color:#72efc1 !important; text-transform:uppercase; }}
    .hero h1 {{ font-family:'Manrope'; font-size:clamp(34px,4.3vw,58px); line-height:1.02; letter-spacing:-2.6px;
        margin:10px 0 14px; font-weight:800; color:#fff !important; }}
    .hero p {{ max-width:820px; color:#d8e5ed !important; font-size:16px; line-height:1.65; margin:0; }}

    /* Cards */
    .card,.feature,.metric {{ background:var(--surface) !important; border:1px solid var(--line) !important;
        box-shadow:var(--shadow); color:var(--ink) !important; }}
    .card {{ border-radius:22px; padding:22px; }}
    .metric {{ border-radius:20px; padding:19px 20px; min-height:108px; }}
    .metric-value {{ font-family:'Manrope'; font-size:32px; line-height:1; font-weight:800; color:var(--ink) !important; }}
    .metric-label {{ font-size:12px; color:var(--muted) !important; margin-top:8px; }}
    .metric-accent {{ width:34px; height:4px; border-radius:99px; background:var(--accent2); margin-bottom:15px; }}
    .section {{ font-family:'Manrope'; font-size:24px; font-weight:800; color:var(--ink) !important; margin:26px 0 12px; letter-spacing:-.5px; }}
    .section-sub {{ color:var(--muted) !important; font-size:13px; margin:-5px 0 14px; }}
    .pill {{ display:inline-block; border-radius:999px; padding:6px 11px; background:var(--accent-bg) !important;
        color:var(--accent) !important; font-size:11px; font-weight:800; border:1px solid rgba(18,185,129,.18); }}
    .feature {{ border-radius:19px; padding:19px; min-height:132px; transition:.18s ease; }}
    .feature:hover {{ transform:translateY(-2px); box-shadow:0 20px 42px rgba(16,24,40,.12); }}
    .feature h4 {{ margin:0 0 7px; font-family:'Manrope'; color:var(--ink) !important; font-size:15px; }}
    .feature p {{ margin:0; color:var(--muted) !important; font-size:13px; line-height:1.52; }}

    /* Streamlit controls: high-contrast in both themes */
    .stTextInput input,.stNumberInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"] > div,
    .stMultiSelect div[data-baseweb="select"] > div,.stDateInput input,.stTimeInput input {{
        background:var(--surface2) !important; color:var(--ink) !important; border-color:var(--line) !important;
    }}
    input::placeholder, textarea::placeholder {{ color:var(--subtle) !important; opacity:1 !important; }}
    [data-baseweb="select"] *, [role="option"] {{ color:var(--ink) !important; }}
    [role="listbox"], [data-baseweb="popover"] > div {{ background:var(--surface) !important; color:var(--ink) !important; }}
    .stRadio label, .stCheckbox label, .stSelectbox label, .stMultiSelect label, .stFileUploader label,
    .stSlider label, .stTextInput label, .stNumberInput label {{ color:var(--ink) !important; font-weight:600 !important; }}
    .stButton>button, .stDownloadButton>button {{
        border-radius:13px !important; font-weight:700 !important; min-height:43px;
        border:1px solid var(--line) !important; background:var(--surface) !important; color:var(--ink) !important;
    }}
    .stButton>button:hover, .stDownloadButton>button:hover {{ border-color:var(--accent2) !important; transform:translateY(-1px); }}
    .stButton>button[kind="primary"] {{ background:linear-gradient(135deg,#087a52,#12b981) !important;
        color:#fff !important; border-color:#12b981 !important; box-shadow:0 12px 25px rgba(18,185,129,.18); }}
    .stButton>button[kind="primary"] * {{ color:#fff !important; }}

    /* Tabs, expanders, alerts, tables */
    .stTabs [data-baseweb="tab-list"] {{ gap:8px; border-bottom:1px solid var(--line); }}
    .stTabs [data-baseweb="tab"] {{ color:var(--muted) !important; font-weight:700; }}
    .stTabs [aria-selected="true"] {{ color:var(--accent) !important; }}
    .streamlit-expanderHeader {{ background:var(--surface) !important; color:var(--ink) !important; border:1px solid var(--line); border-radius:14px; }}
    .stAlert {{ background:var(--surface2) !important; border:1px solid var(--line) !important; color:var(--ink) !important; }}
    .stAlert p,.stAlert span {{ color:var(--ink) !important; }}
    [data-testid="stDataFrame"] {{ border:1px solid var(--line) !important; border-radius:16px; overflow:hidden; }}
    [data-testid="stMetric"] {{ background:var(--surface) !important; border:1px solid var(--line) !important; border-radius:18px; }}
    [data-testid="stMetricLabel"], [data-testid="stMetricValue"] {{ color:var(--ink) !important; }}
    hr {{ border-color:var(--line) !important; }}

    .status-pass {{ color:#12b981 !important; font-weight:800; }}
    .status-review {{ color:#f59e0b !important; font-weight:800; }}
    .status-issue {{ color:#ef6675 !important; font-weight:800; }}
    .small-note {{ color:var(--subtle) !important; font-size:11px; line-height:1.5; }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle, eyebrow="LABEL LENS • INSPECTION INTELLIGENCE"):
    st.markdown(f'''<div class="hero"><div class="eyebrow">{eyebrow}</div>
    <h1>{title}</h1><p>{subtitle}</p></div>''', unsafe_allow_html=True)


def metric_card(value, label):
    st.markdown(f'''<div class="metric"><div class="metric-accent"></div>
    <div class="metric-value">{value}</div><div class="metric-label">{label}</div></div>''', unsafe_allow_html=True)


def feature_card(icon, title, desc):
    st.markdown(f'''<div class="feature"><h4>{icon} {title}</h4>
    <p>{desc}</p></div>''', unsafe_allow_html=True)
