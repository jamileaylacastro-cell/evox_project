import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import io
from pathlib import Path

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="Project ChargeIQ Analytics", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

# ── BRAND PALETTE ────────────────────────────────────────────────────────────
# Lime #BEFF6C · Cream #FFF4EC · White #FFFFFF · Black #000000 (accent)
st.markdown("""
<style>
.stApp{background:#FFF4EC}
section[data-testid="stSidebar"]{background:#000000}
section[data-testid="stSidebar"] *{color:#FFF4EC!important}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{color:#BEFF6C!important}
.kpi-card{background:#fff;border-radius:6px;padding:14px 16px;
  border-left:4px solid #000000;box-shadow:0 1px 6px rgba(0,0,0,.07);height:100%}
.kpi-label{font-size:10px;color:#5C574D;text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:3px}
.kpi-value{font-size:22px;font-weight:700;color:#000000;line-height:1}
.kpi-trend{font-size:10px;margin-top:3px}
.up{color:#4F7A1E}.dn{color:#C1443E}.warn{color:#A8710A}
.sec-hdr{background:#000000;color:#BEFF6C;padding:7px 14px;border-radius:4px;
  font-size:12px;font-weight:700;margin:16px 0 8px 0}
.row-hdr{font-size:10px;font-weight:700;color:#5C574D;text-transform:uppercase;
  letter-spacing:.06em;margin:10px 0 6px 2px}
.formula-box{background:#FFFFFF;border:1px solid #EAE0D0;border-radius:6px;
  padding:10px 14px;font-family:monospace;font-size:11px;
  color:#000000;white-space:pre-line;line-height:1.7}

/* ── Kill Streamlit's default red accents; guarantee readable text on
     every light/lime background, even inside the black sidebar ──────── */

/* Multiselect selected pills — lime bg, black text, everywhere */
span[data-baseweb="tag"], div[data-baseweb="tag"]{
  background-color:#BEFF6C!important; border-color:#000000!important;
}
span[data-baseweb="tag"] *, div[data-baseweb="tag"] *{ color:#000000!important; }
span[data-baseweb="tag"] svg, div[data-baseweb="tag"] svg{ fill:#000000!important; }

/* Select / multiselect closed box — white bg, black text, no red focus ring */
div[data-baseweb="select"] > div{
  border-color:#EAE0D0!important; background:#FFFFFF!important;
  outline:none!important;
}
div[data-baseweb="select"] > div *{ color:#000000!important; }
div[data-baseweb="select"]:focus-within > div,
div[data-baseweb="select"] > div:focus,
div[data-baseweb="select"] > div:focus-within{
  border-color:#BEFF6C!important; box-shadow:0 0 0 1px #BEFF6C!important;
  background:#FFFFFF!important; outline:none!important;
}
div[data-baseweb="select"] input{ outline:none!important; box-shadow:none!important; }
div[data-baseweb="select"] input::selection{ background:#BEFF6C!important; color:#000000!important; }

/* Dropdown option list — white bg by default, lime on hover/selected,
   text always black regardless of sidebar's cream override */
div[data-baseweb="popover"], div[data-baseweb="menu"]{ background:#FFFFFF!important; }
div[data-baseweb="popover"] *, div[data-baseweb="menu"] *{ color:#000000!important; }
div[data-baseweb="popover"] li, div[data-baseweb="menu"] li{ background:#FFFFFF!important; }
div[data-baseweb="popover"] li:hover, div[data-baseweb="menu"] li:hover,
div[data-baseweb="popover"] li[aria-selected="true"],
div[data-baseweb="menu"] li[aria-selected="true"]{
  background-color:#BEFF6C!important;
}
div[data-baseweb="popover"] li:hover *, div[data-baseweb="menu"] li:hover *,
div[data-baseweb="popover"] li[aria-selected="true"] *,
div[data-baseweb="menu"] li[aria-selected="true"] *{ color:#000000!important; }

/* Radio buttons — style only the native input dot, not the row wrapper */
input[type="checkbox"], input[type="radio"]{ accent-color:#BEFF6C!important; }

/* Slider — thumb only; no track/rail background override (was painting
   a much wider box than intended, covering the min/max value labels) */
div[data-testid="stSlider"] div[role="slider"]{
  background-color:#000000!important; border-color:#000000!important;
}

/* Buttons — cover the inner text node too, not just the button element,
   since Streamlit wraps button text in its own <p>/<span> that the
   sidebar's blanket cream-text rule matches directly and wins by
   default inheritance rules unless explicitly overridden here */
button[kind="primary"]{ background-color:#BEFF6C!important; border-color:#000000!important; }
button[kind="primary"] *{ color:#000000!important; }
button[kind="secondary"]{ border-color:#000000!important; background:#FFFFFF!important; }
button[kind="secondary"] *{ color:#000000!important; }

/* File uploader — light bg, so force black text regardless of container */
div[data-testid="stFileUploader"] section{
  background:#FFFFFF!important; border:1px dashed #000000!important;
}
div[data-testid="stFileUploader"] section *{ color:#000000!important; }
div[data-testid="stFileUploader"] section small{ color:#5C574D!important; }
div[data-testid="stFileUploaderDropzoneInstructions"] *{ color:#000000!important; }
div[data-testid="stFileUploader"] button{
  background:#BEFF6C!important; color:#000000!important; border-color:#000000!important;
}
div[data-testid="stFileUploader"] button *{ color:#000000!important; }

/* ── Sidebar-scoped overrides — higher specificity than the blanket
     cream-text rule above, so anything sitting on a light/white
     background inside the black sidebar still reads in black ────────── */
section[data-testid="stSidebar"] div[data-baseweb="select"] *{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] input{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-baseweb="popover"] *,
section[data-testid="stSidebar"] div[data-baseweb="menu"] *{ color:#000000!important; }
section[data-testid="stSidebar"] span[data-baseweb="tag"] *,
section[data-testid="stSidebar"] div[data-baseweb="tag"] *{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] section *{ color:#000000!important; }
section[data-testid="stSidebar"] button[kind="primary"] *{ color:#000000!important; }
section[data-testid="stSidebar"] button[kind="secondary"] *{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-baseweb="select"] input::selection{
  background:#BEFF6C!important; color:#000000!important;
}

/* ── FINAL PASS — target Streamlit's own stable widget wrappers directly.
     These data-testid values are assigned by Streamlit itself (not the
     BaseWeb internals, which can nest differently across versions), so
     this is the most reliable way to guarantee black text survives on
     every light-background widget inside the black sidebar. Placed last
     so it also wins any same-specificity source-order tie. ─────────── */
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] *{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] *{ color:#000000!important; }
section[data-testid="stSidebar"] div[data-testid="stSelectbox"] label,
section[data-testid="stSidebar"] div[data-testid="stMultiSelect"] label{ color:#FFF4EC!important; }
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
div[data-testid="stMultiSelect"] div[data-baseweb="select"] > div{
  background:#FFFFFF!important;
}
</style>
""", unsafe_allow_html=True)

