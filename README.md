# TCN Daily Report Submission Form

A Streamlit form for TCN directors to submit daily reports directly.
- Password-protected per director
- Dynamic objective rows (add/remove freely)
- Auto-calculates burn rate, achievement %, alert status
- Live completeness score before submission
- Saves to Google Sheets (or local JSON if Sheets not set up)

---

## Quick start (no Google Sheets yet)

If you just want to run and test the form locally before setting up Sheets:

```bash
cd tcn_form
pip install -r requirements.txt
streamlit run app.py
```

Use one of these test passwords:
- `pillar1pass` → Rev. Michael Mutai / Pillar 1
- `pillar2pass` → Jennifer Chemutai / Pillar 2
- `pillar3pass` → Genaldon Cherono / Pillar 3
- `adminpass`   → Admin view

Without Sheets configured, submissions save to `submissions_local.json` in the same folder.

---

## Step-by-step: Connect Google Sheets

### Step 1 — Create the Google Sheet

1. Go to https://sheets.google.com
2. Create a new blank spreadsheet
3. Name it something like **TCN Daily Reports**
4. Copy the Spreadsheet ID from the URL:
   `https://docs.google.com/spreadsheets/d/ >>>THIS PART<<< /edit`

### Step 2 — Create a Google Service Account

A service account is a special Google account your app uses to write to the Sheet automatically.

1. Go to https://console.cloud.google.com
2. Create a new project (or use an existing one) — name it e.g. "TCN Reports"
3. In the left menu: **APIs & Services → Library**
4. Search for **Google Sheets API** → click it → click **Enable**
5. Search for **Google Drive API** → click it → click **Enable**
6. In the left menu: **APIs & Services → Credentials**
7. Click **Create Credentials → Service Account**
8. Fill in a name (e.g. "tcn-form-writer") → click **Create and Continue** → click **Done**
9. Click on the service account you just created
10. Go to the **Keys** tab → **Add Key → Create new key → JSON**
11. A JSON file downloads to your computer — **keep this safe, never share it**

### Step 3 — Share the Sheet with the service account

1. Open the JSON file you downloaded — find the `client_email` field, it looks like:
   `tcn-form-writer@your-project.iam.gserviceaccount.com`
2. Open your Google Sheet
3. Click **Share** (top right)
4. Paste that email address and give it **Editor** access
5. Click **Send**

### Step 4 — Configure secrets.toml

1. Open the file `.streamlit/secrets.toml` in this folder
2. Fill in your `spreadsheet_id`
3. Open the downloaded JSON key file and copy each field into the `[gsheets_credentials]` section

The file should look like:
```toml
spreadsheet_id = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"

[gsheets_credentials]
type = "service_account"
project_id = "tcn-reports-123456"
private_key_id = "abc123..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----\n"
client_email = "tcn-form-writer@tcn-reports-123456.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/tcn-form-writer%40tcn-reports-123456.iam.gserviceaccount.com"
```

5. Run the app: `streamlit run app.py`
6. Submit a test report — two new tabs ("Submissions" and "Objectives") will be created in your Sheet automatically

---

## Customising directors and passwords

Open `app.py` and find the `DIRECTORS` dictionary near the top:

```python
DIRECTORS = {
    "pillar1pass": {
        "name": "Rev. Michael Mutai",
        "pillar": "Pillar 1",
        "pillar_code": "P1",
        "objectives": ["NGE-103", "NGE-104"],
    },
    ...
}
```

- Change `"pillar1pass"` to whatever password you want that director to use
- Update `name`, `pillar`, `objectives` to match your M&E framework
- The `objectives` list pre-fills the objective code fields — directors can still add/remove rows

**Important:** After changing passwords, tell directors their new password. Old passwords immediately stop working.

---

## Hosting so directors can access it online (free)

### Option A — Streamlit Community Cloud (recommended)

1. Push your code to a GitHub repository (make sure `secrets.toml` is in `.gitignore`)
2. Go to https://share.streamlit.io
3. Sign in with GitHub
4. Click **New app** → select your repo and `app.py`
5. Under **Advanced settings → Secrets**, paste the contents of your `secrets.toml`
6. Click **Deploy**

Your form will be live at a URL like `https://yourname-tcn-form-abc123.streamlit.app`
Share this URL with your directors. That's it.

### Option B — Run on your own laptop and share via ngrok (quick test)

```bash
# Install ngrok from https://ngrok.com (free tier)
streamlit run app.py &
ngrok http 8501
```

Ngrok gives you a public URL that works while your laptop is on.

---

## What data gets captured

### Submissions tab (one row per report)
| Column | What it is |
|--------|-----------|
| submission_id | Unique ID e.g. SUB-20260316-170423 |
| submitted_at | Exact timestamp |
| pillar | Pillar number |
| director | Director name |
| reporting_date | Date the report covers |
| objectives_json | All objectives as JSON (also split into Objectives tab) |
| today_spend_kes | Today's expenditure |
| mtd_spend_kes | Month-to-date expenditure |
| monthly_budget_kes | Approved monthly budget |
| burn_rate_pct | Auto-calculated burn rate |
| alert_status | Green / Amber / Red |
| key_activities | Narrative |
| operational_issues | Narrative |
| financial_issues | Narrative |
| corrective_measures | Narrative |
| urgent_decisions | Narrative |
| risk_categories | Auto-detected: Financial, Communication, etc. |
| urgency_score | 1=Info, 2=Monitor, 3=Immediate |
| completeness_score | % of required fields filled |

### Objectives tab (one row per objective)
| Column | What it is |
|--------|-----------|
| submission_id | Links back to Submissions tab |
| pillar | Pillar |
| reporting_date | Date |
| obj_code | e.g. KB-201 |
| daily_target | Numeric target |
| daily_achievement | Numeric achievement |
| pct_achievement | Auto-calculated % |
| status | On Track / Behind / Ahead |

---

## Files
```
tcn_form/
├── app.py                     ← The Streamlit form
├── requirements.txt           ← Python packages
├── README.md                  ← This file
├── .streamlit/
│   └── secrets.toml           ← Your credentials (never share this)
└── submissions_local.json     ← Created automatically if Sheets not connected
```

---

## Security notes

- Passwords are stored in plain text in `app.py` — this is fine for a small team internal tool
- Never commit `secrets.toml` to GitHub — it contains your Google credentials
- The form is as secure as whoever has the URL + password
- For higher security needs, consider Streamlit's built-in authentication (requires paid plan) or add a `.streamlit/config.toml` with `[server] headless = true`
