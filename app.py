
import os
import re
import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
USDA_PATH = DATA_DIR / "Dataset USDA Food Clean.csv"
HEALTHY_PATH = DATA_DIR / "Dataset Healthy Clean.csv"
NUTRITION_PATH = DATA_DIR / "nutrition.csv"

st.set_page_config(page_title="Aku Sehat AI", page_icon="🥗", layout="wide")

# UI theme: colorful, modern, and nutrition-focused.
st.markdown("""
<style>
    :root {
        --navy: #102a43;
        --navy-soft: #243b53;
        --teal: #159a8c;
        --teal-dark: #087f73;
        --mint: #e9f8f4;
        --gold: #f2b84b;
        --ink: #172b4d;
        --muted: #6b7c93;
        --line: #e4eaf0;
    }

    .stApp {
        background:
            radial-gradient(circle at 8% 8%, rgba(21,154,140,.10), transparent 28%),
            radial-gradient(circle at 92% 12%, rgba(242,184,75,.10), transparent 24%),
            #f6f8fb;
        color: var(--ink);
    }
    [data-testid="stHeader"] { background: rgba(246,248,251,.88); }
    [data-testid="stToolbar"] { opacity: .75; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1420px; }

    /* Elegant dark sidebar with high-contrast, readable controls. */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #102a43 0%, #173f52 58%, #126b68 100%);
        border-right: 1px solid rgba(255,255,255,.12);
    }
    [data-testid="stSidebar"] > div:first-child { padding: 1.25rem .95rem 1.5rem; }
    [data-testid="stSidebar"] * { box-sizing: border-box; }
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] small {
        color: #edf7f6 !important;
        font-weight: 600;
    }
    [data-testid="stSidebar"] [data-testid="stForm"] {
        background: rgba(255,255,255,.075) !important;
        border: 1px solid rgba(255,255,255,.18) !important;
        border-radius: 20px !important;
        padding: 15px 13px !important;
        box-shadow: 0 14px 30px rgba(0,0,0,.10);
    }
    [data-testid="stSidebar"] input,
    [data-testid="stSidebar"] textarea {
        background: #ffffff !important;
        color: #172b4d !important;
        -webkit-text-fill-color: #172b4d !important;
        caret-color: #159a8c !important;
        border: 1px solid #dbe5eb !important;
        border-radius: 11px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] input::placeholder,
    [data-testid="stSidebar"] textarea::placeholder {
        color: #8295a7 !important;
        -webkit-text-fill-color: #8295a7 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] > div {
        background: #ffffff !important;
        color: #172b4d !important;
        border: 1px solid #dbe5eb !important;
        border-radius: 11px !important;
        min-height: 42px;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] span,
    [data-testid="stSidebar"] [data-baseweb="select"] div,
    [data-testid="stSidebar"] [data-baseweb="select"] input {
        color: #172b4d !important;
        -webkit-text-fill-color: #172b4d !important;
    }
    [data-testid="stSidebar"] [data-testid="stNumberInput"] button {
        color: #173f52 !important;
        background: #eaf5f3 !important;
        border-radius: 8px !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #f2b84b, #f5cf78) !important;
        color: #173f52 !important;
        border: 0 !important;
        box-shadow: none !important;
    }

    h1 {
        color: var(--navy) !important;
        font-weight: 850 !important;
        letter-spacing: -.045em;
    }
    h2, h3 { color: var(--navy) !important; letter-spacing: -.025em; }
    p, li, label { line-height: 1.55; }

    [data-testid="stMetric"] {
        background: rgba(255,255,255,.96);
        border: 1px solid var(--line);
        border-top: 4px solid var(--teal);
        padding: 18px 18px 15px;
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(16,42,67,.07);
    }
    [data-testid="stMetricLabel"] { color: #6b7c93 !important; font-weight: 650; }
    [data-testid="stMetricValue"] { color: var(--navy) !important; font-weight: 850; }

    div[data-testid="stForm"], [data-testid="stExpander"] {
        background: rgba(255,255,255,.94);
        border: 1px solid var(--line);
        border-radius: 18px;
        box-shadow: 0 10px 28px rgba(16,42,67,.055);
    }
    [data-testid="stTabs"] { border-bottom: 1px solid #dfe7ee; }
    [data-testid="stTabs"] button { font-weight: 750; color: #6b7c93; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: var(--teal-dark) !important;
        border-bottom-color: var(--teal) !important;
    }
    .stButton > button {
        border: 1px solid rgba(8,127,115,.12);
        border-radius: 12px;
        padding: .62rem 1rem;
        font-weight: 750;
        color: white;
        background: linear-gradient(135deg, #087f73, #159a8c);
        box-shadow: 0 6px 16px rgba(8,127,115,.18);
        transition: transform .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 22px rgba(8,127,115,.25);
    }
    [data-testid="stProgressBar"] > div > div > div {
        background: linear-gradient(90deg, #159a8c, #f2b84b) !important;
    }
    .small-note { color: var(--muted); font-size: .88rem; }
    .section-card {
        padding: 20px 22px;
        border-radius: 20px;
        background: linear-gradient(135deg, #ffffff, #effaf7);
        border: 1px solid #d7ece7;
        margin: 10px 0 18px;
        box-shadow: 0 8px 22px rgba(16,42,67,.04);
    }
    .food-card {
        padding: 18px;
        border-radius: 18px;
        background: #ffffff;
        border: 1px solid #e4eaf0;
        border-left: 5px solid var(--gold);
        box-shadow: 0 8px 22px rgba(16,42,67,.06);
    }
    .stAlert { border-radius: 14px; }

    /* Compact brand header: simple, polished, and visually layered */
    .brand-header {
        position: relative; overflow: hidden;
        display: flex; align-items: center; gap: 16px;
        padding: 20px 24px; margin: 0 0 16px;
        border: 1px solid #d9e9e5; border-radius: 22px;
        background: linear-gradient(115deg, #edf9f5 0%, #ffffff 62%, #fff7e5 100%);
        box-shadow: 0 10px 28px rgba(16,42,67,.065);
    }
    .brand-header::after {
        content: ''; position:absolute; width:180px; height:180px; right:-70px; top:-105px;
        border-radius:50%; background:rgba(21,154,140,.10); box-shadow:-55px 115px 0 20px rgba(242,184,75,.09);
    }
    .brand-icon {
        position:relative; z-index:1; width:58px; height:58px; display:flex; align-items:center; justify-content:center;
        border-radius:18px; background:linear-gradient(145deg,#087f73,#21b49e);
        font-size:29px; box-shadow:0 9px 18px rgba(8,127,115,.22);
    }
    .brand-copy { position:relative; z-index:1; }
    .brand-kicker { color:#087f73; font-size:.70rem; font-weight:850; letter-spacing:.13em; text-transform:uppercase; margin-bottom:3px; }
    .brand-title { color:#102a43; font-size:1.85rem; font-weight:900; letter-spacing:-.05em; line-height:1.05; }
    .brand-title span { color:#087f73; }
    .brand-subtitle { color:#6b7c93; font-size:.92rem; margin-top:7px; }

    /* Page-specific visual identity */
    .page-hero {
        position:relative; overflow:hidden; padding:18px 22px; margin:8px 0 18px;
        border-radius:18px; border:1px solid #dfe9ef;
        background:linear-gradient(115deg,#ffffff 0%,#f4faf9 68%,#fff8e9 100%);
        box-shadow:0 8px 22px rgba(16,42,67,.045);
    }
    .page-hero::after { content:''; position:absolute; width:115px; height:115px; right:-35px; top:-50px; border-radius:50%; background:rgba(21,154,140,.08); }
    .page-chip { display:inline-block; padding:5px 10px; border-radius:999px; background:#e5f5f0; color:#087f73; font-size:.72rem; font-weight:850; letter-spacing:.06em; text-transform:uppercase; }
    .page-title { margin:7px 0 2px; color:#102a43; font-size:1.35rem; font-weight:850; letter-spacing:-.03em; }
    .page-desc { margin:0; color:#71839a; font-size:.9rem; }
    .section-label { display:flex; align-items:center; gap:9px; margin:20px 0 10px; color:#102a43; font-size:1.12rem; font-weight:850; }
    .section-label span { display:inline-flex; width:30px; height:30px; align-items:center; justify-content:center; border-radius:10px; background:#e6f6f1; color:#087f73; }
    .mini-note { padding:12px 15px; border-radius:13px; background:#fffaf0; border:1px solid #f4e4bf; color:#79632e; font-size:.88rem; }

    /* Sidebar login card and buttons */
    [data-testid="stSidebar"] .login-card {
        background: rgba(255,255,255,.10); border:1px solid rgba(255,255,255,.18);
        border-radius:16px; padding:14px 15px; margin:2px 0 12px;
    }
    [data-testid="stSidebar"] .login-label { color:#b9e9df; font-size:.72rem; font-weight:800; letter-spacing:.10em; }
    [data-testid="stSidebar"] .login-email { color:#ffffff !important; font-size:.88rem; font-weight:700; overflow-wrap:anywhere; margin-top:5px; }
    [data-testid="stSidebar"] .stFormSubmitButton > button {
        background: linear-gradient(135deg,#f3c969,#e8ad3f) !important;
        color:#173f52 !important; border:0 !important; font-weight:850 !important;
        box-shadow:0 7px 16px rgba(0,0,0,.12) !important;
    }
    [data-testid="stSidebar"] .stFormSubmitButton > button:hover { background:#ffd980 !important; }
    [data-testid="stSidebar"] .stButton > button { color:#173f52 !important; }

    /* Tab navigation as rounded page buttons */
    [data-testid="stTabs"] { border-bottom:0 !important; gap:8px; }
    [data-testid="stTabs"] [role="tablist"] { gap:8px; padding:5px; background:#eaf2f1; border:1px solid #d8e7e4; border-radius:16px; }
    [data-testid="stTabs"] button {
        border:1px solid transparent !important; border-radius:11px !important;
        padding:10px 17px !important; color:#557080 !important; font-weight:800 !important;
        background:transparent !important; transition:all .15s ease;
    }
    [data-testid="stTabs"] button:hover { background:#ffffff !important; color:#087f73 !important; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        background:#ffffff !important; color:#087f73 !important;
        border:1px solid #b9ded6 !important; box-shadow:0 4px 12px rgba(16,42,67,.08) !important;
    }
    [data-testid="stTabs"] button[aria-selected="true"]::after { display:none !important; }

    /* Authentication pages */
    .auth-shell {
        max-width: 980px; margin: 2.5rem auto 0; padding: 34px;
        border: 1px solid #d8e9e4; border-radius: 28px;
        background: linear-gradient(135deg, rgba(255,255,255,.98), rgba(237,249,245,.96));
        box-shadow: 0 18px 45px rgba(16,42,67,.10);
    }
    .auth-brand { display:flex; align-items:center; gap:16px; margin-bottom:26px; }
    .auth-icon { width:70px; height:70px; display:flex; align-items:center; justify-content:center;
        border-radius:22px; background:linear-gradient(145deg,#087f73,#21b49e);
        font-size:34px; box-shadow:0 10px 22px rgba(8,127,115,.20); }
    .auth-title { color:#102a43; font-size:2.25rem; font-weight:900; letter-spacing:-.055em; line-height:1.05; }
    .auth-title span { color:#087f73; }
    .auth-subtitle { color:#6b7c93; margin-top:7px; font-size:.96rem; }
    .auth-benefits { display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:10px; margin:22px 0 25px; }
    .auth-benefit { padding:13px; border-radius:15px; background:#f7fcfa; border:1px solid #dceee8; color:#36566a; font-size:.84rem; }
    .auth-benefit strong { display:block; color:#087f73; margin-bottom:3px; }
    .auth-form-card { padding:20px; border:1px solid #e0e9ef; border-radius:20px; background:#ffffff; }
    @media (max-width: 700px) { .auth-shell { padding:22px; } .auth-benefits { grid-template-columns:1fr; } .auth-title { font-size:1.8rem; } }


    /* ULTIMATE POLISH: premium wellness dashboard */
    .stApp::before { content:""; position:fixed; inset:0; pointer-events:none; background:linear-gradient(120deg,rgba(12,148,132,.025),transparent 38%,rgba(242,184,75,.035)); z-index:-1; }
    .main .block-container { animation: pageIn .45s ease-out; }
    @keyframes pageIn { from {opacity:0; transform:translateY(8px)} to {opacity:1; transform:translateY(0)} }
    [data-testid="stVerticalBlock"] > div:has(> .brand-header) { margin-bottom:8px; }
    .brand-header { border-radius:26px !important; padding:22px 26px !important; }
    .brand-title { font-size:2rem !important; }
    .brand-subtitle { max-width:680px; }
    .page-hero { border-radius:22px !important; padding:23px 26px !important; }
    .page-chip { box-shadow:0 3px 10px rgba(8,127,115,.08); }
    .section-card { position:relative; overflow:hidden; }
    .section-card::before { content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:linear-gradient(#159a8c,#f2b84b); }
    .food-card { transition:transform .18s ease, box-shadow .18s ease; }
    .food-card:hover { transform:translateY(-3px); box-shadow:0 14px 30px rgba(16,42,67,.10); }
    .stTextInput input, .stNumberInput input, .stTextArea textarea { border-radius:12px !important; border:1px solid #d7e4e8 !important; background:#fff !important; color:#173f52 !important; }
    .stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div { border-radius:12px !important; border-color:#d7e4e8 !important; }
    .stRadio > div { gap:8px; }
    .stRadio label { background:#f4f9f8; border:1px solid #dcebe7; border-radius:12px; padding:7px 12px; }
    .stDataFrame { border:1px solid #dce7ec; border-radius:16px; overflow:hidden; box-shadow:0 6px 18px rgba(16,42,67,.045); }
    [data-testid="stMetric"]:hover { transform:translateY(-2px); transition:transform .18s ease; }
    .stDownloadButton > button { background:#fff !important; color:#087f73 !important; border:1px solid #b9ded6 !important; }
    .auth-shell { position:relative; overflow:hidden; }
    .auth-shell::before { content:""; position:absolute; width:240px; height:240px; right:-90px; bottom:-120px; border-radius:50%; background:rgba(242,184,75,.12); }
    .auth-form-card { box-shadow:0 8px 24px rgba(16,42,67,.045); }
    .auth-form-card .stFormSubmitButton > button { min-height:46px; font-size:.95rem; }
    @media (max-width:700px) { .brand-header { padding:18px !important; } .brand-title { font-size:1.55rem !important; } .page-hero { padding:18px !important; } }


    /* Streamlit Cloud compatibility: force readable text in light main area. */
    [data-testid="stAppViewContainer"],
    [data-testid="stAppViewContainer"] * {
        --main-text: #17324d;
    }
    [data-testid="stAppViewContainer"] .stMarkdown,
    [data-testid="stAppViewContainer"] .stMarkdown p,
    [data-testid="stAppViewContainer"] .stMarkdown li,
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] legend,
    [data-testid="stAppViewContainer"] [role="radiogroup"] label,
    [data-testid="stAppViewContainer"] [role="radio"] p,
    [data-testid="stAppViewContainer"] [role="tab"] {
        color: #17324d !important;
        -webkit-text-fill-color: #17324d !important;
        opacity: 1 !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p,
    [data-testid="stAppViewContainer"] .stDateInput label,
    [data-testid="stAppViewContainer"] .stTextInput label,
    [data-testid="stAppViewContainer"] .stNumberInput label,
    [data-testid="stAppViewContainer"] .stSelectbox label,
    [data-testid="stAppViewContainer"] .stRadio label {
        color: #36566a !important;
        -webkit-text-fill-color: #36566a !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stTabs"] [role="tab"] {
        color: #557080 !important;
        -webkit-text-fill-color: #557080 !important;
        background: transparent !important;
    }
    [data-testid="stAppViewContainer"] [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        color: #087f73 !important;
        -webkit-text-fill-color: #087f73 !important;
        background: #ffffff !important;
    }
    [data-testid="stAppViewContainer"] input,
    [data-testid="stAppViewContainer"] textarea {
        color: #17324d !important;
        -webkit-text-fill-color: #17324d !important;
        background: #ffffff !important;
    }
    [data-testid="stAppViewContainer"] [data-baseweb="select"] * {
        color: #17324d !important;
        -webkit-text-fill-color: #17324d !important;
    }
    [data-testid="stAppViewContainer"] [role="radio"] {
        color: #17324d !important;
        opacity: 1 !important;
    }

</style>
""", unsafe_allow_html=True)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("SUPABASE_URL dan SUPABASE_KEY belum diatur di file .env.")
    st.stop()

