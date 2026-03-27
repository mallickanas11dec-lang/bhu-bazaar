# =============================================================================
# BHU BAZAAR — app.py  (Premium Edition)
# A zero-cost student marketplace for Banaras Hindu University
# =============================================================================
#
# ── HOW TO CONNECT FIREBASE ──────────────────────────────────────────────────
#
# 1. Go to https://console.firebase.google.com and create a new project.
# 2. Enable Firestore Database (Start in test mode for development).
# 3. Go to Project Settings → Service Accounts → Generate new private key.
#    Downloads a JSON file (serviceAccountKey.json).
#
# OPTION A — Local: place JSON next to app.py, set FIREBASE_KEY_PATH below.
#
# OPTION B — Streamlit Cloud (Secrets):
#
#        [firebase]
#        type = "service_account"
#        project_id = "your-project-id"
#        private_key_id = "..."
#        private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
#        client_email = "..."
#        client_id = "..."
#        auth_uri = "https://accounts.google.com/o/oauth2/auth"
#        token_uri = "https://oauth2.googleapis.com/token"
#        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
#        client_x509_cert_url = "..."
#
#        [email]
#        sender = "your-gmail@gmail.com"
#        password = "your-app-password"   ← Gmail App Password
#
# =============================================================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import re, os, base64, random, smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ── CONFIG ────────────────────────────────────────────────────────────────────
FIREBASE_KEY_PATH  = "serviceAccountKey.json"
ALLOWED_DOMAINS    = r"@(bhu\.ac\.in|itbhu\.ac\.in)$"
CATEGORIES         = ["All", "Books", "Electronics", "Cycles", "Hostel Gear"]
OTP_EXPIRY_MINUTES = 10
HOSTELS            = [
    "Birsa Munda Hostel", "CV Raman Hostel", "GN Jha Hostel",
    "Jagannath Hostel", "Limbdi Hostel", "Mahavir Hostel",
    "Murlidhar Hostel", "Sapt Rishi Hostel", "Other / Day Scholar"
]

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BHU Bazaar — Student Marketplace",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── HIDE FROM SEARCH ENGINES ─────────────────────────────────────────────────
# Injects noindex so Google/Bing will not crawl or index this Streamlit app.
# Streamlit renders into <body>, so we use a JS snippet to also insert the
# meta tag into <head> — this is the most reliable way to noindex on Streamlit Cloud.
st.markdown(
    """
    <meta name='robots' content='noindex,nofollow'>
    <script>
        // Also inject into <head> for crawlers that parse the DOM
        var m = document.createElement('meta');
        m.name = 'robots'; m.content = 'noindex,nofollow';
        document.head && document.head.appendChild(m);
    </script>
    """,
    unsafe_allow_html=True,
)

# ── PREMIUM CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

*, *::before, *::after { box-sizing: border-box; }

:root {
    --saffron:      #F55D00;
    --saffron-lt:   #FF7A24;
    --saffron-pale: #FFF1E8;
    --saffron-glow: rgba(245,93,0,0.15);
    --gold:         #F0A500;
    --gold-pale:    #FFF8E1;
    --ink:          #0F0A00;
    --ink-soft:     #3D3020;
    --muted:        #8A7A6A;
    --border:       #EDE5DB;
    --border-strong:#D4C4B0;
    --bg:           #FDFAF6;
    --surface:      #FFFFFF;
    --surface-warm: #FFF8F2;
    --green:        #1A9E5C;
    --green-pale:   #E8F7EF;
    --red:          #D93025;
    --red-pale:     #FDECEA;
    --radius-sm:    8px;
    --radius-md:    14px;
    --radius-lg:    20px;
    --radius-xl:    28px;
    --shadow-sm:    0 1px 4px rgba(15,10,0,0.06);
    --shadow-md:    0 4px 16px rgba(15,10,0,0.08);
    --shadow-lg:    0 12px 40px rgba(15,10,0,0.10);
    --shadow-glow:  0 8px 32px rgba(245,93,0,0.22);
}

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    color: var(--ink) !important;
    background: var(--bg) !important;
}

.stApp {
    background: var(--bg) !important;
    background-image:
        radial-gradient(ellipse 900px 600px at -5% 0%, rgba(245,93,0,0.04) 0%, transparent 60%),
        radial-gradient(ellipse 600px 400px at 105% 85%, rgba(240,165,0,0.05) 0%, transparent 60%) !important;
}

/* Hide chrome */
#MainMenu, footer, header { visibility: hidden !important; }
.stDeployButton, [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stStatusWidget"],
.viewerBadge_container__1QSob { display: none !important; }

/* Text */
p, span, div, label, h1, h2, h3, h4, h5, h6 { color: var(--ink) !important; }
.stMarkdown p, .stMarkdown span { color: var(--ink) !important; }
.stCaption, .stCaption p { color: var(--muted) !important; font-size: 0.82rem !important; }

/* Inputs */
input, textarea, select {
    color: var(--ink) !important;
    background: var(--surface) !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input, .stTextArea textarea {
    color: var(--ink) !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border-strong) !important;
    border-radius: var(--radius-md) !important;
    padding: 10px 14px !important;
    font-size: 0.92rem !important;
    transition: border-color 0.2s, box-shadow 0.2s !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--saffron) !important;
    box-shadow: 0 0 0 3px var(--saffron-glow) !important;
    outline: none !important;
}
.stTextInput label, .stTextArea label, .stSelectbox label,
.stFileUploader label, .stToggle label {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.79rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
    color: var(--ink-soft) !important;
    margin-bottom: 4px !important;
}

/* Dropdowns */
.stSelectbox *, [data-baseweb="select"] * {
    color: var(--ink) !important;
    background-color: var(--surface) !important;
    font-family: 'DM Sans', sans-serif !important;
}
[data-baseweb="menu"] {
    background: var(--surface) !important;
    border-radius: var(--radius-md) !important;
    box-shadow: var(--shadow-lg) !important;
    border: 1.5px solid var(--border) !important;
}
[data-baseweb="menu"] * { color: var(--ink) !important; background: var(--surface) !important; }
[role="option"]:hover, [data-baseweb="menu"] li:hover { background: var(--saffron-pale) !important; }
[data-baseweb="select"] > div {
    border-radius: var(--radius-md) !important;
    border-color: var(--border-strong) !important;
}

