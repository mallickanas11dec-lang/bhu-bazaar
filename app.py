# =============================================================================
# BHU BAZAAR — app.py
# A zero-cost student marketplace for Banaras Hindu University
# =============================================================================
#
# ── HOW TO CONNECT FIREBASE ──────────────────────────────────────────────────
#
# 1. Go to https://console.firebase.google.com and create a new project.
#
# 2. Enable Firestore Database (Start in test mode for development).
#
# 3. Go to Project Settings → Service Accounts → Generate new private key.
#    This downloads a JSON file (e.g. serviceAccountKey.json).
#
# 4. OPTION A — Local Development (use the JSON file directly):
#    Place the JSON file in the same directory as app.py and set:
#        FIREBASE_KEY_PATH = "serviceAccountKey.json"   (see config below)
#
# 5. OPTION B — Streamlit Cloud Deployment (use Streamlit Secrets):
#    In your Streamlit Cloud dashboard → App Settings → Secrets, paste:
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
#    The app will auto-detect Streamlit Secrets if the JSON file is absent.
#
# 6. In Firestore, the app auto-creates a collection called "products".
#    No manual schema setup needed — Firestore is schema-less.
#
# =============================================================================

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import re
import os
import json
import base64
from datetime import datetime

# ── CONFIG ────────────────────────────────────────────────────────────────────
FIREBASE_KEY_PATH = "serviceAccountKey.json"   # ← Change this to your JSON file path
ALLOWED_DOMAINS   = r"@(bhu\.ac\.in|itbhu\.ac\.in)$"
CATEGORIES        = ["All", "Books", "Electronics", "Cycles", "Hostel Gear"]
HOSTELS           = [
    "Birsa Munda Hostel", "CV Raman Hostel", "GN Jha Hostel",
    "Jagannath Hostel", "Limbdi Hostel", "Mahavir Hostel",
    "Murlidhar Hostel", "Sapt Rishi Hostel", "Other / Day Scholar"
]

# ── THEME & GLOBAL CSS ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="BHU Bazaar",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Poppins', sans-serif;
    color: #1A1A1A !important;
}

/* Force light background and dark text everywhere */
.stApp, .stApp > div, section[data-testid="stSidebar"] {
    background-color: #FFF8F2 !important;
    color: #1A1A1A !important;
}

/* Fix all text elements */
p, span, div, label, h1, h2, h3, h4, h5, h6 {
    color: #1A1A1A !important;
}

/* Fix input text */
input, textarea, select {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}

/* Fix Streamlit specific elements */
.stTextInput input,
.stTextArea textarea {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}

/* ── NUCLEAR DROPDOWN FIX ── */
* { box-sizing: border-box; }

/* Every single div inside selectbox */
.stSelectbox * {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}

/* Baseweb select components */
[data-baseweb="select"] * {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}

/* Dropdown menu and options */
[data-baseweb="menu"] {
    background-color: #FFFFFF !important;
}
[data-baseweb="menu"] * {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}
[role="option"]:hover,
[data-baseweb="menu"] li:hover {
    background-color: #FFF0E5 !important;
}

/* Sign out button fix - keep it visible */
.stButton > button {
    color: #1A1A1A !important;
    background-color: #FFFFFF !important;
}
.stButton > button[kind="primary"] {
    color: #FFFFFF !important;
    background-color: #FF6B00 !important;
}

/* Fix tab text */
.stTabs [data-baseweb="tab"] {
    color: #1A1A1A !important;
}

/* Fix error/warning/success boxes */
.stAlert p {
    color: #1A1A1A !important;
}

/* Fix caption text */
.stCaption {
    color: #555555 !important;
}

/* Fix markdown text */
.stMarkdown p, .stMarkdown span {
    color: #1A1A1A !important;
}

/* ── Root Palette ── */
:root {
    --saffron:   #FF6B00;
    --saffron-lt:#FF8C38;
    --gold:      #FFD700;
    --white:     #FFFFFF;
    --bg:        #FFF8F2;
    --card-bg:   #FFFFFF;
    --text:      #1A1A1A;
    --muted:     #777777;
    --border:    #E8E0D8;
}

/* ── Page background ── */
.stApp { background-color: var(--bg); }