SUPABASE = create_client(SUPABASE_URL, SUPABASE_KEY)


# =========================================================
# AUTHENTICATION
# =========================================================
def register_user(email, password):
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "Format email tidak valid."
    if len(password) < 8:
        return False, "Password minimal 8 karakter."
    try:
        response = SUPABASE.auth.sign_up({"email": email, "password": password})
        if response.user:
            return True, "Registrasi berhasil. Cek email jika verifikasi email aktif."
        return False, "Registrasi gagal."
    except Exception as exc:
        return False, f"Registrasi gagal: {exc}"


def login_user(email, password):
    try:
        response = SUPABASE.auth.sign_in_with_password(
            {"email": email.strip().lower(), "password": password}
        )
        if response.user and response.session:
            return response.user, response.session, None
        return None, None, "Login gagal."
    except Exception as exc:
        return None, None, f"Login gagal: {exc}"


def logout():
    try:
        SUPABASE.auth.sign_out()
    except Exception:
        pass
    for key in [
        "user", "access_token", "refresh_token", "image_result",
        "image_uploaded_name", "recommendation_result"
    ]:
        st.session_state.pop(key, None)
    st.rerun()


def restore_session():
    access_token = st.session_state.get("access_token")
    refresh_token = st.session_state.get("refresh_token")
    if access_token and refresh_token:
        try:
            SUPABASE.auth.set_session(access_token, refresh_token)
        except Exception:
            for key in ["user", "access_token", "refresh_token"]:
                st.session_state.pop(key, None)


def get_current_user():
    restore_session()
    return st.session_state.get("user")