/* Buttons */
.stButton > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.88rem !important;
    border-radius: 100px !important;
    padding: 10px 22px !important;
    border: 1.5px solid var(--border-strong) !important;
    color: var(--ink) !important;
    background: var(--surface) !important;
    transition: all 0.18s ease !important;
    letter-spacing: 0.01em !important;
}
.stButton > button:hover {
    border-color: var(--saffron) !important;
    color: var(--saffron) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button[kind="primary"] {
    background: var(--saffron) !important;
    border-color: var(--saffron) !important;
    color: #FFF !important;
    box-shadow: 0 4px 16px rgba(245,93,0,0.30) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--saffron-lt) !important;
    border-color: var(--saffron-lt) !important;
    color: #FFF !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* Form submit */
[data-testid="stFormSubmitButton"] > button {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 700 !important;
    border-radius: 100px !important;
    background: var(--saffron) !important;
    color: white !important;
    border-color: var(--saffron) !important;
    box-shadow: 0 4px 16px rgba(245,93,0,0.30) !important;
    padding: 12px 28px !important;
    font-size: 0.92rem !important;
}
[data-testid="stFormSubmitButton"] > button:hover {
    background: var(--saffron-lt) !important;
    transform: translateY(-2px) !important;
    box-shadow: var(--shadow-glow) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px !important;
    background: var(--surface-warm) !important;
    padding: 5px !important;
    border-radius: 100px !important;
    border: 1.5px solid var(--border) !important;
    width: fit-content !important;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
    color: var(--muted) !important;
    background: transparent !important;
    border-radius: 100px !important;
    padding: 8px 20px !important;
    border: none !important;
    transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
    background: var(--saffron) !important;
    color: #FFF !important;
    box-shadow: 0 2px 12px rgba(245,93,0,0.28) !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* File uploader */
[data-testid="stFileUploader"] {
    border: 2px dashed var(--border-strong) !important;
    border-radius: var(--radius-md) !important;
    background: var(--surface-warm) !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover { border-color: var(--saffron) !important; }

/* Toggle / checkbox */
.stToggle label { text-transform: none !important; font-size: 0.9rem !important; font-weight: 500 !important; }
.stCheckbox label { text-transform: none !important; font-size: 0.88rem !important; font-weight: 400 !important; letter-spacing: 0 !important; }

/* Alerts */
.stAlert { border-radius: var(--radius-md) !important; border: none !important; }

/* Divider */
hr { border: none !important; border-top: 1.5px solid var(--border) !important; margin: 1.5rem 0 !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--saffron); }

/* ═══════════════════════════════════════
   CUSTOM COMPONENTS
   ═══════════════════════════════════════ */

/* Hero */
.bb-hero {
    background: linear-gradient(135deg, #F55D00 0%, #C44400 55%, #9E3800 100%);
    border-radius: 0 0 var(--radius-xl) var(--radius-xl);
    padding: 2rem 2.5rem 2.2rem;
    color: white;
    position: relative;
    overflow: hidden;
    margin-bottom: 1.8rem;
}
.bb-hero::before {
    content: '';
    position: absolute; top: -50px; right: -50px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, rgba(255,255,255,0.09) 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
}
.bb-hero::after {
    content: '';
    position: absolute; bottom: -70px; left: 15%;
    width: 450px; height: 220px;
    background: radial-gradient(ellipse, rgba(255,255,255,0.05) 0%, transparent 65%);
    border-radius: 50%;
    pointer-events: none;
}
.bb-hero-inner {
    display: flex; align-items: center;
    justify-content: space-between;
    flex-wrap: wrap; gap: 1rem;
    position: relative; z-index: 1;
}
.bb-hero-brand { display: flex; align-items: center; gap: 16px; }
.bb-hero-logo {
    width: 54px; height: 54px;
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(12px);
    border: 1.5px solid rgba(255,255,255,0.3);
    border-radius: 15px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.7rem;
    flex-shrink: 0;
}
.bb-hero-name {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.9rem !important; font-weight: 800 !important;
    color: white !important; letter-spacing: -0.04em; line-height: 1;
}
.bb-hero-tag {
    font-size: 0.77rem !important; color: rgba(255,255,255,0.75) !important;
    font-weight: 400 !important; margin-top: 4px; letter-spacing: 0.03em;
}
.bb-hero-user {
    display: flex; align-items: center; gap: 10px;
    background: rgba(255,255,255,0.13);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 100px; padding: 8px 18px 8px 10px;
}
.bb-hero-avatar {
    width: 32px; height: 32px; border-radius: 50%;
    background: rgba(255,255,255,0.28);
    display: flex; align-items: center; justify-content: center;
    font-size: 0.88rem; font-weight: 700 !important; color: white !important;
}
.bb-hero-uname { font-size: 0.85rem !important; color: white !important; font-weight: 600 !important; }
.bb-stats {
    display: flex; gap: 8px; flex-wrap: wrap;
    margin-top: 1.1rem; position: relative; z-index: 1;
}
.bb-stat {
    background: rgba(255,255,255,0.12);
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 100px; padding: 4px 14px;
    font-size: 0.77rem !important; color: rgba(255,255,255,0.9) !important;
    font-weight: 500 !important;
}

/* Auth */
.bb-auth-wrap { max-width: 460px; margin: 0 auto; padding: 1.5rem 0 2rem; }
.bb-auth-card {
    background: var(--surface); border: 1.5px solid var(--border);
    border-radius: var(--radius-xl); padding: 2.4rem 2.2rem 2rem;
    box-shadow: var(--shadow-lg); position: relative; overflow: hidden;
}
.bb-auth-card::before {
    content: ''; position: absolute; top: 0; left: 0; right: 0;
    height: 4px; background: linear-gradient(90deg, var(--saffron), var(--gold));
}
.bb-auth-title {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.5rem !important; font-weight: 700 !important;
    color: var(--ink) !important; letter-spacing: -0.03em; margin-bottom: 4px !important;
}
.bb-auth-sub { font-size: 0.83rem !important; color: var(--muted) !important; margin-bottom: 1.6rem !important; }

/* Section headings */
.bb-section-head {
    font-family: 'Syne', sans-serif !important;
    font-size: 1.3rem !important; font-weight: 700 !important;
    color: var(--ink) !important; letter-spacing: -0.02em; margin-bottom: 2px;
}
.bb-section-sub { font-size: 0.83rem !important; color: var(--muted) !important; margin-bottom: 1.2rem !important; }

/* Product card */
.bb-card {
    background: var(--surface); border: 1.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 1.1rem; margin-bottom: 1rem;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    position: relative; overflow: hidden;
}
.bb-card:hover { transform: translateY(-3px); box-shadow: var(--shadow-lg); border-color: var(--saffron); }
.bb-card.featured { border-color: var(--gold); box-shadow: 0 0 0 3px rgba(240,165,0,0.18), var(--shadow-md); }
.bb-card.sold { opacity: 0.55; }
.bb-card-img { width: 100%; height: 170px; object-fit: cover; border-radius: var(--radius-md); margin-bottom: 12px; background: var(--surface-warm); display: block; }
.bb-card-badges { display: flex; flex-wrap: wrap; gap: 5px; margin-bottom: 8px; align-items: center; }
.badge { font-size: 0.67rem; font-weight: 700; padding: 3px 10px; border-radius: 100px; letter-spacing: 0.04em; text-transform: uppercase; display: inline-block; }
.badge-featured { background: var(--gold-pale); color: #7A5500; border: 1px solid #F0C050; }
.badge-sold     { background: var(--red-pale);  color: var(--red); }
.badge-cat      { background: var(--saffron-pale); color: var(--saffron); border: 1px solid #FFD0AA; }
.badge-looking  { background: var(--saffron-pale); color: var(--saffron); border: 1px solid #FFD0AA; }
.badge-done     { background: #F0F0F0; color: #888; }
.bb-card-title { font-family: 'Syne', sans-serif !important; font-size: 0.97rem !important; font-weight: 700 !important; color: var(--ink) !important; margin-bottom: 4px; line-height: 1.3; }
.bb-card-price { font-family: 'Syne', sans-serif !important; font-size: 1.2rem !important; font-weight: 800 !important; color: var(--saffron) !important; letter-spacing: -0.02em; }
.bb-card-desc  { font-size: 0.80rem !important; color: var(--muted) !important; line-height: 1.5; margin: 6px 0; }
.bb-card-meta  { font-size: 0.75rem !important; color: var(--muted) !important; display: flex; gap: 10px; flex-wrap: wrap; margin-top: 6px; }

/* WhatsApp button */
.wa-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #1FAD60; color: white !important;
    padding: 8px 16px; border-radius: 100px;
    font-size: 0.80rem !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    text-decoration: none !important; margin-top: 10px;
    transition: background 0.2s, transform 0.15s;
    box-shadow: 0 2px 10px rgba(31,173,96,0.25);
}
.wa-btn:hover { background: #158F4E; transform: translateY(-1px); color: white !important; }

/* Share button */
.share-btn {
    display: inline-flex; align-items: center; gap: 6px;
    background: #25D366; color: white !important;
    padding: 8px 16px; border-radius: 100px;
    font-size: 0.80rem !important; font-weight: 600 !important;
    font-family: 'DM Sans', sans-serif !important;
    text-decoration: none !important; margin-top: 10px; margin-left: 8px;
    transition: background 0.2s, transform 0.15s;
    box-shadow: 0 2px 10px rgba(37,211,102,0.25);
}
.share-btn:hover { background: #1ebe5d; transform: translateY(-1px); color: white !important; }

/* Form card */
.bb-form-card {
    background: var(--surface); border: 1.5px solid var(--border);
    border-radius: var(--radius-lg); padding: 1.8rem;
    margin-bottom: 1rem; box-shadow: var(--shadow-sm);
}

/* Info pills */
.bb-info-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--saffron-pale); border: 1px solid #FFD0AA;
    border-radius: 100px; padding: 5px 14px;
    font-size: 0.78rem; font-weight: 600; color: var(--saffron);
}
.bb-green-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: var(--green-pale); border: 1px solid #A8DBBE;
    border-radius: 100px; padding: 5px 14px;
    font-size: 0.78rem; font-weight: 600; color: var(--green);
}

/* Step indicator */
.bb-steps { display: flex; align-items: center; gap: 0; margin-bottom: 1.8rem; }
.bb-step  { display: flex; align-items: center; gap: 8px; font-size: 0.78rem; font-weight: 600; color: var(--muted); }
.bb-step.active { color: var(--saffron); }
.bb-step.done   { color: var(--green); }
.bb-step-dot {
    width: 28px; height: 28px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 0.72rem; font-weight: 700;
    background: var(--surface-warm); border: 2px solid var(--border); color: var(--muted);
}
.bb-step.active .bb-step-dot { background: var(--saffron); border-color: var(--saffron); color: white; box-shadow: 0 2px 10px rgba(245,93,0,0.35); }
.bb-step.done   .bb-step-dot { background: var(--green);   border-color: var(--green);   color: white; }
.bb-step-line { flex: 1; height: 2px; background: var(--border); min-width: 20px; max-width: 40px; }
.bb-step-line.done { background: var(--green); }

/* Empty state */
.bb-empty { text-align: center; padding: 3.5rem 1rem; }
.bb-empty-icon  { font-size: 3rem; margin-bottom: 12px; }
.bb-empty-title { font-family: 'Syne', sans-serif !important; font-size: 1.1rem !important; font-weight: 700 !important; color: var(--ink-soft) !important; margin-bottom: 6px; }
.bb-empty-sub   { font-size: 0.83rem !important; color: var(--muted) !important; }

/* CTA card */
.bb-cta-card {
    background: linear-gradient(135deg, var(--saffron-pale), var(--gold-pale));
    border: 1.5px solid #FFD0AA; border-radius: var(--radius-lg);
    padding: 2.2rem; text-align: center; margin-top: 1rem;
}

/* Responsive */
@media (max-width: 768px) {
    .bb-hero { padding: 1.4rem 1.2rem 1.6rem; border-radius: 0 0 var(--radius-lg) var(--radius-lg); }
    .bb-hero-name { font-size: 1.45rem !important; }
    .bb-auth-card { padding: 1.8rem 1.4rem; border-radius: var(--radius-lg); }
    .bb-card-img  { height: 135px; }
}
</style>
""", unsafe_allow_html=True)


# ── FIREBASE ──────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_firebase():
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
        else:
            try:
                key_dict = dict(st.secrets["firebase"])
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(key_dict)
            except Exception as e:
                st.error(f"⚠️ Firebase credentials not found. Error: {e}")
                st.stop()
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()


# ── SESSION STATE ─────────────────────────────────────────────────────────────
for key, default in {
    "logged_in":     False,
    "user_email":    "",
    "user_name":     "",
    "deleted_ad":    False,
    "ad_posted":      False,
    "fp_step":       "email",
    "fp_email":      "",
    "fp_otp":        "",
    "fp_otp_expiry": None,
    "fp_verified":   False,
    "show_forgot":   False,
    "shared_ad_id":  "",
    "show_auth":     False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# Capture shared ad deep-link
if "ad" in st.query_params and not st.session_state.shared_ad_id:
    st.session_state.shared_ad_id = st.query_params["ad"]

# Persist login via URL params
params = st.query_params
if not st.session_state.logged_in and "user" in params:
    saved_email = params["user"]
    user_doc = next(
        (u for u in db.collection("users").stream()
         if u.to_dict().get("email","") == saved_email), None
    )
    if user_doc:
        data = user_doc.to_dict()
        st.session_state.logged_in  = True
        st.session_state.user_email = data["email"]
        st.session_state.user_name  = data.get("name","Student")


# ── HELPERS ───────────────────────────────────────────────────────────────────
def valid_bhu_email(email: str) -> bool:
    return bool(re.search(ALLOWED_DOMAINS, email.strip(), re.IGNORECASE))

def whatsapp_url(phone: str, item_title: str) -> str:
    import urllib.parse
    clean = re.sub(r"\D", "", phone)
    if not clean.startswith("91"): clean = "91" + clean
    msg = f"Hi, I saw your ad for *{item_title}* on BHU Bazaar. Is it still available?"
    return f"https://wa.me/{clean}?text={urllib.parse.quote(msg)}"

def share_whatsapp_url(doc_id: str, title: str, price: str, image_url: str) -> str:
    import urllib.parse
    ad_link = f"https://bhu-baazar.streamlit.app/?ad={doc_id}"
    msg = f"Check out *{title}* for ₹{price} on BHU Bazaar: {ad_link}"
    return f"https://wa.me/?text={urllib.parse.quote(msg)}"

def get_email_creds():
    try:    return st.secrets["email"]["sender"], st.secrets["email"]["password"]
    except: return os.environ.get("EMAIL_SENDER",""), os.environ.get("EMAIL_PASSWORD","")

def generate_otp(n: int = 6) -> str:
    return "".join(str(random.randint(0,9)) for _ in range(n))

def send_otp_email(to: str, otp: str) -> bool:
    sender, pwd = get_email_creds()
    if not sender or not pwd: return False
    html = f"""
    <div style="font-family:'DM Sans',sans-serif;max-width:480px;margin:auto;
                border:1.5px solid #EDE5DB;border-radius:20px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#F55D00,#9E3800);padding:28px;text-align:center;">
        <div style="font-size:2rem;margin-bottom:8px;">🏛️</div>
        <h2 style="color:white;margin:0;font-weight:700;">BHU Bazaar</h2>
        <p style="color:rgba(255,255,255,.78);margin:4px 0 0;font-size:.84rem;">Password Reset OTP</p>
      </div>
      <div style="padding:32px;background:#FDFAF6;">
        <p style="color:#3D3020;font-size:.92rem;margin-bottom:20px;">
          Your one-time password — valid for <strong>{OTP_EXPIRY_MINUTES} minutes</strong>.
        </p>
        <div style="background:linear-gradient(135deg,#FFF1E8,#FFF8E1);border:2px solid #FFD0AA;
                    border-radius:16px;padding:24px;text-align:center;margin-bottom:20px;">
          <div style="font-family:monospace;font-size:2.6rem;font-weight:800;
                      letter-spacing:14px;color:#F55D00;">{otp}</div>
        </div>
        <p style="color:#8A7A6A;font-size:.78rem;">If you didn't request this, ignore this email.</p>
      </div>
    </div>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "🔐 BHU Bazaar — Password Reset OTP"
    msg["From"]    = sender
    msg["To"]      = to
    msg.attach(MIMEText(html, "html"))
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(sender, pwd); s.sendmail(sender, to, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email error: {e}"); return False

def avatar_letter(name: str) -> str:
    return name[0].upper() if name else "U"


# ── UI COMPONENTS ─────────────────────────────────────────────────────────────
def render_header(show_user: bool = False):
    if show_user and st.session_state.logged_in:
        name = st.session_state.user_name
        st.markdown(f"""
        <div class="bb-hero">
          <div class="bb-hero-inner">
            <div class="bb-hero-brand">
              <div class="bb-hero-logo">🏛️</div>
              <div>
                <div class="bb-hero-name">BHU Bazaar</div>
                <div class="bb-hero-tag">Student Marketplace · Banaras Hindu University</div>
              </div>
            </div>
            <div class="bb-hero-user">
              <div class="bb-hero-avatar">{avatar_letter(name)}</div>
              <div class="bb-hero-uname">{name}</div>
            </div>
          </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class="bb-hero">
          <div class="bb-hero-inner">
            <div class="bb-hero-brand">
              <div class="bb-hero-logo">🏛️</div>
              <div>
                <div class="bb-hero-name">BHU Bazaar</div>
                <div class="bb-hero-tag">Student Marketplace · Banaras Hindu University</div>
              </div>
            </div>
          </div>
          <div class="bb-stats">
            <div class="bb-stat">📚 Buy &amp; Sell Textbooks</div>
            <div class="bb-stat">🚲 Cycles &amp; Electronics</div>
            <div class="bb-stat">🏠 Hostel Gear</div>
            <div class="bb-stat">✦ 100% Free</div>
          </div>
        </div>""", unsafe_allow_html=True)


def product_card(p: dict, show_manage: bool = False):
    is_featured = p.get("featured", False)
    is_sold     = p.get("sold", False)
    card_cls    = "bb-card featured" if is_featured else ("bb-card sold" if is_sold else "bb-card")

    badges = ""
    if is_featured: badges += '<span class="badge badge-featured">⭐ Featured</span> '
    if is_sold:     badges += '<span class="badge badge-sold">Sold</span> '
    badges += f'<span class="badge badge-cat">{p.get("category","")}</span>'

    img_html = ""
    if p.get("image_url"):
        img_html = f'<img class="bb-card-img" src="{p["image_url"]}" onerror="this.style.display=\'none\'">'

    wa_url     = whatsapp_url(p.get("phone",""), p.get("title",""))
    share_url  = share_whatsapp_url(
                     p.get("doc_id",""),
                     p.get("title",""),
                     p.get("price",""),
                     p.get("image_url","")
                 )
    desc    = p.get("description","")[:112]
    if len(p.get("description","")) > 112: desc += "…"
    hostel  = p.get("seller_hostel","")
    hostel_html = f'<span>🏠 {hostel}</span>' if hostel else ""

    st.markdown(f"""
    <div class="{card_cls}">
        {img_html}
        <div class="bb-card-badges">{badges}</div>
        <div class="bb-card-title">{p.get("title","")}</div>
        <div class="bb-card-price">₹{p.get("price","")}</div>
        <div class="bb-card-desc">{desc}</div>
        <div class="bb-card-meta">
          <span>👤 {p.get("seller_name","")}</span>{hostel_html}
        </div>
        <a class="wa-btn" href="{wa_url}" target="_blank">💬 Chat on WhatsApp</a>
        <a class="share-btn" href="{share_url}" target="_blank">📤 Share Ad</a>
    </div>""", unsafe_allow_html=True)

    if show_manage:
        c1, c2 = st.columns(2)
        doc_id = p.get("doc_id","")
        with c1:
            lbl = "✅ Mark Sold" if not is_sold else "🔄 Mark Available"
            if st.button(lbl, key=f"sold_{doc_id}", use_container_width=True):
                db.collection("products").document(doc_id).update({"sold": not is_sold})
                st.rerun()
        with c2:
            if st.button("🗑️ Delete", key=f"del_{doc_id}", use_container_width=True, type="primary"):
                db.collection("products").document(doc_id).delete()
                st.session_state["deleted_ad"] = True
                st.rerun()


def step_indicator(current: int):
    steps = ["Enter Email", "Verify OTP", "New Password"]
    html  = '<div class="bb-steps">'
    for i, label in enumerate(steps, 1):
        s_cls = "bb-step done" if i < current else ("bb-step active" if i == current else "bb-step")
        dot   = "✓" if i < current else str(i)
        html += f'<div class="{s_cls}"><div class="bb-step-dot">{dot}</div><span>{label}</span></div>'
        if i < 3:
            line_cls = "bb-step-line done" if i < current else "bb-step-line"
            html += f'<div class="{line_cls}"></div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# ── AUTH PAGES ────────────────────────────────────────────────────────────────
def page_login():
    render_header()
    st.markdown('<div class="bb-auth-wrap"><div class="bb-auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="bb-auth-title">Welcome back 👋</div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-auth-sub">Sign in to BHU Bazaar</div>', unsafe_allow_html=True)

    login_input = st.text_input("Email or Phone Number", placeholder="yourname@gmail.com  or  9876543210", key="login_input")
    show_pw     = st.checkbox("Show password", key="show_pw_login")
    password    = st.text_input("Password", type="default" if show_pw else "password", key="login_password")

    if st.button("Sign In →", type="primary", use_container_width=True):
        login_clean = login_input.lower().strip()
        phone_clean = re.sub(r"\D", "", login_input)
        is_email = re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", login_clean)
        is_phone = re.fullmatch(r"\d{10}", phone_clean)

        if not is_email and not is_phone:
            st.error("❌ Please enter a valid email or 10-digit phone number.")
        else:
            user_doc = None
            for u in db.collection("users").stream():
                d = u.to_dict()
                if is_email and d.get("email","") == login_clean:
                    user_doc = u; break
                elif is_phone and re.sub(r"\D","",d.get("phone","")) == phone_clean:
                    user_doc = u; break

            if user_doc and user_doc.to_dict().get("password") == password:
                data = user_doc.to_dict()
                st.session_state.logged_in  = True
                st.session_state.user_email = data["email"]
                st.session_state.user_name  = data.get("name","Student")
                st.query_params["user"]     = data["email"]
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

    st.markdown("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🔑 Forgot Password?", use_container_width=True):
            st.session_state.show_forgot = True
            st.session_state.fp_step     = "email"
            st.rerun()
    with c2:
        st.caption("New here? Register on the next tab →")

    st.markdown('</div></div>', unsafe_allow_html=True)


def page_register():
    render_header()
    st.markdown('<div class="bb-auth-wrap"><div class="bb-auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="bb-auth-title">Create Account 🎓</div>', unsafe_allow_html=True)
    st.markdown('<div class="bb-auth-sub">Join the BHU student marketplace</div>', unsafe_allow_html=True)

    name      = st.text_input("Full Name ✱", key="reg_name")
    email     = st.text_input("Email", placeholder="yourname@gmail.com  (optional if phone given)", key="reg_email")
    phone_reg = st.text_input("Phone Number", placeholder="9876543210  (optional if email given)", key="reg_phone")
    hostel    = st.selectbox("Your Hostel", HOSTELS, key="reg_hostel")
    show_pw   = st.checkbox("Show password", key="show_pw_reg")
    pw_type   = "default" if show_pw else "password"
    password  = st.text_input("Password  (min 6 chars) ✱", type=pw_type, key="reg_password")
    confirm   = st.text_input("Confirm Password ✱", type=pw_type, key="reg_confirm")

    if st.button("Create Account →", type="primary", use_container_width=True):
        email_clean = email.lower().strip()
        phone_clean = re.sub(r"\D","",phone_reg)
        has_email   = bool(re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email_clean))
        has_phone   = bool(re.fullmatch(r"\d{10}", phone_clean))

        if not name.strip():
            st.error("❌ Please enter your full name.")
        elif not has_email and not has_phone:
            st.error("❌ Enter a valid email OR 10-digit phone number.")
        elif len(password) < 6:
            st.error("❌ Password must be at least 6 characters.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        else:
            unique_id = email_clean if has_email else f"{phone_clean}@phone.bhubazaar"
            if any(u.to_dict().get("email","") == unique_id for u in db.collection("users").stream()):
                st.error("❌ Account already exists. Please sign in.")
            else:
                db.collection("users").add({
                    "email":    unique_id, "name": name.strip(),
                    "hostel":   hostel,   "phone": phone_clean,
                    "password": password, "created": datetime.utcnow(),
                })
                st.success("✅ Account created! Head to Sign In to log in.")

    st.markdown('</div></div>', unsafe_allow_html=True)


def page_forgot_password():
    render_header()
    st.markdown('<div class="bb-auth-wrap"><div class="bb-auth-card">', unsafe_allow_html=True)
    st.markdown('<div class="bb-auth-title">Reset Password 🔐</div>', unsafe_allow_html=True)

    step     = st.session_state.fp_step
    step_num = {"email": 1, "otp": 2, "reset": 3}.get(step, 1)
    step_indicator(step_num)

    if step == "email":
        st.markdown('<div class="bb-auth-sub">Enter your registered email — we\'ll send an OTP.</div>', unsafe_allow_html=True)
        fp_in = st.text_input("Registered Email", placeholder="yourname@gmail.com", key="fp_email_input")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Back to Login", use_container_width=True):
                st.session_state.show_forgot = False; st.rerun()
        with c2:
            if st.button("Send OTP 📧", type="primary", use_container_width=True):
                em = fp_in.lower().strip()
                if not re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", em):
                    st.error("❌ Enter a valid email address.")
                else:
                    ud = next((u for u in db.collection("users").stream() if u.to_dict().get("email","") == em), None)
                    if not ud:
                        st.error("❌ No account found with this email.")
                    else:
                        otp    = generate_otp()
                        expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)
                        st.session_state.fp_email      = em
                        st.session_state.fp_otp        = otp
                        st.session_state.fp_otp_expiry = expiry
                        st.session_state.fp_verified   = False
                        sndr, _ = get_email_creds()
                        if not sndr:
                            st.warning(f"⚠️ Email not configured. Dev OTP: **`{otp}`**")
                            st.session_state.fp_step = "otp"; st.rerun()
                        else:
                            with st.spinner("Sending OTP…"):
                                ok = send_otp_email(em, otp)
                            if ok: st.session_state.fp_step = "otp"; st.rerun()
                            else:  st.error("❌ Failed to send email. Check Secrets config.")

    elif step == "otp":
        masked = st.session_state.fp_email[:3] + "***@" + st.session_state.fp_email.split("@")[-1]
        st.success(f"✅ OTP sent to **{masked}**")
        st.markdown(f'<div class="bb-auth-sub">Enter the 6-digit code — valid {OTP_EXPIRY_MINUTES} min.</div>', unsafe_allow_html=True)
        otp_in = st.text_input("Enter OTP", placeholder="6-digit code", max_chars=6, key="otp_input")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Resend OTP", use_container_width=True):
                st.session_state.fp_step = "email"; st.rerun()
        with c2:
            if st.button("Verify ✅", type="primary", use_container_width=True):
                if datetime.utcnow() > st.session_state.fp_otp_expiry:
                    st.error("⏰ OTP expired. Request a new one.")
                    st.session_state.fp_step = "email"; st.rerun()
                elif otp_in.strip() != st.session_state.fp_otp:
                    st.error("❌ Incorrect OTP. Try again.")
                else:
                    st.session_state.fp_verified = True
                    st.session_state.fp_step     = "reset"; st.rerun()

    elif step == "reset":
        if not st.session_state.fp_verified:
            st.error("⚠️ Unauthorised. Restart the process.")
            st.session_state.fp_step = "email"; st.rerun()
        st.success("✅ OTP verified! Set your new password.")
        show_pw = st.checkbox("Show password", key="fp_show_pw")
        pw_t    = "default" if show_pw else "password"
        new_pw  = st.text_input("New Password (min 6 chars)", type=pw_t, key="fp_new_pw")
        conf_pw = st.text_input("Confirm New Password",       type=pw_t, key="fp_conf_pw")
        if st.button("Update Password 🔑", type="primary", use_container_width=True):
            if len(new_pw) < 6:
                st.error("❌ Password must be at least 6 characters.")
            elif new_pw != conf_pw:
                st.error("❌ Passwords do not match.")
            else:
                ud = next((u for u in db.collection("users").stream() if u.to_dict().get("email","") == st.session_state.fp_email), None)
                if ud:
                    db.collection("users").document(ud.id).update({"password": new_pw})
                    st.session_state.fp_step     = "email"
                    st.session_state.fp_email    = ""
                    st.session_state.fp_otp      = ""
                    st.session_state.fp_otp_expiry = None
                    st.session_state.fp_verified = False
                    st.session_state.show_forgot = False
                    st.success("🎉 Password updated! Please sign in.")
                    st.rerun()
                else:
                    st.error("❌ User not found.")

    st.markdown('</div></div>', unsafe_allow_html=True)


# ── MAIN APP ──────────────────────────────────────────────────────────────────
def app_main():
    render_header(show_user=st.session_state.logged_in)

    _, col_out = st.columns([7, 1])
    with col_out:
        if st.session_state.logged_in:
            if st.button("Sign Out"):
                for k in ["logged_in","user_email","user_name"]:
                    st.session_state[k] = False if k == "logged_in" else ""
                st.query_params.clear(); st.rerun()
        else:
            if st.button("🔑 Sign In / Register"):
                st.session_state["show_auth"] = True
                st.rerun()

    # Show login/register modal for guests who clicked Sign In
    if st.session_state.get("show_auth") and not st.session_state.logged_in:
        with st.expander("🔑 Sign In or Register", expanded=True):
            t1, t2 = st.tabs(["Sign In", "Register"])
            with t1: page_login()
            with t2: page_register()
        st.stop()

    tab_home, tab_post, tab_want, tab_myads = st.tabs(
        ["🏠  Browse", "📢  Post an Ad", "🙋  Want to Buy", "📦  My Ads"]
    )

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1 — BROWSE
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_home:
        docs     = db.collection("products").stream()
        products = []
        for doc in docs:
            d = doc.to_dict(); d["doc_id"] = doc.id; products.append(d)
        products = sorted(products, key=lambda x: x.get("created",""), reverse=True)
        products = sorted(products, key=lambda x: (not x.get("featured"), x.get("sold")))

        # ── Shared ad deep-link: highlight the specific ad ──────────────────
        shared_id = st.session_state.get("shared_ad_id", "")
        if shared_id:
            shared_ad = next((p for p in products if p.get("doc_id") == shared_id), None)
            if shared_ad:
                st.markdown("""
                <div style="background:linear-gradient(135deg,#FFF1E8,#FFF8E1);
                            border:2px solid #F55D00;border-radius:16px;
                            padding:14px 20px;margin-bottom:1.2rem;
                            display:flex;align-items:center;gap:10px;">
                  <span style="font-size:1.4rem;">📤</span>
                  <span style="font-size:0.9rem;font-weight:600;color:#F55D00;">
                    Someone shared this ad with you! Scroll down or it's shown first below.
                  </span>
                </div>""", unsafe_allow_html=True)
                product_card(shared_ad)
                st.markdown("<hr>", unsafe_allow_html=True)
            st.session_state.shared_ad_id = ""  # clear after showing
        # ────────────────────────────────────────────────────────────────────

        total  = len(products)
        active = sum(1 for p in products if not p.get("sold"))
        sold_n = total - active
        st.markdown(f"""
        <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:1.2rem;">
          <div class="bb-info-pill">✦ {active} Active Listings</div>
          <div class="bb-green-pill">✓ {sold_n} Sold</div>
        </div>""", unsafe_allow_html=True)

        search_q = st.text_input("", placeholder="🔍  Search — books, cycles, electronics, hostel gear…",
                                 key="search_q", label_visibility="collapsed")
        selected_cat = st.radio("Category", CATEGORIES, horizontal=True,
                                label_visibility="collapsed", key="cat_filter")

        if selected_cat != "All":
            products = [p for p in products if p.get("category") == selected_cat]
        if search_q:
            q = search_q.lower()
            products = [p for p in products
                        if q in p.get("title","").lower() or q in p.get("description","").lower()]

        if not products:
            st.markdown("""
            <div class="bb-empty">
              <div class="bb-empty-icon">🏪</div>
              <div class="bb-empty-title">No listings found</div>
              <div class="bb-empty-sub">Try a different search, or post the first ad!</div>
            </div>""", unsafe_allow_html=True)
        else:
            cols = st.columns(3)
            for i, p in enumerate(products):
                with cols[i % 3]: product_card(p)

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2 — POST AN AD
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_post:
        if not st.session_state.logged_in:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#FFF1E8,#FFF8E1);
                        border:2px solid #F55D00;border-radius:16px;
                        padding:2rem;text-align:center;margin-top:1rem;">
              <div style="font-size:2.5rem;margin-bottom:12px;">🔐</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                          color:#F55D00;margin-bottom:8px;">Login Required to Post an Ad</div>
              <div style="font-size:.85rem;color:#8A7A6A;">
                Please sign in or register to publish your listing.
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            t1, t2 = st.tabs(["Sign In", "Register"])
            with t1: page_login()
            with t2: page_register()
            st.stop()
        st.markdown('<div class="bb-section-head">📢 Post a New Ad</div>', unsafe_allow_html=True)
        st.markdown('<div class="bb-section-sub">Fields marked ✱ are required.</div>', unsafe_allow_html=True)
        st.markdown('<div class="bb-form-card">', unsafe_allow_html=True)

        with st.form("post_ad_form", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            with col_a:
                title    = st.text_input("Item Title ✱", placeholder="e.g. Engineering Physics by H.K. Malik")
                category = st.selectbox("Category ✱", CATEGORIES[1:])
                price    = st.text_input("Asking Price ✱", value="₹", placeholder="₹ 0")
            with col_b:
                phone    = st.text_input("WhatsApp Number ✱", placeholder="10-digit mobile number")
                featured = st.toggle("⭐  Feature this listing  (gold highlight)", value=False)
                uploaded_image = st.file_uploader("Upload Photo  (optional)", type=["jpg","jpeg","png","webp"])
            desc = st.text_area("Description ✱", placeholder="Condition, edition, reason for selling, any defects…", height=110)
            image_url = ""
            if uploaded_image:
                image_url = f"data:{uploaded_image.type};base64,{base64.b64encode(uploaded_image.read()).decode()}"
                st.image(uploaded_image, width=180, caption="Preview")
            submitted = st.form_submit_button("Post Ad 🚀", type="primary", use_container_width=True)

        st.markdown('</div>', unsafe_allow_html=True)

        # Show success message that survived a rerun
        if st.session_state.pop("ad_posted", False):
            st.success("✅ Your ad is live! Check the Browse tab to see it.")

        if submitted:
            price_clean = price.replace("₹","").strip()
            errors = []
            if not title:      errors.append("Item title is required.")
            if not price_clean or not price_clean.replace(".","").isdigit():
                errors.append("Enter a valid price (numbers only).")
            if not desc:       errors.append("Description is required.")
            if not re.match(r"^\d{10}$", re.sub(r"\D","",phone)):
                errors.append("Enter a valid 10-digit phone number.")
            if errors:
                for e in errors: st.error(e)
            else:
                ud = db.collection("users").where("email","==",st.session_state.user_email).limit(1).stream()
                ud_doc = next(ud, None)
                seller_hostel = ud_doc.to_dict().get("hostel","") if ud_doc else ""
                db.collection("products").add({
                    "title":         title.strip(),
                    "category":      category,
                    "price":         price_clean,
                    "description":   desc.strip(),
                    "seller_name":   st.session_state.user_name,
                    "seller_email":  st.session_state.user_email,
                    "seller_hostel": seller_hostel,
                    "phone":         re.sub(r"\D","",phone),
                    "image_url":     image_url.strip(),
                    "featured":      featured,
                    "sold":          False,
                    "created":       datetime.utcnow(),
                })
                st.session_state["ad_posted"] = True
                st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3 — WANT TO BUY
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_want:
        col_form, col_feed = st.columns([1, 1], gap="large")

        with col_form:
            st.markdown('<div class="bb-section-head">🙋 Post a Requirement</div>', unsafe_allow_html=True)
            st.markdown('<div class="bb-section-sub">Can\'t find it? Let sellers come to you.</div>', unsafe_allow_html=True)
            st.markdown('<div class="bb-form-card">', unsafe_allow_html=True)
            with st.form("want_form", clear_on_submit=True):
                w_title    = st.text_input("What are you looking for? ✱", placeholder="e.g. Physics Textbook, Cycle")
                w_category = st.selectbox("Category ✱", CATEGORIES[1:])
                w_budget   = st.text_input("Your Budget  (optional)", value="₹", placeholder="₹ 0")
                w_desc     = st.text_area("More details  (optional)", placeholder="Edition, condition, urgency…", height=90)
                w_phone    = st.text_input("WhatsApp Number ✱", placeholder="10-digit number")
                w_submit   = st.form_submit_button("Post Requirement 🙋", type="primary", use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)

            if w_submit:
                ph = re.sub(r"[^0-9]","",w_phone)
                if not w_title:
                    st.error("Describe what you are looking for.")
                elif len(ph) != 10:
                    st.error("Enter a valid 10-digit WhatsApp number.")
                else:
                    db.collection("requirements").add({
                        "title":       w_title.strip(),   "category":    w_category,
                        "budget":      w_budget.replace("₹","").strip(),
                        "description": w_desc.strip(),
                        "buyer_name":  st.session_state.user_name,
                        "buyer_email": st.session_state.user_email,
                        "phone":       ph, "fulfilled": False, "created": datetime.utcnow(),
                    })
                    st.success("✅ Requirement posted! Sellers will reach you on WhatsApp.")

        with col_feed:
            st.markdown('<div class="bb-section-head">📋 All Requirements</div>', unsafe_allow_html=True)
            ws = st.text_input("", placeholder="🔍  Search requirements…",
                               key="want_search", label_visibility="collapsed")
            reqs = []
            for doc in db.collection("requirements").stream():
                d = doc.to_dict(); d["doc_id"] = doc.id; reqs.append(d)
            reqs = sorted(reqs, key=lambda x: x.get("created",""), reverse=True)
            if ws:
                reqs = [r for r in reqs if ws.lower() in r.get("title","").lower()]

            if not reqs:
                st.markdown("""
                <div class="bb-empty">
                  <div class="bb-empty-icon">🙋</div>
                  <div class="bb-empty-title">No requirements yet</div>
                  <div class="bb-empty-sub">Post the first one!</div>
                </div>""", unsafe_allow_html=True)
            else:
                for r in reqs:
                    is_done   = r.get("fulfilled", False)
                    wa_link   = whatsapp_url(r.get("phone",""), r.get("title",""))
                    b_cls     = "badge badge-done" if is_done else "badge badge-looking"
                    b_lbl     = "Fulfilled" if is_done else "Looking"
                    op        = "0.55" if is_done else "1"
                    budget_h  = f'<div style="font-size:.88rem;color:var(--saffron);font-weight:700;margin:4px 0;">Budget: ₹{r.get("budget","")}</div>' if r.get("budget","") else ""
                    desc_t    = r.get("description","")[:90] + ("…" if len(r.get("description","")) > 90 else "")
                    cat_h     = f'<span class="badge badge-cat" style="margin-left:4px">{r.get("category","")}</span>'

                    st.markdown(f"""
                    <div class="bb-card" style="opacity:{op}">
                      <div class="bb-card-badges"><span class="{b_cls}">{b_lbl}</span>{cat_h}</div>
                      <div class="bb-card-title">{r.get("title","")}</div>
                      {budget_h}
                      <div class="bb-card-desc">{desc_t}</div>
                      <div class="bb-card-meta"><span>👤 {r.get("buyer_name","")}</span></div>
                      <a class="wa-btn" href="{wa_link}" target="_blank">💬 I Can Help!</a>
                    </div>""", unsafe_allow_html=True)

                    if r.get("buyer_email","") == st.session_state.user_email:
                        lbl = "✅ Mark Fulfilled" if not is_done else "🔄 Still Looking"
                        rc1, rc2 = st.columns(2)
                        with rc1:
                            if st.button(lbl, key=f"req_{r['doc_id']}", use_container_width=True):
                                db.collection("requirements").document(r["doc_id"]).update({"fulfilled": not is_done}); st.rerun()
                        with rc2:
                            if st.button("🗑️ Delete", key=f"del_req_{r['doc_id']}", use_container_width=True):
                                db.collection("requirements").document(r["doc_id"]).delete(); st.rerun()

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 4 — MY ADS
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_myads:
        if not st.session_state.logged_in:
            st.markdown("""
            <div style="background:linear-gradient(135deg,#FFF1E8,#FFF8E1);
                        border:2px solid #F55D00;border-radius:16px;
                        padding:2rem;text-align:center;margin-top:1rem;">
              <div style="font-size:2.5rem;margin-bottom:12px;">🔐</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                          color:#F55D00;margin-bottom:8px;">Login Required</div>
              <div style="font-size:.85rem;color:#8A7A6A;">
                Sign in to view and manage your listings.
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            t1, t2 = st.tabs(["Sign In", "Register"])
            with t1: page_login()
            with t2: page_register()
            st.stop()
        st.markdown('<div class="bb-section-head">📦 My Listings</div>', unsafe_allow_html=True)
        if st.session_state.pop("deleted_ad", False):
            st.success("✅ Ad deleted successfully.")

        my_products = []
        for doc in db.collection("products").stream():
            d = doc.to_dict()
            if d.get("seller_email","") == st.session_state.user_email:
                d["doc_id"] = doc.id; my_products.append(d)
        my_products = sorted(my_products, key=lambda x: x.get("created",""), reverse=True)

        if not my_products:
            st.markdown("""
            <div class="bb-cta-card">
              <div style="font-size:2.5rem;margin-bottom:12px;">🏪</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                          color:var(--ink);margin-bottom:6px;">No listings yet</div>
              <div style="font-size:.85rem;color:var(--muted);">
                Head to <strong>Post an Ad</strong> to get started!
              </div>
            </div>""", unsafe_allow_html=True)
        else:
            sold_n = sum(1 for p in my_products if p.get("sold"))
            st.markdown(f"""
            <div style="display:flex;gap:10px;margin-bottom:1.2rem;flex-wrap:wrap;">
              <div class="bb-info-pill">📦 {len(my_products)} Total</div>
              <div class="bb-green-pill">✓ {sold_n} Sold</div>
            </div>""", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, p in enumerate(my_products):
                with cols[i % 2]: product_card(p, show_manage=True)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def main():
    if st.session_state.show_forgot:
        page_forgot_password()
    else:
        app_main()

if __name__ == "__main__":
    main()