# ── DATA SOURCE CONFIG ──────────────────────────────────────────────────────
BASE = Path(__file__).parent

FILE_LABELS = {
    "transactions":    "Session Logs (transactions.xlsx)",
    "charge_points":   "Charge Point Information (.xlsx)",
    "station_profile": "Station Profile (.xlsx)",
    "user_details":    "User Details (.xlsx)",
    "wallet_txn":      "Wallet Transactions (.xlsx)",
    "financials":      "Financials Workbook (.xlsx)",
}
FILE_DEFAULTS = {
    "transactions":    "transactions.xlsx",
    "charge_points":   "Charge_Point_Information__Connector_Type__Charger_Type__Capacity__Fees_Rates_.xlsx",
    "station_profile": "Station_Profile.xlsx",
    "user_details":    "UserDetails.xlsx",
    "wallet_txn":      "walletTransactions.xlsx",
    "financials":      "ProjectChargeIQ_Financials.xlsx",
}

def disk_path(filename):
    for candidate in [BASE / filename, BASE / "data" / filename]:
        if candidate.exists():
            return candidate
    return None

bundled_status = {key: disk_path(fname) is not None for key, fname in FILE_DEFAULTS.items()}
all_bundled = all(bundled_status.values())

if "chargeiq_data_ready" not in st.session_state:
    st.session_state.chargeiq_data_ready = False
if "chargeiq_file_bytes" not in st.session_state:
    st.session_state.chargeiq_file_bytes = {}

# ── DATA GATE — request files before the dashboard ever loads ──────────────
if not st.session_state.chargeiq_data_ready:
    col_ico, col_ttl = st.columns([1, 10])
    with col_ico:
        st.markdown("<div style='font-size:34px;text-align:center;margin-top:2px'>⚡</div>",
                    unsafe_allow_html=True)
    with col_ttl:
        st.markdown("<h2 style='margin:0;color:#000000'>Project ChargeIQ</h2>"
                    "<p style='margin:0;color:#5C574D;font-size:12px'>"
                    "Provide your data to begin — upload files below or use the bundled dataset.</p>",
                    unsafe_allow_html=True)
    st.markdown("---")

    if all_bundled:
        st.success("✅ Bundled dataset found alongside the app. You can start immediately, "
                   "or upload replacements for any file below before starting.")
    else:
        found = [FILE_DEFAULTS[k] for k, v in bundled_status.items() if v]
        need  = [FILE_DEFAULTS[k] for k, v in bundled_status.items() if not v]
        if found:
            st.info(f"Found {len(found)}/6 bundled files. Upload the remaining {len(need)} to continue.")
        else:
            st.warning("No bundled data found. Upload all 6 files below to continue.")

    st.markdown("<div class='sec-hdr'>Upload data files</div>", unsafe_allow_html=True)
    up_cols = st.columns(3)
    gate_uploaded = {}
    for i, (key, label) in enumerate(FILE_LABELS.items()):
        with up_cols[i % 3]:
            status = "✅ bundled" if bundled_status[key] else "⚠️ required"
            st.caption(f"{label} — {status}")
            gate_uploaded[key] = st.file_uploader(label, type=["xlsx"],
                                                  key=f"gate_up_{key}", label_visibility="collapsed")

    st.markdown("<br>", unsafe_allow_html=True)
    ready_now = all(
        gate_uploaded.get(k) is not None or bundled_status[k]
        for k in FILE_DEFAULTS
    )

    btn_col1, btn_col2 = st.columns([1, 4])
    with btn_col1:
        clicked = st.button("Load Dashboard →", type="primary", disabled=not ready_now,
                            use_container_width=True)
    with btn_col2:
        if not ready_now:
            st.caption("Upload the remaining required files to enable this button.")

    if clicked:
        resolved = {}
        for key, fname in FILE_DEFAULTS.items():
            up = gate_uploaded.get(key)
            if up is not None:
                resolved[key] = up.getvalue()
            else:
                p = disk_path(fname)
                resolved[key] = p.read_bytes() if p else None
        st.session_state.chargeiq_file_bytes = resolved
        st.session_state.chargeiq_data_ready = True
        st.rerun()

    st.stop()

file_bytes = st.session_state.chargeiq_file_bytes