def show_auth():
    st.markdown(
        """
        <div class="auth-shell">
            <div class="auth-brand">
                <div class="auth-icon">🥗</div>
                <div>
                    <div class="auth-title">Aku Sehat <span>AI</span></div>
                    <div class="auth-subtitle">Teman pintar untuk mencatat pola makan, kebugaran, dan keputusan nutrisi harian.</div>
                </div>
            </div>
            <div class="auth-benefits">
                <div class="auth-benefit"><strong>01 · Catat</strong>Simpan konsumsi makanan secara praktis.</div>
                <div class="auth-benefit"><strong>02 · Pahami</strong>Pantau kalori dan makronutrien harian.</div>
                <div class="auth-benefit"><strong>03 · Rencanakan</strong>Dapatkan rekomendasi sesuai tujuanmu.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_tab, register_tab = st.tabs(["🔐 Login", "✨ Buat Akun"] )

    with login_tab:
        st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
        st.subheader("Selamat datang kembali")
        st.caption("Masuk untuk melanjutkan pencatatan dan pemantauan nutrisi.")
        with st.form("login_form"):
            email = st.text_input("Email", placeholder="nama@email.com")
            password = st.text_input("Password", type="password", placeholder="Masukkan password")
            submitted = st.form_submit_button("Masuk ke Aku Sehat AI", use_container_width=True)
            if submitted:
                user, session, error = login_user(email, password)
                if user and session:
                    st.session_state["user"] = user
                    st.session_state["access_token"] = session.access_token
                    st.session_state["refresh_token"] = session.refresh_token
                    st.success("Login berhasil.")
                    st.rerun()
                else:
                    st.error(error or "Login gagal.")
        st.markdown('</div>', unsafe_allow_html=True)

    with register_tab:
        st.markdown('<div class="auth-form-card">', unsafe_allow_html=True)
        st.subheader("Mulai perjalanan sehatmu")
        st.caption("Buat akun untuk menyimpan profil, catatan makanan, dan simulasi.")
        with st.form("register_form"):
            email = st.text_input("Email untuk akun", placeholder="nama@email.com")
            password_1 = st.text_input("Password baru", type="password", placeholder="Minimal 8 karakter")
            password_2 = st.text_input("Konfirmasi password", type="password", placeholder="Ulangi password")
            submitted = st.form_submit_button("Buat Akun", use_container_width=True)
            if submitted:
                if password_1 != password_2:
                    st.error("Konfirmasi password tidak sama.")
                else:
                    ok, message = register_user(email, password_1)
                    (st.success if ok else st.error)(message)
        st.markdown('</div>', unsafe_allow_html=True)


# =========================================================
# DATASET BACKEND
# =========================================================
@st.cache_data
def load_catalog():
    """Load only the cleaned Nutrition Indonesia dataset.

    The application intentionally uses one source so recommendations and manual
    correction do not mix USDA/Healthy records with Indonesian food records.
    Only the four complete core nutrients are used: calories, protein, fat,
    and carbohydrates. Rows with missing or implausible core values are removed.
    All values are normalized to a per-100 g basis.
    """
    if not NUTRITION_PATH.exists():
        return pd.DataFrame()

    nf = pd.read_csv(NUTRITION_PATH)
    nf = nf.rename(columns={
        "name": "food_name",
        "proteins": "protein_g",
        "fat": "fat_g",
        "carbohydrate": "carbs_g",
    })

    required = ["food_name", "calories", "protein_g", "fat_g", "carbs_g"]
    missing = [c for c in required if c not in nf.columns]
    if missing:
        raise ValueError(f"Kolom wajib pada nutrition.csv tidak ditemukan: {missing}")

    nf = nf.drop(columns=[c for c in nf.columns if c.lower().startswith("unnamed:")], errors="ignore").copy()
    for col in ["calories", "protein_g", "fat_g", "carbs_g"]:
        nf[col] = pd.to_numeric(nf[col], errors="coerce")

    nf["food_name"] = nf["food_name"].fillna("").astype(str).str.strip()
    nf["food_type"] = nf.get("food_type", "").fillna("").astype(str) if hasattr(nf.get("food_type", ""), "fillna") else ""
    for col in ["fiber_g", "sugar_g", "sodium_mg", "health_score"]:
        nf[col] = np.nan

    # Keep only complete core nutrition rows.
    nf = nf.dropna(subset=required)
    nf = nf[(nf["food_name"] != "") & (nf["calories"] > 0)]
    core = ["protein_g", "fat_g", "carbs_g"]
    nf = nf[(nf[core] >= 0).all(axis=1)]
    nf = nf[(nf[core] <= 100).all(axis=1)]

    # Energy consistency check with modest tolerance for database rounding.
    macro_energy = 4 * nf["protein_g"] + 9 * nf["fat_g"] + 4 * nf["carbs_g"]
    nf = nf[macro_energy <= nf["calories"] * 1.35]

    nf["serving_size"] = 100.0
    nf["serving_unit"] = "G"
    nf["source"] = "Nutrition Indonesia"

    catalog = nf[[
        "food_name", "food_type", "calories", "protein_g", "fat_g", "carbs_g",
        "fiber_g", "sugar_g", "sodium_mg", "health_score", "serving_size",
        "serving_unit", "source"
    ]].copy()
    catalog = catalog.drop_duplicates(
        subset=["food_name", "calories", "protein_g", "fat_g", "carbs_g"]
    ).reset_index(drop=True)
    return catalog

def validate_nutrients(nutrients):
    """Return warnings for impossible or suspicious nutrient combinations."""
    warnings = []
    try:
        calories = float(nutrients.get("calories") or 0)
        protein = float(nutrients.get("protein_g") or 0)
        fat = float(nutrients.get("fat_g") or 0)
        carbs = float(nutrients.get("carbs_g") or 0)
        if min(calories, protein, fat, carbs) < 0:
            warnings.append("Nilai nutrisi tidak boleh negatif.")
        macro_energy = 4 * protein + 9 * fat + 4 * carbs
        if calories > 0 and macro_energy > calories * 1.35:
            warnings.append("Kalori tidak konsisten dengan jumlah makronutrien.")
        if protein > 1000 or fat > 1000 or carbs > 1000:
            warnings.append("Nilai makronutrien sangat tinggi; periksa satuan dan porsinya.")
    except (TypeError, ValueError):
        warnings.append("Ada nilai nutrisi yang tidak valid.")
    return warnings

def indonesia_catalog_only():
    """Return the Indonesian nutrition source as the primary recommendation catalog."""
    catalog = load_catalog()
    if catalog.empty:
        return catalog
    result = catalog[catalog["source"].eq("Nutrition Indonesia")].copy()
    return result if not result.empty else catalog.copy()


def best_indonesia_match(query, limit=12):
    """Search only the Indonesian nutrition catalog for correction/recommendation workflows."""
    catalog = indonesia_catalog_only()
    if catalog.empty:
        return catalog
    q = normalize_text(query)
    if not q:
        return catalog.head(limit)
    names = catalog["food_name"].fillna("").astype(str).map(normalize_text)
    score = pd.Series(0, index=catalog.index, dtype="int64")
    for variant in query_variants(query):
        v = normalize_text(variant)
        if not v:
            continue
        score += names.str.contains(re.escape(v), na=False).astype(int) * 20
        for word in v.split():
            if len(word) >= 3:
                score += names.str.contains(re.escape(word), na=False).astype(int) * 2
    result = catalog.loc[score > 0].copy()
    if result.empty:
        return result
    result["_score"] = score.loc[result.index]
    return result.sort_values(["_score", "protein_g"], ascending=[False, False]).drop(columns="_score").head(limit)


def normalize_text(value):
    value = str(value or "").lower()
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    return re.sub(r"\s+", " ", value).strip()


TRANSLATION_TERMS = {
    "nasi": ["rice"],
    "nasi putih": ["white rice", "cooked rice"],
    "nasi goreng": ["fried rice"],
    "ayam": ["chicken"],
    "ayam goreng": ["fried chicken"],
    "dada ayam": ["chicken breast"],
    "ikan": ["fish"],
    "ikan goreng": ["fried fish"],
    "telur": ["egg"],
    "telur rebus": ["boiled egg"],
    "sayur": ["vegetable", "vegetables"],
    "bayam": ["spinach"],
    "kangkung": ["water spinach"],
    "kentang": ["potato"],
    "roti": ["bread"],
    "susu": ["milk"],
    "apel": ["apple"],
    "pisang": ["banana"],
    "tempe": ["tempeh"],
    "tahu": ["tofu"],
    "daging sapi": ["beef"],
    "udang": ["shrimp"],
    "kacang": ["nuts", "beans"],
    "selai kacang": ["peanut butter"],
    "alpukat": ["avocado"],
}


def query_variants(query):
    q = str(query or "").strip()
    variants = [q]
    normalized = normalize_text(q)
    for indo, english_terms in TRANSLATION_TERMS.items():
        if indo in normalized:
            variants.extend(english_terms)
    return list(dict.fromkeys([v for v in variants if v]))


def search_catalog(query, limit=40):
    catalog = load_catalog()
    if catalog.empty:
        return catalog

    variants = query_variants(query)
    if not variants:
        return catalog.head(limit)

    score = pd.Series(0, index=catalog.index, dtype="int64")
    names = catalog["food_name"].fillna("").astype(str).str.lower()

    for variant in variants:
        words = normalize_text(variant).split()
        if not words:
            continue
        exact_phrase = names.str.contains(re.escape(normalize_text(variant)), na=False)
        score += exact_phrase.astype(int) * 10
        for word in words:
            if len(word) >= 3:
                score += names.str.contains(re.escape(word), na=False).astype(int)

    result = catalog.loc[score > 0].copy()
    if result.empty:
        return result

    result["_score"] = score.loc[result.index]
    return result.sort_values(["_score", "protein_g"], ascending=[False, False]).drop(columns="_score").head(limit)


def calculate_nutrients(row, amount_grams):
    """Calculate nutrients from canonical per-100 g catalog values."""
    try:
        amount_grams = float(amount_grams)
    except (TypeError, ValueError):
        return None, "Berat porsi tidak valid."
    if amount_grams <= 0:
        return None, "Berat porsi harus lebih besar dari 0."
    nutrients = {}
    for col in ["calories", "protein_g", "fat_g", "carbs_g"]:
        value = pd.to_numeric(row.get(col), errors="coerce")
        nutrients[col] = None if pd.isna(value) else round(float(value) * amount_grams / 100.0, 2)
    warnings = validate_nutrients(nutrients)
    if warnings:
        return None, " ".join(warnings)
    return nutrients, None

def nutrients_from_100g(estimated):
    grams = float(estimated.get("estimated_grams") or 100)
    result = {}
    for col in ["calories", "protein_g", "fat_g", "carbs_g"]:
        per_100 = estimated.get(f"{col}_per_100g")
        try:
            result[col] = round(float(per_100) * grams / 100.0, 2)
        except (TypeError, ValueError):
            result[col] = None
    return result


# =========================================================
# SUPABASE DATA
# =========================================================
def get_profile(user_id):
    response = SUPABASE.table("profiles").select("*").eq("user_id", str(user_id)).limit(1).execute()
    return response.data[0] if response.data else {}


def save_profile(user_id, profile):
    payload = {
        "user_id": str(user_id),
        "name": profile["name"],
        "age": int(profile["age"]),
        "sex": profile["sex"],
        "height_cm": float(profile["height_cm"]),
        "weight_kg": float(profile["weight_kg"]),
        "activity": profile["activity"],
        "goal": profile["goal"],
        "calorie_target": float(profile["calorie_target"]),
        "protein_target": float(profile["protein_target"]),
    }
    return SUPABASE.table("profiles").upsert(payload, on_conflict="user_id").execute()


def get_meals(user_id, selected_date):
    response = (
        SUPABASE.table("meals")
        .select("*")
        .eq("user_id", str(user_id))
        .eq("meal_date", str(selected_date))
        .order("id", desc=True)
        .execute()
    )
    return pd.DataFrame(response.data or [])


def save_meal(user_id, selected_date, meal_type, food_name, grams, nutrients, source):
    payload = {
        "user_id": str(user_id),
        "meal_date": str(selected_date),
        "meal_type": meal_type,
        "food_name": str(food_name),
        "grams": float(grams),
        "calories": nutrients.get("calories"),
        "protein_g": nutrients.get("protein_g"),
        "fat_g": nutrients.get("fat_g"),
        "carbs_g": nutrients.get("carbs_g"),
        "source": source,
    }
    return SUPABASE.table("meals").insert(payload).execute()


def delete_meal(user_id, meal_id):
    return (
        SUPABASE.table("meals")
        .delete()
        .eq("id", int(meal_id))
        .eq("user_id", str(user_id))
        .execute()
    )


def totals(meals):
    cols = ["calories", "protein_g", "fat_g", "carbs_g"]
    if meals.empty:
        return {col: 0.0 for col in cols}
    return {
        col: float(pd.to_numeric(meals.get(col, pd.Series(dtype=float)), errors="coerce").fillna(0).sum())
        for col in cols
    }


# =========================================================
# TARGETS AND RECOMMENDATIONS
# =========================================================
def calculate_tdee(age, sex, height_cm, weight_kg, activity):
    """Estimasi kebutuhan energi pemeliharaan (TDEE) menggunakan Mifflin-St Jeor."""
    constant = 5 if sex == "Laki-laki" else -161
    bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + constant
    factor = {"Sedentari": 1.2, "Rendah": 1.2, "Ringan": 1.375, "Sedang": 1.55, "Tinggi": 1.725, "Sangat tinggi": 1.9}[activity]
    return bmr * factor


def estimate_targets(age, sex, height_cm, weight_kg, activity, goal):
    tdee = calculate_tdee(age, sex, height_cm, weight_kg, activity)
    adjustment = {
        "Menurunkan berat badan": -300,
        "Mempertahankan berat badan": 0,
        "Menaikkan berat badan": 250,
    }[goal]
    calorie_target = round(max(1200, tdee + adjustment))
    protein_target = round(weight_kg * (1.6 if goal == "Menaikkan berat badan" else 1.4))
    return calorie_target, protein_target


def classify_food(food_name, food_type=""):
    """Classify food into practical gym-meal roles using transparent keywords."""
    text = normalize_text(f"{food_name} {food_type}")
    if any(k in text for k in [
        "saus", "sauce", "sambal", "bumbu", "garam", "gula", "minyak",
        "oil", "dressing", "sirup", "syrup", "kaldu", "seasoning",
        "mayonnaise", "kecap", "cuka"
    ]):
        return "Bumbu/saus"
    if any(k in text for k in [
        "ayam", "ikan", "tuna", "salmon", "udang", "daging", "sapi",
        "kambing", "telur", "tempe", "tahu", "kacang", "kedelai",
        "protein", "hati", "ampela", "kerang"
    ]):
        return "Protein utama"
    if any(k in text for k in [
        "nasi", "beras", "roti", "mie", "mi ", "kentang", "ubi", "singkong",
        "jagung", "oat", "sereal", "bihun", "pasta", "tepung"
    ]):
        return "Karbohidrat"
    if any(k in text for k in [
        "bayam", "kangkung", "sayur", "sawi", "wortel", "brokoli", "kol",
        "kembang kol", "selada", "buncis", "labu", "terong", "tomat"
    ]):
        return "Sayuran"
    if any(k in text for k in [
        "apel", "pisang", "jeruk", "mangga", "pepaya", "semangka", "melon",
        "nanas", "anggur", "alpukat", "buah", "stroberi"
    ]):
        return "Buah"
    if any(k in text for k in ["susu", "yogurt", "keju", "minuman", "jus"]):
        return "Minuman/produk susu"
    return "Lainnya"


def recommendation_reason(goal, gym_focus, row, remaining_calories, remaining_protein):
    category = row.get("category", "Lainnya")
    calories = float(row.get("calories") or 0)
    protein = float(row.get("protein_g") or 0)
    fat = float(row.get("fat_g") or 0)
    fiber = float(row.get("fiber_g") or 0)
    portion = float(row.get("reference_grams") or 100)
    protein_density = protein / max(calories, 1) * 100

    if gym_focus == "Cutting" or goal == "Menurunkan berat badan":
        focus_text = "mendukung pengaturan kalori dan kecukupan protein untuk cutting"
    elif gym_focus == "Bulking" or goal == "Menaikkan berat badan":
        focus_text = "mendukung penambahan energi dan protein untuk bulking"
    elif gym_focus == "Performa latihan":
        focus_text = "mendukung energi latihan dan pemulihan melalui kombinasi protein serta karbohidrat"
    else:
        focus_text = "mendukung keseimbangan energi dan protein untuk maintenance"

    notes = [f"kategori {category.lower()}"]
    if protein_density >= 8:
        notes.append("kepadatan protein baik")
    if fiber >= 3:
        notes.append("mengandung serat")
    if fat <= 15:
        notes.append("lemak relatif terkontrol")
    return (
        f"Pilihan ini {focus_text}. {', '.join(notes)}. "
        f"Porsi rekomendasi awal sekitar {portion:.0f} g dan tetap perlu disesuaikan "
        f"dengan sisa target harian serta cara pengolahan makanan."
    )


def _portion_limits(category, gym_focus):
    limits = {
        "Protein utama": (100, 180),
        "Karbohidrat": (100, 200),
        "Sayuran": (100, 200),
        "Buah": (100, 180),
        "Minuman/produk susu": (100, 250),
        "Lainnya": (50, 150),
    }
    low, high = limits.get(category, (50, 150))
    if gym_focus == "Bulking":
        high = min(high + 50, 300)
    return low, high


def build_recommendations(goal, gym_focus, remaining_calories, remaining_protein, query=""):
    # Recommendations intentionally use the Indonesian nutrition dataset first,
    # avoiding branded/international USDA products in the normal user flow.
    catalog = indonesia_catalog_only()
    if catalog.empty:
        return pd.DataFrame()

    candidates = best_indonesia_match(query, limit=1000) if query.strip() else catalog.copy()
    if candidates.empty:
        return candidates.copy()

    for col in ["calories", "protein_g", "fat_g", "carbs_g", "fiber_g"]:
        candidates[col] = pd.to_numeric(candidates[col], errors="coerce").fillna(0)
    candidates["food_name"] = candidates["food_name"].fillna("").astype(str).str.strip()
    candidates["category"] = candidates.apply(
        lambda r: classify_food(r.get("food_name", ""), r.get("food_type", "")), axis=1
    )

    # Prioritize Indonesian nutrition records. International data remains a fallback
    # when the user explicitly searches or the Indonesian catalog has no match.
    candidates["is_indonesia"] = candidates["source"].eq("Nutrition Indonesia").astype(int)
    candidates = candidates[
        (candidates["calories"] >= 20) &
        (candidates["protein_g"] >= 0) &
        (~candidates["category"].eq("Bumbu/saus"))
    ].copy()
    if candidates.empty:
        return candidates

    candidates["protein_density"] = candidates["protein_g"] / candidates["calories"] * 100
    candidates["fat_ratio"] = candidates["fat_g"] * 9 / candidates["calories"] * 100
    candidates["score"] = candidates["is_indonesia"] * 18

    # Avoid recommending items with implausibly low protein as the primary gym food,
    # while still allowing carbs, fruit, and vegetables to appear.
    candidates["score"] += np.where(
        candidates["category"].eq("Protein utama"),
        candidates["protein_g"] * 1.8 + candidates["protein_density"] * 1.2,
        candidates["protein_g"] * 0.35
    )
    candidates["score"] += candidates["fiber_g"].clip(upper=10) * 0.8

    if gym_focus == "Cutting" or goal == "Menurunkan berat badan":
        candidates["score"] += candidates["protein_density"] * 1.4
        candidates["score"] -= candidates["fat_ratio"].clip(lower=0) * 0.22
    elif gym_focus == "Bulking" or goal == "Menaikkan berat badan":
        candidates["score"] += candidates["protein_g"] * 0.55 + candidates["carbs_g"] * 0.18
    elif gym_focus == "Performa latihan":
        candidates["score"] += candidates["protein_g"] * 0.55 + candidates["carbs_g"] * 0.25
    else:
        candidates["score"] += candidates["protein_density"] * 0.65
        candidates["score"] -= candidates["fat_ratio"].clip(lower=0) * 0.12

    # Practical portions by food role, then fit to the remaining daily targets.
    def choose_portion(row):
        low, high = _portion_limits(row["category"], gym_focus)
        if row["calories"] <= 0:
            return low
        target_kcal = min(max(float(remaining_calories or 0), 150), 450)
        estimated = target_kcal / row["calories"] * 100
        return float(np.clip(estimated, low, high))

    candidates["reference_grams"] = candidates.apply(choose_portion, axis=1)
    candidates["portion_calories"] = candidates["calories"] * candidates["reference_grams"] / 100
    candidates["portion_protein"] = candidates["protein_g"] * candidates["reference_grams"] / 100
    candidates["portion_carbs"] = candidates["carbs_g"] * candidates["reference_grams"] / 100

    if remaining_calories > 0:
        candidates["score"] -= (
            abs(candidates["portion_calories"] - min(remaining_calories, 450)) /
            max(min(remaining_calories, 450), 1) * 1.5
        )
    if remaining_protein > 0:
        candidates["score"] += (
            candidates["portion_protein"].clip(upper=remaining_protein) /
            max(remaining_protein, 1) * 5
        )

    # Prefer a diverse set of categories rather than eight nearly identical rows.
    candidates = candidates.sort_values(
        ["score", "is_indonesia", "protein_density"], ascending=[False, False, False]
    )
    selected = []
    category_counts = {}
    for _, row in candidates.iterrows():
        cat = row["category"]
        if category_counts.get(cat, 0) >= 3:
            continue
        selected.append(row)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if len(selected) >= 8:
            break
    if not selected:
        return pd.DataFrame()

    result = pd.DataFrame(selected).copy()
    result["reason"] = result.apply(
        lambda row: recommendation_reason(goal, gym_focus, row, remaining_calories, remaining_protein), axis=1
    )
    return result.reset_index(drop=True)


# =========================================================
# GEMINI IMAGE ANALYSIS
# =========================================================
def analyze_image(uploaded_file):
    if not GEMINI_API_KEY:
        return None, "GEMINI_API_KEY belum diatur di file .env."

    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=GEMINI_API_KEY)
        prompt = """
Analisis gambar makanan. Kembalikan HANYA JSON valid tanpa markdown dengan struktur:
{
  "food_name_id": "nama hidangan dalam Bahasa Indonesia",
  "food_name_en": "closest English name for nutrition search",
  "portion_class": "kecil|sedang|besar|tidak diketahui",
  "estimated_grams": number,
  "confidence": number between 0 and 1,
  "notes": "catatan singkat",
  "components": [
    {
      "name_id": "nama komponen, misalnya nasi putih",
      "name_en": "white rice",
      "estimated_grams": number or null,
      "calories": number or null,
      "protein_g": number or null,
      "fat_g": number or null,
      "carbs_g": number or null,
      "fiber_g": number or null,
      "notes": "catatan komponen"
    }
  ],
  "calories_per_100g": number or null,
  "protein_g_per_100g": number or null,
  "fat_g_per_100g": number or null,
  "carbs_g_per_100g": number or null,
  "fiber_g_per_100g": number or null,
  "sugar_g_per_100g": number or null,
  "sodium_mg_per_100g": number or null
}
Perkirakan porsi setiap komponen secara konservatif. Untuk hidangan campuran, pecah menjadi komponen yang terlihat, misalnya nasi, ayam, sambal, dan lalapan. Nilai nutrisi komponen harus berupa estimasi untuk seluruh komponen pada porsi yang terlihat, bukan per 100 gram. Jika tidak yakin, gunakan null atau "tidak diketahui". Jumlahkan komponen secara masuk akal untuk membantu pengguna memahami total hidangan.
"""

        image_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/jpeg"
        last_error = None
        response = None
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                        prompt,
                    ],
                )
                break
            except Exception as exc:
                last_error = exc
                if "503" not in str(exc) and "UNAVAILABLE" not in str(exc).upper():
                    raise
                import time
                time.sleep(2 * (attempt + 1))
        if response is None:
            raise last_error or RuntimeError("Model tidak memberikan respons.")
        raw = (response.text or "").strip()
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        parsed = json.loads(raw)
        return parsed, None
    except Exception as exc:
        return None, f"Analisis gambar gagal: {exc}"


# =========================================================
# APPLICATION
# =========================================================
user = get_current_user()
if not user:
    show_auth()
    st.stop()

user_id = str(user.id)
profile = get_profile(user_id)

with st.sidebar:
    st.markdown(
        f"""<div class=\"login-card\"><div class=\"login-label\">LOGIN AKTIF</div><div class=\"login-email\">{getattr(user, 'email', 'pengguna')}</div></div>""",
        unsafe_allow_html=True,
    )
    if st.button("Logout", use_container_width=True):
        logout()

    st.divider()
    st.header("Profil dan Target")
    with st.form("profile_form"):
        name = st.text_input("Nama", value=profile.get("name") or "")
        age = st.number_input("Usia", min_value=13, max_value=100, value=int(profile.get("age") or 20))
        sexes = ["Perempuan", "Laki-laki"]
        current_sex = profile.get("sex") if profile.get("sex") in sexes else "Laki-laki"
        sex = st.selectbox("Jenis kelamin", sexes, index=sexes.index(current_sex))
        height = st.number_input("Tinggi (cm)", min_value=100.0, max_value=230.0, value=float(profile.get("height_cm") or 160.0))
        weight = st.number_input("Berat (kg)", min_value=25.0, max_value=250.0, value=float(profile.get("weight_kg") or 55.0))
        activities = ["Sedentari", "Ringan", "Sedang", "Tinggi", "Sangat tinggi"]
        current_activity = profile.get("activity") if profile.get("activity") in activities else "Sedang"
        activity = st.selectbox("Tingkat aktivitas harian", activities, index=activities.index(current_activity), help="Sedentari: jarang bergerak; Ringan: latihan 1–3 hari/minggu; Sedang: 3–5 hari/minggu; Tinggi: latihan berat 6–7 hari/minggu; Sangat tinggi: latihan sangat berat/pekerjaan fisik berat.")
        goals = ["Menurunkan berat badan", "Mempertahankan berat badan", "Menaikkan berat badan"]
        current_goal = profile.get("goal") if profile.get("goal") in goals else "Mempertahankan berat badan"
        goal = st.selectbox("Tujuan", goals, index=goals.index(current_goal))

        estimated_calories, estimated_protein = estimate_targets(age, sex, height, weight, activity, goal)
        calorie_target = st.number_input(
            "Target kalori", min_value=800.0, max_value=8000.0,
            value=float(profile.get("calorie_target") or estimated_calories)
        )
        protein_target = st.number_input(
            "Target protein (g)", min_value=0.0, max_value=500.0,
            value=float(profile.get("protein_target") or estimated_protein)
        )

        if st.form_submit_button("Simpan profil", use_container_width=True):
            try:
                save_profile(user_id, {
                    "name": name, "age": age, "sex": sex,
                    "height_cm": height, "weight_kg": weight,
                    "activity": activity, "goal": goal,
                    "calorie_target": calorie_target,
                    "protein_target": protein_target,
                })
                st.success("Profil berhasil disimpan.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menyimpan profil: {exc}")

