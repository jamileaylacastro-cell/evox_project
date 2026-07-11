import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
from datetime import datetime, timedelta

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

# ── LOAD ALL DATA ──────────────────────────────────────────────────────────
@st.cache_data
def load_all():
    tx = pd.read_excel("/mnt/user-data/uploads/transactions.xlsx",
                       sheet_name="transactions.csv")
    cp = pd.read_excel("/mnt/user-data/uploads/Charge_Point_Information__Connector_Type__Charger_Type__Capacity__Fees_Rates_.xlsx")
    sp = pd.read_excel("/mnt/user-data/uploads/Station_Profile.xlsx")
    ud = pd.read_excel("/mnt/user-data/uploads/UserDetails.xlsx")
    wt = pd.read_excel("/mnt/user-data/uploads/walletTransactions.xlsx")
    fin = pd.read_excel("/mnt/user-data/uploads/EVOxCharge_Financials_-_AIM_MAIDA.xlsx",
                        sheet_name=None)

    # Clean transactions
    tx["STARTTIME"] = pd.to_datetime(tx["STARTTIME"], errors="coerce")
    tx["ENDTIME"]   = pd.to_datetime(tx["ENDTIME"],   errors="coerce")
    tx = tx[tx["STARTTIME"].dt.year > 2020].copy()
    tx["DATE"]  = tx["STARTTIME"].dt.date
    tx["MONTH"] = tx["STARTTIME"].dt.to_period("M")
    tx["HOUR"]  = tx["STARTTIME"].dt.hour
    tx["DURATION_MIN"] = (tx["ENDTIME"] - tx["STARTTIME"]).dt.total_seconds() / 60

    # Station coordinates — merge SP into CP, then into TX
    sp_coords = sp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE","BUSINESS_START","BUSINESS_END","RATE_PER_KWH"]].first().reset_index()
    cp = cp.merge(sp_coords[["STATIONNAME","BUSINESS_START","BUSINESS_END"]], on="STATIONNAME", how="left")

    # Station-level coord lookup (from CP, fallback to SP)
    cp_coords = cp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE"]].first().reset_index()
    tx = tx.merge(cp_coords, on="STATIONNAME", how="left")

    # For stations missing from CP, fall back to SP
    sp_ll = sp.groupby("STATIONNAME")[["LATITUDE","LONGITUDE"]].first().reset_index()
    missing = tx["LATITUDE"].isna()
    tx_miss = tx[missing].drop(columns=["LATITUDE","LONGITUDE"]).merge(
        sp_ll, on="STATIONNAME", how="left")
    tx.loc[missing, "LATITUDE"]  = tx_miss["LATITUDE"].values
    tx.loc[missing, "LONGITUDE"] = tx_miss["LONGITUDE"].values

    # Capacity per charger
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

    # Financials — OVERALL sheet
    fin_overall = fin["OVERALL"].dropna(subset=["CPO"]).copy()
    fin_overall.columns = ["CPO","Revenue","ActualElecCost","EstElecCost",
                            "ActualRent","EstRent","EstIncome2026"]
    fin_overall = fin_overall[fin_overall["CPO"] != "SUB TOTAL:"].copy()

    # Financials — ACTUAL OPEX
    opex = fin["ACTUAL OPEX (JAN-JUN)"].copy()
    opex.columns = ["CPO","ElecJan","ElecFeb","ElecMar","ElecApr","ElecMay","ElecJun",
                    "RentJan","RentFeb","RentMar","RentApr","RentMay","RentJun","Remarks"]
    opex = opex[opex["CPO"].notna() & (opex["CPO"] != "CPO") & (opex["CPO"] != "CPO - JV")].copy()

    # Financials — FEES AND ASSUMPTIONS
    fees = fin["FEES AND ASSUMPTIONS"].dropna(subset=["CPO"]).copy()
    fees = fees[fees["CPO"] != "CPO - JV"].copy()

    return tx, cp, cp_cap, sp, ud, wt, fin_overall, opex, fees

tx, cp, cp_cap, sp, ud, wt, fin_overall, opex_df, fees_df = load_all()