# ── LOAD ALL DATA ──────────────────────────────────────────────────────────
@st.cache_data
def load_all(tx_b, cp_b, sp_b, ud_b, wt_b, fin_b):
    tx = pd.read_excel(io.BytesIO(tx_b), sheet_name="transactions.csv")
    cp = pd.read_excel(io.BytesIO(cp_b))
    sp = pd.read_excel(io.BytesIO(sp_b))
    ud = pd.read_excel(io.BytesIO(ud_b))
    wt = pd.read_excel(io.BytesIO(wt_b))
    fin = pd.read_excel(io.BytesIO(fin_b), sheet_name=None)

    tx["STARTTIME"] = pd.to_datetime(tx["STARTTIME"], errors="coerce")
    tx["ENDTIME"]   = pd.to_datetime(tx["ENDTIME"],   errors="coerce")
    tx = tx[tx["STARTTIME"].dt.year > 2020].copy()
    tx["DATE"]  = tx["STARTTIME"].dt.date
    tx["MONTH"] = tx["STARTTIME"].dt.to_period("M")
    tx["HOUR"]  = tx["STARTTIME"].dt.hour
    tx["DURATION_MIN"] = (tx["ENDTIME"] - tx["STARTTIME"]).dt.total_seconds() / 60

    sp_coords = sp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE","BUSINESS_START","BUSINESS_END","RATE_PER_KWH"]].first().reset_index()
    cp = cp.merge(sp_coords[["STATIONNAME","BUSINESS_START","BUSINESS_END"]], on="STATIONNAME", how="left")

    cp_coords = cp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE"]].first().reset_index()
    tx = tx.merge(cp_coords, on="STATIONNAME", how="left")

    sp_ll = sp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE"]].first().reset_index()
    missing_ll = tx["LATITUDE"].isna()
    tx_miss = tx[missing_ll].drop(columns=["LATITUDE","LONGITUDE"]).merge(
        sp_ll, on="STATIONNAME", how="left")
    tx.loc[missing_ll, "LATITUDE"]  = tx_miss["LATITUDE"].values
    tx.loc[missing_ll, "LONGITUDE"] = tx_miss["LONGITUDE"].values

    # ── Charge Point Info is stored at the CONNECTOR level, not one row
    #    per charger — a single CHARGER_ID can have 2, 4, 6, or 8 rows
    #    (one per physical plug). Grouping by CHARGER_ID and taking the
    #    first row (the old approach) silently discarded real connectors
    #    and could pick an incomplete row over a complete sibling row.
    #
    #    "Total chargepoints" = rows with a real PLUG_TYPE and
    #    CAPACITY_KW > 0 (regardless of online/offline, so offline counts
    #    can still be reported).
    #    "Available capacity" (the utilization denominator) = the subset
    #    of those that are also NETWORK_STATUS == 'Online', since an
    #    offline connector contributes no real capacity for the period.
    cp_cap = cp[
        cp["PLUG_TYPE"].notna() &
        (cp["PLUG_TYPE"].astype(str).str.strip() != "") &
        cp["CAPACITY_KW"].notna() &
        (cp["CAPACITY_KW"] > 0)
    ].copy()
    cp_excluded_count = len(cp) - len(cp_cap)

    fin_overall = fin["OVERALL"].dropna(subset=["CPO"]).copy()
    fin_overall.columns = ["CPO","Revenue","ActualElecCost","EstElecCost",
                            "ActualRent","EstRent","EstIncome2026"]
    fin_overall = fin_overall[fin_overall["CPO"] != "SUB TOTAL:"].copy()

    opex = fin["ACTUAL OPEX (JAN-JUN)"].copy()
    opex.columns = ["CPO","ElecJan","ElecFeb","ElecMar","ElecApr","ElecMay","ElecJun",
                    "RentJan","RentFeb","RentMar","RentApr","RentMay","RentJun","Remarks"]
    opex = opex[opex["CPO"].notna() & (opex["CPO"] != "CPO") & (opex["CPO"] != "CPO - JV")].copy()

    fees = fin["FEES AND ASSUMPTIONS"].dropna(subset=["CPO"]).copy()
    fees = fees[fees["CPO"] != "CPO - JV"].copy()

    return tx, cp, cp_cap, sp, ud, wt, fin_overall, opex, fees, cp_excluded_count

tx, cp, cp_cap, sp, ud, wt, fin_overall, opex_df, fees_df, cp_excluded_count = load_all(
    file_bytes["transactions"], file_bytes["charge_points"], file_bytes["station_profile"],
    file_bytes["user_details"], file_bytes["wallet_txn"], file_bytes["financials"]

)

# ── SIDEBAR FILTERS ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ Project ChargeIQ")
    if st.button("🔄 Change data source", use_container_width=True):
        st.session_state.chargeiq_data_ready = False
        st.session_state.chargeiq_file_bytes = {}
        st.rerun()
    st.markdown("---")
    st.markdown("### Filters")
    view = st.radio("Dashboard View",
                    ["🏢  Company / Ops", "🏪  Host Partner Site"])
    is_company = view.startswith("🏢")

    all_stations = sorted(tx["STATIONNAME"].dropna().unique().tolist())

    if is_company:
        sel_stations = st.multiselect("Stations", all_stations, default=all_stations[:10])
        if not sel_stations:
            sel_stations = all_stations
    else:
        sel_station  = st.selectbox("Site", all_stations, index=0)
        sel_stations = [sel_station]

    all_months    = sorted(tx["MONTH"].dropna().unique().tolist(), reverse=True)
    month_labels  = [str(m) for m in all_months]
    sel_month_lbl = st.selectbox("Month", month_labels, index=0)
    sel_month     = all_months[month_labels.index(sel_month_lbl)]

    charge_types = st.multiselect("Charge Type",
        tx["CHARGE_TYPE"].dropna().unique().tolist(),
        default=tx["CHARGE_TYPE"].dropna().unique().tolist())

    op_hours = st.slider("Operating hrs / day", 8, 24, 12)
    if st.checkbox("Use 24-hr capacity", value=False):
        op_hours = 24

    # Target utilization: ONE network-wide target in Company/Ops view
    # (applies uniformly when comparing all selected stations), or a
    # target PER STATION in Host Partner view — each station's slider
    # keeps its own remembered value (via its own widget key) when you
    # switch between sites, rather than sharing one global setting.
    #
    # Range and default reflect published EV charger utilization
    # benchmarks, not an assumption of high usage: public charger
    # utilization typically sits at 5–15%, McKinsey cites ~15% as the
    # threshold for economic viability, and even the most mature EU
    # markets peak around 30%. Source: Topal, O. (2025), "A comprehensive
    # analysis of capacity utilization rates of fast-charging stations in
    # shopping malls," Int J Low-Carbon Tech, 20, 1646–1660.
    # https://doi.org/10.1093/ijlct/ctaf100
    if is_company:
        target_util = st.slider("Network Target Utilization %", 1, 40, 15,
                                key="target_network")
    else:
        station_key = sel_stations[0]
        target_util = st.slider(
            f"Target Utilization % — {station_key[:22]}", 1, 40, 15,
            key=f"target_station_{station_key}")
    st.caption("📚 Range reflects published benchmarks: public EV chargers "
              "typically run 5–15% utilization; ~15% is the threshold "
              "commonly cited for economic viability ([source](https://doi.org/10.1093/ijlct/ctaf100)).")

    st.markdown("---")
    days_in_month = tx[tx["MONTH"] == sel_month]["DATE"].nunique()
    n_uploaded = sum(1 for k in FILE_DEFAULTS if st.session_state.get(f"gate_up_{k}") is not None)
    src_label = "Bundled data" if n_uploaded == 0 else f"{n_uploaded}/6 files uploaded"
    st.markdown(f"<small style='color:#FFF4EC'>Period: **{sel_month}**<br>"
                f"Active days: **{days_in_month}**<br>"
                f"Source: {src_label}</small>",
                unsafe_allow_html=True)