selected_date = st.date_input("Tanggal pencatatan", value=date.today())
meals = get_meals(user_id, selected_date)
daily_totals = totals(meals)
remaining_calories = max(float(calorie_target) - daily_totals["calories"], 0)
remaining_protein = max(float(protein_target) - daily_totals["protein_g"], 0)

st.markdown(
    """<div class="brand-header"><div class="brand-icon">🥗</div><div class="brand-copy"><div class="brand-kicker">Personal Nutrition Companion</div><div class="brand-title">Aku Sehat <span>AI</span></div><div class="brand-subtitle">Pola makan lebih terarah, keputusan lebih cerdas, langkah lebih konsisten.</div></div></div>""",
    unsafe_allow_html=True,
)

dashboard_tab, log_tab, recommendation_tab, simulation_tab = st.tabs(
    ["Dashboard", "Catat Makanan", "Rekomendasi", "What-if Simulation"]
)

# =========================================================
# DASHBOARD
# =========================================================
with dashboard_tab:
    st.markdown("""<div class="page-hero"><span class="page-chip">Overview harian</span><div class="page-title">Pantau progres kesehatanmu</div><p class="page-desc">Lihat asupan, target, dan keseimbangan nutrisi dalam satu ringkasan yang mudah dipahami.</p></div>""", unsafe_allow_html=True)
    st.subheader(f"Ringkasan tanggal {selected_date}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Kalori", f"{daily_totals['calories']:.0f} / {calorie_target:.0f} kcal")
    c2.metric("Protein", f"{daily_totals['protein_g']:.1f} / {protein_target:.0f} g")
    c3.metric("Sisa kalori", f"{remaining_calories:.0f} kcal")
    c4.metric("Sisa protein", f"{remaining_protein:.1f} g")

    st.info(f"Tujuan profil: **{goal}**")
    st.markdown("### Progress target harian")
    cal_progress = min(daily_totals["calories"] / max(float(calorie_target), 1), 1.0)
    protein_progress = min(daily_totals["protein_g"] / max(float(protein_target), 1), 1.0)
    pc1, pc2 = st.columns(2)
    with pc1:
        st.write(f"Kalori: {daily_totals['calories']:.0f} / {float(calorie_target):.0f} kkal")
        st.progress(cal_progress)
    with pc2:
        st.write(f"Protein: {daily_totals['protein_g']:.1f} / {float(protein_target):.1f} g")
        st.progress(protein_progress)

    if meals.empty:
        st.info("Belum ada catatan makanan pada tanggal ini.")
    else:
        st.markdown("### Catatan harian")
        display_cols = [
            "id", "meal_type", "food_name", "grams", "calories",
            "protein_g", "fat_g", "carbs_g", "source"
        ]
        available_cols = [col for col in display_cols if col in meals.columns]
        st.dataframe(meals[available_cols], use_container_width=True, hide_index=True)

        delete_id = st.number_input("ID catatan untuk dihapus", min_value=0, step=1, value=0)
        if st.button("Hapus catatan") and delete_id > 0:
            try:
                delete_meal(user_id, int(delete_id))
                st.success("Catatan berhasil dihapus.")
                st.rerun()
            except Exception as exc:
                st.error(f"Gagal menghapus catatan: {exc}")

        st.markdown("### Komposisi makronutrien harian")
        st.caption("Satu pie chart gabungan. Persentase dihitung berdasarkan kontribusi energi: protein 4 kkal/g, karbohidrat 4 kkal/g, dan lemak 9 kkal/g.")
        macro_values = {
            "Protein": daily_totals["protein_g"] * 4,
            "Karbohidrat": daily_totals["carbs_g"] * 4,
            "Lemak": daily_totals["fat_g"] * 9,
        }
        macro_df = pd.DataFrame({"Makronutrien": list(macro_values.keys()), "Energi (kkal)": list(macro_values.values())})
        macro_df = macro_df[macro_df["Energi (kkal)"] > 0]
        if macro_df.empty:
            st.info("Belum ada data makronutrien untuk divisualisasikan.")
        else:
            st.vega_lite_chart(
                macro_df,
                {
                    "mark": {"type": "arc", "innerRadius": 65, "tooltip": True},
                    "encoding": {
                        "theta": {"field": "Energi (kkal)", "type": "quantitative", "stack": True},
                        "color": {"field": "Makronutrien", "type": "nominal", "legend": {"title": "Nutrisi"}},
                        "tooltip": [
                            {"field": "Makronutrien", "type": "nominal"},
                            {"field": "Energi (kkal)", "type": "quantitative", "format": ".1f"},
                        ],
                    },
                    "view": {"stroke": None},
                },
                use_container_width=True,
            )
            total_macro_kcal = float(macro_df["Energi (kkal)"].sum())
            st.caption(" | ".join([f"{row['Makronutrien']}: {row['Energi (kkal)'] / total_macro_kcal * 100:.1f}%" for _, row in macro_df.iterrows()]))

