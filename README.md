# EVOxCharge Analytics Dashboard

Built with Streamlit + PyDeck

## Setup

```bash
pip install -r requirements.txt
streamlit run evox_app.py
```

## Required data files

Place these Excel files in the **same folder** as `evox_app.py`
(or in a `/data` subfolder):

| File | Source |
|------|--------|
| `transactions.xlsx` | Session Logs export |
| `UserDetails.xlsx` | User Profile export |
| `walletTransactions.xlsx` | Transaction Logs export |
| `Station_Profile.xlsx` | Station Profile export |
| `Charge_Point_Information_...xlsx` | Charge Point Info export |
| `Financials.xlsx` | Financials workbook |

## Security — DO NOT commit data files to GitHub

Add `*.xlsx` to your `.gitignore` (already included here).
For deployment, use one of the options below.

## Deployment options

### Option A — Streamlit Community Cloud (recommended for sharing)
1. Push only `evox_app.py`, `requirements.txt`, `.gitignore` to GitHub
2. Upload data files as Streamlit Secrets or use a private Google Sheet
3. Deploy at share.streamlit.io

### Option B — Private GitHub repo + Streamlit Cloud
1. Make the GitHub repo **private**
2. Add all files including data
3. Streamlit Cloud can still deploy from private repos (free tier)

### Option C — Azure / internal hosting
For internal EVOxCharge use with access control.