# ── FILTER ─────────────────────────────────────────────────────────────────
days = max(days_in_month, 1)

df = tx[
    (tx["STATIONNAME"].isin(sel_stations)) &
    (tx["MONTH"] == sel_month) &
    (tx["CHARGE_TYPE"].isin(charge_types)) &
    (~tx["ISERROR"].astype(bool))
].copy()

df_all = tx[
    (tx["STATIONNAME"].isin(sel_stations)) &
    (tx["MONTH"] == sel_month)
].copy()

prior_month = sel_month - 1
df_prior = tx[
    (tx["STATIONNAME"].isin(sel_stations)) &
    (tx["MONTH"] == prior_month) &
    (tx["CHARGE_TYPE"].isin(charge_types)) &
    (~tx["ISERROR"].astype(bool))
].copy()

# ── CORE METRICS ─────────────────────────────────────────────────────────────
# cp_sel = all data-quality-valid connectors at the selected station(s),
# regardless of online/offline (used for total counts + reliability KPIs)
cp_sel = cp_cap[cp_cap["STATIONNAME"].isin(sel_stations)]
# Only ONLINE connectors contribute real, usable capacity for the period
cp_sel_online = cp_sel[cp_sel["NETWORK_STATUS"] == "Online"]
total_avail_kwh = cp_sel_online["CAPACITY_KW"].sum() * op_hours * days
actual_kwh      = df["ENERGY_KWH"].sum()
prior_kwh       = df_prior["ENERGY_KWH"].sum()
net_util        = (actual_kwh / total_avail_kwh * 100) if total_avail_kwh > 0 else 0
util_gap        = net_util - target_util

total_rev  = df["TOTALAMOUNT"].sum()
prior_rev  = df_prior["TOTALAMOUNT"].sum()
mom_rev    = (total_rev - prior_rev) / prior_rev * 100 if prior_rev > 0 else 0
total_sess = len(df)
prior_sess = len(df_prior)
mom_sess   = (total_sess - prior_sess) / prior_sess * 100 if prior_sess > 0 else 0
error_rate = (df_all["ISERROR"].astype(bool).sum() / len(df_all) * 100) if len(df_all) > 0 else 0
total_cps   = len(cp_sel)
online_cps  = len(cp_sel_online)
offline_cps = len(cp_sel[cp_sel["NETWORK_STATUS"] == "Offline"])
faulty_cps  = len(cp_sel[cp_sel["CONNECTOR_STATUS"] == "Faulty"])
uptime_pct  = (online_cps / total_cps * 100) if total_cps > 0 else 0
avg_dur     = df["DURATION_MIN"].mean() if len(df) else 0

# Peak hour
if len(df):
    hourly_kwh = df.groupby("HOUR")["ENERGY_KWH"].sum()
    peak_hour  = int(hourly_kwh.idxmax()) if len(hourly_kwh) else 0
    peak_share = (hourly_kwh.max() / hourly_kwh.sum() * 100) if hourly_kwh.sum() > 0 else 0
else:
    peak_hour, peak_share = 0, 0

# Revenue detail (safe column lookups — some exports may not include every fee column)
avg_rev_session = (total_rev / total_sess) if total_sess > 0 else 0
overstay_rev = df["OVERSTAYFEE"].sum() if "OVERSTAYFEE" in df.columns else None

# Refunds (from wallet transactions, scoped to the selected month where possible)
if "TRANSACTION_DATE" in wt.columns:
    wt2 = wt.copy()
    wt2["TRANSACTION_DATE"] = pd.to_datetime(wt2["TRANSACTION_DATE"], errors="coerce")
    wt_period = wt2[wt2["TRANSACTION_DATE"].dt.to_period("M") == sel_month]
else:
    wt_period = wt
refund_count = wt_period["REFUNDEDTRANSACTIONNO"].notna().sum() if "REFUNDEDTRANSACTIONNO" in wt_period.columns else 0
refund_total = len(wt_period)
refund_rate  = (refund_count / refund_total * 100) if refund_total > 0 else 0

# Customer metrics — scoped to selected station(s) + month
unique_customers  = df["USERID"].nunique() if "USERID" in df.columns else 0
sessions_per_user = df.groupby("USERID").size() if "USERID" in df.columns and len(df) else pd.Series(dtype=int)
repeat_customers  = (sessions_per_user > 1).sum() if len(sessions_per_user) else 0
repeat_rate        = (repeat_customers / unique_customers * 100) if unique_customers > 0 else 0
avg_rev_per_cust    = (total_rev / unique_customers) if unique_customers > 0 else 0

active = len(ud[ud["ACCOUNT_STATUS"]=="Active"]) if "ACCOUNT_STATUS" in ud.columns else len(ud)
avg_wallet = ud["WALLET_BALANCE"].mean() if "WALLET_BALANCE" in ud.columns else 0

# ── HEADER ──────────────────────────────────────────────────────────────────
col_ico, col_ttl = st.columns([1, 12])
with col_ico:
    st.markdown("<div style='font-size:34px;text-align:center;margin-top:2px'>⚡</div>",
                unsafe_allow_html=True)
with col_ttl:
    title = "Network Dashboard" if is_company else f"Site Dashboard — {sel_stations[0]}"
    st.markdown(f"<h2 style='margin:0;color:#000000'>Project ChargeIQ — {title}</h2>"
                f"<p style='margin:0;color:#5C574D;font-size:11px'>"
                f"{sel_month} · {days} active days · Op hrs: {op_hours}h/day</p>",
                unsafe_allow_html=True)
st.markdown("---")

