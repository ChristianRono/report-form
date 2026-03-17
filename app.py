"""
TCN Daily Report — Submission Form
- Password-protected per director
- Dynamic objective rows (add/remove)
- Writes to Google Sheets
- Completeness validation before submit
- 100% free, no API key needed
"""

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import json
import re
import time

# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TCN Daily Report",
    page_icon="📋",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─────────────────────────────────────────────────────────────────────────────
# Styling
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Instrument+Sans:wght@400;500;600&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] { font-family: 'Instrument Sans', sans-serif; }

/* ── Main background: warm off-white ── */
.stApp { background: #f7f5f0; color: #1a1916; }

/* ── All Streamlit default text ── */
p, span, label, div { color: #1a1916; }

/* ── Login card ── */
.login-wrap {
    max-width: 420px; margin: 80px auto 0; padding: 36px;
    background: #ffffff; border: 1px solid #e0ddd6;
    border-radius: 16px; box-shadow: 0 2px 16px rgba(0,0,0,0.06);
}
.login-logo { font-family:'DM Serif Display',serif; font-size:28px; color:#b8934a; text-align:center; margin-bottom:4px; }
.login-sub  { font-size:13px; color:#7a7770; text-align:center; margin-bottom:28px; line-height:1.6; }

/* ── Form sections ── */
.form-section {
    background:#ffffff; border:1px solid #e0ddd6;
    border-radius:12px; padding:22px 24px; margin-bottom:20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.section-label {
    font-size:11px; font-weight:700; letter-spacing:.1em;
    text-transform:uppercase; color:#b8934a; margin-bottom:16px;
    padding-bottom:10px; border-bottom:2px solid #f0ede6;
}

/* ── Objective rows ── */
.obj-row {
    background:#faf9f6; border:1px solid #e8e5de;
    border-radius:8px; padding:14px 16px; margin-bottom:12px;
}

.required { color:#c0392b; font-weight:600; }
.field-hint { font-size:12px; color:#8a8780; margin-top:-6px; margin-bottom:10px; line-height:1.5; }

/* ── Buttons ── */
.stButton > button {
    background:#ffffff !important; color:#1a1916 !important;
    border:1px solid #d0cdc6 !important; border-radius:7px !important;
    font-size:13px !important; font-weight:500 !important;
    transition:all .15s !important;
}
.stButton > button:hover {
    background:#faf9f6 !important;
    border-color:#b8934a !important;
    color:#b8934a !important;
}
.stButton > button[kind="primary"] {
    background:#b8934a !important; color:#ffffff !important;
    border-color:#b8934a !important; font-weight:700 !important;
    font-size:14px !important; letter-spacing:.02em !important;
}
.stButton > button[kind="primary"]:hover {
    background:#a07d3a !important; border-color:#a07d3a !important;
}
.stButton > button:disabled {
    background:#e8e5de !important; color:#aaa9a6 !important;
    border-color:#e0ddd6 !important; cursor:not-allowed !important;
}

/* ── All input fields ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
.stDateInput > div > div > input {
    background:#ffffff !important;
    border:1px solid #d0cdc6 !important;
    color:#1a1916 !important;
    border-radius:7px !important;
    font-size:13px !important;
    font-family:'Instrument Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus,
.stNumberInput > div > div > input:focus {
    border-color:#b8934a !important;
    box-shadow: 0 0 0 2px rgba(184,147,74,0.15) !important;
}
.stTextInput > div > div > input::placeholder,
.stTextArea > div > div > textarea::placeholder { color:#b0aea8 !important; }

/* ── Select boxes ── */
.stSelectbox > div > div {
    background:#ffffff !important;
    border:1px solid #d0cdc6 !important;
    color:#1a1916 !important;
    border-radius:7px !important;
    font-size:13px !important;
}
.stSelectbox label, .stTextInput label,
.stTextArea label, .stNumberInput label,
.stDateInput label, .stCheckbox label {
    color:#3a3835 !important;
    font-size:13px !important;
    font-weight:500 !important;
}

/* ── Checkbox ── */
.stCheckbox > label { color:#1a1916 !important; font-size:13px !important; }

/* ── Metrics ── */
[data-testid="stMetric"] {
    background:#ffffff; border:1px solid #e0ddd6;
    border-radius:10px; padding:14px !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
[data-testid="stMetricLabel"] { color:#7a7770 !important; font-size:11px !important; font-weight:600 !important; }
[data-testid="stMetricValue"] { color:#1a1916 !important; font-family:'DM Mono',monospace !important; font-size:20px !important; }

/* ── Alert / message boxes ── */
.success-box {
    background:#f0faf2; border:1px solid #6dba7d; border-left:4px solid #2e8b42;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#1a4a24; margin:10px 0; line-height:1.6;
}
.error-box {
    background:#fdf2f2; border:1px solid #e89090; border-left:4px solid #c0392b;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#6b1a1a; margin:10px 0; line-height:1.6;
}
.warn-box {
    background:#fef9ec; border:1px solid #e8c96a; border-left:4px solid #c8960a;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#5a4200; margin:10px 0; line-height:1.6;
}
.info-box {
    background:#eef5fc; border:1px solid #7ab0d4; border-left:4px solid #2a7ab8;
    border-radius:8px; padding:14px 18px; font-size:13px;
    color:#1a3a5a; margin:10px 0; line-height:1.6;
}

/* ── Director badge ── */
.director-badge {
    display:inline-block; background:#ffffff;
    border:1px solid #e0ddd6; border-left:4px solid #b8934a;
    border-radius:8px; padding:12px 18px; font-size:13px;
    color:#5a5855; margin-bottom:22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.director-name   { font-size:17px; font-weight:700; color:#1a1916; margin-bottom:2px; }
.director-pillar { font-size:12px; color:#b8934a; font-family:'DM Mono',monospace; font-weight:500; }

/* ── Page titles ── */
.page-title { font-family:'DM Serif Display',serif; font-size:28px; color:#1a1916; letter-spacing:-.02em; margin-bottom:4px; }
.page-sub   { font-size:13px; color:#7a7770; margin-bottom:26px; line-height:1.6; }

/* ── Progress bar ── */
.progress-wrap  { margin:18px 0; }
.progress-track { height:6px; background:#e8e5de; border-radius:3px; overflow:hidden; margin-top:8px; }
.progress-fill  { height:100%; border-radius:3px; background:#b8934a; transition:width .4s ease; }
.progress-label { display:flex; justify-content:space-between; font-size:12px; color:#7a7770; font-weight:500; }

/* ── Tabs ── */
[data-testid="stTabs"] button { color:#7a7770 !important; font-size:13px !important; font-weight:500 !important; }
[data-testid="stTabs"] button[aria-selected="true"] { color:#b8934a !important; border-bottom-color:#b8934a !important; font-weight:600 !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border:1px solid #e0ddd6 !important; border-radius:8px !important; }

/* ── Hide sidebar ── */
[data-testid="stSidebar"] { display: none; }

/* ── Divider ── */
hr { border-color: #e0ddd6 !important; }

/* ── Streamlit info/warning/error native boxes ── */
[data-testid="stAlert"] { border-radius:8px !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Director registry
# Edit this dict to add/change directors and passwords
# Format: "password" : { director info }
# ─────────────────────────────────────────────────────────────────────────────
DIRECTORS = {
    "pillar1pass": {
        "name": "Rev. Michael Mutai",
        "pillar": "Pillar 1",
        "pillar_code": "P1",
        "objectives": ["NGE-103", "NGE-104"],   # pre-known objective codes for this pillar
    },
    "pillar2pass": {
        "name": "Jennifer Chemutai",
        "pillar": "Pillar 2",
        "pillar_code": "P2",
        "objectives": ["KB-201", "KB-202"],
    },
    "pillar3pass": {
        "name": "Genaldon Cherono",
        "pillar": "Pillar 3",
        "pillar_code": "P3",
        "objectives": ["OB-301"],
    },
    "pillar4pass": {
        "name": "Director Four",
        "pillar": "Pillar 4",
        "pillar_code": "P4",
        "objectives": ["P4-401"],
    },
    "pillar5pass": {
        "name": "Director Five",
        "pillar": "Pillar 5",
        "pillar_code": "P5",
        "objectives": ["P5-501"],
    },
    # Admin can view all submissions
    "adminpass": {
        "name": "Admin",
        "pillar": "Admin",
        "pillar_code": "ADMIN",
        "objectives": [],
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# Google Sheets connection
# ─────────────────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Column headers written to Google Sheet
SHEET_HEADERS = [
    "submission_id", "submitted_at", "pillar", "director",
    "reporting_date", "prepared_by",
    # Objectives — up to 5 per submission stored as JSON
    "objectives_json",
    # Financials
    "today_spend_kes", "mtd_spend_kes", "monthly_budget_kes",
    "burn_rate_pct", "alert_status",
    # Narrative
    "key_activities", "objectives_advanced",
    "operational_issues", "financial_issues",
    "corrective_measures", "urgent_decisions",
    # Meta
    "risk_categories", "urgency_score", "completeness_score",
]

@st.cache_resource
def get_sheet(credentials_dict: dict, spreadsheet_id: str):
    """Connect to Google Sheets — cached so it only authenticates once."""
    creds = Credentials.from_service_account_info(credentials_dict, scopes=SCOPES)
    client = gspread.authorize(creds)
    sh = client.open_by_key(spreadsheet_id)

    # Ensure sheet tabs exist
    existing = [ws.title for ws in sh.worksheets()]

    for tab in ["Submissions", "Objectives"]:
        if tab not in existing:
            ws = sh.add_worksheet(title=tab, rows=1000, cols=30)
            if tab == "Submissions":
                ws.append_row(SHEET_HEADERS)
            else:
                ws.append_row(["submission_id", "pillar", "reporting_date",
                                "obj_code", "daily_target", "daily_achievement",
                                "pct_achievement", "status"])

    return sh

def append_submission(sh, record: dict, objectives: list):
    """Write one report submission across two sheet tabs."""
    sub_id = f"SUB-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    record["submission_id"] = sub_id
    record["submitted_at"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    record["objectives_json"] = json.dumps(objectives)

    # Submissions tab
    row = [record.get(h, "") for h in SHEET_HEADERS]
    sh.worksheet("Submissions").append_row(row, value_input_option="USER_ENTERED")

    # Objectives tab — one row per objective
    obj_ws = sh.worksheet("Objectives")
    for obj in objectives:
        pct = None
        try:
            t, a = float(obj.get("target", 0) or 0), float(obj.get("achievement", 0) or 0)
            if t > 0:
                pct = round(a / t * 100, 1)
        except:
            pass
        obj_ws.append_row([
            sub_id,
            record.get("pillar",""),
            record.get("reporting_date",""),
            obj.get("code",""),
            obj.get("target",""),
            obj.get("achievement",""),
            pct if pct is not None else "",
            obj.get("status",""),
        ], value_input_option="USER_ENTERED")

    return sub_id

# ─────────────────────────────────────────────────────────────────────────────
# Completeness scoring
# ─────────────────────────────────────────────────────────────────────────────
def completeness_score(record: dict, objectives: list) -> tuple[int, list]:
    """Returns (score 0-100, list of missing fields)."""
    checks = {
        "Reporting date":        bool(record.get("reporting_date")),
        "Key activities":        len(record.get("key_activities","").strip()) > 10,
        "At least one objective":len(objectives) > 0,
        "Objective codes filled":all(o.get("code","").strip() for o in objectives),
        "Today's expenditure":   record.get("today_spend_kes") is not None,
        "MTD expenditure":       record.get("mtd_spend_kes") is not None,
        "Monthly budget":        record.get("monthly_budget_kes") and record["monthly_budget_kes"] > 0,
        "Alert status":          bool(record.get("alert_status")),
        "Operational issues":    len(record.get("operational_issues","").strip()) > 5,
        "Corrective measures":   len(record.get("corrective_measures","").strip()) > 5,
    }
    passed = sum(checks.values())
    missing = [k for k, v in checks.items() if not v]
    score = round(passed / len(checks) * 100)
    return score, missing

# ─────────────────────────────────────────────────────────────────────────────
# Risk auto-classification
# ─────────────────────────────────────────────────────────────────────────────
def classify_risks(text: str) -> tuple[list, int]:
    blob = text.lower()
    cats = []
    if any(w in blob for w in ["fund","financ","budget","tla","airtime","money","kes","cash","reimburse"]):
        cats.append("Financial")
    if any(w in blob for w in ["airtime","phone","communicat","contact","follow-up","network"]):
        cats.append("Communication")
    if any(w in blob for w in ["transport","travel","weather","road","distance","field","vehicle"]):
        cats.append("Logistical")
    if any(w in blob for w in ["staff","facilitator","personnel","absent","sick","human resource"]):
        cats.append("Human Resource")
    if any(w in blob for w in ["stakeholder","government","partner","external","guest","community"]):
        cats.append("External")
    cats = list(dict.fromkeys(cats))

    urgency = 1
    if any(w in blob for w in ["urgent","critical","immediate","block","cannot","no funds","zero","suspend","halt"]):
        urgency = 3
    elif any(w in blob for w in ["limited","challenge","shortage","difficulty","risk","concern","lack"]):
        urgency = 2
    return cats, urgency

# ─────────────────────────────────────────────────────────────────────────────
# Session state init
# ─────────────────────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "director" not in st.session_state:
    st.session_state.director = None
if "objectives" not in st.session_state:
    st.session_state.objectives = []
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "sub_id" not in st.session_state:
    st.session_state.sub_id = None

# ─────────────────────────────────────────────────────────────────────────────
# ── LOGIN SCREEN ──────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
if not st.session_state.authenticated:
    st.markdown("""
    <div class="login-wrap">
        <div class="login-logo">TCN</div>
        <div class="login-sub">Transformational Compassion Network<br>Daily Report Submission</div>
    </div>
    """, unsafe_allow_html=True)

    # Render inside the visual card using columns trick
    col = st.columns([1,2,1])[1]
    with col:
        password = st.text_input("Enter your access password", type="password",
                                 placeholder="Password given by your coordinator")
        if st.button("Sign in", type="primary", use_container_width=True):
            if password in DIRECTORS:
                st.session_state.authenticated = True
                st.session_state.director = DIRECTORS[password]
                # Pre-populate objectives from known codes
                st.session_state.objectives = [
                    {"code": code, "target": "", "achievement": "", "status": "On Track"}
                    for code in DIRECTORS[password].get("objectives", [])
                ] or [{"code": "", "target": "", "achievement": "", "status": "On Track"}]
                st.rerun()
            else:
                st.markdown('<div style="max-width:400px;margin:8px auto"><div class="error-box">Incorrect password. Contact your coordinator.</div></div>', unsafe_allow_html=True)
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ── ADMIN VIEW ───────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
director = st.session_state.director

if director["pillar_code"] == "ADMIN":
    st.markdown('<p class="page-title">Admin — Submission overview</p>', unsafe_allow_html=True)

    # Check if sheets credentials are configured
    creds_ok = "gsheets_credentials" in st.secrets and "spreadsheet_id" in st.secrets

    if creds_ok:
        try:
            sh = get_sheet(dict(st.secrets["gsheets_credentials"]), st.secrets["spreadsheet_id"])
            ws = sh.worksheet("Submissions")
            data = ws.get_all_records()
            if data:
                import pandas as pd
                df = pd.DataFrame(data)
                st.markdown(f"**{len(df)} total submissions**")
                st.dataframe(df, use_container_width=True)
            else:
                st.info("No submissions yet.")
        except Exception as e:
            st.error(f"Could not load sheet: {e}")
    else:
        st.markdown('<div class="warn-box">Google Sheets not configured — submissions are being stored locally only.<br>See setup instructions in README to connect a sheet.</div>', unsafe_allow_html=True)

    if st.button("Sign out"):
        for k in ["authenticated","director","objectives","submitted","sub_id"]:
            st.session_state[k] = None if k != "authenticated" else False
        st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ── SUCCESS SCREEN ────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.submitted:
    st.markdown(f"""
    <div style="text-align:center;padding:60px 20px">
        <div style="font-size:52px;margin-bottom:16px">✅</div>
        <div style="font-family:'DM Serif Display',serif;font-size:28px;color:#2e7d47;margin-bottom:8px">Report submitted</div>
        <div style="font-size:13px;color:#5a5855;margin-bottom:4px">Submission ID: <span style="font-family:'DM Mono',monospace;color:#b8934a;font-weight:600">{st.session_state.sub_id}</span></div>
        <div style="font-size:13px;color:#7a7770">{datetime.now().strftime("%d %B %Y, %H:%M")}</div>
    </div>
    """, unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1,1,1])
    with col_b:
        if st.button("Submit another report", use_container_width=True):
            st.session_state.submitted = False
            st.session_state.sub_id = None
            # Reset objectives to defaults
            st.session_state.objectives = [
                {"code": code, "target": "", "achievement": "", "status": "On Track"}
                for code in director.get("objectives", [])
            ] or [{"code": "", "target": "", "achievement": "", "status": "On Track"}]
            st.rerun()
    with col_c:
        if st.button("Sign out", use_container_width=True):
            for k in ["authenticated","director","objectives","submitted","sub_id"]:
                st.session_state[k] = None if k != "authenticated" else False
            st.rerun()
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# ── MAIN FORM ─────────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────

# Director badge
st.markdown(f"""
<div class="director-badge">
    <div class="director-name">{director['name']}</div>
    <div class="director-pillar">{director['pillar']} · Daily Report Form</div>
</div>
""", unsafe_allow_html=True)

st.markdown('<p class="page-title">Daily Performance & Financial Update</p>', unsafe_allow_html=True)
st.markdown(f'<p class="page-sub">Submission deadline: <strong>5:00 PM daily</strong> · All fields marked <span class="required">*</span> are required</p>', unsafe_allow_html=True)

# ── Section 1: Report header ──────────────────────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">1 · Report header</div>', unsafe_allow_html=True)

c1, c2 = st.columns(2)
with c1:
    reporting_date = st.date_input("Reporting date *", value=date.today(), format="DD/MM/YYYY")
with c2:
    prepared_by = st.text_input("Prepared by *", value="Technical Team",
                                 placeholder="Name of report preparer")
st.markdown('</div>', unsafe_allow_html=True)

# ── Section 2: Executive snapshot ────────────────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">2 · Executive snapshot</div>', unsafe_allow_html=True)

key_activities = st.text_area(
    "Key activities conducted today *",
    height=110,
    placeholder="Describe the main activities you carried out today. Be specific — what happened, where, and with whom.",
    help="Minimum 10 characters required"
)

objectives_advanced = st.text_area(
    "Objectives advanced",
    height=80,
    placeholder="Which programme objectives were progressed today and how?",
)

risks_text = st.text_area(
    "Immediate risks identified",
    height=80,
    placeholder="List any risks, blockers, or challenges encountered today.",
)

urgent_decisions = st.text_area(
    "Urgent decisions required",
    height=60,
    placeholder="Any decisions needed from leadership or finance? Leave blank if none.",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── Section 3: Performance objectives ────────────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">3 · Performance objectives</div>', unsafe_allow_html=True)
st.markdown('<div class="field-hint">Add one row per objective. You can add or remove rows as needed.</div>', unsafe_allow_html=True)

# Render each objective row
objectives_to_remove = []
for idx, obj in enumerate(st.session_state.objectives):
    st.markdown(f'<div class="obj-row">', unsafe_allow_html=True)
    oc1, oc2, oc3, oc4, oc5 = st.columns([2, 2, 2, 2, 0.7])
    with oc1:
        code = st.text_input("Objective code", value=obj.get("code",""),
                              key=f"obj_code_{idx}", placeholder="e.g. KB-201")
    with oc2:
        target_raw = st.text_input("Daily target", value=str(obj.get("target","")),
                                    key=f"obj_target_{idx}", placeholder="e.g. 8333")
    with oc3:
        ach_raw = st.text_input("Achievement", value=str(obj.get("achievement","")),
                                 key=f"obj_ach_{idx}", placeholder="e.g. 6000")
    with oc4:
        status = st.selectbox("Status", ["On Track","Behind","Ahead"],
                               index=["On Track","Behind","Ahead"].index(obj.get("status","On Track"))
                                     if obj.get("status","On Track") in ["On Track","Behind","Ahead"] else 0,
                               key=f"obj_status_{idx}")
    with oc5:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("✕", key=f"rm_obj_{idx}", help="Remove this objective"):
            objectives_to_remove.append(idx)

    # Auto-calculate % if both numbers present
    try:
        t_val = float(re.sub(r"[^\d.]","",target_raw)) if target_raw else 0
        a_val = float(re.sub(r"[^\d.]","",ach_raw))   if ach_raw   else 0
        if t_val > 0:
            pct = round(a_val / t_val * 100, 1)
            auto_status = "On Track" if 80 <= pct <= 110 else ("Ahead" if pct > 110 else "Behind")
            st.markdown(
                f'<div style="font-size:11px;color:#5a5855;margin-top:-6px;margin-bottom:6px;background:#faf9f6;border:1px solid #e8e5de;border-radius:6px;padding:6px 10px">'
                f'Calculated: <span style="font-family:\'DM Mono\',monospace;color:#b8934a;font-weight:600">{pct}%</span> '
                f'→ auto-status: <span style="color:{"#2e7d47" if auto_status=="On Track" else "#a07d3a" if auto_status=="Ahead" else "#c0392b"}">{auto_status}</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    except:
        pass

    # Update session state values from this iteration
    st.session_state.objectives[idx] = {
        "code": code,
        "target": target_raw,
        "achievement": ach_raw,
        "status": status,
    }
    st.markdown('</div>', unsafe_allow_html=True)

# Apply removals (reverse order to preserve indices)
for idx in sorted(objectives_to_remove, reverse=True):
    if len(st.session_state.objectives) > 1:
        st.session_state.objectives.pop(idx)
        st.rerun()

if st.button("＋ Add another objective", key="add_obj"):
    st.session_state.objectives.append({"code":"","target":"","achievement":"","status":"On Track"})
    st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# ── Section 4: Financial snapshot ────────────────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">4 · Financial snapshot</div>', unsafe_allow_html=True)

fc1, fc2, fc3 = st.columns(3)
with fc1:
    today_spend = st.number_input("Today's expenditure (KES) *", min_value=0.0,
                                   value=0.0, format="%.0f", help="Enter 0 if nothing was spent today")
with fc2:
    mtd_spend = st.number_input("Month-to-date expenditure (KES) *", min_value=0.0,
                                 value=0.0, format="%.0f")
with fc3:
    monthly_budget = st.number_input("Approved monthly budget (KES) *", min_value=0.0,
                                      value=0.0, format="%.0f")

# Auto-calculate burn rate and alert
burn_rate = None
auto_alert = None
if monthly_budget > 0:
    burn_rate = round(mtd_spend / monthly_budget * 100, 1)
    auto_alert = "Green" if burn_rate <= 60 else ("Amber" if burn_rate <= 90 else "Red")
    color = {"Green":"#2e7d47","Amber":"#a07d3a","Red":"#c0392b"}.get(auto_alert,"#6b6963")
    day_pct = round(date.today().day / 30 * 100)
    st.markdown(
        f'<div style="font-size:12px;color:#5a5855;margin:6px 0 12px;background:#faf9f6;border:1px solid #e8e5de;border-radius:6px;padding:8px 12px">'
        f'Burn rate: <span style="font-family:\'DM Mono\',monospace;color:#b8934a;font-weight:600">{burn_rate}%</span> &nbsp;·&nbsp; '
        f'Auto alert: <span style="color:{color};font-weight:600">{auto_alert}</span> &nbsp;·&nbsp; '
        f'Expected at day {date.today().day}: ~{day_pct}%'
        f'</div>',
        unsafe_allow_html=True
    )

alert_options = ["Green","Amber","Red"]
alert_default = alert_options.index(auto_alert) if auto_alert in alert_options else 0
alert_status = st.selectbox(
    "Alert status *",
    alert_options,
    index=alert_default,
    help="Auto-suggested based on burn rate. Override if needed."
)
st.markdown('</div>', unsafe_allow_html=True)

# ── Section 5: Issues & corrective actions ───────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">5 · Issues & corrective actions</div>', unsafe_allow_html=True)

ic1, ic2 = st.columns(2)
with ic1:
    operational_issues = st.text_area(
        "Operational issues *",
        height=100,
        placeholder="Describe any operational problems encountered. Write 'None' if no issues.",
    )
    financial_issues = st.text_area(
        "Financial issues",
        height=80,
        placeholder="Any financial problems — missing funds, reimbursements, etc.",
    )
with ic2:
    corrective_measures = st.text_area(
        "Corrective measures taken *",
        height=100,
        placeholder="What did you do to address the issues above? Be specific: who did what.",
    )
    # Show auto-detected risk categories
    risk_blob = " ".join([risks_text, operational_issues, financial_issues])
    risk_cats, urgency_score = classify_risks(risk_blob)
    if risk_cats:
        cats_display = " · ".join(risk_cats)
        urgency_labels = {1:"Informational 🟢", 2:"Monitor 🟡", 3:"Immediate action 🔴"}
        st.markdown(
            f'<div style="background:#faf9f6;border:1px solid #e0ddd6;border-radius:6px;'
            f'padding:10px 12px;font-size:12px;color:#3a3835;margin-top:8px">'
            f'<div style="color:#b8934a;margin-bottom:4px;font-size:10px;text-transform:uppercase;letter-spacing:.08em;font-weight:700">Auto-detected</div>'
            f'Risk categories: <span style="color:#a07d3a;font-weight:600">{cats_display}</span><br>'
            f'Urgency: <span style="color:{"#c0392b" if urgency_score==3 else "#a07d3a" if urgency_score==2 else "#2e7d47"}">{urgency_labels[urgency_score]}</span>'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown('</div>', unsafe_allow_html=True)

# ── Section 6: Attachments note ──────────────────────────────────────────────
st.markdown('<div class="form-section"><div class="section-label">6 · Attachments</div>', unsafe_allow_html=True)
has_receipts = st.checkbox("I have proof of expenditure to submit (receipts, invoices)")
has_activity_docs = st.checkbox("I have activity documentation (photos, attendance sheets)")
attachments_note = st.text_input("Notes on attachments", placeholder="e.g. 3 receipts will be submitted physically tomorrow")
st.markdown('<div class="field-hint">Physical attachments should be submitted to the technical team by end of day.</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Completeness preview
# ─────────────────────────────────────────────────────────────────────────────
record_preview = {
    "reporting_date": str(reporting_date),
    "key_activities": key_activities,
    "operational_issues": operational_issues,
    "corrective_measures": corrective_measures,
    "today_spend_kes": today_spend,
    "mtd_spend_kes": mtd_spend,
    "monthly_budget_kes": monthly_budget,
    "alert_status": alert_status,
}
comp_score, missing_fields = completeness_score(record_preview, st.session_state.objectives)
comp_color = "#2e7d47" if comp_score >= 90 else "#a07d3a" if comp_score >= 70 else "#c0392b"

st.markdown(f"""
<div class="progress-wrap">
    <div class="progress-label">
        <span>Report completeness</span>
        <span style="color:{comp_color};font-family:'DM Mono',monospace;font-weight:500">{comp_score}%</span>
    </div>
    <div class="progress-track">
        <div class="progress-fill" style="width:{comp_score}%;background:{comp_color}"></div>
    </div>
</div>
""", unsafe_allow_html=True)

if missing_fields:
    missing_str = " · ".join(missing_fields)
    st.markdown(f'<div class="warn-box"><strong>Still needed:</strong> {missing_str}</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Submit button
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
col_sub, col_sign = st.columns([3, 1])

with col_sub:
    submit_clicked = st.button(
        "Submit report →",
        type="primary",
        use_container_width=True,
        disabled=(comp_score < 50),
        help="Complete at least 50% of required fields to enable submission"
    )

with col_sign:
    if st.button("Sign out", use_container_width=True):
        for k in ["authenticated","director","objectives","submitted","sub_id"]:
            st.session_state[k] = None if k != "authenticated" else False
        st.rerun()

if comp_score < 50:
    st.markdown('<div class="error-box">Complete more required fields to enable submission (minimum 50%).</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# Submission logic
# ─────────────────────────────────────────────────────────────────────────────
if submit_clicked and comp_score >= 50:
    # Build clean objectives list
    clean_objectives = []
    for obj in st.session_state.objectives:
        if obj.get("code","").strip():
            t_raw = re.sub(r"[^\d.]","", str(obj.get("target","")))
            a_raw = re.sub(r"[^\d.]","", str(obj.get("achievement","")))
            clean_objectives.append({
                "code": obj["code"].strip(),
                "target": float(t_raw) if t_raw else None,
                "achievement": float(a_raw) if a_raw else None,
                "status": obj.get("status","On Track"),
            })

    risk_cats_final, urgency_final = classify_risks(
        " ".join([risks_text, operational_issues, financial_issues, corrective_measures])
    )

    record = {
        "pillar":           director["pillar"],
        "director":         director["name"],
        "reporting_date":   str(reporting_date),
        "prepared_by":      prepared_by,
        "today_spend_kes":  today_spend,
        "mtd_spend_kes":    mtd_spend,
        "monthly_budget_kes": monthly_budget,
        "burn_rate_pct":    burn_rate if burn_rate else "",
        "alert_status":     alert_status,
        "key_activities":   key_activities,
        "objectives_advanced": objectives_advanced,
        "operational_issues":  operational_issues,
        "financial_issues":    financial_issues,
        "corrective_measures": corrective_measures,
        "urgent_decisions":    urgent_decisions,
        "risk_categories":  ", ".join(risk_cats_final),
        "urgency_score":    urgency_final,
        "completeness_score": comp_score,
        "attachments_receipts": has_receipts,
        "attachments_docs":     has_activity_docs,
        "attachments_note":     attachments_note,
    }

    # Try Google Sheets first, fall back to local JSON
    sub_id = None
    creds_ok = "gsheets_credentials" in st.secrets and "spreadsheet_id" in st.secrets

    if creds_ok:
        try:
            with st.spinner("Submitting…"):
                sh = get_sheet(dict(st.secrets["gsheets_credentials"]), st.secrets["spreadsheet_id"])
                sub_id = append_submission(sh, record, clean_objectives)
        except Exception as e:
            st.markdown(f'<div class="error-box">Could not reach Google Sheets: {e}<br>Saving locally instead.</div>', unsafe_allow_html=True)
            creds_ok = False

    if not creds_ok:
        # Local fallback — save to JSON file
        import os
        sub_id = f"LOCAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        record["submission_id"] = sub_id
        record["submitted_at"]  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record["objectives"]    = clean_objectives

        save_path = "submissions_local.json"
        existing = []
        if os.path.exists(save_path):
            try:
                with open(save_path) as f:
                    existing = json.load(f)
            except:
                pass
        existing.append(record)
        with open(save_path, "w") as f:
            json.dump(existing, f, indent=2, default=str)

        st.markdown(f'<div class="info-box">Saved locally to <code>submissions_local.json</code> (Google Sheets not configured).<br>Submission ID: {sub_id}</div>', unsafe_allow_html=True)

    if sub_id:
        st.session_state.submitted = True
        st.session_state.sub_id = sub_id
        time.sleep(0.5)
        st.rerun()