# =========================================================
# FOOD LOG
# =========================================================
with log_tab:
    st.markdown("""<div class="page-hero"><span class="page-chip">Food tracking</span><div class="page-title">Catat makanan dengan lebih praktis</div><p class="page-desc">Gunakan analisis AI atau input manual, lalu periksa kembali hasilnya sebelum disimpan.</p></div>""", unsafe_allow_html=True)
    st.subheader("Catat makanan")
    method = st.radio(
        "Metode input",
        ["Input manual", "Analisis gambar AI"],
        horizontal=True
    )

    if method == "Input manual":
        with st.form("manual_food_form"):
            food_name = st.text_input("Nama makanan")
            meal_type = st.selectbox("Sesi makan", ["Sarapan", "Makan siang", "Makan malam", "Camilan"])
            grams = st.number_input("Berat makanan (gram)", min_value=1.0, max_value=5000.0, value=100.0)
            calories = st.number_input("Kalori (kcal)", min_value=0.0, value=100.0)
            protein = st.number_input("Protein (g)", min_value=0.0, value=0.0)
            fat = st.number_input("Lemak (g)", min_value=0.0, value=0.0)
            carbs = st.number_input("Karbohidrat (g)", min_value=0.0, value=0.0)
            submitted = st.form_submit_button("Simpan makanan manual")
            if submitted:
                if not food_name.strip():
                    st.error("Nama makanan wajib diisi.")
                elif calories <= 0:
                    st.error("Kalori harus lebih besar dari 0.")
                else:
                    try:
                        save_meal(
                            user_id, selected_date, meal_type, food_name.strip(), grams,
                            {
                                "calories": calories, "protein_g": protein, "fat_g": fat,
                                "carbs_g": carbs,
                            },
                            "Manual",
                        )
                        st.success("Makanan berhasil disimpan ke riwayat.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menyimpan makanan: {exc}")

    else:
        uploaded = st.file_uploader("Unggah gambar makanan", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, caption="Gambar makanan", use_container_width=True)
            if st.button("Analisis gambar dengan AI"):
                with st.spinner("AI sedang menganalisis gambar..."):
                    result, error = analyze_image(uploaded)
                if error:
                    st.error(error)
                else:
                    st.session_state["image_result"] = result
                    st.session_state["image_uploaded_name"] = uploaded.name
                    st.rerun()

        result = st.session_state.get("image_result")
        if result:
            st.markdown("### Hasil analisis AI")
            col_a, col_b = st.columns(2)
            with col_a:
                st.info(f"**Nama makanan**\n\n{result.get('food_name_id') or result.get('food_name_en') or 'Tidak diketahui'}")
                st.info(f"**Klasifikasi porsi**\n\n{str(result.get('portion_class') or 'Tidak diketahui').capitalize()}")
            with col_b:
                grams_default = float(result.get("estimated_grams") or 100)
                st.info(f"**Perkiraan berat**\n\n{grams_default:.0f} gram")
                confidence = result.get("confidence")
                confidence_text = f"{float(confidence) * 100:.0f}%" if confidence is not None else "Tidak tersedia"
                st.info(f"**Keyakinan AI**\n\n{confidence_text}")
            st.write(f"**Catatan:** {result.get('notes') or 'Tidak ada catatan.'}")

            # Rincian komponen hidangan: tampilkan setiap item sebelum total
            components = result.get("components") or []
            valid_components = [c for c in components if isinstance(c, dict)]
            if valid_components:
                st.markdown("#### Rincian nutrisi setiap komponen")
                component_rows = []
                for comp in valid_components:
                    component_rows.append({
                        "Komponen": comp.get("name_id") or comp.get("name_en") or "Tidak diketahui",
                        "Berat (g)": comp.get("estimated_grams"),
                        "Kalori (kkal)": comp.get("calories"),
                        "Protein (g)": comp.get("protein_g"),
                        "Lemak (g)": comp.get("fat_g"),
                        "Karbohidrat (g)": comp.get("carbs_g"),
                    })
                component_df = pd.DataFrame(component_rows)
                numeric_cols = [c for c in component_df.columns if c != "Komponen"]
                for col in numeric_cols:
                    component_df[col] = pd.to_numeric(component_df[col], errors="coerce")
                st.dataframe(component_df.round(2), use_container_width=True, hide_index=True)
                totals = {col: component_df[col].sum(min_count=1) for col in numeric_cols}
                st.markdown("**Total estimasi hidangan**")
                total_cols = st.columns(4)
                total_cols[0].metric("Kalori", f"{totals.get('Kalori (kkal)', 0) or 0:.0f} kkal")
                total_cols[1].metric("Protein", f"{totals.get('Protein (g)', 0) or 0:.1f} g")
                total_cols[2].metric("Lemak", f"{totals.get('Lemak (g)', 0) or 0:.1f} g")
                total_cols[3].metric("Karbohidrat", f"{totals.get('Karbohidrat (g)', 0) or 0:.1f} g")
                st.caption("Angka per komponen adalah estimasi AI berdasarkan tampilan gambar dan dapat berbeda dari porsi sebenarnya.")
            else:
                st.info("AI belum memecah hidangan menjadi komponen. Coba unggah gambar yang memperlihatkan tiap item dengan jelas.")

            corrected_name = st.text_input(
                "Koreksi nama makanan",
                value=str(result.get("food_name_id") or result.get("food_name_en") or ""),
                key="ai_corrected_name",
                help="Setelah nama diubah, referensi nutrisi akan dicari ulang dari dataset Nutrition Indonesia."
            )
            corrected_grams = st.number_input(
                "Koreksi berat (gram)",
                min_value=1.0, max_value=5000.0,
                value=grams_default, key="ai_corrected_grams"
            )
            ai_meal_type = st.selectbox(
                "Sesi makan", ["Sarapan", "Makan siang", "Makan malam", "Camilan"],
                key="ai_meal_type"
            )

            # Recalculate after correction. The corrected name is authoritative:
            # when it changes, do not continue using the old AI food/component total.
            corrected_query = corrected_name.strip()
            correction_candidates = best_indonesia_match(corrected_query, limit=12)
            selected_row = None
            corrected_dataset_nutrients = None
            corrected_dataset_error = None

            if not correction_candidates.empty:
                # Gunakan kandidat pertama yang paling relevan secara otomatis.
                # Dropdown dihilangkan agar alur koreksi lebih sederhana dan tidak membingungkan.
                selected_row = correction_candidates.iloc[0]
                st.caption(
                    f"Referensi otomatis: **{selected_row['food_name']}** · "
                    f"{float(selected_row['calories']):.0f} kkal/100 g · Nutrition Indonesia"
                )
                corrected_dataset_nutrients, corrected_dataset_error = calculate_nutrients(
                    selected_row, corrected_grams
                )
                if corrected_dataset_error:
                    st.warning(corrected_dataset_error)
                else:
                    st.markdown("#### Nutrisi setelah koreksi")
                    # Hanya tampilkan kolom yang memiliki nilai nutrisi.
                    corrected_display = pd.DataFrame([corrected_dataset_nutrients]).round(2)
                    corrected_display = corrected_display.dropna(axis=1, how="all")
                    corrected_display = corrected_display.loc[:, [
                        col for col in corrected_display.columns
                        if not corrected_display[col].isna().all()
                    ]]
                    st.dataframe(
                        corrected_display,
                        use_container_width=True,
                        hide_index=True
                    )
                    st.success(
                        f"Data nutrisi sudah disesuaikan dengan **{selected_row['food_name']}** "
                        f"dan berat **{corrected_grams:.0f} g**."
                    )
            else:
                st.warning(
                    "Nama koreksi belum ditemukan pada dataset Nutrition Indonesia. "
                    "Gunakan nama yang lebih umum, misalnya ayam goreng, dada ayam, ikan, telur, nasi, tempe, tahu, atau susu."
                )

            # AI component totals are retained only when no corrected dataset match
            # is available. This prevents stale nutrients after the user changes the food.
            component_grams_total = sum(float(c.get("estimated_grams") or 0) for c in valid_components)
            component_scale = (
                corrected_grams / component_grams_total
                if component_grams_total > 0 else 1.0
            )
            component_nutrients = None
            if valid_components and correction_candidates.empty:
                component_nutrients = {
                    "calories": round(sum(float(c.get("calories") or 0) for c in valid_components) * component_scale, 2),
                    "protein_g": round(sum(float(c.get("protein_g") or 0) for c in valid_components) * component_scale, 2),
                    "fat_g": round(sum(float(c.get("fat_g") or 0) for c in valid_components) * component_scale, 2),
                    "carbs_g": round(sum(float(c.get("carbs_g") or 0) for c in valid_components) * component_scale, 2),
                }
                st.markdown("#### Estimasi komponen AI setelah penyesuaian berat")
                st.dataframe(
                    pd.DataFrame([component_nutrients]).round(2),
                    use_container_width=True,
                    hide_index=True
                )

            nutrients_to_save = corrected_dataset_nutrients or component_nutrients
            source_to_save = (
                f"AI correction + Nutrition Indonesia"
                if corrected_dataset_nutrients is not None
                else "AI component estimate"
            )
            if nutrients_to_save:
                if st.button("Konfirmasi dan simpan hasil koreksi", key="save_corrected_ai"):
                    warnings = validate_nutrients(nutrients_to_save)
                    if warnings:
                        st.error("Data nutrisi tidak valid: " + " ".join(warnings))
                    else:
                        try:
                            save_meal(
                                user_id,
                                selected_date,
                                ai_meal_type,
                                corrected_name.strip() or (selected_row["food_name"] if selected_row is not None else "Makanan AI"),
                                corrected_grams,
                                nutrients_to_save,
                                source_to_save,
                            )
                            st.success("Hasil koreksi dan nutrisi terbaru berhasil disimpan.")
                            st.session_state.pop("image_result", None)
                            st.session_state.pop("ai_corrected_dataset_choice", None)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan hasil koreksi: {exc}")
            else:
                st.info("Lengkapi koreksi nama atau gunakan input manual jika makanan belum tersedia.")

            if st.button("Hapus hasil analisis", key="clear_ai_result"):
                st.session_state.pop("image_result", None)
                st.rerun()