/* ── Topbar / Hero ── */
.bhu-header {
    background: linear-gradient(135deg, #FF6B00 0%, #E65000 100%);
    color: white;
    padding: 1.2rem 2rem;
    border-radius: 0 0 18px 18px;
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 20px rgba(255,107,0,0.3);
}
.bhu-header h1 { margin: 0; font-size: 1.8rem; font-weight: 700; letter-spacing: -0.5px; }
.bhu-header p  { margin: 0; font-size: 0.85rem; opacity: 0.85; }

/* ── Nav tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 6px;
    background: transparent;
}
.stTabs [data-baseweb="tab"] {
    background: white;
    border-radius: 30px !important;
    padding: 6px 20px;
    font-weight: 500;
    border: 2px solid var(--border);
    color: var(--text);
}
.stTabs [aria-selected="true"] {
    background: var(--saffron) !important;
    color: white !important;
    border-color: var(--saffron) !important;
}

/* ── Product card ── */
.prod-card {
    background: var(--card-bg);
    border: 1.5px solid var(--border);
    border-radius: 14px;
    padding: 1rem;
    margin-bottom: 1rem;
    transition: box-shadow .2s;
    position: relative;
    overflow: hidden;
}
.prod-card:hover { box-shadow: 0 6px 24px rgba(0,0,0,0.10); }

/* Featured / gold border */
.prod-card.featured {
    border: 2.5px solid var(--gold);
    box-shadow: 0 0 0 3px rgba(255,215,0,0.25);
}

/* ── Badges ── */
.badge-featured {
    background: var(--gold);
    color: #5a3e00;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
}
.badge-sold {
    background: #e53e3e;
    color: white;
    font-size: 0.68rem;
    font-weight: 700;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 6px;
    letter-spacing: 0.5px;
}
.badge-cat {
    background: #FFF0E5;
    color: var(--saffron);
    font-size: 0.7rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    display: inline-block;
    margin-bottom: 6px;
    border: 1px solid #FFD0AA;
}

/* ── Price chip ── */
.price-chip {
    font-size: 1.25rem;
    font-weight: 700;
    color: var(--saffron);
}

/* ── WhatsApp button ── */
.wa-btn {
    display: inline-block;
    background: #25D366;
    color: white !important;
    padding: 7px 16px;
    border-radius: 30px;
    font-size: 0.8rem;
    font-weight: 600;
    text-decoration: none !important;
    margin-top: 8px;
}
.wa-btn:hover { background: #128C7E; }

/* ── Auth card ── */
.auth-card {
    max-width: 440px;
    margin: 2rem auto;
    background: white;
    border-radius: 20px;
    padding: 2.5rem 2rem;
    box-shadow: 0 8px 40px rgba(255,107,0,0.12);
    border: 1.5px solid var(--border);
}

/* ── Streamlit button overrides ── */
.stButton > button {
    border-radius: 30px !important;
    font-weight: 600 !important;
    transition: all .2s !important;
}
.stButton > button[kind="primary"] {
    background: var(--saffron) !important;
    border-color: var(--saffron) !important;
}
.stButton > button[kind="primary"]:hover {
    background: var(--saffron-lt) !important;
}

/* ── Input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: 10px !important;
}

/* ── Responsive grid helper ── */
@media (max-width: 640px) {
    .bhu-header h1 { font-size: 1.3rem; }
    .prod-card { padding: .75rem; }
}
</style>
""", unsafe_allow_html=True)


# ── FIREBASE INITIALISATION ───────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def init_firebase():
    """
    Initialise Firebase once per session.
    Prefers a local JSON key file; falls back to st.secrets for cloud deployments.
    """
    if not firebase_admin._apps:
        if os.path.exists(FIREBASE_KEY_PATH):
            cred = credentials.Certificate(FIREBASE_KEY_PATH)
        else:
            # Streamlit Cloud: load credentials from Secrets
            try:
                key_dict = dict(st.secrets["firebase"])
                key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
                cred = credentials.Certificate(key_dict)
            except Exception as e:
                st.error(
                    "⚠️ Firebase credentials not found.\n\n"
                    f"Place `{FIREBASE_KEY_PATH}` next to app.py, or configure "
                    "Streamlit Secrets (see comments at the top of app.py).\n\n"
                    f"Error: {e}"
                )
                st.stop()
        firebase_admin.initialize_app(cred)
    return firestore.client()

db = init_firebase()


# ── SESSION STATE DEFAULTS ────────────────────────────────────────────────────
for key, default in {
    "logged_in": False,
    "user_email": "",
    "user_name": "",
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ── PERSIST LOGIN ACROSS REFRESH using URL query params ──────────────────────
params = st.query_params
if not st.session_state.logged_in and "user" in params:
    saved_email = params["user"]
    all_users   = db.collection("users").stream()
    user_doc    = next((u for u in all_users if u.to_dict().get("email","") == saved_email), None)
    if user_doc:
        data = user_doc.to_dict()
        st.session_state.logged_in  = True
        st.session_state.user_email = data["email"]
        st.session_state.user_name  = data.get("name","Student")


# ── HELPERS ───────────────────────────────────────────────────────────────────
def valid_bhu_email(email: str) -> bool:
    return bool(re.search(ALLOWED_DOMAINS, email.strip(), re.IGNORECASE))

def whatsapp_url(phone: str, item_title: str) -> str:
    phone_clean = re.sub(r"\D", "", phone)
    if not phone_clean.startswith("91"):
        phone_clean = "91" + phone_clean
    msg = f"Hi, I saw your ad for *{item_title}* on BHU Bazaar. Is it still available?"
    import urllib.parse
    return f"https://wa.me/{phone_clean}?text={urllib.parse.quote(msg)}"

def render_header():
    st.markdown("""
    <div class="bhu-header">
        <div style="font-size:2.5rem">🏛️</div>
        <div>
            <h1>BHU Bazaar</h1>
            <p>The student marketplace of Banaras Hindu University</p>
        </div>
    </div>""", unsafe_allow_html=True)

def product_card(p: dict, show_manage: bool = False):
    """Render a single product card."""
    is_featured = p.get("featured", False)
    is_sold     = p.get("sold", False)
    card_class  = "prod-card featured" if is_featured else "prod-card"

    badges = ""
    if is_featured:
        badges += '<span class="badge-featured">⭐ FEATURED</span> '
    if is_sold:
        badges += '<span class="badge-sold">SOLD</span> '
    badges += f'<span class="badge-cat">{p.get("category","")}</span>'

    img_html = ""
    if p.get("image_url"):
        img_html = f'<img src="{p["image_url"]}" style="width:100%;height:160px;object-fit:cover;border-radius:10px;margin-bottom:10px;" onerror="this.style.display=\'none\'">'

    wa_url  = whatsapp_url(p.get("phone",""), p.get("title",""))
    wa_html = f'<a class="wa-btn" href="{wa_url}" target="_blank">💬 Chat on WhatsApp</a>'

    st.markdown(f"""
    <div class="{card_class}">
        {img_html}
        {badges}
        <div style="font-weight:700;font-size:1rem;margin:.3rem 0">{p.get("title","")}</div>
        <div class="price-chip">₹{p.get("price","")}</div>
        <div style="font-size:.82rem;color:#555;margin:.4rem 0">{p.get("description","")[:120]}{"…" if len(p.get("description",""))>120 else ""}</div>
        <div style="font-size:.78rem;color:#888;margin-top:.4rem">
            👤 {p.get("seller_name","")} &nbsp;·&nbsp; 🏠 {p.get("seller_hostel","")}
        </div>
        {wa_html}
    </div>""", unsafe_allow_html=True)

    if show_manage:
        col1, col2 = st.columns(2)
        doc_id = p.get("doc_id", "")
        with col1:
            label = "✅ Mark as SOLD" if not is_sold else "🔄 Mark as Available"
            if st.button(label, key=f"sold_{doc_id}", use_container_width=True):
                db.collection("products").document(doc_id).update({"sold": not is_sold})
                st.rerun()
        with col2:
            if st.button("🗑️ Delete Ad", key=f"del_{doc_id}", use_container_width=True, type="primary"):
                db.collection("products").document(doc_id).delete()
                st.success("Ad deleted.")
                st.rerun()


# ── AUTH PAGES ────────────────────────────────────────────────────────────────
def page_login():
    render_header()
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("### 👋 Welcome back!")
    st.caption("Sign in with your email or phone number")

    login_input = st.text_input("Email or Phone Number", placeholder="yourname@gmail.com or 9876543210", key="login_input")
    show_pw     = st.checkbox("👁️ Show password", key="show_pw_login")
    password    = st.text_input("Password", type="default" if show_pw else "password", key="login_password")

    if st.button("Sign In", type="primary", use_container_width=True):
        login_clean  = login_input.lower().strip()
        phone_clean  = re.sub(r"\D", "", login_input)

        # Check if input is email or phone
        is_email = re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", login_clean)
        is_phone = re.fullmatch(r"\d{10}", phone_clean)

        if not is_email and not is_phone:
            st.error("❌ Please enter a valid email or 10-digit phone number.")
        else:
            all_users = db.collection("users").stream()
            user_doc  = None
            for u in all_users:
                d = u.to_dict()
                if is_email and d.get("email","") == login_clean:
                    user_doc = u
                    break
                elif is_phone and re.sub(r"\D","",d.get("phone","")) == phone_clean:
                    user_doc = u
                    break

            if user_doc and user_doc.to_dict().get("password") == password:
                data = user_doc.to_dict()
                st.session_state.logged_in  = True
                st.session_state.user_email = data["email"]
                st.session_state.user_name  = data.get("name","Student")
                st.query_params["user"] = data["email"]
                st.rerun()
            else:
                st.error("❌ Invalid credentials. Please try again.")

    st.markdown("---")
    st.caption("New here? Register below 👇")
    st.markdown('</div>', unsafe_allow_html=True)

def page_register():
    render_header()
    st.markdown('<div class="auth-card">', unsafe_allow_html=True)
    st.markdown("### 🎓 Create your account")
    st.caption("Register with email OR phone number — both are optional together, but at least one is required")

    name      = st.text_input("Full Name ✱", key="reg_name")
    email     = st.text_input("Email (optional if phone given)", placeholder="yourname@gmail.com", key="reg_email")
    phone_reg = st.text_input("Phone Number (optional if email given)", placeholder="9876543210", key="reg_phone")
    hostel    = st.selectbox("Your Hostel", HOSTELS, key="reg_hostel")

    # Show/hide password toggle
    show_pw  = st.checkbox("👁️ Show password", key="show_pw_reg")
    pw_type  = "default" if show_pw else "password"
    password = st.text_input("Password (min 6 chars) ✱", type=pw_type, key="reg_password")
    confirm  = st.text_input("Confirm Password ✱",       type=pw_type, key="reg_confirm")

    if st.button("Create Account", type="primary", use_container_width=True):
        email_clean = email.lower().strip()
        phone_clean = re.sub(r"\D", "", phone_reg)

        has_email = bool(re.fullmatch(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", email_clean))
        has_phone = bool(re.fullmatch(r"\d{10}", phone_clean))

        # Use email as unique ID; if no email, use phone@bhubazaar.app as internal ID
        if not name.strip():
            st.error("❌ Please enter your full name.")
        elif not has_email and not has_phone:
            st.error("❌ Please enter a valid email address OR a 10-digit phone number.")
        elif has_phone and not re.fullmatch(r"\d{10}", phone_clean):
            st.error("❌ Phone number must be exactly 10 digits.")
        elif len(password) < 6:
            st.error("❌ Password must be at least 6 characters.")
        elif password != confirm:
            st.error("❌ Passwords do not match.")
        else:
            # Create a unique identifier — prefer email, fallback to phone-based ID
            unique_id = email_clean if has_email else f"{phone_clean}@phone.bhubazaar"

            all_users = db.collection("users").stream()
            already_exists = any(
                u.to_dict().get("email","") == unique_id
                for u in all_users
            )
            if already_exists:
                st.error("❌ An account already exists with this email/phone. Please sign in.")
            else:
                db.collection("users").add({
                    "email":    unique_id,
                    "name":     name.strip(),
                    "hostel":   hostel,
                    "phone":    phone_clean,
                    "password": password,
                    "created":  datetime.utcnow(),
                })
                st.success("✅ Account created! Go to Sign In tab to log in.")
    st.markdown('</div>', unsafe_allow_html=True)


# ── MAIN APP (logged-in) ──────────────────────────────────────────────────────
def app_main():
    render_header()

    # ── Top bar ──
    col_name, col_logout = st.columns([4,1])
    with col_name:
        st.markdown(f"👤 **{st.session_state.user_name}** · {st.session_state.user_email}")
    with col_logout:
        if st.button("Sign Out"):
            for k in ["logged_in","user_email","user_name"]:
                st.session_state[k] = "" if k != "logged_in" else False
            st.query_params.clear()
            st.rerun()

    st.markdown("---")

    # ── Navigation tabs ──
    tab_home, tab_post, tab_myads = st.tabs(["🏠 Browse", "📢 Post an Ad", "📦 My Ads"])

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 1 — HOME FEED
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_home:
        st.markdown("### 🛒 Available Items")

        # Search & filter row
        search_col, cat_col = st.columns([3,1])
        with search_col:
            search_q = st.text_input("🔍 Search items…", label_visibility="collapsed",
                                     placeholder="Search items…")
        with cat_col:
            selected_cat = st.radio("Category", CATEGORIES, horizontal=True, label_visibility="collapsed")

        # Pull products from Firestore (no index needed)
        docs = db.collection("products").stream()
        products = []
        for doc in docs:
            d = doc.to_dict()
            d["doc_id"] = doc.id
            products.append(d)
        # Sort in Python instead of Firestore to avoid index requirement
        products = sorted(products, key=lambda x: x.get("created", ""), reverse=True)

        # Filter
        if selected_cat != "All":
            products = [p for p in products if p.get("category") == selected_cat]
        if search_q:
            q = search_q.lower()
            products = [p for p in products
                        if q in p.get("title","").lower()
                        or q in p.get("description","").lower()]

        # Featured first
        products = sorted(products, key=lambda x: (not x.get("featured"), x.get("sold")))

        if not products:
            st.info("No items found. Be the first to post an ad! 🎉")
        else:
            cols = st.columns(3)
            for i, p in enumerate(products):
                with cols[i % 3]:
                    product_card(p)

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 2 — POST AN AD
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_post:
        st.markdown("### 📢 Post a New Ad")
        st.caption("All fields marked ✱ are required")

        with st.form("post_ad_form", clear_on_submit=True):
            title    = st.text_input("Item Title ✱", placeholder="e.g. Engineering Physics by H.K. Malik")
            category = st.selectbox("Category ✱", CATEGORIES[1:])  # skip "All"
            price    = st.text_input("Price ✱", value="₹", placeholder="₹ 0")
            desc     = st.text_area("Description ✱", placeholder="Condition, edition, reason for selling…", height=120)
            uploaded_image = st.file_uploader("Upload Image (optional)", type=["jpg","jpeg","png","webp"])
            image_url = ""
            if uploaded_image:
                img_bytes = uploaded_image.read()
                img_b64   = base64.b64encode(img_bytes).decode()
                mime      = uploaded_image.type
                image_url = f"data:{mime};base64,{img_b64}"
                st.image(uploaded_image, width=200)
            phone    = st.text_input("WhatsApp / Phone Number ✱", placeholder="10-digit mobile number")

            # Fetch seller's hostel from profile
            user_doc  = db.collection("users").where("email","==",st.session_state.user_email).limit(1).stream()
            user_data = next(user_doc, None)
            seller_hostel = user_data.to_dict().get("hostel","") if user_data else ""

            featured = st.toggle("⭐ Mark as Featured (gold highlight)", value=False)

            submitted = st.form_submit_button("Post Ad 🚀", type="primary", use_container_width=True)

        if submitted:
            price_clean = price.replace("₹","").strip()
            errors = []
            if not title:     errors.append("Item title is required.")
            if not price_clean or not price_clean.replace(".","").isdigit():
                errors.append("Enter a valid price (numbers only after ₹).")
            if not desc:      errors.append("Description is required.")
            if not re.match(r"^\d{10}$", re.sub(r"\D","",phone)):
                errors.append("Enter a valid 10-digit phone number.")

            if errors:
                for e in errors:
                    st.error(e)
            else:
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
                st.success("✅ Your ad has been posted! It will appear on the home feed shortly.")

    # ═══════════════════════════════════════════════════════════════════════════
    # TAB 3 — MY ADS
    # ═══════════════════════════════════════════════════════════════════════════
    with tab_myads:
        st.markdown("### 📦 My Ads")

        # Fetch all and filter in Python to avoid Firestore index requirement
        all_docs = db.collection("products").stream()
        my_products = []
        for doc in all_docs:
            d = doc.to_dict()
            if d.get("seller_email","") == st.session_state.user_email:
                d["doc_id"] = doc.id
                my_products.append(d)
        my_products = sorted(my_products, key=lambda x: x.get("created",""), reverse=True)

        if not my_products:
            st.info("You haven't posted any ads yet. Go to 'Post an Ad' to get started!")
        else:
            st.caption(f"You have **{len(my_products)}** ad(s) listed.")
            cols = st.columns(2)
            for i, p in enumerate(my_products):
                with cols[i % 2]:
                    product_card(p, show_manage=True)


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
def main():
    if st.session_state.logged_in:
        app_main()
    else:
        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "✍️ Register"])
        with auth_tab1:
            page_login()
        with auth_tab2:
            page_register()

if __name__ == "__main__":
    main()
