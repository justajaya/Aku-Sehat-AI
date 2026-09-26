
import os
import re
import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="Aku Sehat AI", page_icon="🥗", layout="wide")

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


def _trend_date(value):
    import datetime as _dt
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if value is None:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return _dt.datetime.strptime(s[:19], fmt).date()
        except Exception:
            pass
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00")).date()
    except Exception:
        return None

def _calorie_trend(rows, days=7):
    import datetime as _dt
    import pandas as _pd
    today = _dt.date.today()
    dates = [today - _dt.timedelta(days=days-1-i) for i in range(days)]
    totals = {d: 0.0 for d in dates}
    if not isinstance(rows, list):
        rows = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        d = _trend_date(item.get("date") or item.get("tanggal") or item.get("created_at") or item.get("timestamp") or item.get("waktu"))
        raw = item.get("calories", item.get("kalori", item.get("calories_kcal", item.get("energy", item.get("Energi (kkal)")))))
        if d not in totals:
            continue
        try:
            val = float(str(raw).replace(",", ".")) if raw is not None else 0.0
        except Exception:
            continue
        if val >= 0:
            totals[d] += val
    return _pd.DataFrame({"Tanggal": dates, "Kalori": [round(totals[d], 1) for d in dates]})

def render_calorie_trend(rows, target_calories=0, days=7):
    import plotly.graph_objects as _go
    trend = _calorie_trend(rows, days)
    target = float(target_calories or 0)
    avg = float(trend["Kalori"].mean()) if len(trend) else 0.0
    today_cal = float(trend.iloc[-1]["Kalori"]) if len(trend) else 0.0
    remaining = max(target - today_cal, 0.0) if target else 0.0

    st.markdown(
        '<div class="trend-section"><div class="trend-kicker">PERKEMBANGAN</div>'
        '<div class="trend-title">Perkembangan kalori</div>'
        '<div class="trend-desc">Pantau asupan kalori harian dari makanan yang tersimpan di riwayat.</div></div>',
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    cards = [
        ("Rata-rata", f"{avg:,.0f}", "kcal", "7 hari terakhir"),
        ("Hari ini", f"{today_cal:,.0f}", "kcal", "tercatat dari riwayat"),
        ("Target harian", f"{target:,.0f}", "kcal", f"{remaining:,.0f} kcal tersisa" if target else "Target belum diatur"),
    ]
    for col, (label, val, unit, note) in zip((c1, c2, c3), cards):
        with col:
            st.markdown(
                f'<div class="trend-stat"><div class="trend-label">{label}</div>'
                f'<div class="trend-value">{val} <span>{unit}</span></div>'
                f'<div class="trend-note">{note}</div></div>',
                unsafe_allow_html=True
            )

    fig = _go.Figure()
    fig.add_trace(_go.Scatter(
        x=trend["Tanggal"], y=trend["Kalori"], mode="lines+markers",
        name="Kalori dikonsumsi",
        line=dict(width=3, color="#159a83"),
        marker=dict(size=8, color="#159a83"),
        hovertemplate="%{x|%d %b}<br>%{y:,.0f} kcal<extra></extra>"
    ))
    if target > 0:
        fig.add_trace(_go.Scatter(
            x=trend["Tanggal"], y=[target] * len(trend), mode="lines",
            name="Target harian",
            line=dict(width=2, dash="dash", color="#d79a35"),
            hovertemplate="Target: %{y:,.0f} kcal<extra></extra>"
        ))
    fig.update_layout(
        height=350, margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        xaxis=dict(showgrid=False, tickformat="%d %b"),
        yaxis=dict(title="Kalori (kcal)", gridcolor="rgba(15,61,54,.10)", zeroline=False)
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


st.markdown('<style>\n.trend-stat{background:rgba(255,255,255,.80);border:1px solid rgba(15,61,54,.10);border-radius:20px;padding:18px 20px;box-shadow:0 10px 28px rgba(15,61,54,.07);min-height:118px}\n.trend-label{color:#58736e;font-size:.78rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase}\n.trend-value{color:#123f38;font-size:1.65rem;font-weight:800;line-height:1.2;margin-top:8px}\n.trend-value span{font-size:.82rem;font-weight:700;color:#6d8580}\n.trend-note{color:#7b918c;font-size:.78rem;margin-top:5px}\n.trend-kicker{color:#159a83;font-size:.72rem;font-weight:800;letter-spacing:.12em}\n.trend-title{color:#123f38;font-size:1.45rem;font-weight:800;margin-top:2px}\n.trend-desc{color:#6d817c;font-size:.9rem;margin:3px 0 14px}\n</style>', unsafe_allow_html=True)
# UI theme: colorful, modern, and nutrition-focused.
st.markdown('<style>\n.ai-insight-shell{background:linear-gradient(135deg,rgba(255,255,255,.92),rgba(232,250,244,.92));border:1px solid rgba(18,137,119,.16);border-radius:24px;padding:22px 24px;margin:22px 0;box-shadow:0 14px 38px rgba(18,76,70,.08)}\n.ai-insight-kicker{color:#0a8d7b;font-size:.72rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}\n.ai-insight-title{color:#123b56;font-size:1.35rem;font-weight:850;margin:4px 0}\n.ai-insight-desc{color:#66807a;font-size:.9rem;margin-bottom:14px}\n</style>', unsafe_allow_html=True)
st.markdown("""<style>
/* v6: background is a background-image only; never overlay Streamlit content. */
.stApp {background: radial-gradient(ellipse 750px 450px at 0% 0%,rgba(25,181,151,.18),transparent 72%),radial-gradient(ellipse 680px 500px at 100% 4%,rgba(116,128,241,.13),transparent 72%),radial-gradient(ellipse 550px 420px at 85% 98%,rgba(251,195,97,.14),transparent 72%),linear-gradient(135deg,#f7fbff,#f0f9f5 52%,#fffaf2) !important;color:#19334b;}
[data-testid="stAppViewContainer"] {background:transparent !important;}
[data-testid="stHeader"] {background:rgba(247,251,255,.86) !important;}
.block-container {max-width:1360px;padding-top:2.1rem;padding-bottom:4rem;}
[data-testid="stSidebar"] {background:linear-gradient(155deg,#102c46,#0c5661 56%,#108778) !important;}
[data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 {color:#f4fffd !important;}
[data-testid="stSidebar"] .login-card {color:#f4fffd !important;margin-bottom:8px;}
[data-testid="stSidebar"] .login-label {color:#d9fffa !important;font-weight:800;letter-spacing:.08em;font-size:.78rem;}
[data-testid="stSidebar"] .login-email {color:#ffffff !important;font-size:.92rem;margin-top:4px;}
[data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stWidgetLabel"] label,
[data-testid="stSidebar"] [data-testid="stForm"] [data-testid="stWidgetLabel"] {color:#173b50 !important;font-weight:650 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] small {color:#587383 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] input {background:#ffffff !important;color:#173b50 !important;-webkit-text-fill-color:#173b50 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] textarea {background:#ffffff !important;color:#173b50 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] [role="combobox"] {background:#ffffff !important;color:#173b50 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] [data-baseweb="select"] * {color:#173b50 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] button {color:#173b50 !important;}
[data-testid="stSidebar"] [data-testid="stForm"] button[kind="primaryFormSubmit"] {color:#ffffff !important;}
.brand-header,.page-hero {background:linear-gradient(115deg,rgba(255,255,255,.97),rgba(231,250,242,.95) 60%,rgba(255,247,229,.95));border:1px solid rgba(24,150,128,.15);border-radius:26px;padding:27px 30px;margin-bottom:22px;box-shadow:0 16px 44px rgba(27,73,81,.085);}
.brand-header {display:flex;align-items:center;gap:22px;}
.brand-icon,.auth-icon {font-size:2.5rem;background:linear-gradient(135deg,#0d9984,#7d80ec);border-radius:19px;padding:13px;}
.brand-kicker,.page-chip {color:#0a8d7b;font-weight:750;font-size:.78rem;letter-spacing:.12em;text-transform:uppercase;}
.brand-title,.auth-title {color:#183d51;font-size:2.4rem;font-weight:850;letter-spacing:-.05em;}
.brand-title span,.auth-title span {color:#0d9b85;}
.brand-subtitle,.auth-subtitle,.page-desc {color:#637d8c;font-size:.96rem;}
.page-title {font-size:1.8rem;font-weight:800;color:#19394e;letter-spacing:-.035em;margin:7px 0;}
.auth-shell {padding:32px 30px;border-radius:27px;background:linear-gradient(120deg,#e9faf3,#fff 55%,#fff4e4);box-shadow:0 15px 42px rgba(24,81,84,.09);margin-bottom:25px;}
.auth-brand {display:flex;align-items:center;gap:18px;}
.auth-benefits {display:flex;gap:14px;flex-wrap:wrap;margin-top:26px;}
.auth-benefit {background:#ffffffbd;border:1px solid #d8eee5;border-radius:15px;padding:15px;flex:1;min-width:190px;color:#527184;}
.auth-benefit strong {display:block;color:#137f72;margin-bottom:7px;}
[data-testid="stMetric"],div[data-testid="stForm"],[data-testid="stExpander"] {background:rgba(255,255,255,.94);border:1px solid #dcebe7;border-radius:18px;padding:14px;box-shadow:0 8px 28px rgba(21,66,74,.055);}
.stButton>button,.stFormSubmitButton>button {border-radius:12px;background:linear-gradient(105deg,#0d9b86,#0a7b83);color:white;font-weight:700;border:0;}
[data-testid="stTabs"] [role="tablist"] {background:#e9f5f0;border-radius:14px;padding:6px;}
[data-testid="stTabs"] button[aria-selected="true"] {background:white;border-radius:10px;color:#087e71;}
@media(max-width:720px){.brand-title{font-size:1.65rem}.brand-header{padding:20px}.auth-benefits{display:block}.auth-benefit{margin-bottom:9px}}

/* v6.1 premium visual system */
:root {
  --ink:#123b56; --muted:#6d8795; --teal:#0b9b86; --teal-dark:#08786f;
  --line:#dcece8; --card:#ffffff; --soft:#eef8f5;
}
[data-testid="stSidebar"] [data-testid="stWidgetLabel"],
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p,
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] label { color:#173b50 !important; font-weight:700 !important; }
[data-testid="stSidebar"] [data-testid="stTextInput"] label,
[data-testid="stSidebar"] [data-testid="stNumberInput"] label,
[data-testid="stSidebar"] [data-testid="stSelectbox"] label { color:#173b50 !important; }
[data-testid="stSidebar"] [data-testid="stForm"] { background:rgba(255,255,255,.96) !important; border:1px solid rgba(255,255,255,.55) !important; box-shadow:0 18px 40px rgba(3,43,52,.16) !important; }
[data-testid="stMetric"] { position:relative; overflow:hidden; min-height:112px; padding:20px 20px 18px !important; background:linear-gradient(145deg,#ffffff 0%,#f7fcfb 100%) !important; border:1px solid #d8ebe6 !important; box-shadow:0 12px 32px rgba(23,72,82,.07) !important; }
[data-testid="stMetric"]:after { content:""; position:absolute; width:90px; height:90px; border-radius:50%; right:-28px; top:-32px; background:rgba(20,180,150,.08); }
[data-testid="stMetricLabel"] { color:#688493 !important; font-weight:700 !important; }
[data-testid="stMetricValue"] { color:#123b56 !important; font-weight:850 !important; letter-spacing:-.04em; }
.page-hero { position:relative; overflow:hidden; }
.page-hero:after { content:""; position:absolute; width:230px; height:230px; right:-70px; top:-100px; border-radius:50%; background:rgba(20,177,150,.10); pointer-events:none; }
.page-title { position:relative; z-index:1; }
.macro-panel { background:linear-gradient(145deg,rgba(255,255,255,.97),rgba(246,252,250,.92)); border:1px solid #dcece8; border-radius:24px; padding:22px 22px 18px; box-shadow:0 14px 36px rgba(25,75,83,.07); height:100%; }
.macro-heading { font-size:1.18rem; font-weight:850; color:#123b56; margin-bottom:5px; }
.macro-subheading { color:#76909d; font-size:.88rem; line-height:1.55; margin-bottom:8px; }
.macro-legend-card { background:linear-gradient(160deg,#ffffff,#f4fbf8); border:1px solid #dcece8; border-radius:22px; padding:18px; margin-top:12px; box-shadow:0 10px 28px rgba(20,72,82,.055); }
.macro-item { display:grid; grid-template-columns:14px 1fr auto; gap:12px; align-items:center; padding:13px 12px; border-radius:15px; background:#fff; border:1px solid #e5f0ed; margin-bottom:9px; }
.macro-item:last-child { margin-bottom:0; }
.macro-dot { width:11px; height:11px; border-radius:50%; box-shadow:0 0 0 4px rgba(18,59,86,.035); }
.macro-name { color:#173b50; font-weight:800; font-size:.94rem; }
.macro-meta { color:#78909c; font-size:.78rem; margin-top:2px; }
.macro-percent { color:#123b56; font-weight:850; font-size:1rem; }
.macro-total { margin-top:12px; padding:14px 15px; border-radius:16px; background:linear-gradient(135deg,#e8f8f3,#eef6ff); color:#123b56; border:1px solid #d7ebe6; }
.food-result-shell { background:linear-gradient(145deg,#ffffff 0%,#f4fbf8 100%); border:1px solid #d9ebe7; border-radius:25px; padding:22px; box-shadow:0 14px 38px rgba(22,73,82,.07); margin:14px 0 22px; }
.food-result-head { display:flex; align-items:center; justify-content:space-between; gap:16px; margin-bottom:17px; }
.food-result-title { color:#123b56; font-size:1.25rem; font-weight:850; }
.food-result-sub { color:#718a97; font-size:.84rem; margin-top:3px; }
.source-pill { display:inline-flex; align-items:center; gap:7px; padding:8px 12px; border-radius:999px; background:#e8f7f2; color:#087b6d; font-weight:800; font-size:.76rem; border:1px solid #cdece2; white-space:nowrap; }
.nutrient-card { background:#fff; border:1px solid #dfede9; border-radius:18px; padding:16px 17px; box-shadow:0 8px 22px rgba(19,69,79,.045); min-height:98px; }
.nutrient-label { color:#78909c; font-size:.78rem; font-weight:700; margin-bottom:6px; }
.nutrient-value { color:#123b56; font-size:1.55rem; line-height:1.1; font-weight:850; letter-spacing:-.03em; }
.nutrient-unit { color:#78909c; font-size:.82rem; font-weight:650; }
.resolution-card { background:linear-gradient(135deg,#edf9f5,#f2f7ff); border:1px solid #d7ebe7; border-radius:22px; padding:19px 21px; margin:12px 0 18px; box-shadow:0 10px 28px rgba(21,73,82,.055); }
.resolution-label { color:#6f8996; font-size:.75rem; text-transform:uppercase; letter-spacing:.1em; font-weight:850; }
.resolution-name { color:#123b56; font-size:1.2rem; font-weight:850; margin:3px 0 7px; }
.resolution-detail { color:#617d8c; font-size:.86rem; line-height:1.5; }
.correction-shell { background:rgba(255,255,255,.72); border:1px solid #deece9; border-radius:24px; padding:22px; box-shadow:0 10px 30px rgba(25,75,83,.045); margin-top:18px; }
.section-kicker { color:#0b9b86; text-transform:uppercase; letter-spacing:.1em; font-weight:850; font-size:.72rem; }
.stButton>button:hover,.stFormSubmitButton>button:hover { transform:translateY(-1px); box-shadow:0 9px 22px rgba(11,155,134,.18); }
[data-testid="stTabs"] [role="tablist"] { box-shadow:0 7px 20px rgba(22,70,80,.05); }

</style>""", unsafe_allow_html=True)

def read_secret(name, default=None):
    """Read configuration from environment variables or Streamlit Secrets."""
    value = os.getenv(name)
    if value:
        return str(value).strip()
    try:
        value = st.secrets.get(name)
        if value:
            return str(value).strip()
    except (KeyError, FileNotFoundError, RuntimeError, TypeError):
        pass
    return default


SUPABASE_URL = read_secret("SUPABASE_URL")
SUPABASE_KEY = read_secret("SUPABASE_KEY")
GEMINI_API_KEY = read_secret("GEMINI_API_KEY")
# Default mengikuti model yang disarankan oleh pesan error Gemini pada project ini.
GEMINI_MODEL = read_secret("GEMINI_MODEL", "gemini-3.8-flash")
# Normalisasi konfigurasi agar tidak mengirim awalan "models/" dan
# otomatis memperbaiki nama model lama yang memicu 404 pada project ini.
GEMINI_MODEL = GEMINI_MODEL.removeprefix("models/")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning("Konfigurasi Supabase belum lengkap. Isi .env agar login dan riwayat aktif.")
    st.info("Pastikan .env berada dalam folder yang sama dengan app.py, lalu restart Streamlit.")
    st.stop()
try:
    SUPABASE = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as exc:
    st.error("Supabase gagal diinisialisasi. Periksa URL dan anon key pada .env.")
    st.exception(exc)
    st.stop()


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


def exact_indonesia_match(query, limit=12):
    """Match a food against the dataset ONLY when the normalized full name matches.

    This deliberately does not use fuzzy/token scoring. A food is considered a
    dataset match only when the complete normalized food name is identical.
    This prevents unrelated foods from inheriting nutrition values just because
    they share words such as "segar", "goreng", or "ayam".
    """
    catalog = indonesia_catalog_only()
    if catalog.empty:
        return catalog.head(0)
    q = normalize_text(query)
    if not q:
        return catalog.head(0)
    names = catalog["food_name"].fillna("").astype(str).map(normalize_text)
    result = catalog.loc[names.eq(q)].copy()
    return result.head(limit)


def dataset_match_for_ai(result, corrected_name=None):
    """Resolve the AI food to an exact dataset record, never a fuzzy record."""
    names_to_try = []
    if corrected_name:
        names_to_try.append(str(corrected_name).strip())
    if isinstance(result, dict):
        names_to_try.extend([
            str(result.get("food_name_id") or "").strip(),
            str(result.get("food_name") or "").strip(),
        ])
        components = result.get("components") or []
        if len(components) == 1 and isinstance(components[0], dict):
            names_to_try.extend([
                str(components[0].get("name_id") or "").strip(),
            ])
    seen = set()
    for name in names_to_try:
        normalized = normalize_text(name)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        matches = exact_indonesia_match(name, limit=1)
        if not matches.empty:
            return matches.iloc[0]
    return None


def validated_indonesia_match(query, limit=12):
    """Backward-compatible wrapper: dataset matching is now exact-only."""
    return exact_indonesia_match(query, limit=limit)

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


def build_recommendations(goal, gym_focus, remaining_calories, remaining_protein, query="", max_meal_kcal=None):
    """Build a robust candidate pool from the existing Indonesian nutrition catalog.

    The old workflow could return an empty DataFrame when a natural-language
    preference contained several comma-separated foods. This version treats the
    preference as a set of terms, ranks matching foods, and always falls back to
    the full catalog when the preference is too restrictive. AI is used later to
    interpret and compose a meal from this validated candidate pool.
    """
    catalog = indonesia_catalog_only()
    if catalog.empty:
        return pd.DataFrame()

    candidates = catalog.copy()
    candidates["food_name"] = candidates["food_name"].fillna("").astype(str).str.strip()
    candidates["category"] = candidates.apply(
        lambda r: classify_food(r.get("food_name", ""), r.get("food_type", "")), axis=1
    )

    for col in ["calories", "protein_g", "fat_g", "carbs_g", "fiber_g"]:
        candidates[col] = pd.to_numeric(candidates[col], errors="coerce").fillna(0)

    candidates = candidates[
        (candidates["calories"] >= 20) &
        (~candidates["category"].eq("Bumbu/saus"))
    ].copy()
    if candidates.empty:
        return pd.DataFrame()

    # ---------------------------------------------------------
    # Preference matching: split comma/"dan" input into terms.
    # Example: "ayam, nasi, telur" -> ayam | nasi | telur.
    # A food only needs to match one term; matches are ranked higher.
    # ---------------------------------------------------------
    raw_query = str(query or "").strip()
    terms = [t.strip() for t in re.split(r"[,;]|\bdan\b", raw_query, flags=re.IGNORECASE) if t.strip()]
    if raw_query and terms:
        match_score = pd.Series(0.0, index=candidates.index)
        names = candidates["food_name"].map(normalize_text)
        for term in terms:
            variants = query_variants(term)
            term_score = pd.Series(0.0, index=candidates.index)
            for variant in variants:
                v = normalize_text(variant)
                if not v:
                    continue
                phrase = names.str.contains(re.escape(v), na=False)
                term_score += phrase.astype(float) * 12
                for word in v.split():
                    if len(word) >= 3:
                        term_score += names.str.contains(re.escape(word), na=False).astype(float) * 2
            match_score += term_score.clip(upper=14)
        # If the preference produces matches, use them first but keep the
        # remainder available as alternatives. If it produces no matches,
        # DO NOT show the old "no food found" dead-end.
        matched = candidates.loc[match_score > 0].copy()
        if not matched.empty:
            matched["preference_score"] = match_score.loc[matched.index]
            rest = candidates.loc[match_score <= 0].copy()
            rest["preference_score"] = 0.0
            candidates = pd.concat([matched, rest], ignore_index=True)
        else:
            candidates["preference_score"] = 0.0
            st.info("Preferensi belum cocok dengan nama dataset secara langsung. Sistem tetap mencari pilihan yang paling sesuai dari katalog nutrisi.")
    else:
        candidates["preference_score"] = 0.0

    candidates["is_indonesia"] = candidates["source"].eq("Nutrition Indonesia").astype(int)
    candidates["protein_density"] = candidates["protein_g"] / candidates["calories"].clip(lower=1) * 100
    candidates["fat_ratio"] = candidates["fat_g"] * 9 / candidates["calories"].clip(lower=1) * 100

    # Base score combines user preference, protein density, fiber, goal and
    # numerical fit. The numerical score remains deterministic and auditable.
    candidates["score"] = candidates["preference_score"] * 3 + candidates["is_indonesia"] * 18
    candidates["score"] += np.where(
        candidates["category"].eq("Protein utama"),
        candidates["protein_g"] * 1.8 + candidates["protein_density"] * 1.2,
        candidates["protein_g"] * 0.35,
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

    def choose_portion(row):
        low, high = _portion_limits(row["category"], gym_focus)
        target_kcal = min(max(float(remaining_calories or 0), 150), float(max_meal_kcal or 450), 450)
        estimated = target_kcal / max(float(row["calories"]), 1) * 100
        return float(np.clip(estimated, low, high))

    candidates["reference_grams"] = candidates.apply(choose_portion, axis=1)
    candidates["portion_calories"] = candidates["calories"] * candidates["reference_grams"] / 100
    candidates["portion_protein"] = candidates["protein_g"] * candidates["reference_grams"] / 100
    candidates["portion_carbs"] = candidates["carbs_g"] * candidates["reference_grams"] / 100

    if remaining_calories > 0:
        target = min(float(remaining_calories), 450)
        candidates["score"] -= abs(candidates["portion_calories"] - target) / max(target, 1) * 1.5
    if remaining_protein > 0:
        candidates["score"] += candidates["portion_protein"].clip(upper=remaining_protein) / max(remaining_protein, 1) * 5

    candidates = candidates.sort_values(
        ["score", "preference_score", "protein_density"], ascending=[False, False, False]
    )

    selected = []
    category_counts = {}
    for _, row in candidates.iterrows():
        cat = row["category"]
        if category_counts.get(cat, 0) >= 3:
            continue
        selected.append(row)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if len(selected) >= 12:
            break

    if not selected:
        return pd.DataFrame()

    result = pd.DataFrame(selected).copy().reset_index(drop=True)
    result["reason"] = result.apply(
        lambda row: recommendation_reason(goal, gym_focus, row, remaining_calories, remaining_protein),
        axis=1,
    )
    return result


def generate_ai_meal_recommendation(goal, gym_focus, remaining_calories, remaining_protein, preference, candidates, max_meal_kcal=None):
    """Use Gemini to turn validated dataset candidates into a personalized meal.

    AI does not invent nutrition values. All numeric nutrition values shown to the
    model come from the existing catalog and the program-calculated portions.
    """
    if candidates is None or candidates.empty:
        return None, None, (
            "Kandidat makanan belum tersedia. Periksa data/nutrition.csv dan pastikan "
            "kolom name, calories, proteins, fat, dan carbohydrate tersedia."
        )

    rows = []
    for _, r in candidates.head(12).iterrows():
        rows.append({
            "food_name": str(r.get("food_name", "")),
            "category": str(r.get("category", "Lainnya")),
            "reference_grams": round(float(r.get("reference_grams", 100)), 1),
            "calories": round(float(r.get("portion_calories", 0)), 1),
            "protein_g": round(float(r.get("portion_protein", 0)), 1),
            "carbs_g": round(float(r.get("portion_carbs", 0)), 1),
            "fat_g": round(float(r.get("fat_g", 0)) * float(r.get("reference_grams", 100)) / 100, 1),
        })

    prompt = f"""
Kamu adalah AI decision-support component pada aplikasi Aku Sehat AI.
Gunakan HANYA kandidat makanan dan angka yang diberikan aplikasi. Jangan mengarang
makanan atau angka nutrisi baru. Jangan memberikan diagnosis medis.

Konteks pengguna:
- Tujuan profil: {goal}
- Fokus nutrisi: {gym_focus}
- Sisa kalori hari ini: {float(remaining_calories):.0f} kcal
- Sisa protein hari ini: {float(remaining_protein):.1f} g
- Preferensi pengguna: {preference or 'tidak ada'}
- Batas kalori satu rekomendasi: {float(max_meal_kcal or 450):.0f} kcal

Kandidat tervalidasi dari dataset Nutrition Indonesia:
{json.dumps(rows, ensure_ascii=False, indent=2)}

Tugas:
1. Pilih kombinasi 2-4 kandidat yang paling masuk akal sebagai satu rekomendasi makan.
2. Utamakan preferensi jika tersedia, lalu pertimbangkan kecocokan dengan sisa target.
3. Gunakan angka nutrisi kandidat apa adanya; jangan membuat angka baru.
4. Jelaskan alasan pemilihan secara singkat.
5. Berikan satu alternatif menggunakan kandidat yang tersedia.

Gunakan Bahasa Indonesia dan format:
### Rekomendasi AI
**Menu:** ...

**Estimasi:** ...

**Mengapa dipilih:** ...

**Alternatif:** ...

**Catatan:** Nilai nutrisi berasal dari dataset aplikasi dan merupakan estimasi berdasarkan porsi referensi.
"""
    try:
        text, model_used = _generate_gemini_text(prompt)
        return text, model_used, None
    except Exception as exc:
        return None, None, str(exc)

# =========================================================
# GEMINI PERSONAL NUTRITION INSIGHT
# =========================================================
def _generate_gemini_text(prompt):
    """Generate text with the same Gemini fallback chain used by image analysis."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY belum diatur di file .env atau Streamlit Secrets.")
    client, models = _gemini_clients()
    last_error = None
    import time
    for model in models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(model=model, contents=prompt)
                text = (response.text or "").strip()
                if text:
                    return text, model
                raise RuntimeError("Gemini mengembalikan respons kosong.")
            except Exception as exc:
                last_error = exc
                message = str(exc).upper()
                retryable = any(x in message for x in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"])
                model_error = any(x in message for x in ["404", "NOT_FOUND", "INVALID_ARGUMENT", "MODEL"])
                if retryable and attempt == 0:
                    time.sleep(1.5)
                    continue
                if model_error:
                    break
                break
    raise RuntimeError(f"Semua model Gemini untuk insight gagal digunakan. Detail terakhir: {last_error}")


def generate_nutrition_insight(
    selected_date,
    daily_totals,
    calorie_target,
    protein_target,
    goal,
    meals_df,
    trend_rows,
):
    """Analyze only recorded nutrition data; do not invent measurements or diagnoses."""
    import json as _json

    foods = []
    if meals_df is not None and not meals_df.empty:
        for _, row in meals_df.iterrows():
            foods.append({
                "nama": str(row.get("food_name", "")),
                "sesi": str(row.get("meal_type", "")),
                "gram": float(row.get("grams", 0) or 0),
                "kalori": float(row.get("calories", 0) or 0),
                "protein_g": float(row.get("protein_g", 0) or 0),
                "karbohidrat_g": float(row.get("carbs_g", 0) or 0),
                "lemak_g": float(row.get("fat_g", 0) or 0),
            })

    prompt = f"""
Kamu adalah AI Nutrition Coach untuk aplikasi Aku Sehat AI.

Analisis data nutrisi pengguna berikut.

ATURAN:
- Gunakan HANYA data yang diberikan. Jangan mengarang angka atau riwayat.
- Jangan memberikan diagnosis medis.
- Jika data 7 hari tidak cukup, katakan bahwa pola belum dapat disimpulkan.
- Jangan menyarankan diet ekstrem.
- Saran harus praktis dan terkait dengan target pengguna.
- Gunakan bahasa Indonesia.
- Jangan mengubah angka yang diberikan.

DATA HARI INI ({selected_date}):
{_json.dumps({
    "target_kalori_kcal": round(float(calorie_target), 1),
    "target_protein_g": round(float(protein_target), 1),
    "tujuan": str(goal),
    "total_kalori_kcal": round(float(daily_totals["calories"]), 1),
    "protein_g": round(float(daily_totals["protein_g"]), 1),
    "karbohidrat_g": round(float(daily_totals["carbs_g"]), 1),
    "lemak_g": round(float(daily_totals["fat_g"]), 1),
    "makanan": foods,
}, ensure_ascii=False, indent=2)}

DATA KALORI 7 HARI:
{_json.dumps([
    {"tanggal": str(r.get("date")), "kalori": round(float(r.get("calories", 0)), 1)}
    for r in trend_rows
], ensure_ascii=False, indent=2)}

Format jawaban:

### Ringkasan hari ini
2-3 kalimat mengenai posisi asupan terhadap target.

### Insight pola
2-3 poin hanya jika didukung data. Jangan membuat pola jika datanya belum cukup.

### Saran makan berikutnya
1-2 arah pilihan makanan berdasarkan kebutuhan yang terlihat. Jangan mengarang angka nutrisi.

### Catatan
1 kalimat bahwa insight hanya berdasarkan makanan yang tercatat di aplikasi.
"""
    return _generate_gemini_text(prompt)


# =========================================================
# GEMINI IMAGE ANALYSIS
# =========================================================
def _clean_json_response(raw_text):
    raw = (raw_text or "").strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
    raw = re.sub(r"\s*```$", "", raw)
    # Some models occasionally add a short sentence around the JSON.
    if not raw.startswith("{"):
        left, right = raw.find("{"), raw.rfind("}")
        if left >= 0 and right > left:
            raw = raw[left:right + 1]
    return json.loads(raw)


def _gemini_clients():
    if not GEMINI_API_KEY:
        return None, []
    from google import genai
    client = genai.Client(api_key=GEMINI_API_KEY)
    configured = GEMINI_MODEL.strip() if GEMINI_MODEL else ""
    # Gemini 2.0 Flash has been retired. Normalize old local .env values
    # so an existing project does not fail with a 404 before reaching the
    # currently supported vision-capable model.
    deprecated_aliases = {
        # Gemini 2.5 is still a legacy endpoint, but Google currently limits
        # access for new users/projects. Use the current Flash generation.
        "gemini-2.0-flash": "gemini-3.8-flash",
        "models/gemini-2.0-flash": "gemini-3.8-flash",
        "gemini-2.5-flash": "gemini-3.8-flash",
        "models/gemini-2.5-flash": "gemini-3.8-flash",
        "gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
        "models/gemini-2.5-flash-lite": "gemini-3.5-flash-lite",
    }
    configured = deprecated_aliases.get(configured, configured)
    candidates = [
        configured,
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3.5-flash-lite",
    ]
    models = []
    for model in candidates:
        model = model.removeprefix("models/").strip()
        model = deprecated_aliases.get(model, model)
        if model and model not in models:
            models.append(model)
    return client, models


def _generate_gemini(image_bytes, mime_type, prompt):
    """Generate content with a small model fallback chain for API compatibility."""
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY belum diatur di file .env atau Streamlit Secrets.")
    from google.genai import types
    client, models = _gemini_clients()
    last_error = None
    import time
    for model in models:
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=[
                        types.Part.from_bytes(data=image_bytes, mime_type=mime_type or "image/jpeg"),
                        prompt,
                    ],
                )
                text = (response.text or "").strip()
                if text:
                    return text, model
                raise RuntimeError("Gemini mengembalikan respons kosong.")
            except Exception as exc:
                last_error = exc
                message = str(exc).upper()
                retryable = any(x in message for x in ["503", "UNAVAILABLE", "429", "RESOURCE_EXHAUSTED"])
                model_error = any(x in message for x in ["404", "NOT_FOUND", "INVALID_ARGUMENT", "MODEL"])
                if retryable and attempt == 0:
                    time.sleep(1.5)
                    continue
                if model_error:
                    break
                break
    raise RuntimeError(f"Semua model Gemini yang dikonfigurasi gagal digunakan. Detail terakhir: {last_error}")


def _normalize_ai_result(parsed):
    """Normalize AI output and derive total nutrients from visible components when possible."""
    if not isinstance(parsed, dict):
        raise ValueError("Format respons AI bukan objek JSON.")
    parsed.setdefault("food_name_id", parsed.get("food_name") or parsed.get("food_name_en") or "Makanan tidak teridentifikasi")
    parsed.setdefault("food_name_en", "")
    parsed.setdefault("components", [])
    try:
        grams = float(parsed.get("estimated_grams") or 100)
    except (TypeError, ValueError):
        grams = 100.0
    parsed["estimated_grams"] = max(1.0, grams)
    try:
        parsed["confidence"] = float(parsed.get("confidence")) if parsed.get("confidence") is not None else None
    except (TypeError, ValueError):
        parsed["confidence"] = None

    components = [c for c in parsed.get("components", []) if isinstance(c, dict)]
    parsed["components"] = components
    totals = {}
    for key in ["calories", "protein_g", "fat_g", "carbs_g"]:
        values = []
        for comp in components:
            try:
                v = float(comp.get(key))
                if v >= 0:
                    values.append(v)
            except (TypeError, ValueError):
                pass
        if values:
            totals[key] = round(sum(values), 2)
    # If components are unavailable, use the AI's per-100 g estimate.
    if len(totals) < 4:
        fallback = nutrients_from_100g(parsed)
        for key, value in fallback.items():
            if key not in totals and value is not None:
                totals[key] = value
    parsed["total_nutrients"] = totals
    return parsed


def analyze_image(uploaded_file):
    prompt = """
Anda adalah mesin analisis makanan berbasis visi. Analisis GAMBAR yang diberikan
terlebih dahulu; jangan menggunakan dataset eksternal sebagai sumber identitas.
Identifikasi apa yang benar-benar terlihat, termasuk hidangan campuran dan
komponen yang terlihat. Jangan menebak makanan lain hanya karena namanya mirip.

Kembalikan HANYA JSON valid dengan struktur:
{
  "food_name_id": "nama makanan/hidangan utama dalam Bahasa Indonesia",
  "food_name_en": "English equivalent",
  "portion_class": "kecil|sedang|besar|tidak diketahui",
  "estimated_grams": number,
  "confidence": number 0..1,
  "notes": "asumsi visual dan keterbatasan",
  "components": [
    {
      "name_id": "nama komponen yang benar-benar terlihat",
      "name_en": "English name",
      "estimated_grams": number,
      "calories": number,
      "protein_g": number,
      "fat_g": number,
      "carbs_g": number,
      "fiber_g": number or null,
      "notes": "asumsi komponen"
    }
  ],
  "calories_per_100g": number or null,
  "protein_g_per_100g": number or null,
  "fat_g_per_100g": number or null,
  "carbs_g_per_100g": number or null,
  "fiber_g_per_100g": number or null
}

Aturan penting:
1. Bedakan makanan utama dengan garnish, saus, minyak, dan pelengkap bila terlihat.
2. Untuk hidangan campuran, pecah komponen dan estimasikan berat masing-masing.
3. Nilai nutrisi pada komponen adalah estimasi untuk BERAT KOMPONEN YANG TERLIHAT,
   bukan angka per 100 gram.
4. Jangan mengarang komponen yang tidak terlihat jelas.
5. Jika identitas atau berat tidak pasti, turunkan confidence dan jelaskan di notes.
6. Jangan mencari nama dataset atau memaksakan kecocokan dengan makanan lain.
"""
    try:
        image_bytes = uploaded_file.getvalue()
        mime_type = uploaded_file.type or "image/jpeg"
        raw, model_used = _generate_gemini(image_bytes, mime_type, prompt)
        parsed = _normalize_ai_result(_clean_json_response(raw))
        parsed["model_used"] = model_used
        return parsed, None
    except Exception as exc:
        return None, f"Analisis gambar gagal: {exc}"


def analyze_corrected_food(image_bytes, mime_type, corrected_name, corrected_grams):
    """Re-check the same image after user correction; still no fuzzy dataset lookup."""
    if not image_bytes:
        return None, "Gambar asli tidak tersedia. Unggah dan analisis gambar kembali."
    grams = float(corrected_grams)
    prompt = f"""
Analisis ulang gambar makanan ini dengan mempertimbangkan koreksi pengguna.
Nama makanan yang dikoreksi: {corrected_name.strip()}
Berat porsi yang dikoreksi: {grams:.1f} gram.

Gunakan gambar sebagai bukti utama. Jika nama koreksi tidak sesuai dengan yang
terlihat, jangan diam-diam menggantinya dengan makanan lain; nyatakan konflik
tersebut dalam notes dan turunkan confidence. Jangan menggunakan dataset.

Kembalikan HANYA JSON:
{{
  "food_name": "nama yang dianalisis",
  "estimated_grams": {grams:.1f},
  "calories": number,
  "protein_g": number,
  "fat_g": number,
  "carbs_g": number,
  "confidence": number 0..1,
  "notes": "penjelasan singkat"
}}
Nilai nutrisi harus untuk keseluruhan porsi {grams:.1f} gram.
"""
    try:
        raw, model_used = _generate_gemini(image_bytes, mime_type or "image/jpeg", prompt)
        parsed = _clean_json_response(raw)
        nutrients = {
            "calories": float(parsed.get("calories") or 0),
            "protein_g": float(parsed.get("protein_g") or 0),
            "fat_g": float(parsed.get("fat_g") or 0),
            "carbs_g": float(parsed.get("carbs_g") or 0),
        }
        warnings = validate_nutrients(nutrients)
        if warnings:
            return None, "; ".join(warnings)
        return {
            "food_name": corrected_name.strip(),
            "grams": grams,
            "nutrients": nutrients,
            "confidence": parsed.get("confidence"),
            "notes": parsed.get("notes"),
            "model_used": model_used,
            "correction_name": corrected_name.strip(),
            "correction_grams": grams,
        }, None
    except Exception as exc:
        return None, f"Analisis ulang AI gagal: {exc}"


def resolve_food_result(ai_result, grams=None, corrected_name=None):
    """Final nutrition resolver: exact dataset match first, otherwise AI result.

    The dataset is never used to substitute a different food. For mixed dishes,
    an exact dataset match is accepted only when the WHOLE dish name matches.
    Otherwise the AI's component analysis remains the source of truth.
    """
    grams = float(grams or ai_result.get("estimated_grams") or 100)
    dataset_row = dataset_match_for_ai(ai_result, corrected_name=corrected_name)
    if dataset_row is not None:
        nutrients, error = calculate_nutrients(dataset_row, grams)
        if nutrients and not error:
            return {
                "food_name": corrected_name.strip() if corrected_name else str(dataset_row["food_name"]),
                "grams": grams,
                "nutrients": nutrients,
                "source": "Dataset Nutrition Indonesia — exact match",
                "dataset_food_name": str(dataset_row["food_name"]),
                "matched": True,
            }
    ai_nutrients = ai_result.get("total_nutrients") or {}
    if not ai_nutrients:
        ai_nutrients = nutrients_from_100g(ai_result)
    ai_nutrients = {k: (round(float(v), 2) if v is not None else None) for k, v in ai_nutrients.items()}
    warnings = validate_nutrients(ai_nutrients)
    if warnings:
        return {
            "food_name": corrected_name.strip() if corrected_name else str(ai_result.get("food_name_id") or "Makanan AI"),
            "grams": grams,
            "nutrients": None,
            "source": "AI Vision",
            "warnings": warnings,
            "matched": False,
        }
    return {
        "food_name": corrected_name.strip() if corrected_name else str(ai_result.get("food_name_id") or "Makanan AI"),
        "grams": grams,
        "nutrients": ai_nutrients,
        "source": "AI Vision — estimasi dari gambar",
        "matched": False,
    }


# =========================================================
# APPLICATION
# =========================================================
try:
    user = get_current_user()
except Exception as exc:
    st.error("Gagal memeriksa sesi login. Periksa koneksi dan konfigurasi Supabase.")
    st.exception(exc)
    st.stop()
if not user:
    show_auth()
    st.stop()

user_id = str(user.id)
try:
    profile = get_profile(user_id)
except Exception as exc:
    st.error("Gagal memuat profil. Jalankan supabase_schema.sql dan periksa kebijakan RLS.")
    st.exception(exc)
    st.stop()

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
try:
    meals = get_meals(user_id, selected_date)
except Exception as exc:
    st.error("Gagal memuat riwayat makanan. Periksa tabel meals dan koneksi Supabase.")
    st.exception(exc)
    st.stop()
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
        st.caption("Persentase dihitung berdasarkan kontribusi energi dari karbohidrat (4 kkal/g), protein (4 kkal/g), dan lemak (9 kkal/g). Total kalori ditampilkan di pusat diagram agar tidak terjadi penghitungan ganda.")
        macro_values = {
            "Karbohidrat": max(float(daily_totals["carbs_g"]) * 4, 0.0),
            "Protein": max(float(daily_totals["protein_g"]) * 4, 0.0),
            "Lemak": max(float(daily_totals["fat_g"]) * 9, 0.0),
        }
        macro_colors = {
            "Karbohidrat": "#16B894",
            "Protein": "#399AF2",
            "Lemak": "#8B5CF6",
        }
        macro_df = pd.DataFrame({
            "Makronutrien": list(macro_values.keys()),
            "Energi (kkal)": list(macro_values.values()),
        })
        total_macro_kcal = float(macro_df["Energi (kkal)"].sum())
        if total_macro_kcal <= 0:
            st.info("Belum ada data makronutrien untuk divisualisasikan.")
        else:
            import plotly.graph_objects as go
            macro_df["Persentase"] = macro_df["Energi (kkal)"] / total_macro_kcal * 100
            fig = go.Figure(data=[go.Pie(
                labels=macro_df["Makronutrien"],
                values=macro_df["Energi (kkal)"],
                hole=0.66,
                sort=False,
                direction="clockwise",
                texttemplate="%{percent:.1%}",
                textinfo="text",
                textposition="inside",
                insidetextorientation="radial",
                hovertemplate="<b>%{label}</b><br>%{percent:.1%}<br>%{value:.1f} kkal<extra></extra>",
                marker={"colors": [macro_colors[name] for name in macro_df["Makronutrien"]], "line": {"color": "#ffffff", "width": 4}},
                textfont={"size": 14, "color": "#ffffff"},
            )])
            fig.update_layout(
                height=470,
                margin=dict(l=8, r=8, t=8, b=8),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                annotations=[{
                    "text": f"<span style='font-size:13px;color:#78909b'>Total asupan</span><br><b style='font-size:27px;color:#103b4b'>{daily_totals['calories']:.0f}</b><br><span style='font-size:13px;color:#78909b'>kkal</span>",
                    "x": 0.5, "y": 0.5, "showarrow": False,
                }],
            )
            chart_col, detail_col = st.columns([1.2, 1], gap="large")
            with chart_col:
                st.markdown('<div class="macro-heading">Komposisi energi harian</div><div class="macro-subheading">Proporsi kontribusi karbohidrat, protein, dan lemak dari seluruh energi yang tercatat.</div>', unsafe_allow_html=True)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            with detail_col:
                st.markdown('<div class="macro-heading">Detail komposisi</div><div class="macro-subheading">Setiap kartu menunjukkan kontribusi energi dan proporsi makronutrien.</div>', unsafe_allow_html=True)
                for _, row in macro_df.iterrows():
                    name = row["Makronutrien"]
                    color = macro_colors[name]
                    pct = float(row["Persentase"])
                    st.markdown(
                        f'<div class="macro-item"><span class="macro-dot" style="background:{color}"></span><div><div class="macro-name">{name}</div><div class="macro-meta">{row["Energi (kkal)"]:.1f} kkal dari total energi</div></div><div class="macro-percent">{pct:.1f}%</div></div>',
                        unsafe_allow_html=True,
                    )
                st.markdown(
                    f'<div class="macro-total"><strong>Total energi tercatat</strong><br><span style="font-size:1.2rem;font-weight:850;color:#123b56">{daily_totals["calories"]:.0f} kkal</span><br><span style="font-size:.84rem;color:#718793">Target harian {float(calorie_target):.0f} kkal</span></div>',
                    unsafe_allow_html=True,
                )

# =========================================================
# FOOD LOG
# =========================================================
    # Perkembangan kalori — hanya di Dashboard
    import datetime as _dt
    _trend_rows = []
    _trend_end = selected_date
    for _i in range(6, -1, -1):
        _d = _trend_end - _dt.timedelta(days=_i)
        try:
            _df = get_meals(user_id, _d)
            _day_calories = float(_df["calories"].fillna(0).sum()) if not _df.empty and "calories" in _df.columns else 0.0
        except Exception:
            _day_calories = 0.0
        _trend_rows.append({"date": _d, "calories": _day_calories})
    render_calorie_trend(_trend_rows, calorie_target, days=7)

    st.markdown(
        '<div class="ai-insight-shell"><div class="ai-insight-kicker">AI PERSONAL COACH</div>'
        '<div class="ai-insight-title">Insight nutrisi personal</div>'
        '<div class="ai-insight-desc">Gemini membaca catatan makanan dan perkembangan kalori untuk menemukan insight yang relevan dengan targetmu.</div></div>',
        unsafe_allow_html=True,
    )

    if st.button("✨ Analisis dengan AI", key="generate_ai_nutrition_insight"):
        try:
            with st.spinner("AI sedang menganalisis pola makanmu..."):
                _insight, _insight_model = generate_nutrition_insight(
                    selected_date=selected_date,
                    daily_totals=daily_totals,
                    calorie_target=calorie_target,
                    protein_target=protein_target,
                    goal=goal,
                    meals_df=meals,
                    trend_rows=_trend_rows,
                )
            st.session_state["nutrition_insight"] = _insight
            st.session_state["nutrition_insight_model"] = _insight_model
            st.session_state.pop("nutrition_insight_error", None)
        except Exception as exc:
            st.session_state["nutrition_insight_error"] = str(exc)

    if st.session_state.get("nutrition_insight"):
        st.markdown(
            '<div class="ai-insight-shell">',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["nutrition_insight"])
        st.caption(
            f"Insight dibuat berdasarkan data yang tercatat. Model: "
            f"{st.session_state.get('nutrition_insight_model', GEMINI_MODEL)}"
        )
        st.markdown("</div>", unsafe_allow_html=True)
    elif st.session_state.get("nutrition_insight_error"):
        st.warning(f"AI insight belum dapat dibuat: {st.session_state['nutrition_insight_error']}")


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
        uploaded = st.file_uploader("Unggah gambar makanan", type=["jpg", "jpeg", "png"], key="food_image_uploader")
        if uploaded:
            current_bytes = uploaded.getvalue()
            current_name = uploaded.name
            if st.session_state.get("image_uploaded_name") != current_name or st.session_state.get("image_bytes") != current_bytes:
                st.session_state.pop("image_result", None)
                st.session_state.pop("corrected_ai_result", None)
                st.session_state.pop("corrected_ai_error", None)
            st.image(uploaded, caption="Gambar makanan", use_container_width=True)
            if st.button("✨ Analisis makanan dengan AI", key="analyze_food_image"):
                with st.spinner("AI sedang membaca makanan, komponen, porsi, dan estimasi nutrisi..."):
                    result, error = analyze_image(uploaded)
                if error:
                    st.error(error)
                else:
                    st.session_state["image_result"] = result
                    st.session_state["image_uploaded_name"] = current_name
                    st.session_state["image_bytes"] = current_bytes
                    st.session_state["image_mime_type"] = uploaded.type or "image/jpeg"
                    st.session_state.pop("corrected_ai_result", None)
                    st.session_state.pop("corrected_ai_error", None)
                    st.rerun()

        if uploaded is None and st.session_state.get("image_result"):
            st.info("Unggah kembali gambar jika ingin menganalisis makanan baru.")
        result = st.session_state.get("image_result")
        if result:
            grams_default = float(result.get("estimated_grams") or 100)
            resolved_initial = resolve_food_result(result, grams_default)

            st.markdown("### Hasil analisis AI")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"**Makanan teridentifikasi**\n\n{result.get('food_name_id') or result.get('food_name_en') or 'Tidak diketahui'}")
            with col_b:
                st.markdown(f"**Perkiraan porsi**\n\n{grams_default:.0f} gram · {str(result.get('portion_class') or 'tidak diketahui').capitalize()}")
            with col_c:
                confidence = result.get("confidence")
                confidence_text = f"{float(confidence) * 100:.0f}%" if confidence is not None else "Tidak tersedia"
                st.markdown(f"**Confidence AI**\n\n{confidence_text}")
            st.caption(f"Model: {result.get('model_used', GEMINI_MODEL)} · {result.get('notes') or 'Tidak ada catatan tambahan.'}")

            components = result.get("components") or []
            valid_components = [c for c in components if isinstance(c, dict)]
            if valid_components:
                st.markdown("#### 🔎 Rincian yang dibaca AI")
                rows = []
                for comp in valid_components:
                    rows.append({
                        "Komponen": comp.get("name_id") or comp.get("name_en") or "Tidak diketahui",
                        "Berat (g)": comp.get("estimated_grams"),
                        "Kalori": comp.get("calories"),
                        "Protein": comp.get("protein_g"),
                        "Lemak": comp.get("fat_g"),
                        "Karbo": comp.get("carbs_g"),
                    })
                cdf = pd.DataFrame(rows)
                for col in cdf.columns[1:]:
                    cdf[col] = pd.to_numeric(cdf[col], errors="coerce")
                st.dataframe(cdf.round(2), use_container_width=True, hide_index=True)

            # Compact resolution + nutrition cards
            n = resolved_initial.get("nutrients") or {}
            source_text = resolved_initial.get("source") or "AI Vision"
            source_badge = "Dataset exact match" if resolved_initial.get("matched") else "AI Vision · estimasi gambar"
            food_title = resolved_initial.get("food_name") or result.get("food_name_id") or result.get("food_name_en") or "Makanan teridentifikasi"
            st.markdown(
                f'<div class="resolution-card"><div class="resolution-label">Resolusi nutrisi</div><div class="resolution-name">{food_title}</div><div class="resolution-detail"><span class="source-pill">● {source_badge}</span> &nbsp; {resolved_initial.get("grams", grams_default):.0f} gram · {source_text}</div></div>',
                unsafe_allow_html=True,
            )

            if n:
                st.markdown('<div class="food-result-shell"><div class="food-result-head"><div><div class="food-result-title">Ringkasan nutrisi porsi ini</div><div class="food-result-sub">Nilai final yang akan digunakan jika kamu menyimpan makanan ke riwayat.</div></div><span class="source-pill">✓ Hasil siap ditinjau</span></div>', unsafe_allow_html=True)
                m1, m2, m3, m4 = st.columns(4)
                cards = [(m1,"Kalori",f"{n['calories']:.0f}","kkal"),(m2,"Protein",f"{n['protein_g']:.1f}","g"),(m3,"Lemak",f"{n['fat_g']:.1f}","g"),(m4,"Karbohidrat",f"{n['carbs_g']:.1f}","g")]
                for col, label, value, unit in cards:
                    with col:
                        st.markdown(f'<div class="nutrient-card"><div class="nutrient-label">{label}</div><div class="nutrient-value">{value} <span class="nutrient-unit">{unit}</span></div></div>', unsafe_allow_html=True)

            st.markdown('<div class="correction-shell"><div class="section-kicker">Refine hasil</div><h3 style="margin:4px 0 5px;color:#123b56">Koreksi jika hasil AI belum sesuai</h3><div style="color:#718a97;font-size:.88rem;margin-bottom:15px">Ubah nama atau porsi, lalu minta AI memeriksa kembali gambar sebelum hasil disimpan.</div>', unsafe_allow_html=True)
            corrected_name = st.text_input(
                "Nama makanan",
                value=str(result.get("food_name_id") or result.get("food_name_en") or ""),
                key="ai_corrected_name",
                help="Koreksi ini akan dianalisis ulang terhadap gambar. Dataset hanya dipakai bila nama lengkap memiliki exact match."
            )
            corrected_grams = st.number_input(
                "Berat makanan (gram)", min_value=1.0, max_value=5000.0,
                value=grams_default, key="ai_corrected_grams"
            )
            ai_meal_type = st.selectbox(
                "Sesi makan", ["Sarapan", "Makan siang", "Makan malam", "Camilan"],
                key="ai_meal_type"
            )

            corrected_exact = exact_indonesia_match(corrected_name, limit=1)
            if not corrected_exact.empty:
                row = corrected_exact.iloc[0]
                preview_nutrients, preview_error = calculate_nutrients(row, corrected_grams)
                if preview_nutrients and not preview_error:
                    st.success(f"Exact match tersedia setelah koreksi: **{row['food_name']}**")
                    st.markdown(f'<div class="resolution-detail" style="margin:8px 0 12px">Pratinjau dataset · {preview_nutrients["calories"]:.0f} kkal · {preview_nutrients["protein_g"]:.1f} g protein · {preview_nutrients["fat_g"]:.1f} g lemak · {preview_nutrients["carbs_g"]:.1f} g karbohidrat</div>', unsafe_allow_html=True)
            else:
                st.caption("Belum ada kecocokan exact untuk nama koreksi ini. Analisis ulang akan menentukan hasil final dari gambar.")

            if st.button("🔄 Analisis ulang sesuai koreksi", key="reanalyze_corrected_ai"):
                with st.spinner("AI sedang memeriksa ulang gambar berdasarkan koreksi..."):
                    ai_corrected, ai_error = analyze_corrected_food(
                        st.session_state.get("image_bytes", b""),
                        st.session_state.get("image_mime_type", "image/jpeg"),
                        corrected_name, corrected_grams,
                    )
                if ai_error:
                    st.session_state["corrected_ai_error"] = ai_error
                    st.session_state.pop("corrected_ai_result", None)
                else:
                    st.session_state["corrected_ai_result"] = ai_corrected
                    st.session_state.pop("corrected_ai_error", None)
                st.rerun()

            corrected_ai_result = st.session_state.get("corrected_ai_result")
            if corrected_ai_result and (corrected_ai_result.get("correction_name") != corrected_name.strip() or abs(float(corrected_ai_result.get("correction_grams", 0)) - float(corrected_grams)) > 0.001):
                corrected_ai_result = None
                st.info("Koreksi berubah. Klik 'Analisis ulang sesuai koreksi' sebelum menyimpan.")
            corrected_ai_error = st.session_state.get("corrected_ai_error")
            if corrected_ai_error:
                st.error(corrected_ai_error)
            if corrected_ai_result:
                st.markdown("#### Hasil analisis ulang AI")
                rn = corrected_ai_result["nutrients"]
                q1, q2, q3, q4 = st.columns(4)
                q1.metric("Kalori", f"{rn['calories']:.0f} kkal")
                q2.metric("Protein", f"{rn['protein_g']:.1f} g")
                q3.metric("Lemak", f"{rn['fat_g']:.1f} g")
                q4.metric("Karbohidrat", f"{rn['carbs_g']:.1f} g")
                if corrected_ai_result.get("confidence") is not None:
                    st.caption(f"Confidence AI: {float(corrected_ai_result['confidence']) * 100:.0f}% · {corrected_ai_result.get('notes') or ''}")


            # Final save source after correction: exact dataset > corrected AI > initial AI.
            final_resolution = None
            if corrected_ai_result:
                corrected_ai_as_result = {
                    "food_name_id": corrected_ai_result.get("food_name") or corrected_name,
                    "estimated_grams": corrected_grams,
                    "total_nutrients": corrected_ai_result.get("nutrients") or {},
                }
                final_resolution = resolve_food_result(
                    corrected_ai_as_result,
                    corrected_grams,
                    corrected_name=corrected_name,
                )
                # If corrected AI was used and no exact match exists, preserve its
                # direct whole-portion nutrition rather than trying another lookup.
                if not final_resolution.get("matched"):
                    final_resolution["nutrients"] = corrected_ai_result.get("nutrients")
                    final_resolution["source"] = "AI Vision — estimasi dari gambar setelah koreksi"
            else:
                initial_name = str(result.get("food_name_id") or result.get("food_name_en") or "").strip()
                changed = (corrected_name.strip() != initial_name or abs(float(corrected_grams) - float(grams_default)) > 0.001)
                if changed:
                    st.warning("Nama atau berat telah diubah. Jalankan analisis ulang AI agar hasil yang disimpan sesuai koreksi.")
                    final_resolution = None
                else:
                    final_resolution = resolved_initial

            if final_resolution and final_resolution.get("nutrients"):
                st.markdown("### 💾 Siap disimpan ke riwayat")
                st.write(f"**{final_resolution['food_name']}** · {final_resolution['grams']:.0f} g")
                st.caption(f"Sumber final: **{final_resolution['source']}**")
                if st.button("✅ Konfirmasi & simpan ke riwayat", key="save_ai_food"):
                    warnings = validate_nutrients(final_resolution["nutrients"])
                    if warnings:
                        st.error("Data nutrisi tidak valid: " + " ".join(warnings))
                    else:
                        try:
                            save_meal(
                                user_id, selected_date, ai_meal_type,
                                final_resolution["food_name"], final_resolution["grams"],
                                final_resolution["nutrients"], final_resolution["source"],
                            )
                            st.success("Hasil final berhasil disimpan ke riwayat makanan.")
                            for key in ["image_result", "image_uploaded_name", "image_bytes", "image_mime_type", "corrected_ai_result", "corrected_ai_error"]:
                                st.session_state.pop(key, None)
                            st.rerun()
                        except Exception as exc:
                            st.error(f"Gagal menyimpan hasil AI: {exc}")

            if st.button("🗑️ Hapus hasil analisis", key="clear_ai_result"):
                for key in ["image_result", "image_uploaded_name", "image_bytes", "image_mime_type", "corrected_ai_result", "corrected_ai_error"]:
                    st.session_state.pop(key, None)
                st.rerun()

# =========================================================
# RECOMMENDATIONS
# =========================================================
with recommendation_tab:
    st.markdown("""<div class="page-hero"><span class="page-chip">Smart recommendation</span><div class="page-title">Rekomendasi makanan berbasis AI</div><p class="page-desc">Program menyaring data nutrisi terlebih dahulu, kemudian AI memilih kombinasi makanan dan menjelaskan alasannya berdasarkan targetmu.</p></div>""", unsafe_allow_html=True)

    estimated_calories, estimated_protein = estimate_targets(age, sex, height, weight, activity, goal)
    ec1, ec2, ec3 = st.columns(3)
    ec1.metric("Estimasi kebutuhan", f"{estimated_calories:,.0f} kkal/hari")
    ec2.metric("Estimasi protein", f"{estimated_protein:,.0f} g/hari")
    ec3.metric("Target manual", f"{calorie_target:,.0f} kkal/hari")

    st.caption(
        "Estimasi menggunakan Mifflin–St Jeor dan faktor aktivitas. Target manual tetap menjadi target utama aplikasi."
    )

    gym_focus = st.selectbox(
        "Fokus nutrisi gym",
        ["Maintenance", "Cutting", "Bulking", "Performa latihan"],
        help="Fokus ini digunakan untuk mengatur prioritas rekomendasi; bukan diagnosis medis."
    )

    q1, q2 = st.columns([1.7, 1])
    with q1:
        recommendation_query = st.text_input(
            "Preferensi makanan (opsional)",
            placeholder="Contoh: ayam, nasi, telur, makanan murah...",
            help="Boleh memasukkan beberapa preferensi sekaligus. Sistem akan memecahnya menjadi beberapa kata kunci."
        )
    with q2:
        max_meal_kcal = st.number_input(
            "Batas kalori rekomendasi", min_value=100.0, max_value=1500.0,
            value=float(min(max(remaining_calories, 250), 650)), step=50.0
        )

    st.markdown(
        f"""<div class="ai-insight-shell">
        <div class="ai-insight-kicker">AI DECISION SUPPORT</div>
        <div class="ai-insight-title">Konteks yang digunakan AI</div>
        <div class="ai-insight-desc">Sistem tidak meminta AI mengarang nilai nutrisi. Kandidat dan angka nutrisi disiapkan dari dataset, lalu AI digunakan untuk memilih, menggabungkan, dan menjelaskan.</div>
        <b>Sisa kalori:</b> {remaining_calories:.0f} kcal &nbsp; · &nbsp;
        <b>Sisa protein:</b> {remaining_protein:.1f} g &nbsp; · &nbsp;
        <b>Tujuan:</b> {goal} &nbsp; · &nbsp;
        <b>Fokus:</b> {gym_focus}
        </div>""", unsafe_allow_html=True
    )

    if st.button("✨ Buat rekomendasi dengan AI", type="primary", use_container_width=True):
        with st.spinner("Menyiapkan kandidat nutrisi dan meminta AI memilih kombinasi yang sesuai..."):
            recommendations = build_recommendations(
                goal, gym_focus, remaining_calories, remaining_protein, recommendation_query, max_meal_kcal
            )
            st.session_state["recommendation_result"] = recommendations
            ai_text, ai_model, ai_error = generate_ai_meal_recommendation(
                goal, gym_focus, remaining_calories, remaining_protein,
                recommendation_query, recommendations, max_meal_kcal,
            )
            st.session_state["ai_recommendation_text"] = ai_text
            st.session_state["ai_recommendation_model"] = ai_model
            st.session_state["ai_recommendation_error"] = ai_error

    recommendations = st.session_state.get("recommendation_result")
    ai_text = st.session_state.get("ai_recommendation_text")
    ai_error = st.session_state.get("ai_recommendation_error")

    if recommendations is None:
        st.info("Masukkan preferensi jika ada, lalu klik 'Buat rekomendasi dengan AI'.")
    else:
        if ai_text:
            st.markdown(
                f"""<div class="ai-insight-shell">
                <div class="ai-insight-kicker">🤖 GEMINI AI RECOMMENDATION</div>
                <div class="ai-insight-title">Rekomendasi yang dipersonalisasi</div>
                <div class="ai-insight-desc">AI menggunakan kandidat dari dataset aplikasi dan konteks targetmu.</div>
                </div>""", unsafe_allow_html=True
            )
            st.markdown(ai_text)
            if st.session_state.get("ai_recommendation_model"):
                st.caption(f"Model AI: {st.session_state['ai_recommendation_model']}")
        elif ai_error:
            st.warning(
                "AI belum dapat menghasilkan narasi rekomendasi. Kandidat dataset tetap tersedia di bawah. "
                f"Detail: {ai_error}"
            )

        if isinstance(recommendations, pd.DataFrame) and recommendations.empty:
            st.error("Dataset tidak memiliki kandidat yang memenuhi filter dasar. Periksa nutrition.csv.")
        else:
            st.markdown("### Kandidat yang digunakan AI")
            st.caption("Angka di tabel berasal dari dataset dan perhitungan program, bukan angka yang dibuat AI.")
            for idx, row in recommendations.head(8).iterrows():
                with st.container(border=True):
                    title_col, tag_col = st.columns([3, 1])
                    with title_col:
                        st.markdown(f"### {row['food_name']}")
                        st.caption(f"{row.get('category', 'Lainnya')} · {row.get('source', 'Nutrition Indonesia')}")
                    with tag_col:
                        pref_score = float(row.get("preference_score", 0))
                        st.markdown(
                            f'<span class="source-pill">{"Preferensi cocok" if pref_score > 0 else "Alternatif"}</span>',
                            unsafe_allow_html=True
                        )
                    a, b, c, d = st.columns(4)
                    a.metric("Porsi referensi", f"{float(row.get('reference_grams', 100)):.0f} g")
                    b.metric("Kalori", f"{float(row.get('portion_calories', 0)):.0f} kcal")
                    c.metric("Protein", f"{float(row.get('portion_protein', 0)):.1f} g")
                    d.metric("Karbohidrat", f"{float(row.get('portion_carbs', 0)):.1f} g")
                    st.write(row["reason"])

            with st.expander("Lihat data kandidat lengkap"):
                cols = ["food_name", "category", "calories", "protein_g", "fat_g", "carbs_g", "reference_grams", "portion_calories", "portion_protein"]
                st.dataframe(recommendations[cols], use_container_width=True, hide_index=True)

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