# ── STATION PROFILE — Host Partner Site view only ───────────────────────────
if not is_company:
    import re as _re
    _station = sel_stations[0]

    _sp_row = sp[sp["STATIONNAME"] == _station]

    # Region/City — Station Profile has no dedicated field, so it's derived
    # from ADDRESS (last two comma-separated segments, zip code stripped).
    def _region_city(addr):
        if not isinstance(addr, str) or not addr.strip():
            return "—"
        parts = [p.strip() for p in addr.split(",")]
        if len(parts) >= 2:
            tail = parts[-1]
            tail = _re.sub(r"\d{4,}$", "", tail).strip()
            return f"{parts[-2]}, {tail}" if tail else parts[-2]
        return addr

    region_city = _region_city(_sp_row["ADDRESS"].iloc[0]) if len(_sp_row) and "ADDRESS" in _sp_row.columns else "—"

    # Status — from Station Profile's STATION_ACTIVE flag
    is_active = bool(_sp_row["STATION_ACTIVE"].iloc[0]) if len(_sp_row) and "STATION_ACTIVE" in _sp_row.columns else True

    # First / Last year of operation — derived from actual session history,
    # since Station Profile has no explicit launch/decommission date field
    _station_sessions = tx[tx["STATIONNAME"] == _station]
    if len(_station_sessions):
        first_year = int(_station_sessions["STARTTIME"].dt.year.min())
        last_year  = int(_station_sessions["STARTTIME"].dt.year.max())
    else:
        first_year, last_year = None, None
    last_op_display = "-" if is_active else (str(last_year) if last_year else "-")

    # Operating hours
    if len(_sp_row) and "BUSINESS_START" in _sp_row.columns and "BUSINESS_END" in _sp_row.columns:
        b_start = str(_sp_row["BUSINESS_START"].iloc[0])[:5]
        b_end   = str(_sp_row["BUSINESS_END"].iloc[0])[:5]
        op_hrs_display = "24 Hours" if (b_start == "00:00" and b_end in ("23:59","24:00")) else f"{b_start} – {b_end}"
    else:
        op_hrs_display = "—"

    # Charge points + capacity — from the corrected connector-level cp_cap
    _station_cps = cp_cap[cp_cap["STATIONNAME"] == _station]
    n_charge_points = len(_station_cps)
    total_capacity  = _station_cps["CAPACITY_KW"].sum()

    status_color = "#4F7A1E" if is_active else "#C1443E"
    status_label = "🟢 Active" if is_active else "🔴 Inactive"

    st.markdown(f"""
    <div style='background:#fff;border-radius:8px;padding:16px 20px;
                border-left:4px solid #000000;box-shadow:0 1px 6px rgba(0,0,0,.07);
                margin-bottom:16px'>
      <div style='font-size:14px;font-weight:700;color:#000;margin-bottom:12px'>
        🏪 Station Profile — {_station}
      </div>
      <div style='display:grid;grid-template-columns:repeat(4,1fr);gap:14px 24px'>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Station Name</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{_station}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Region / City</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{region_city}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Status</div>
          <div style='font-size:13px;color:{status_color};font-weight:600'>{status_label}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Operating Hours</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{op_hrs_display}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Year of First Operation</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{first_year if first_year else '—'}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Year of Last Operation</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{last_op_display}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Number of Charge Points</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{n_charge_points}</div>
        </div>
        <div>
          <div style='font-size:9px;color:#5C574D;text-transform:uppercase;letter-spacing:.05em'>Charger Capacity</div>
          <div style='font-size:13px;color:#000;font-weight:600'>{total_capacity:,.1f} kW</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── FORMULA EXPANDER ────────────────────────────────────────────────────────
with st.expander("📐 Energy-Based Utilization Formula", expanded=False):
    st.markdown(f"""<div class='formula-box'>
Utilization Rate (%) = Σ Actual kWh Charged ÷ Total Available Capacity × 100

Σ Actual kWh Charged     = {actual_kwh:,.1f} kWh  (ENERGY_KWH where ISERROR=0)
Total Available Capacity = Online Connectors × CAPACITY_KW × {op_hours} hrs/day × {days} days
                         = {online_cps} online connectors × {op_hours} hrs × {days} days
                         = {total_avail_kwh:,.0f} kWh
Network Utilization      = {actual_kwh:,.1f} ÷ {total_avail_kwh:,.0f} × 100 = {net_util:.1f}%
Gap vs {target_util}% target   = {util_gap:+.1f} pp
</div>""", unsafe_allow_html=True)
    st.caption(
        f"📋 **Connector data quality:** {len(cp):,} raw rows in Charge Point Information → "
        f"{len(cp_cap):,} valid (has PLUG_TYPE and CAPACITY_KW > 0) → "
        f"{cp_excluded_count:,} excluded for missing/zero capacity data. "
        f"Of the valid connectors, {total_cps:,} belong to your current selection, "
        f"of which {online_cps:,} are Online and count toward available capacity "
        f"({offline_cps:,} Offline, {faulty_cps:,} Faulty)."
    )

# ── KPI HELPER ────────────────────────────────────────────────────────────────
def kpi(col, label, value, trend, tclass="up", border="#000000"):
    col.markdown(
        f"<div class='kpi-card' style='border-left-color:{border}'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-trend {tclass}'>{trend}</div></div>",
        unsafe_allow_html=True)

st.markdown("<div class='sec-hdr'>Key Performance Indicators</div>", unsafe_allow_html=True)

# ── ROW 1: UTILIZATION ───────────────────────────────────────────────────────
st.markdown("<div class='row-hdr'>Utilization</div>", unsafe_allow_html=True)
r1c1,r1c2,r1c3,r1c4 = st.columns(4)
gap_cls = "up" if util_gap >= 0 else ("warn" if util_gap >= -10 else "dn")
kpi(r1c1,"Network Utilization",f"{net_util:.1f}%",
    f"{'▲' if util_gap>=0 else '▼'} {util_gap:+.1f} pp vs {target_util}% target",
    gap_cls, "#BEFF6C" if util_gap>=0 else "#C1443E")
kpi(r1c2,"Actual kWh Charged",f"{actual_kwh:,.0f}",
    f"{'▲' if actual_kwh>prior_kwh else '▼'} vs prior month",
    "up" if actual_kwh>=prior_kwh else "dn","#BEFF6C")
kpi(r1c3,"Avg Session Duration",f"{avg_dur:.0f} min",
    f"Peak hour: {peak_hour:02d}:00 ({peak_share:.0f}% of daily kWh)",
    "up","#BEFF6C")
kpi(r1c4,"Total Sessions",f"{total_sess:,}",
    f"{'▲' if mom_sess>=0 else '▼'} {abs(mom_sess):.1f}% MoM",
    "up" if mom_sess>=0 else "dn","#BEFF6C")

# ── ROW 2: RELIABILITY ───────────────────────────────────────────────────────
st.markdown("<div class='row-hdr'>Reliability</div>", unsafe_allow_html=True)
r2c1,r2c2,r2c3,r2c4 = st.columns(4)
kpi(r2c1,"Charger Uptime",f"{uptime_pct:.1f}%",
    f"{online_cps}/{total_cps} connectors online",
    "up" if uptime_pct>=90 else ("warn" if uptime_pct>=75 else "dn"),
    "#BEFF6C" if uptime_pct>=90 else ("#A8710A" if uptime_pct>=75 else "#C1443E"))
kpi(r2c2,"Chargers Offline",f"{offline_cps}",
    f"of {total_cps} total connectors",
    "up" if offline_cps==0 else "dn",
    "#BEFF6C" if offline_cps==0 else "#C1443E")
kpi(r2c3,"Faulty Connectors",f"{faulty_cps}",
    "Flagged in Charge Point Info",
    "up" if faulty_cps==0 else "dn",
    "#BEFF6C" if faulty_cps==0 else "#C1443E")
kpi(r2c4,"Error Session Rate",f"{error_rate:.1f}%",
    "▼ needs attention" if error_rate>5 else "Within threshold",
    "dn" if error_rate>5 else "up","#C1443E" if error_rate>5 else "#BEFF6C")

# ── ROW 3: REVENUE ───────────────────────────────────────────────────────────
st.markdown("<div class='row-hdr'>Revenue</div>", unsafe_allow_html=True)
r3c1,r3c2,r3c3,r3c4 = st.columns(4)
kpi(r3c1,"Total Revenue",f"₱{total_rev:,.0f}",
    f"{'▲' if mom_rev>=0 else '▼'} {abs(mom_rev):.1f}% MoM",
    "up" if mom_rev>=0 else "dn","#BEFF6C")
kpi(r3c2,"Avg Revenue / Session",f"₱{avg_rev_session:,.0f}",
    f"{total_sess:,} sessions this period",
    "up","#BEFF6C")
kpi(r3c3,"Refund Rate",f"{refund_rate:.1f}%",
    f"{refund_count:,} of {refund_total:,} wallet txns",
    "dn" if refund_rate>3 else "up","#C1443E" if refund_rate>3 else "#BEFF6C")
if overstay_rev is not None:
    kpi(r3c4,"Overstay Fee Revenue",f"₱{overstay_rev:,.0f}",
        "Parking demand signal","up","#BEFF6C")
else:
    kpi(r3c4,"Overstay Fee Revenue","—",
        "OVERSTAYFEE column not found","warn","#A8710A")

# ── ROW 4: CUSTOMER ──────────────────────────────────────────────────────────
st.markdown("<div class='row-hdr'>Customer</div>", unsafe_allow_html=True)
r4c1,r4c2,r4c3,r4c4 = st.columns(4)
if is_company:
    kpi(r4c1,"Registered Users",f"{len(ud):,}",f"{active:,} active accounts","up","#000000")
    kpi(r4c2,"Active Users (period)",f"{unique_customers:,}",
        "Distinct users this month","up","#BEFF6C")
    kpi(r4c3,"Repeat Customer Rate",f"{repeat_rate:.1f}%",
        f"{repeat_customers:,} of {unique_customers:,} customers","up","#BEFF6C")
    kpi(r4c4,"Avg Wallet Balance",f"₱{avg_wallet:,.0f}","Across active users","up","#000000")
else:
    kpi(r4c1,"Unique Customers",f"{unique_customers:,}","At this site this month","up","#000000")
    kpi(r4c2,"Repeat Customer Rate",f"{repeat_rate:.1f}%",
        f"{repeat_customers:,} of {unique_customers:,} customers","up","#BEFF6C")
    kpi(r4c3,"Avg Revenue / Customer",f"₱{avg_rev_per_cust:,.0f}","This site, this month","up","#BEFF6C")
    top_pm = df_all["PAYMENT_METHOD"].value_counts().index[0] if len(df_all) and "PAYMENT_METHOD" in df_all.columns else "—"
    kpi(r4c4,"Top Payment Method",top_pm,"Most used at this site","up","#000000")

st.markdown("<br>", unsafe_allow_html=True)

# ── MAP DATA (built for both views — the Site Performance table below needs
#    it regardless of whether the map itself is shown) ─────────────────────
station_rows = []
for sname in sel_stations:
    s_df  = df[df["STATIONNAME"] == sname]
    s_cp  = cp_cap[cp_cap["STATIONNAME"] == sname]
    s_all = df_all[df_all["STATIONNAME"] == sname]
    s_kwh  = s_df["ENERGY_KWH"].sum()
    s_cap  = s_cp[s_cp["NETWORK_STATUS"]=="Online"]["CAPACITY_KW"].sum()
    s_avail = s_cap * op_hours * days
    s_util  = round(s_kwh / s_avail * 100, 1) if s_avail > 0 else 0
    s_rev   = s_df["TOTALAMOUNT"].sum()
    s_err   = round(s_all["ISERROR"].astype(bool).sum() / max(len(s_all),1)*100, 1)
    lat = s_df["LATITUDE"].dropna().mean()
    lon = s_df["LONGITUDE"].dropna().mean()
    if pd.isna(lat):
        ll = s_cp[["LATITUDE","LONGITUDE"]].dropna()
        if len(ll): lat, lon = ll.iloc[0]["LATITUDE"], ll.iloc[0]["LONGITUDE"]
    if pd.isna(lat): continue
    color = [143,203,62,220] if s_util>=target_util else ([168,113,10,210] if s_util>=target_util*0.7 else [193,68,62,220])
    station_rows.append({
        "STATIONNAME": sname, "LATITUDE": lat, "LONGITUDE": lon,
        "util_pct": s_util, "energy_kwh": round(s_kwh,1),
        "avail_kwh": round(s_avail,1), "revenue": round(s_rev,0),
        "sessions": len(s_df), "error_rate": s_err,
        "color": color,
        "radius": max(int(s_kwh/max(actual_kwh,1)*1200)+150, 120),
        "weight": round(s_kwh/max(actual_kwh,1), 3),
    })
map_df = pd.DataFrame(station_rows)

# ── GEOGRAPHIC HEATMAP — Company / Ops view only ────────────────────────────
if is_company:
    st.markdown("<div class='sec-hdr'>📍 Geographic Heatmap — Utilization by Location</div>",
                unsafe_allow_html=True)

    if map_df["LATITUDE"].isna().all() or len(map_df) == 0:
        st.warning("No station coordinates found for the current selection. "
                  "Check that LATITUDE/LONGITUDE are populated in Station Profile "
                  "or Charge Point Information for these stations.")
    else:
        map_col, bar_col = st.columns([3, 2])

        with map_col:
            map_mode = st.radio("Map layer",
                ["🔥 Heatmap (Utilization)","🔵 Bubbles (Utilization %)"],
                horizontal=True)
            center_lat = map_df["LATITUDE"].mean()
            center_lon = map_df["LONGITUDE"].mean()
            view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon,
                                       zoom=9.5, pitch=35 if "Bubble" in map_mode else 0)
            if "Heatmap" in map_mode:
                pts = []
                for _, r in map_df.iterrows():
                    w = max(r["util_pct"] / 100, 0.05)
                    n = max(1, int(w*100))
                    for _ in range(n):
                        pts.append({"lat": r["LATITUDE"]+np.random.uniform(-.004,.004),
                                     "lon": r["LONGITUDE"]+np.random.uniform(-.004,.004)})
                layer  = pdk.Layer("HeatmapLayer", data=pd.DataFrame(pts),
                    get_position=["lon","lat"], aggregation="SUM",
                    opacity=0.75, threshold=0.03,
                    color_range=[[193,68,62,170],[168,113,10,190],[190,255,108,200],
                                 [143,203,62,220],[79,122,30,240]])
                layers = [layer]
                tooltip = None
            else:
                layer  = pdk.Layer("ScatterplotLayer", data=map_df,
                    get_position=["LONGITUDE","LATITUDE"],
                    get_fill_color="color", get_radius="radius",
                    radius_min_pixels=6, radius_max_pixels=90, pickable=True)
                labels = pdk.Layer("TextLayer", data=map_df,
                    get_position=["LONGITUDE","LATITUDE"],
                    get_text="STATIONNAME", get_size=12,
                    get_color=[0,0,0,230], get_pixel_offset=[0,-24], billboard=True)
                layers  = [layer, labels]
                tooltip = {"html":"""<div style='background:#000000;padding:10px 14px;
                  border-radius:6px;color:#FFF4EC;font-size:12px;min-width:180px'>
                  <b style='color:#BEFF6C'>⚡ {STATIONNAME}</b><hr style='border-color:#BEFF6C;margin:5px 0'>
                  Utilization: <b>{util_pct}%</b><br>kWh actual: <b>{energy_kwh}</b><br>
                  Sessions: <b>{sessions}</b><br>Revenue: <b>₱{revenue}</b><br>
                  Error rate: <b>{error_rate}%</b></div>"""}

            # Free CARTO basemap — no Mapbox token required, unlike mapbox:// styles
            deck = pdk.Deck(
                layers=layers, initial_view_state=view_state,
                map_provider="carto", map_style="light",
                tooltip=tooltip,
            )
            st.pydeck_chart(deck, use_container_width=True)
            l1,l2,l3 = st.columns(3)
            if "Heatmap" in map_mode:
                l1.markdown("🟩 High utilization"); l2.markdown("🟧 Near target"); l3.markdown("🟥 Low utilization")
            else:
                l1.markdown("🟩 ≥ Target"); l2.markdown("🟧 Near target"); l3.markdown("🟥 Below target")

        with bar_col:
            n_total = len(map_df)
            title_suffix = f" (Top 10 of {n_total})" if n_total > 10 else ""
            st.markdown(f"**Utilization by Station vs {target_util}% target**{title_suffix}")
            for _, r in map_df.sort_values("util_pct", ascending=False).head(10).iterrows():
                u = r["util_pct"]; g = u - target_util
                bc = "#BEFF6C" if u>=target_util else ("#A8710A" if u>=target_util*0.7 else "#C1443E")
                gc = "#4F7A1E" if g>=0 else "#C1443E"
                st.markdown(
                    f"<div style='margin-bottom:9px'>"
                    f"<div style='display:flex;justify-content:space-between;font-size:11px;"
                    f"color:#000000;margin-bottom:2px'>"
                    f"<b>{r['STATIONNAME'][:30]}</b>"
                    f"<span style='color:{gc}'>{'▲' if g>=0 else '▼'}{abs(g):.1f}pp</span></div>"
                    f"<div style='background:#EAE0D0;border-radius:2px;height:12px;overflow:hidden'>"
                    f"<div style='width:{min(u,100)}%;height:100%;background:{bc};border-radius:2px'></div></div>"
                    f"<div style='display:flex;justify-content:space-between;font-size:9px;"
                    f"color:#5C574D;margin-top:1px'>"
                    f"<span>{r['energy_kwh']:,.0f} kWh</span><b>{u}%</b></div></div>",
                    unsafe_allow_html=True)

# ── CHARTS ──────────────────────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Session & Energy Analysis</div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
with c1:
    st.markdown("**Sessions by Hour of Day**")
    h = df.groupby("HOUR").size().reset_index(name="Sessions")
    if len(h): st.bar_chart(h.set_index("HOUR"), color="#BEFF6C", height=200)
with c2:
    st.markdown("**Energy (kWh) by Charge Type**")
    ct = df.groupby("CHARGE_TYPE")["ENERGY_KWH"].sum().reset_index()
    ct.columns = ["Charge Type","kWh"]
    if len(ct): st.bar_chart(ct.set_index("Charge Type"), color="#BEFF6C", height=200)
with c3:
    st.markdown("**Payment Method Mix**")
    pm = df_all.groupby("PAYMENT_METHOD").size().reset_index(name="Count")
    if len(pm): st.bar_chart(pm.set_index("PAYMENT_METHOD"), color="#000000", height=200)

# ── SITE PERFORMANCE TABLE ───────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Site Performance — Energy Utilization vs Capacity</div>",
            unsafe_allow_html=True)
if len(map_df):
    tbl = map_df[["STATIONNAME","util_pct","energy_kwh","avail_kwh",
                   "sessions","revenue","error_rate"]].copy()
    tbl["gap_pp"] = (tbl["util_pct"] - target_util).round(1)
    tbl["action"] = tbl["util_pct"].apply(
        lambda u: "✅ Expand" if u>=target_util
        else ("🟡 Monitor" if u>=target_util*0.7
        else ("⚠️ Optimize" if u>=target_util*0.4 else "🔴 Review")))
    tbl = tbl.rename(columns={
        "STATIONNAME":"Station","util_pct":"Util %","energy_kwh":"kWh Actual",
        "avail_kwh":"kWh Available","sessions":"Sessions",
        "revenue":"Revenue (₱)","error_rate":"Error %",
        "gap_pp":"Gap (pp)","action":"Action"
    }).sort_values("Util %", ascending=False)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ── FINANCIALS (CPO breakdown table — network-wide, Company view only) ──────
if is_company:
    st.markdown("<div class='sec-hdr'>💰 Financials — Revenue & Operating Costs by CPO (Jan–Jun 2026)</div>",
                unsafe_allow_html=True)
    fd = fin_overall[["CPO","Revenue","ActualElecCost","ActualRent","EstIncome2026"]].copy()
    fd.columns = ["CPO / Station","Revenue (₱)","Elec Cost (₱)","Rent/Share (₱)","Est. Income 2026 (₱)"]
    for col in fd.columns[1:]:
        fd[col] = fd[col].apply(lambda x: f"₱{x:,.0f}" if pd.notna(x) and isinstance(x,(int,float)) else "—")
    st.dataframe(fd.dropna(subset=["CPO / Station"]), use_container_width=True, hide_index=True)

# ── USER SEGMENTS (charts — Company view only) ───────────────────────────────
if is_company:
    st.markdown("<div class='sec-hdr'>👤 User Segments</div>", unsafe_allow_html=True)
    br1,br2 = st.columns(2)
    with br1:
        st.markdown("**Car Brand Distribution (Top 10)**")
        if "CARBRAND" in ud.columns:
            brands = ud["CARBRAND"].value_counts().head(10).reset_index()
            brands.columns = ["Brand","Users"]
            st.bar_chart(brands.set_index("Brand"), color="#BEFF6C", height=200)
    with br2:
        st.markdown("**Plug Type Distribution**")
        if "PLUG_TYPE" in ud.columns:
            plugs = ud["PLUG_TYPE"].value_counts().reset_index()
            plugs.columns = ["Plug Type","Users"]
            st.bar_chart(plugs.set_index("Plug Type"), color="#BEFF6C", height=200)

# ── HOST PARTNER CONNECTOR DETAIL ────────────────────────────────────────────
if not is_company:
    st.markdown(f"<div class='sec-hdr'>🔌 Connector Detail — {sel_stations[0]}</div>",
                unsafe_allow_html=True)
    # Charge Point Info is connector-level (a charger can have multiple plug
    # rows), but Session Logs only track CHARGER_ID — so group here by
    # charger for display, summing capacity and listing all its plug types,
    # rather than showing one card per port (which would double-count
    # that charger's sessions across cards).
    site_rows = cp_cap[cp_cap["STATIONNAME"]==sel_stations[0]]
    if len(site_rows):
        site_cps = site_rows.groupby("CHARGER_ID").agg(
            CAPACITY_KW=("CAPACITY_KW","sum"),
            PLUG_TYPE=("PLUG_TYPE", lambda x: " + ".join(sorted(set(x)))),
            CHARGER_TYPE=("CHARGER_TYPE","first"),
            NETWORK_STATUS=("NETWORK_STATUS","first"),
            CONNECTOR_STATUS=("CONNECTOR_STATUS","first"),
            PORTS=("PLUG_TYPE","count"),
        ).reset_index()
    else:
        site_cps = site_rows
    if len(site_cps):
        cols = st.columns(min(len(site_cps),5))
        for i,(_, row) in enumerate(site_cps.iterrows()):
            if i>=5: break
            sc = "#4F7A1E" if row.get("NETWORK_STATUS")=="Online" else "#C1443E"
            cs = row.get("CONNECTOR_STATUS","—")
            cs_col = "#4F7A1E" if cs=="Available" else ("#000000" if cs=="Charging" else "#C1443E")
            cp_sess = df[df["CHARGER_ID"]==row["CHARGER_ID"]]
            cp_kwh  = cp_sess["ENERGY_KWH"].sum()
            cp_avail = row.get("CAPACITY_KW",0) * op_hours * days
            cp_util  = round(cp_kwh/cp_avail*100,1) if cp_avail>0 else 0
            ports_label = f" · {int(row['PORTS'])} ports" if row.get("PORTS",1) > 1 else ""
            cols[i].markdown(
                f"<div style='background:white;border-radius:6px;padding:11px;"
                f"border-top:3px solid {sc};box-shadow:0 1px 4px rgba(0,0,0,.07)'>"
                f"<div style='font-size:11px;font-weight:600;color:#000000'>{row['CHARGER_ID']}</div>"
                f"<div style='font-size:9px;color:#5C574D'>{row.get('CHARGER_TYPE','—')} · {row.get('CAPACITY_KW','—')}kW{ports_label}</div>"
                f"<div style='font-size:9px;color:#5C574D'>{row.get('PLUG_TYPE','—')}</div>"
                f"<div style='font-size:9px;color:{cs_col};margin-top:3px'>● {cs}</div>"
                f"<hr style='margin:5px 0;border-color:#EAE0D0'>"
                f"<div style='font-size:9px;color:#5C574D'>Util: <b style='color:#000000'>{cp_util}%</b></div>"
                f"<div style='font-size:9px;color:#5C574D'>kWh: <b style='color:#000000'>{cp_kwh:,.0f}</b></div>"
                f"<div style='font-size:9px;color:#5C574D'>Sessions: <b style='color:#000000'>{len(cp_sess)}</b></div>"
                f"</div>", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:10px;color:#8A8377'>"
    "Project ChargeIQ Analytics · AIM MAIDA Capstone · "
    "Built with Streamlit + PyDeck</div>",
    unsafe_allow_html=True)