# =========================================================
# RECOMMENDATIONS
# =========================================================
with recommendation_tab:
    st.markdown("""<div class="page-hero"><span class="page-chip">Smart recommendation</span><div class="page-title">Temukan pilihan yang sesuai dengan targetmu</div><p class="page-desc">Rekomendasi diprioritaskan dari makanan Indonesia dan disesuaikan dengan tujuan serta sisa kebutuhan harian.</p></div>""", unsafe_allow_html=True)
    st.subheader("Rekomendasi makanan")
    st.write(f"**Tujuan profil:** {goal}")
    st.write(f"**Sisa target hari ini:** {remaining_calories:.0f} kcal dan {remaining_protein:.1f} g protein.")

    estimated_calories, estimated_protein = estimate_targets(age, sex, height, weight, activity, goal)
    with st.container(border=True):
        st.markdown("### Estimasi kebutuhan harian")
        ec1, ec2, ec3 = st.columns(3)
        ec1.metric("Estimasi kalori", f"{estimated_calories:,.0f} kkal/hari")
        ec2.metric("Estimasi protein", f"{estimated_protein:,.0f} g/hari")
        ec3.metric("Target manual", f"{calorie_target:,.0f} kkal/hari")
        st.caption("Estimasi dihitung dari Mifflin–St Jeor + faktor aktivitas + penyesuaian tujuan. Nilai target manual tetap dapat diubah di sidebar dan digunakan sebagai target utama aplikasi.")

    gym_focus = st.selectbox(
        "Fokus nutrisi gym",
        ["Maintenance", "Cutting", "Bulking", "Performa latihan"],
        help="Fokus ini memengaruhi prioritas protein, lemak, energi, dan serat. Bukan diagnosis medis."
    )
    st.caption("Rekomendasi memprioritaskan makanan Indonesia, mengecualikan bumbu/saus sebagai menu utama, serta menyesuaikan tujuan gym, sisa kalori, protein, dan kategori makanan.")

    recommendation_query = st.text_input(
        "Preferensi makanan (opsional)",
        placeholder="Contoh: ayam, nasi, telur, makanan murah..."
    )

    if st.button("Buat rekomendasi"):
        recommendations = build_recommendations(
            goal, gym_focus, remaining_calories, remaining_protein, recommendation_query
        )
        st.session_state["recommendation_result"] = recommendations

    recommendations = st.session_state.get("recommendation_result")
    if recommendations is None:
        st.info("Masukkan preferensi jika ada, lalu klik 'Buat rekomendasi'.")
    elif isinstance(recommendations, pd.DataFrame) and recommendations.empty:
        st.warning("Belum ditemukan makanan yang cocok dari dataset. Coba kata kunci lain.")
    else:
        for idx, row in recommendations.iterrows():
            with st.container(border=True):
                st.markdown(f"### {row['food_name']}")
                a, b, c = st.columns(3)
                a.metric("Kalori / 100 g", f"{float(row['calories']):.0f} kcal")
                b.metric("Protein / 100 g", f"{float(row['protein_g']):.1f} g")
                c.metric("Porsi referensi", f"{float(row.get('reference_grams', 100)):.0f} g")
                st.write(f"**Kategori:** {row.get('category', 'Lainnya')} | **Sumber:** {row.get('source', 'Tidak diketahui')}")
                st.caption("Rekomendasi dipilih dari katalog Nutrition Indonesia dan ditujukan sebagai referensi, bukan resep medis individual.")
                st.write(row["reason"])
                st.caption(f"Perkiraan porsi {float(row.get('reference_grams', 100)):.0f} g: {float(row.get('portion_calories', 0)):.0f} kkal dan {float(row.get('portion_protein', 0)):.1f} g protein. Data dinormalisasi ke basis per 100 g.")

