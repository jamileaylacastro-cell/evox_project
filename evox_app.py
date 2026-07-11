import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from pathlib import Path

# ── RESOLVE DATA FILES ─────────────────────────────────────────────────────
# Looks beside this script first, then in a /data subfolder
BASE = Path(__file__).parent

FILE_MAP = {
    "transactions":    "transactions.xlsx",
    "charge_points":   "Charge_Point_Information__Connector_Type__Charger_Type__Capacity__Fees_Rates_.xlsx",
    "station_profile": "Station_Profile.xlsx",
    "user_details":    "UserDetails.xlsx",
    "wallet_txn":      "walletTransactions.xlsx",
    "financials":      "EVOxCharge_Financials_-_AIM_MAIDA.xlsx",
}

def data_path(filename):
    for candidate in [BASE / filename, BASE / "data" / filename]:
        if candidate.exists():
            return str(candidate)
    return None

missing = [f for f in FILE_MAP.values() if data_path(f) is None]

# ── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="EVOxCharge Analytics", page_icon="⚡",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#F4F6FA}
section[data-testid="stSidebar"]{background:#0A1628}
section[data-testid="stSidebar"] *{color:#B5D4F4!important}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3{color:#FFFFFF!important}
.kpi-card{background:#fff;border-radius:6px;padding:14px 16px;
  border-left:4px solid #185FA5;box-shadow:0 1px 4px rgba(0,0,0,.08);height:100%}
.kpi-label{font-size:10px;color:#64748B;text-transform:uppercase;
  letter-spacing:.06em;margin-bottom:3px}
.kpi-value{font-size:24px;font-weight:600;color:#0A1628;line-height:1}
.kpi-trend{font-size:10px;margin-top:3px}
.up{color:#107C10}.dn{color:#A32D2D}.warn{color:#BA7517}
.sec-hdr{background:#0A1628;color:#fff;padding:7px 14px;border-radius:4px;
  font-size:12px;font-weight:600;margin:14px 0 8px 0}
.formula-box{background:#F4F6FA;border:1px solid #E2E8F0;border-radius:6px;
  padding:10px 14px;font-family:monospace;font-size:11px;
  color:#0A1628;white-space:pre-line;line-height:1.7}
</style>
""", unsafe_allow_html=True)

# ── MISSING FILE GUARD ──────────────────────────────────────────────────────
if missing:
    st.error("❌ Missing data files. Place these in the same folder as `evox_app.py` (or in a `/data` subfolder):")
    for f in missing:
        st.markdown(f"- `{f}`")
    st.info("📁 Your folder should look like:\n```\nevox_app.py\nrequirements.txt\ntransactions.xlsx\nUserDetails.xlsx\nwalletTransactions.xlsx\nStation_Profile.xlsx\nCharge_Point_Information_...xlsx\nEVOxCharge_Financials_...xlsx\n```")
    st.stop()

# ── LOAD ALL DATA ──────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    tx = pd.read_excel(data_path(FILE_MAP["transactions"]),
                       sheet_name="transactions.csv")
    cp = pd.read_excel(data_path(FILE_MAP["charge_points"]))
    sp = pd.read_excel(data_path(FILE_MAP["station_profile"]))
    ud = pd.read_excel(data_path(FILE_MAP["user_details"]))
    wt = pd.read_excel(data_path(FILE_MAP["wallet_txn"]))
    fin = pd.read_excel(data_path(FILE_MAP["financials"]), sheet_name=None)

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

    cp_cap = cp.groupby("CHARGER_ID").agg(
        CAPACITY_KW=("CAPACITY_KW","first"),
        CHARGER_TYPE=("CHARGER_TYPE","first"),
        PLUG_TYPE=("PLUG_TYPE","first"),
        STATIONNAME=("STATIONNAME","first"),
        CHARGER_ACTIVE=("CHARGER_ACTIVE","first"),
        NETWORK_STATUS=("NETWORK_STATUS","first"),
        CONNECTOR_STATUS=("CONNECTOR_STATUS","first"),
        LATITUDE=("LATITUDE","first"),
        LONGITUDE=("LONGITUDE","first"),
    ).reset_index()

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

    return tx, cp, cp_cap, sp, ud, wt, fin_overall, opex, fees

tx, cp, cp_cap, sp, ud, wt, fin_overall, opex_df, fees_df = load_all()

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ EVOxCharge")
    st.markdown("---")
    view = st.radio("Dashboard View",
                    ["🏢  Company / Ops", "🏪  Host Partner Site"])
    is_company = view.startswith("🏢")

    st.markdown("### Filters")
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

    target_util = st.slider("Target Utilization %", 50, 90, 70)

    st.markdown("---")
    days_in_month = tx[tx["MONTH"] == sel_month]["DATE"].nunique()
    st.markdown(f"<small style='color:#5a7fa5'>Period: **{sel_month}**<br>"
                f"Active days: **{days_in_month}**<br>"
                f"Source: Real EVOxCharge data</small>", unsafe_allow_html=True)

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

# ── UTILIZATION ─────────────────────────────────────────────────────────────
cp_sel = cp_cap[cp_cap["STATIONNAME"].isin(sel_stations) & (cp_cap["CHARGER_ACTIVE"] == 1)]
total_avail_kwh = cp_sel["CAPACITY_KW"].sum() * op_hours * days
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
online_cps  = len(cp_sel[cp_sel["NETWORK_STATUS"] == "Online"])
offline_cps = len(cp_sel[cp_sel["NETWORK_STATUS"] == "Offline"])
faulty_cps  = len(cp[cp["STATIONNAME"].isin(sel_stations) & (cp["CONNECTOR_STATUS"] == "Faulty")])

# ── HEADER ──────────────────────────────────────────────────────────────────
col_ico, col_ttl = st.columns([1, 12])
with col_ico:
    st.markdown("<div style='background:#185FA5;border-radius:8px;padding:8px 10px;"
                "font-size:22px;text-align:center;margin-top:6px'>⚡</div>",
                unsafe_allow_html=True)
with col_ttl:
    title = "Network Dashboard" if is_company else f"Site Dashboard — {sel_stations[0]}"
    st.markdown(f"<h2 style='margin:0;color:#0A1628'>EVOxCharge — {title}</h2>"
                f"<p style='margin:0;color:#64748B;font-size:11px'>"
                f"{sel_month} · {days} active days · Op hrs: {op_hours}h/day</p>",
                unsafe_allow_html=True)
st.markdown("---")

# ── FORMULA EXPANDER ────────────────────────────────────────────────────────
with st.expander("📐 Energy-Based Utilization Formula", expanded=False):
    st.markdown(f"""<div class='formula-box'>
Utilization Rate (%) = Σ Actual kWh Charged ÷ Total Available Capacity × 100

Σ Actual kWh Charged     = {actual_kwh:,.1f} kWh  (ENERGY_KWH where ISERROR=0)
Total Available Capacity = Active Connectors × CAPACITY_KW × {op_hours} hrs/day × {days} days
                         = {total_avail_kwh:,.0f} kWh
Network Utilization      = {actual_kwh:,.1f} ÷ {total_avail_kwh:,.0f} × 100 = {net_util:.1f}%
Gap vs {target_util}% target   = {util_gap:+.1f} pp
</div>""", unsafe_allow_html=True)

# ── KPI ROW ─────────────────────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Key Performance Indicators</div>", unsafe_allow_html=True)

def kpi(col, label, value, trend, tclass="up", border="#185FA5"):
    col.markdown(
        f"<div class='kpi-card' style='border-left-color:{border}'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}</div>"
        f"<div class='kpi-trend {tclass}'>{trend}</div></div>",
        unsafe_allow_html=True)

k1,k2,k3,k4,k5,k6 = st.columns(6)
gap_cls = "up" if util_gap >= 0 else ("warn" if util_gap >= -10 else "dn")
kpi(k1,"Network Utilization (kWh)",f"{net_util:.1f}%",
    f"{'▲' if util_gap>=0 else '▼'} {util_gap:+.1f} pp vs {target_util}% target",
    gap_cls, "#107C10" if util_gap>=0 else "#E24B4A")
kpi(k2,"Actual kWh Charged",f"{actual_kwh:,.0f}",
    f"{'▲' if actual_kwh>prior_kwh else '▼'} vs prior month",
    "up" if actual_kwh>=prior_kwh else "dn","#0F6E56")
kpi(k3,"Total Sessions",f"{total_sess:,}",
    f"{'▲' if mom_sess>=0 else '▼'} {abs(mom_sess):.1f}% MoM",
    "up" if mom_sess>=0 else "dn","#0F6E56")
kpi(k4,"Total Revenue",f"₱{total_rev:,.0f}",
    f"{'▲' if mom_rev>=0 else '▼'} {abs(mom_rev):.1f}% MoM",
    "up" if mom_rev>=0 else "dn","#0F6E56")
kpi(k5,"Error Session Rate",f"{error_rate:.1f}%",
    "▼ needs attention" if error_rate>5 else "Within threshold",
    "dn" if error_rate>5 else "up","#E24B4A" if error_rate>5 else "#0F6E56")
kpi(k6,"Charger Status",f"{online_cps}/{total_cps} online",
    f"{offline_cps} offline · {faulty_cps} faulty" if (offline_cps+faulty_cps)>0 else "All online",
    "dn" if offline_cps>0 else "up","#E24B4A" if offline_cps>0 else "#0F6E56")

st.markdown("<br>", unsafe_allow_html=True)

# ── MAP + UTIL BAR ──────────────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>📍 Station Heatmap — Energy Utilization</div>",
            unsafe_allow_html=True)
map_col, bar_col = st.columns([3, 2])

station_rows = []
for sname in sel_stations:
    s_df  = df[df["STATIONNAME"] == sname]
    s_cp  = cp_cap[cp_cap["STATIONNAME"] == sname]
    s_all = df_all[df_all["STATIONNAME"] == sname]
    s_kwh  = s_df["ENERGY_KWH"].sum()
    s_cap  = s_cp[s_cp["CHARGER_ACTIVE"]==1]["CAPACITY_KW"].sum()
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
    color = [16,124,16,210] if s_util>=target_util else ([242,200,17,210] if s_util>=target_util-10 else [226,75,74,210])
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

with map_col:
    map_mode = st.radio("Map layer",
        ["🔥 Heatmap (Energy density)","🔵 Bubbles (Utilization %)"],
        horizontal=True)
    center_lat = map_df["LATITUDE"].mean() if len(map_df) else 14.55
    center_lon = map_df["LONGITUDE"].mean() if len(map_df) else 121.03
    view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon,
                               zoom=10, pitch=35 if "Bubble" in map_mode else 0)
    if "Heatmap" in map_mode:
        pts = []
        for _, r in map_df.iterrows():
            n = max(1, int(r["weight"]*100))
            for _ in range(n):
                pts.append({"lat": r["LATITUDE"]+np.random.uniform(-.003,.003),
                             "lon": r["LONGITUDE"]+np.random.uniform(-.003,.003)})
        layer  = pdk.Layer("HeatmapLayer", data=pd.DataFrame(pts),
            get_position=["lon","lat"], aggregation="SUM",
            opacity=0.85, threshold=0.03,
            color_range=[[0,50,0,180],[0,160,0,210],[255,255,0,220],
                         [255,140,0,230],[220,50,50,245]])
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
            get_color=[255,255,255,200], get_pixel_offset=[0,-24], billboard=True)
        layers  = [layer, labels]
        tooltip = {"html":"""<div style='background:#0A1628;padding:10px 14px;
          border-radius:6px;color:white;font-size:12px;min-width:180px'>
          <b>⚡ {STATIONNAME}</b><hr style='border-color:#185FA5;margin:5px 0'>
          Utilization: <b>{util_pct}%</b><br>kWh actual: <b>{energy_kwh}</b><br>
          Sessions: <b>{sessions}</b><br>Revenue: <b>₱{revenue}</b><br>
          Error rate: <b>{error_rate}%</b></div>"""}
    st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10", tooltip=tooltip),
        use_container_width=True)
    l1,l2,l3 = st.columns(3)
    if "Heatmap" in map_mode:
        l1.markdown("🟢 Low density"); l2.markdown("🟡 Moderate"); l3.markdown("🔴 High density")
    else:
        l1.markdown("🟢 ≥ Target"); l2.markdown("🟡 Near target"); l3.markdown("🔴 Below target")

with bar_col:
    st.markdown(f"**Utilization by Station vs {target_util}% target**")
    for _, r in map_df.sort_values("util_pct", ascending=False).iterrows():
        u = r["util_pct"]; g = u - target_util
        bc = "#107C10" if u>=target_util else ("#EF9F27" if u>=target_util-10 else "#E24B4A")
        gc = "#107C10" if g>=0 else "#E24B4A"
        st.markdown(
            f"<div style='margin-bottom:9px'>"
            f"<div style='display:flex;justify-content:space-between;font-size:11px;"
            f"color:#0A1628;margin-bottom:2px'>"
            f"<b>{r['STATIONNAME'][:30]}</b>"
            f"<span style='color:{gc}'>{'▲' if g>=0 else '▼'}{abs(g):.1f}pp</span></div>"
            f"<div style='background:#E2E8F0;border-radius:2px;height:12px;overflow:hidden'>"
            f"<div style='width:{min(u,100)}%;height:100%;background:{bc};border-radius:2px'></div></div>"
            f"<div style='display:flex;justify-content:space-between;font-size:9px;"
            f"color:#64748B;margin-top:1px'>"
            f"<span>{r['energy_kwh']:,.0f} kWh</span><b>{u}%</b></div></div>",
            unsafe_allow_html=True)

# ── CHARTS ──────────────────────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Session & Energy Analysis</div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
with c1:
    st.markdown("**Sessions by Hour of Day**")
    h = df.groupby("HOUR").size().reset_index(name="Sessions")
    if len(h): st.bar_chart(h.set_index("HOUR"), color="#185FA5", height=200)
with c2:
    st.markdown("**Energy (kWh) by Charge Type**")
    ct = df.groupby("CHARGE_TYPE")["ENERGY_KWH"].sum().reset_index()
    ct.columns = ["Charge Type","kWh"]
    if len(ct): st.bar_chart(ct.set_index("Charge Type"), color="#0F6E56", height=200)
with c3:
    st.markdown("**Payment Method Mix**")
    pm = df_all.groupby("PAYMENT_METHOD").size().reset_index(name="Count")
    if len(pm): st.bar_chart(pm.set_index("PAYMENT_METHOD"), color="#BA7517", height=200)

# ── SITE PERFORMANCE TABLE ───────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Site Performance — Energy Utilization vs Capacity</div>",
            unsafe_allow_html=True)
if len(map_df):
    tbl = map_df[["STATIONNAME","util_pct","energy_kwh","avail_kwh",
                   "sessions","revenue","error_rate"]].copy()
    tbl["gap_pp"] = (tbl["util_pct"] - target_util).round(1)
    tbl["action"] = tbl["util_pct"].apply(
        lambda u: "✅ Expand" if u>=target_util
        else ("🟡 Monitor" if u>=target_util-10
        else ("⚠️ Optimize" if u>=target_util-25 else "🔴 Review")))
    tbl = tbl.rename(columns={
        "STATIONNAME":"Station","util_pct":"Util %","energy_kwh":"kWh Actual",
        "avail_kwh":"kWh Available","sessions":"Sessions",
        "revenue":"Revenue (₱)","error_rate":"Error %",
        "gap_pp":"Gap (pp)","action":"Action"
    }).sort_values("Util %", ascending=False)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ── FINANCIALS ───────────────────────────────────────────────────────────────
if is_company:
    st.markdown("<div class='sec-hdr'>💰 Financials — Revenue & Operating Costs (Jan–Jun 2026)</div>",
                unsafe_allow_html=True)
    f1,f2 = st.columns([2,1])
    with f1:
        fd = fin_overall[["CPO","Revenue","ActualElecCost","ActualRent","EstIncome2026"]].copy()
        fd.columns = ["CPO / Station","Revenue (₱)","Elec Cost (₱)","Rent/Share (₱)","Est. Income 2026 (₱)"]
        for col in fd.columns[1:]:
            fd[col] = fd[col].apply(lambda x: f"₱{x:,.0f}" if pd.notna(x) and isinstance(x,(int,float)) else "—")
        st.dataframe(fd.dropna(subset=["CPO / Station"]), use_container_width=True, hide_index=True)
    with f2:
        tr = fin_overall["Revenue"].sum()
        te = fin_overall["ActualElecCost"].sum()
        trent = fin_overall["ActualRent"].sum()
        gm = tr - te - trent
        st.markdown(
            f"<div class='kpi-card' style='border-left-color:#0F6E56'>"
            f"<div class='kpi-label'>Total Network Revenue</div>"
            f"<div class='kpi-value'>₱{tr/1e6:.2f}M</div>"
            f"<div class='kpi-trend up'>All CPOs · Jan–Jun 2026</div></div><br>"
            f"<div class='kpi-card' style='border-left-color:#E24B4A'>"
            f"<div class='kpi-label'>Total Electricity Cost</div>"
            f"<div class='kpi-value'>₱{te/1e6:.2f}M</div>"
            f"<div class='kpi-trend dn'>Actual · Jan–Jun 2026</div></div><br>"
            f"<div class='kpi-card' style='border-left-color:#BA7517'>"
            f"<div class='kpi-label'>Gross Margin</div>"
            f"<div class='kpi-value'>₱{gm/1e6:.2f}M</div>"
            f"<div class='kpi-trend {'up' if gm>0 else 'dn'}'>"
            f"{gm/tr*100:.1f}% margin (Rev − Elec − Rent)</div></div>",
            unsafe_allow_html=True)

# ── USER INSIGHTS ────────────────────────────────────────────────────────────
if is_company:
    st.markdown("<div class='sec-hdr'>👤 User Insights</div>", unsafe_allow_html=True)
    ud_c = ud
    u1,u2,u3,u4 = st.columns(4)
    active = len(ud_c[ud_c["ACCOUNT_STATUS"]=="Active"])
    avg_w  = ud_c["WALLET_BALANCE"].mean()
    top_b  = ud_c["CARBRAND"].value_counts().index[0] if len(ud_c) else "—"
    top_p  = ud_c["PLUG_TYPE"].value_counts().index[0]  if len(ud_c) else "—"
    kpi(u1,"Registered Users",f"{len(ud_c):,}",f"{active:,} active","up","#185FA5")
    kpi(u2,"Avg Wallet Balance",f"₱{avg_w:,.0f}","Across active users","up","#0F6E56")
    kpi(u3,"Top Car Brand",top_b,f"{ud_c['CARBRAND'].value_counts().iloc[0]:,} users","up","#BA7517")
    kpi(u4,"Most Common Plug",top_p,f"{ud_c['PLUG_TYPE'].value_counts().iloc[0]:,} users","up","#185FA5")
    br1,br2 = st.columns(2)
    with br1:
        st.markdown("**Car Brand Distribution (Top 10)**")
        brands = ud_c["CARBRAND"].value_counts().head(10).reset_index()
        brands.columns = ["Brand","Users"]
        st.bar_chart(brands.set_index("Brand"), color="#185FA5", height=200)
    with br2:
        st.markdown("**Plug Type Distribution**")
        plugs = ud_c["PLUG_TYPE"].value_counts().reset_index()
        plugs.columns = ["Plug Type","Users"]
        st.bar_chart(plugs.set_index("Plug Type"), color="#0F6E56", height=200)

# ── HOST PARTNER CONNECTOR DETAIL ────────────────────────────────────────────
if not is_company:
    st.markdown(f"<div class='sec-hdr'>🔌 Connector Detail — {sel_stations[0]}</div>",
                unsafe_allow_html=True)
    site_cps = cp[cp["STATIONNAME"]==sel_stations[0]].drop_duplicates("CHARGER_ID")
    if len(site_cps):
        cols = st.columns(min(len(site_cps),5))
        for i,(_, row) in enumerate(site_cps.iterrows()):
            if i>=5: break
            sc = "#107C10" if row.get("NETWORK_STATUS")=="Online" else "#E24B4A"
            cs = row.get("CONNECTOR_STATUS","—")
            cs_col = "#107C10" if cs=="Available" else ("#185FA5" if cs=="Charging" else "#E24B4A")
            cp_sess = df[df["CHARGER_ID"]==row["CHARGER_ID"]]
            cp_kwh  = cp_sess["ENERGY_KWH"].sum()
            cp_avail = row.get("CAPACITY_KW",0) * op_hours * days
            cp_util  = round(cp_kwh/cp_avail*100,1) if cp_avail>0 else 0
            cols[i].markdown(
                f"<div style='background:white;border-radius:6px;padding:11px;"
                f"border-top:3px solid {sc};box-shadow:0 1px 4px rgba(0,0,0,.07)'>"
                f"<div style='font-size:11px;font-weight:600;color:#0A1628'>{row['CHARGER_ID']}</div>"
                f"<div style='font-size:9px;color:#64748B'>{row.get('CHARGER_TYPE','—')} · {row.get('CAPACITY_KW','—')}kW</div>"
                f"<div style='font-size:9px;color:#64748B'>{row.get('PLUG_TYPE','—')}</div>"
                f"<div style='font-size:9px;color:{cs_col};margin-top:3px'>● {cs}</div>"
                f"<hr style='margin:5px 0;border-color:#E2E8F0'>"
                f"<div style='font-size:9px;color:#64748B'>Util: <b style='color:#0A1628'>{cp_util}%</b></div>"
                f"<div style='font-size:9px;color:#64748B'>kWh: <b style='color:#0A1628'>{cp_kwh:,.0f}</b></div>"
                f"<div style='font-size:9px;color:#64748B'>Sessions: <b style='color:#0A1628'>{len(cp_sess)}</b></div>"
                f"</div>", unsafe_allow_html=True)

# ── FOOTER ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:10px;color:#94A3B8'>"
    "EVOxCharge Analytics · AIM MAIDA Capstone · "
    "Built with Streamlit + PyDeck</div>",
    unsafe_allow_html=True)