# ── SIDEBAR ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚡ EVOxCharge")
    st.markdown("---")

    view = st.radio("Dashboard View",
                    ["🏢  Company / Ops", "🏪  Host Partner Site"],
                    label_visibility="visible")
    is_company = view.startswith("🏢")

    st.markdown("### Filters")
    all_stations = sorted(tx["STATIONNAME"].dropna().unique().tolist())

    if is_company:
        sel_stations = st.multiselect("Stations", all_stations, default=all_stations[:10])
        if not sel_stations:
            sel_stations = all_stations
    else:
        sel_station = st.selectbox("Site", all_stations, index=0)
        sel_stations = [sel_station]

    all_months = sorted(tx["MONTH"].dropna().unique().tolist(), reverse=True)
    month_labels = [str(m) for m in all_months]
    sel_month_label = st.selectbox("Month", month_labels, index=0)
    sel_month = all_months[month_labels.index(sel_month_label)]

    charge_types = st.multiselect("Charge Type",
        tx["CHARGE_TYPE"].dropna().unique().tolist(),
        default=tx["CHARGE_TYPE"].dropna().unique().tolist())

    op_hours = st.slider("Operating hrs / day", 8, 24, 12)
    use_24h  = st.checkbox("Use 24-hr capacity", value=False)
    if use_24h: op_hours = 24

    target_util = st.slider("Target Utilization %", 50, 90, 70)

    st.markdown("---")
    days_in_month = tx[tx["MONTH"] == sel_month]["DATE"].nunique()
    st.markdown(f"<small style='color:#5a7fa5'>Period: **{sel_month}**<br>"
                f"Active days: **{days_in_month}**<br>"
                f"Source: Real EVOxCharge data</small>", unsafe_allow_html=True)

# ── FILTER ─────────────────────────────────────────────────────────────────
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

days = max(days_in_month, 1)

# Prior month for MoM
prior_month = sel_month - 1
df_prior = tx[
    (tx["STATIONNAME"].isin(sel_stations)) &
    (tx["MONTH"] == prior_month) &
    (tx["CHARGE_TYPE"].isin(charge_types)) &
    (~tx["ISERROR"].astype(bool))
].copy()

# ── CAPACITY & UTILIZATION ─────────────────────────────────────────────────
cp_sel = cp_cap[cp_cap["STATIONNAME"].isin(sel_stations) & (cp_cap["CHARGER_ACTIVE"] == 1)]

# Total available capacity kWh
total_avail_kwh = cp_sel["CAPACITY_KW"].sum() * op_hours * days

# Actual kWh
actual_kwh = df["ENERGY_KWH"].sum()
prior_kwh  = df_prior["ENERGY_KWH"].sum()

net_util = (actual_kwh / total_avail_kwh * 100) if total_avail_kwh > 0 else 0
util_gap = net_util - target_util

# Per-station utilization
def site_util(station):
    s_kwh  = df[df["STATIONNAME"] == station]["ENERGY_KWH"].sum()
    s_cap  = cp_cap[(cp_cap["STATIONNAME"] == station) & (cp_cap["CHARGER_ACTIVE"] == 1)]["CAPACITY_KW"].sum()
    s_avail = s_cap * op_hours * days
    return round(s_kwh / s_avail * 100, 1) if s_avail > 0 else 0

# Revenue
total_rev  = df["TOTALAMOUNT"].sum()
prior_rev  = df_prior["TOTALAMOUNT"].sum()
mom_rev    = (total_rev - prior_rev) / prior_rev * 100 if prior_rev > 0 else 0

# Sessions
total_sess  = len(df)
prior_sess  = len(df_prior)
mom_sess    = (total_sess - prior_sess) / prior_sess * 100 if prior_sess > 0 else 0

# Error rate
error_rate = (df_all["ISERROR"].astype(bool).sum() / len(df_all) * 100) if len(df_all) > 0 else 0

# Avg session duration
avg_dur = df["DURATION_MIN"].mean() if len(df) > 0 else 0

# Charger status
total_cps   = len(cp_sel)
online_cps  = len(cp_sel[cp_sel["NETWORK_STATUS"] == "Online"])
offline_cps = len(cp_sel[cp_sel["NETWORK_STATUS"] == "Offline"])
faulty_cps  = len(cp[cp["STATIONNAME"].isin(sel_stations) & (cp["CONNECTOR_STATUS"] == "Faulty")])

# ── HEADER ─────────────────────────────────────────────────────────────────
col_ico, col_ttl = st.columns([1, 12])
with col_ico:
    st.markdown("<div style='background:#185FA5;border-radius:8px;padding:8px 10px;"
                "font-size:22px;text-align:center;margin-top:6px'>⚡</div>",
                unsafe_allow_html=True)