# =========================================================
# WHAT-IF SIMULATION
# =========================================================
with simulation_tab:
    st.markdown("""<div class="page-hero"><span class="page-chip">Decision support</span><div class="page-title">Uji skenario sebelum mengubah kebiasaan</div><p class="page-desc">Bandingkan perubahan asupan harian dengan target energi dan protein secara sederhana.</p></div>""", unsafe_allow_html=True)
    st.subheader("What-if Simulation: dampak perubahan asupan")
    st.write(f"**Tujuan profil:** {goal}")
    st.caption(
        "Simulasi menggunakan estimasi kebutuhan energi pemeliharaan (TDEE). "
        "Arah perubahan berat badan merupakan kecenderungan, bukan kepastian medis."
    )

    maintenance_calories = calculate_tdee(age, sex, height, weight, activity)

    st.markdown("### 1. Tentukan perubahan asupan harian")
    st.write(
        "Masukkan perubahan terhadap target asupan harian profil. "
        "Contoh: **+500 kkal** berarti total asupan harian dinaikkan 500 kkal dari target profil; **+50 g protein** berarti protein dinaikkan 50 g. Protein tidak dihitung ulang menjadi tambahan kalori agar tidak terjadi penghitungan ganda."
    )

    c1, c2 = st.columns(2)
    with c1:
        extra_calories = st.number_input(
            "Perubahan total energi per hari (kkal)",
            min_value=-1500.0, max_value=3000.0, value=0.0, step=50.0,
            help="Nilai positif = menambah kalori; nilai negatif = mengurangi kalori."
        )
    with c2:
        extra_protein = st.number_input(
            "Perubahan total protein per hari (g)",
            min_value=-200.0, max_value=300.0, value=0.0, step=5.0,
            help="Nilai positif = menambah protein; nilai negatif = mengurangi protein."
        )

    duration_days = st.slider("Durasi skenario (hari)", min_value=1, max_value=30, value=7)

    # Baseline menggunakan target profil, sehingga simulasi tidak bergantung pada
    # jumlah makanan yang sudah dicatat hari ini (yang mungkin belum lengkap).
    baseline_calories = float(calorie_target)
    baseline_protein = float(protein_target)
    simulated_calories = baseline_calories + extra_calories
    simulated_protein = max(0.0, baseline_protein + extra_protein)
    if simulated_calories < 1200:
        st.warning("Kalori skenario berada di bawah 1.200 kkal/hari. Jangan gunakan target rendah tanpa pendampingan tenaga kesehatan.")
    if simulated_protein > weight * 3:
        st.warning("Protein skenario sangat tinggi dibandingkan berat badan. Periksa kembali satuan dan kebutuhanmu.")

    calorie_gap_to_maintenance = simulated_calories - maintenance_calories
    protein_gap_to_target = simulated_protein - baseline_protein
    total_energy_gap = calorie_gap_to_maintenance * duration_days
    rough_weight_change = total_energy_gap / 7700.0

    st.markdown("### 2. Ringkasan angka")
    a, b, c = st.columns(3)
    a.metric("TDEE / pemeliharaan", f"{maintenance_calories:.0f} kkal")
    b.metric("Kalori skenario / hari", f"{simulated_calories:.0f} kkal")
    c.metric("Selisih dari TDEE", f"{calorie_gap_to_maintenance:+.0f} kkal")

    d, e, f = st.columns(3)
    d.metric("Protein target", f"{baseline_protein:.1f} g")
    e.metric("Protein skenario", f"{simulated_protein:.1f} g")
    f.metric("Perubahan protein", f"{protein_gap_to_target:+.1f} g")

    st.markdown("### 3. Apakah skenario sesuai dengan tujuan?")

    # Klasifikasi arah energi hanya menggunakan satu kondisi yang relevan.
    # Toleransi ±100 kkal/hari dipakai sebagai zona relatif dekat dengan TDEE.
    if calorie_gap_to_maintenance < -100:
        energy_direction = "defisit energi"
        energy_detail = (
            f"Asupan skenario berada {abs(calorie_gap_to_maintenance):.0f} kkal/hari "
            "di bawah estimasi kebutuhan pemeliharaan (TDEE), sehingga berat badan "
            "secara teoritis cenderung menurun jika pola ini konsisten."
        )
    elif calorie_gap_to_maintenance > 100:
        energy_direction = "surplus energi"
        energy_detail = (
            f"Asupan skenario berada {calorie_gap_to_maintenance:.0f} kkal/hari "
            "di atas estimasi kebutuhan pemeliharaan (TDEE), sehingga berat badan "
            "secara teoritis cenderung meningkat jika pola ini konsisten."
        )
    else:
        energy_direction = "mendekati pemeliharaan"
        energy_detail = (
            "Asupan skenario relatif dekat dengan estimasi kebutuhan pemeliharaan "
            "(TDEE), sehingga berat badan secara teoritis cenderung dipertahankan."
        )

    if goal == "Menurunkan berat badan":
        aligned = calorie_gap_to_maintenance < -100
        goal_detail = (
            "Kondisi ini sesuai dengan tujuan menurunkan berat badan."
            if aligned else
            "Kondisi ini belum sesuai dengan tujuan menurunkan berat badan; "
            "dibutuhkan defisit energi yang memadai."
        )
    elif goal == "Menaikkan berat badan":
        aligned = calorie_gap_to_maintenance > 100
        goal_detail = (
            "Kondisi ini sesuai dengan tujuan menaikkan berat badan."
            if aligned else
            "Kondisi ini belum sesuai dengan tujuan menaikkan berat badan; "
            "dibutuhkan surplus energi yang memadai."
        )
    else:
        aligned = abs(calorie_gap_to_maintenance) <= 100
        goal_detail = (
            "Kondisi ini sesuai dengan tujuan mempertahankan berat badan."
            if aligned else
            "Kondisi ini belum sesuai dengan tujuan mempertahankan berat badan; "
            "asupan perlu didekatkan ke kebutuhan pemeliharaan."
        )

    # Hanya satu kotak status ditampilkan, sesuai kondisi skenario.
    message = f"**{energy_direction.capitalize()}:** {energy_detail} {goal_detail}"
    if aligned:
        st.success(message)
    else:
        st.warning(message)

    st.markdown("### 4. Proyeksi sederhana selama periode simulasi")
    p1, p2 = st.columns(2)
    p1.metric("Akumulasi selisih energi", f"{total_energy_gap:+.0f} kkal")
    p2.metric("Perkiraan teoritis perubahan berat", f"{rough_weight_change:+.2f} kg")
    st.caption(
        "Perkiraan kg menggunakan pendekatan kasar 7.700 kkal ≈ 1 kg. "
        "Angka ini bukan prediksi akurat karena perubahan berat dipengaruhi adaptasi metabolisme, "
        "komposisi tubuh, cairan, aktivitas, dan ketepatan estimasi makanan."
    )

    st.markdown("### 5. Interpretasi protein")
    st.caption(
        "Analisis berikut adalah panduan umum untuk pengguna aktif/gym. "
        "Kebutuhan aktual dapat berbeda berdasarkan intensitas latihan, komposisi tubuh, "
        "kondisi kesehatan, dan kualitas pola makan secara keseluruhan."
    )

    # Referensi praktis berbasis berat badan untuk pengguna aktif.
    # Ini bukan diagnosis medis dan bukan target wajib untuk semua orang.
    protein_reference_low = weight * 1.4
    protein_reference_high = weight * 2.0
    protein_reference_mid = weight * 1.6
    protein_per_kg = simulated_protein / weight if weight > 0 else 0.0
    protein_percent_of_mid = (
        simulated_protein / protein_reference_mid * 100
        if protein_reference_mid > 0 else 0.0
    )
    protein_gap_to_low = simulated_protein - protein_reference_low
    protein_gap_to_high = simulated_protein - protein_reference_high

    if simulated_protein < protein_reference_low:
        protein_status = "Belum mencapai kisaran referensi"
        status_detail = (
            f"Asupan protein masih sekitar {abs(protein_gap_to_low):.1f} g di bawah batas bawah "
            "referensi pengguna aktif."
        )
        protein_advice = (
            "Tambahkan satu atau dua sumber protein yang mudah diperoleh, misalnya dada ayam, "
            "ikan, telur, tempe, tahu, atau susu. Naikkan secara bertahap sambil memastikan "
            "kalori, karbohidrat, lemak sehat, sayur, dan cairan tetap tercukupi."
        )
        status_kind = "warning"
    elif simulated_protein > protein_reference_high:
        protein_status = "Melebihi kisaran referensi"
        status_detail = (
            f"Asupan protein sekitar {abs(protein_gap_to_high):.1f} g di atas batas atas "
            "referensi pengguna aktif."
        )
        protein_advice = (
            "Evaluasi apakah jumlah tersebut benar-benar diperlukan. Jangan sampai protein "
            "menggeser kebutuhan karbohidrat, lemak sehat, serat, dan variasi makanan. "
            "Jika memiliki kondisi ginjal atau kondisi medis tertentu, konsultasikan dengan tenaga kesehatan."
        )
        status_kind = "warning"
    else:
        protein_status = "Berada dalam kisaran referensi"
        status_detail = (
            "Asupan protein berada dalam kisaran praktis yang sering digunakan untuk membantu "
            "pemulihan dan pemeliharaan massa otot pada pengguna aktif."
        )
        protein_advice = (
            "Pertahankan konsistensi dan sebarkan protein ke beberapa waktu makan. "
            "Padukan dengan latihan beban yang teratur, tidur yang cukup, dan asupan energi yang sesuai tujuan."
        )
        status_kind = "success"

    # Evaluasi hubungan protein dengan tujuan dan energi skenario.
    if goal == "Menurunkan berat badan":
        goal_protein_note = (
            "Saat cutting, protein yang cukup membantu mempertahankan massa otot, tetapi hasil tetap "
            "bergantung pada defisit energi yang realistis dan latihan yang konsisten."
        )
    elif goal == "Menaikkan berat badan":
        goal_protein_note = (
            "Saat bulking, protein perlu didukung surplus energi yang terkontrol dan latihan progresif; "
            "protein tinggi saja tidak menjamin pertambahan massa otot."
        )
    else:
        goal_protein_note = (
            "Saat maintenance, pertahankan protein yang konsisten sambil menjaga total energi mendekati "
            "kebutuhan pemeliharaan dan menyesuaikannya dengan aktivitas."
        )

    # Ringkasan visual.
    m1, m2, m3 = st.columns(3)
    m1.metric("Protein per kg BB", f"{protein_per_kg:.2f} g/kg")
    m2.metric("Titik tengah referensi", f"{protein_reference_mid:.1f} g")
    m3.metric("Pencapaian titik tengah", f"{protein_percent_of_mid:.0f}%")

    if status_kind == "success":
        st.success(f"**{protein_status}** — {status_detail}")
    else:
        st.warning(f"**{protein_status}** — {status_detail}")

    st.markdown("#### Rentang referensi berbasis berat badan")
    st.write(
        f"Untuk berat badan **{weight:.1f} kg**, kisaran referensi yang digunakan adalah "
        f"**{protein_reference_low:.1f}–{protein_reference_high:.1f} g protein/hari** "
        "(1,4–2,0 g/kg). Nilai ini merupakan acuan umum, bukan angka yang harus dipenuhi secara mutlak."
    )
    st.progress(min(max(simulated_protein / protein_reference_high, 0.0), 1.0))
    st.caption(
        f"Posisi protein skenario: {simulated_protein:.1f} g dari batas atas referensi "
        f"{protein_reference_high:.1f} g. Progress dibatasi pada 100% untuk memudahkan pembacaan."
    )

    st.markdown("#### Perbandingan dengan target profil")
    comparison_cols = st.columns(3)
    comparison_cols[0].metric("Target profil", f"{baseline_protein:.1f} g")
    comparison_cols[1].metric("Protein skenario", f"{simulated_protein:.1f} g")
    comparison_cols[2].metric("Perubahan", f"{protein_gap_to_target:+.1f} g")

    if protein_gap_to_target < 0:
        st.write(
            f"Skenario mengurangi protein sebesar **{abs(protein_gap_to_target):.1f} g/hari** "
            "dibandingkan target profil. Pastikan pengurangan ini tidak membuat asupan protein "
            "berada di bawah kebutuhan yang direncanakan, terutama ketika latihan dilakukan rutin."
        )
    elif protein_gap_to_target > 0:
        st.write(
            f"Skenario menambah protein sebesar **{protein_gap_to_target:.1f} g/hari** "
            "dibandingkan target profil. Penambahan dapat membantu mencapai target, tetapi manfaatnya "
            "bergantung pada kecukupan energi, kualitas latihan, dan pemulihan."
        )
    else:
        st.write("Protein skenario sama dengan target protein profil.")

    st.markdown("#### Interpretasi berdasarkan tujuan")
    st.info(goal_protein_note)
    st.write(f"**Saran praktis:** {protein_advice}")

    st.markdown("#### Contoh pembagian protein harian")
    meal_count = 4
    suggested_per_meal = simulated_protein / meal_count if meal_count else 0
    st.write(
        f"Sebagai ilustrasi, protein **{simulated_protein:.1f} g/hari** dapat dibagi ke sekitar "
        f"**{meal_count} waktu makan**, masing-masing ±**{suggested_per_meal:.1f} g**. "
        "Pembagian ini hanya contoh agar target lebih mudah dicapai, bukan aturan wajib."
    )
    st.caption(
        "Contoh sumber protein lokal: telur, ikan kembung, tuna, dada ayam, tempe, tahu, "
        "susu, dan yoghurt tanpa tambahan gula. Pilih kombinasi sesuai preferensi, anggaran, "
        "toleransi, dan kebutuhan energi."
    )

    st.markdown("#### Checklist evaluasi skenario")
    checks = [
        ("Protein berada pada kisaran acuan", protein_reference_low <= simulated_protein <= protein_reference_high),
        ("Kalori skenario mendukung tujuan", aligned),
        ("Perubahan protein tidak terlalu ekstrem", simulated_protein <= weight * 3),
        ("Masih ada ruang untuk karbohidrat, lemak, dan serat", simulated_protein * 4 < simulated_calories * 0.45 if simulated_calories > 0 else False),
    ]
    for label, passed in checks:
        st.write(("✅ " if passed else "⚠️ ") + label)

    st.caption(
        "Catatan: baseline simulasi menggunakan target profil yang tersimpan, bukan total makanan yang dicatat hari ini. "
        "Interpretasi ini bersifat edukatif; konsultasikan dengan ahli gizi atau tenaga kesehatan untuk kebutuhan khusus."
    )