with col_ttl:
    title = "Network Dashboard" if is_company else f"Site Dashboard — {sel_stations[0]}"
    st.markdown(f"<h2 style='margin:0;color:#0A1628'>EVOxCharge — {title}</h2>"
                f"<p style='margin:0;color:#64748B;font-size:11px'>"
                f"{sel_month} · {days} active days · "
                f"Op hrs: {op_hours}h/day · "
                f"{'All selected stations' if is_company else sel_stations[0]}</p>",
                unsafe_allow_html=True)

st.markdown("---")

# ── FORMULA EXPANDER ────────────────────────────────────────────────────────
with st.expander("📐 Energy-Based Utilization Formula", expanded=False):
    st.markdown(f"""<div class='formula-box'>
Utilization Rate (%) = Σ Actual kWh Charged ÷ Total Available Capacity × 100

Σ Actual kWh Charged     = {actual_kwh:,.1f} kWh
  Source: transactions.xlsx · ENERGY_KWH (ISERROR = 0)

Total Available Capacity = Active Connectors × CAPACITY_KW × Op hrs/day × Days in period
                         = {total_cps} connectors × (mixed kW) × {op_hours} hrs × {days} days
                         = {total_avail_kwh:,.0f} kWh
  Source: Charge_Point_Information · CAPACITY_KW (CHARGER_ACTIVE = 1)
  Operating hrs: Station_Profile · BUSINESS_START / BUSINESS_END

Network Utilization = {actual_kwh:,.1f} ÷ {total_avail_kwh:,.0f} × 100 = {net_util:.1f}%
Gap vs {target_util}% target = {util_gap:+.1f} pp
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
kpi(k1,"Network Utilization (kWh)",
    f"{net_util:.1f}%",
    f"{'▲' if util_gap>=0 else '▼'} {util_gap:+.1f} pp vs {target_util}% target",
    gap_cls, "#107C10" if util_gap>=0 else "#E24B4A")
kpi(k2,"Actual kWh Charged",
    f"{actual_kwh:,.0f}",
    f"{'▲' if actual_kwh>prior_kwh else '▼'} vs prior month",
    "up" if actual_kwh >= prior_kwh else "dn","#0F6E56")
kpi(k3,"Total Sessions",
    f"{total_sess:,}",
    f"{'▲' if mom_sess>=0 else '▼'} {abs(mom_sess):.1f}% MoM",
    "up" if mom_sess>=0 else "dn","#0F6E56")
kpi(k4,"Total Revenue",
    f"₱{total_rev:,.0f}",
    f"{'▲' if mom_rev>=0 else '▼'} {abs(mom_rev):.1f}% MoM",
    "up" if mom_rev>=0 else "dn","#0F6E56")
kpi(k5,"Error Session Rate",
    f"{error_rate:.1f}%",
    "▼ needs attention" if error_rate>5 else "Within threshold",
    "dn" if error_rate>5 else "up",
    "#E24B4A" if error_rate>5 else "#0F6E56")
kpi(k6,"Charger Status",
    f"{online_cps}/{total_cps} online",
    f"{offline_cps} offline · {faulty_cps} faulty" if (offline_cps+faulty_cps)>0 else "All online",
    "dn" if offline_cps>0 else "up",
    "#E24B4A" if offline_cps>0 else "#0F6E56")

st.markdown("<br>", unsafe_allow_html=True)

# ── MAP + UTILIZATION BAR ───────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>📍 Station Heatmap — Energy Utilization</div>",
            unsafe_allow_html=True)

map_col, bar_col = st.columns([3, 2])

# Build per-station summary for map
station_rows = []
for sname in sel_stations:
    s_df   = df[df["STATIONNAME"] == sname]
    s_cp   = cp_cap[cp_cap["STATIONNAME"] == sname]
    s_all  = df_all[df_all["STATIONNAME"] == sname]
    s_kwh  = s_df["ENERGY_KWH"].sum()
    s_cap  = s_cp[s_cp["CHARGER_ACTIVE"]==1]["CAPACITY_KW"].sum()
    s_avail = s_cap * op_hours * days
    s_util  = round(s_kwh / s_avail * 100, 1) if s_avail > 0 else 0
    s_rev   = s_df["TOTALAMOUNT"].sum()
    s_sess  = len(s_df)
    s_err   = round(s_all["ISERROR"].astype(bool).sum() / max(len(s_all),1)*100, 1)
    lat = s_df["LATITUDE"].dropna().mean()
    lon = s_df["LONGITUDE"].dropna().mean()
    if pd.isna(lat):
        cp_ll = s_cp[["LATITUDE","LONGITUDE"]].dropna()
        if len(cp_ll):
            lat, lon = cp_ll.iloc[0]["LATITUDE"], cp_ll.iloc[0]["LONGITUDE"]
    if pd.isna(lat): continue

    if s_util >= target_util:             color = [16,124,16,210]
    elif s_util >= target_util - 10:      color = [242,200,17,210]
    else:                                  color = [226,75,74,210]

    station_rows.append({
        "STATIONNAME": sname,
        "LATITUDE": lat,
        "LONGITUDE": lon,
        "util_pct": s_util,
        "energy_kwh": round(s_kwh,1),
        "avail_kwh": round(s_avail,1),
        "revenue": round(s_rev,0),
        "sessions": s_sess,
        "error_rate": s_err,
        "color": color,
        "radius": max(int(s_kwh/max(actual_kwh,1)*1200)+150, 120),
        "weight": round(s_kwh/max(actual_kwh,1), 3),
    })

map_df = pd.DataFrame(station_rows)

with map_col:
    map_mode = st.radio("Map layer",
        ["🔥 Heatmap (Energy density)", "🔵 Bubbles (Utilization %)"],
        horizontal=True)

    if len(map_df):
        center_lat = map_df["LATITUDE"].mean()
        center_lon = map_df["LONGITUDE"].mean()
    else:
        center_lat, center_lon = 14.55, 121.03

    view_state = pdk.ViewState(
        latitude=center_lat, longitude=center_lon,
        zoom=10, pitch=35 if "Bubble" in map_mode else 0)

    if "Heatmap" in map_mode:
        # Expand points weighted by kWh
        pts = []
        for _, r in map_df.iterrows():
            n = max(1, int(r["weight"] * 100))
            for _ in range(n):
                pts.append({"lat": r["LATITUDE"] + np.random.uniform(-.003,.003),
                             "lon": r["LONGITUDE"] + np.random.uniform(-.003,.003)})
        pts_df = pd.DataFrame(pts)
        layer = pdk.Layer("HeatmapLayer", data=pts_df,
            get_position=["lon","lat"], aggregation="SUM",
            opacity=0.85, threshold=0.03,
            color_range=[[0,50,0,180],[0,160,0,210],[255,255,0,220],
                         [255,140,0,230],[220,50,50,245]])
        layers = [layer]
    else:
        tooltip = {
            "html": """<div style='background:#0A1628;padding:10px 14px;
              border-radius:6px;color:white;font-size:12px;min-width:180px'>
              <b>⚡ {STATIONNAME}</b><hr style='border-color:#185FA5;margin:5px 0'>
              Utilization: <b>{util_pct}%</b><br>
              kWh actual: <b>{energy_kwh}</b><br>
              kWh available: <b>{avail_kwh}</b><br>
              Sessions: <b>{sessions}</b><br>
              Revenue: <b>₱{revenue}</b><br>
              Error rate: <b>{error_rate}%</b>
              </div>"""
        }
        bubble = pdk.Layer("ScatterplotLayer", data=map_df,
            get_position=["LONGITUDE","LATITUDE"],
            get_fill_color="color", get_radius="radius",
            radius_min_pixels=6, radius_max_pixels=90, pickable=True)
        labels = pdk.Layer("TextLayer", data=map_df,
            get_position=["LONGITUDE","LATITUDE"],
            get_text="STATIONNAME", get_size=12,
            get_color=[255,255,255,200],
            get_pixel_offset=[0,-24], billboard=True)
        layers = [bubble, labels]

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip=tooltip if "Bubble" in map_mode else None,
    )
    st.pydeck_chart(deck, use_container_width=True)

    if "Heatmap" in map_mode:
        c1,c2,c3 = st.columns(3)
        c1.markdown("🟢 Low energy density")
        c2.markdown("🟡 Moderate density")
        c3.markdown("🔴 High energy density")
    else:
        c1,c2,c3 = st.columns(3)
        c1.markdown("🟢 ≥ Target util")
        c2.markdown("🟡 Near target (−10pp)")
        c3.markdown("🔴 Below target")

with bar_col:
    st.markdown(f"**Utilization by Station vs {target_util}% target**")
    if len(map_df):
        for _, r in map_df.sort_values("util_pct", ascending=False).iterrows():
            u = r["util_pct"]
            g = u - target_util
            bc = "#107C10" if u>=target_util else ("#EF9F27" if u>=target_util-10 else "#E24B4A")
            gc = "#107C10" if g>=0 else "#E24B4A"
            st.markdown(
                f"<div style='margin-bottom:9px'>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:11px;color:#0A1628;margin-bottom:2px'>"
                f"<span><b>{r['STATIONNAME'][:28]}</b></span>"
                f"<span style='color:{gc}'>{'▲' if g>=0 else '▼'}{abs(g):.1f}pp</span></div>"
                f"<div style='background:#E2E8F0;border-radius:2px;height:12px;overflow:hidden'>"
                f"<div style='width:{min(u,100)}%;height:100%;"
                f"background:{bc};border-radius:2px'></div></div>"
                f"<div style='display:flex;justify-content:space-between;"
                f"font-size:9px;color:#64748B;margin-top:1px'>"
                f"<span>{r['energy_kwh']:,.0f} kWh actual</span>"
                f"<span><b>{u}%</b></span></div></div>",
                unsafe_allow_html=True)
    else:
        st.info("No stations with location data for selected filters.")

# ── CHARTS ─────────────────────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Session & Energy Analysis</div>", unsafe_allow_html=True)

c1,c2,c3 = st.columns(3)

with c1:
    st.markdown("**Sessions by Hour of Day**")
    hourly = df.groupby("HOUR").size().reset_index(name="Sessions")
    if len(hourly):
        st.bar_chart(hourly.set_index("HOUR"), color="#185FA5", height=200)
    else:
        st.info("No data")

with c2:
    st.markdown("**Energy (kWh) by Charge Type**")
    ct = df.groupby("CHARGE_TYPE")["ENERGY_KWH"].sum().reset_index()
    ct.columns = ["Charge Type","kWh"]
    if len(ct):
        st.bar_chart(ct.set_index("Charge Type"), color="#0F6E56", height=200)
    else:
        st.info("No data")

with c3:
    st.markdown("**Payment Method Mix**")
    pm = df_all.groupby("PAYMENT_METHOD").size().reset_index(name="Count")
    if len(pm):
        st.bar_chart(pm.set_index("PAYMENT_METHOD"), color="#BA7517", height=200)
    else:
        st.info("No data")

# ── SITE PERFORMANCE TABLE ──────────────────────────────────────────────────
st.markdown("<div class='sec-hdr'>Site Performance — Energy Utilization vs Capacity</div>",
            unsafe_allow_html=True)

if len(map_df):
    tbl = map_df[["STATIONNAME","util_pct","energy_kwh","avail_kwh",
                   "sessions","revenue","error_rate"]].copy()
    tbl["gap_pp"] = (tbl["util_pct"] - target_util).round(1)
    tbl["action"] = tbl["util_pct"].apply(
        lambda u: "✅ Expand" if u>=target_util
        else ("🟡 Monitor" if u>=target_util-10
        else ("⚠️ Optimize" if u>=target_util-25
        else "🔴 Review")))
    tbl = tbl.rename(columns={
        "STATIONNAME":"Station","util_pct":"Util %","energy_kwh":"kWh Actual",
        "avail_kwh":"kWh Available","sessions":"Sessions",
        "revenue":"Revenue (₱)","error_rate":"Error %",
        "gap_pp":"Gap (pp)","action":"Action"
    }).sort_values("Util %", ascending=False)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

# ── FINANCIALS (Company View) ────────────────────────────────────────────────
if is_company and len(fin_overall):
    st.markdown("<div class='sec-hdr'>💰 Financials — Revenue & Operating Costs (Jan–Jun 2026)</div>",
                unsafe_allow_html=True)

    f1, f2 = st.columns([2, 1])
    with f1:
        fin_disp = fin_overall[["CPO","Revenue","ActualElecCost","ActualRent","EstIncome2026"]].copy()
        fin_disp.columns = ["CPO / Station","Revenue (₱)","Elec Cost (₱)","Rent/Share (₱)","Est. Income 2026 (₱)"]
        fin_disp = fin_disp[fin_disp["CPO / Station"].notna()].copy()
        for col in ["Revenue (₱)","Elec Cost (₱)","Rent/Share (₱)","Est. Income 2026 (₱)"]:
            fin_disp[col] = fin_disp[col].apply(
                lambda x: f"₱{x:,.0f}" if pd.notna(x) and isinstance(x,(int,float)) else "—")
        st.dataframe(fin_disp, use_container_width=True, hide_index=True)
    with f2:
        total_r = fin_overall["Revenue"].sum()
        total_e = fin_overall["ActualElecCost"].sum()
        total_rent = fin_overall["ActualRent"].sum()
        gross_m = total_r - total_e - total_rent
        st.markdown(
            f"<div class='kpi-card' style='border-left-color:#0F6E56'>"
            f"<div class='kpi-label'>Total Network Revenue</div>"
            f"<div class='kpi-value'>₱{total_r/1e6:.2f}M</div>"
            f"<div class='kpi-trend up'>All CPOs Jan–Jun 2026</div></div><br>"
            f"<div class='kpi-card' style='border-left-color:#E24B4A'>"
            f"<div class='kpi-label'>Total Electricity Cost</div>"
            f"<div class='kpi-value'>₱{total_e/1e6:.2f}M</div>"
            f"<div class='kpi-trend dn'>Actual Jan–Jun 2026</div></div><br>"
            f"<div class='kpi-card' style='border-left-color:#BA7517'>"
            f"<div class='kpi-label'>Gross Margin (Rev − Elec − Rent)</div>"
            f"<div class='kpi-value'>₱{gross_m/1e6:.2f}M</div>"
            f"<div class='kpi-trend {'up' if gross_m>0 else 'dn'}'>"
            f"{gross_m/total_r*100:.1f}% margin</div></div>",
            unsafe_allow_html=True)

# ── USER INSIGHTS ────────────────────────────────────────────────────────────
if is_company:
    st.markdown("<div class='sec-hdr'>👤 User Insights</div>", unsafe_allow_html=True)
    ud_clean = pd.read_excel("/mnt/user-data/uploads/UserDetails.xlsx")

    u1,u2,u3,u4 = st.columns(4)
    active = len(ud_clean[ud_clean["ACCOUNT_STATUS"]=="Active"])
    avg_wallet = ud_clean["WALLET_BALANCE"].mean()
    top_brand = ud_clean["CARBRAND"].value_counts().index[0] if len(ud_clean) else "—"
    top_plug  = ud_clean["PLUG_TYPE"].value_counts().index[0] if len(ud_clean) else "—"

    kpi(u1,"Registered Users",f"{len(ud_clean):,}",f"{active:,} active accounts","up","#185FA5")
    kpi(u2,"Avg Wallet Balance",f"₱{avg_wallet:,.0f}","Across active users","up","#0F6E56")
    kpi(u3,"Top Car Brand",top_brand,f"{ud_clean['CARBRAND'].value_counts().iloc[0]:,} users","up","#BA7517")
    kpi(u4,"Most Common Plug",top_plug,f"{ud_clean['PLUG_TYPE'].value_counts().iloc[0]:,} users","up","#185FA5")

    br1, br2 = st.columns(2)
    with br1:
        st.markdown("**Car Brand Distribution (Top 10)**")
        brands = ud_clean["CARBRAND"].value_counts().head(10).reset_index()
        brands.columns = ["Brand","Users"]
        st.bar_chart(brands.set_index("Brand"), color="#185FA5", height=200)
    with br2:
        st.markdown("**Plug Type Distribution**")
        plugs = ud_clean["PLUG_TYPE"].value_counts().reset_index()
        plugs.columns = ["Plug Type","Users"]
        st.bar_chart(plugs.set_index("Plug Type"), color="#0F6E56", height=200)

# ── HOST PARTNER CONNECTOR DETAIL ────────────────────────────────────────────
if not is_company:
    st.markdown(f"<div class='sec-hdr'>🔌 Connector Detail — {sel_stations[0]}</div>",
                unsafe_allow_html=True)
    site_cps = cp[cp["STATIONNAME"] == sel_stations[0]].drop_duplicates("CHARGER_ID")
    if len(site_cps):
        cols = st.columns(min(len(site_cps), 5))
        for i, (_, row) in enumerate(site_cps.iterrows()):
            if i >= 5: break
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
    else:
        st.info("No connector data available for this station.")

# ── FOOTER ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:10px;color:#94A3B8'>"
    "EVOxCharge Analytics · AIM MAIDA Capstone · "
    "Real data: transactions, charge points, station profile, financials, user details · "
    "Built with Streamlit + PyDeck"
    "</div>", unsafe_allow_html=True)
