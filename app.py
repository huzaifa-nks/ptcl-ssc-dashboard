import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="PTCL Executive SSC Dashboard", layout="wide")

# Custom Styling
st.markdown("<style>.metric-card {background-color: #f8f9fa; border-radius: 10px; padding: 15px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);}</style>", unsafe_allow_html=True)

st.title("🇵🇰 PTCL Daily SSC Complaint & Quality Analytics Dashboard")
st.caption("Comprehensive GPON vs Copper Performance Tracking | MTTR, Denial %, Repeat %, & 100 Per Line Rate")

# File Uploader
st.sidebar.header("📁 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Excel Dashboard File", type=["xlsx"])

if uploaded_file is None:
    st.info("👈 Please upload the 'Daily SSC Dashboard Data' Excel file from the sidebar to launch the dashboard.")
    st.stop()

@st.cache_data
def load_data(file_bytes):
    xls = pd.ExcelFile(file_bytes)
    base_df = pd.read_excel(xls, sheet_name='Base')
    denial_df = pd.read_excel(xls, sheet_name='Denial')
    repeat_df = pd.read_excel(xls, sheet_name='Repeat')
    mttr_df = pd.read_excel(xls, sheet_name='MTTR')
    
    # Cleaning numeric columns safely
    for df in [repeat_df, mttr_df, denial_df, base_df]:
        for col in df.columns:
            col_str = str(col)
            if any(k in col_str for k in ['Repeated', 'leadtime', 'SRs', 'HSI', 'BB', 'PSTN', 'IPTV', 'Count', 'DENIAL', 'CLAIMED']):
                df[col] = pd.to_numeric(df[col].replace('?', 0), errors='coerce').fillna(0)
                
    return base_df, denial_df, repeat_df, mttr_df

base_df, denial_df, repeat_df, mttr_df = load_data(uploaded_file)

# ------------------------------------------
# FILTERS: ZONE & REGION
# ------------------------------------------
st.sidebar.header("🔍 Filters")

# Clean raw data to exclude summary rows for filtering
valid_base = base_df[~base_df['CRM_REGION_NM'].isin(['NATIONAL', 'CENTRAL', 'NORTH', 'SOUTH'])].copy()

# Zone Filter
zones = ["All"] + sorted(list(valid_base['Zone_Region'].dropna().unique()))
selected_zone = st.sidebar.selectbox("Select Zone", zones)

# Region Filter (Dependent on Zone selection)
if selected_zone != "All":
    available_regions = sorted(list(valid_base[valid_base['Zone_Region'] == selected_zone]['CRM_REGION_NM'].dropna().unique()))
else:
    available_regions = sorted(list(valid_base['CRM_REGION_NM'].dropna().unique()))

regions = ["All"] + available_regions
selected_region = st.sidebar.selectbox("Select Region", regions)

# Filter Function
def filter_df(df):
    temp = df[~df['CRM_REGION_NM'].isin(['NATIONAL', 'CENTRAL', 'NORTH', 'SOUTH'])].copy()
    if selected_zone != "All":
        temp = temp[temp['Zone_Region'] == selected_zone]
    if selected_region != "All":
        temp = temp[temp['CRM_REGION_NM'] == selected_region]
    return temp

f_base = filter_df(base_df)
f_denial = filter_df(denial_df)
f_repeat = filter_df(repeat_df)
f_mttr = filter_df(mttr_df)

# ------------------------------------------
# METRIC CALCULATIONS
# ------------------------------------------
# Active Base
base_gpon = f_base['HSI_GPON_Count'].sum() + f_base['PSTN_GPON_Count'].sum() + f_base['IPTV_GPON_Count'].sum()
base_copper = f_base['Broadband_Count'].sum() + f_base['PSTN_Count'].sum() + f_base['IPTV_Count'].sum()

# SRs (Complaints)
srs_gpon = f_repeat['HSI'].sum() + f_repeat['PSTN_GPON'].sum() + f_repeat['IPTV_GPON'].sum()
srs_copper = f_repeat['BB'].sum() + f_repeat['PSTN'].sum() + f_repeat['IPTV'].sum()

# Repeat Complaints
repeat_gpon = f_repeat['HSI_Repeated'].sum() + f_repeat['PSTN_GPON_Repeated'].sum() + f_repeat['IPTV_GPON_Repeated'].sum()
repeat_copper = f_repeat['BB_Repeated'].sum() + f_repeat['PSTN_Repeated'].sum() + f_repeat['IPTV_Repeated'].sum()

# Denial Metrics
claim_gpon = f_denial['HSI_CLAIMED'].sum() + f_denial['PSTN_GPON_CLAIMED'].sum() + f_denial['IPTV_GPON_CLAIMED'].sum()
claim_copper = f_denial['BB_CLAIMED'].sum() + f_denial['PSTN_CLAIMED'].sum() + f_denial['IPTV_CLAIMED'].sum()

denial_gpon = f_denial['HSI_OBD_DENIAL'].sum() + f_denial['PSTN_GPON_OBD_DENIAL'].sum() + f_denial['IPTV_GPON_OBD_DENIAL'].sum()
denial_copper = f_denial['BB_OBD_DENIAL'].sum() + f_denial['PSTN_OBD_DENIAL'].sum() + f_denial['IPTV_OBD_DENIAL'].sum()

# MTTR Metrics
closed_gpon = f_mttr['HSI_SRs'].sum() + f_mttr['PSTN_GPON_SRs'].sum() + f_mttr['IPTV_GPON_SRs'].sum()
closed_copper = f_mttr['BB_SRs'].sum() + f_mttr['PSTN_SRs'].sum() + f_mttr['IPTV_SRs'].sum()

lt_gpon = f_mttr['HSI_leadtime'].sum() + f_mttr['PSTN_GPON_leadtime'].sum() + f_mttr['IPTV_GPON_leadtime'].sum()
lt_copper = f_mttr['BB_leadtime'].sum() + f_mttr['PSTN_leadtime'].sum() + f_mttr['IPTV_leadtime'].sum()

# Rates
mttr_gpon = (lt_gpon / 3600 / closed_gpon) if closed_gpon > 0 else 0
mttr_copper = (lt_copper / 3600 / closed_copper) if closed_copper > 0 else 0

denial_rate_gpon = (denial_gpon / claim_gpon * 100) if claim_gpon > 0 else 0
denial_rate_copper = (denial_copper / claim_copper * 100) if claim_copper > 0 else 0

repeat_rate_gpon = (repeat_gpon / srs_gpon * 100) if srs_gpon > 0 else 0
repeat_rate_copper = (repeat_copper / srs_copper * 100) if srs_copper > 0 else 0

per_100_gpon = (srs_gpon / base_gpon * 100) if base_gpon > 0 else 0
per_100_copper = (srs_copper / base_copper * 100) if base_copper > 0 else 0

# Totals
total_base = base_gpon + base_copper
total_srs = srs_gpon + srs_copper
total_closed = closed_gpon + closed_copper
total_lt = lt_gpon + lt_copper
total_claim = claim_gpon + claim_copper
total_denial = denial_gpon + denial_copper
total_repeat = repeat_gpon + repeat_copper

overall_mttr = (total_lt / 3600 / total_closed) if total_closed > 0 else 0
overall_denial_rate = (total_denial / total_claim * 100) if total_claim > 0 else 0
overall_repeat_rate = (total_repeat / total_srs * 100) if total_srs > 0 else 0
overall_100_per_line = (total_srs / total_base * 100) if total_base > 0 else 0

# ------------------------------------------
# EXECUTIVE OVERVIEW (TOP KPI CARDS)
# ------------------------------------------
st.markdown("### 📌 Executive Overview")
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)

kpi1.metric("📦 Active Base", f"{total_base:,.0f}")
kpi2.metric("⏱️ Overall MTTR", f"{overall_mttr:.2f} hrs")
kpi3.metric("🚫 OBD Denial %", f"{overall_denial_rate:.2f}%")
kpi4.metric("🔄 Repeat %", f"{overall_repeat_rate:.2f}%")
kpi5.metric("📈 100 Per Line Rate", f"{overall_100_per_line:.2f}")

st.markdown("---")

# ------------------------------------------
# DASHBOARD TABS
# ------------------------------------------
tab1, tab2, tab3 = st.tabs(["⚡ Technology Comparison (GPON vs Copper)", "🗺️ Region-Wise Deep Dive", "🛠️ Service Breakdown (BB / PSTN / IPTV)"])

with tab1:
    st.subheader("GPON vs Copper Performance Summary")
    
    comp_df = pd.DataFrame({
        "KPI Metric": ["Active Base Count", "Total Complaints (SRs)", "Closed SRs", "MTTR (Avg Hours)", "OBD Claimed SRs", "OBD Denials", "Denial Rate (%)", "Repeated SRs", "Repeat Rate (%)", "100 Per Line Rate"],
        "GPON (Fiber)": [f"{base_gpon:,.0f}", f"{srs_gpon:,.0f}", f"{closed_gpon:,.0f}", f"{mttr_gpon:.2f} hrs", f"{claim_gpon:,.0f}", f"{denial_gpon:,.0f}", f"{denial_rate_gpon:.2f}%", f"{repeat_gpon:,.0f}", f"{repeat_rate_gpon:.2f}%", f"{per_100_gpon:.2f}"],
        "Copper (Legacy)": [f"{base_copper:,.0f}", f"{srs_copper:,.0f}", f"{closed_copper:,.0f}", f"{mttr_copper:.2f} hrs", f"{claim_copper:,.0f}", f"{denial_copper:,.0f}", f"{denial_rate_copper:.2f}%", f"{repeat_copper:,.0f}", f"{repeat_rate_copper:.2f}%", f"{per_100_copper:.2f}"]
    })
    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        fig1 = go.Figure(data=[
            go.Bar(name='GPON', x=['MTTR (Hours)', '100 Per Line'], y=[mttr_gpon, per_100_gpon], marker_color='#00CC96'),
            go.Bar(name='Copper', x=['MTTR (Hours)', '100 Per Line'], y=[mttr_copper, per_100_copper], marker_color='#EF553B')
        ])
        fig1.update_layout(barmode='group', title="MTTR vs 100 Per Line Rate")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = go.Figure(data=[
            go.Bar(name='GPON', x=['Denial %', 'Repeat %'], y=[denial_rate_gpon, repeat_rate_gpon], marker_color='#00CC96'),
            go.Bar(name='Copper', x=['Denial %', 'Repeat %'], y=[denial_rate_copper, repeat_rate_copper], marker_color='#EF553B')
        ])
        fig2.update_layout(barmode='group', title="Denial % vs Repeat %")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("🗺️ Region-Wise Performance Metrics")
    
    # Calculating Region-level aggregations
    reg_summary = []
    for reg in f_base['CRM_REGION_NM'].unique():
        b_sub = f_base[f_base['CRM_REGION_NM'] == reg]
        m_sub = f_mttr[f_mttr['CRM_REGION_NM'] == reg]
        r_sub = f_repeat[f_repeat['CRM_REGION_NM'] == reg]
        d_sub = f_denial[f_denial['CRM_REGION_NM'] == reg]
        
        r_base = b_sub['HSI_GPON_Count'].sum() + b_sub['PSTN_GPON_Count'].sum() + b_sub['IPTV_GPON_Count'].sum() + b_sub['Broadband_Count'].sum() + b_sub['PSTN_Count'].sum() + b_sub['IPTV_Count'].sum()
        r_srs = r_sub['HSI'].sum() + r_sub['PSTN_GPON'].sum() + r_sub['IPTV_GPON'].sum() + r_sub['BB'].sum() + r_sub['PSTN'].sum() + r_sub['IPTV'].sum()
        
        r_closed = m_sub['HSI_SRs'].sum() + m_sub['PSTN_GPON_SRs'].sum() + m_sub['IPTV_GPON_SRs'].sum() + m_sub['BB_SRs'].sum() + m_sub['PSTN_SRs'].sum() + m_sub['IPTV_SRs'].sum()
        r_lt = m_sub['HSI_leadtime'].sum() + m_sub['PSTN_GPON_leadtime'].sum() + m_sub['IPTV_GPON_leadtime'].sum() + m_sub['BB_leadtime'].sum() + m_sub['PSTN_leadtime'].sum() + m_sub['IPTV_leadtime'].sum()
        
        r_claim = d_sub['HSI_CLAIMED'].sum() + d_sub['PSTN_GPON_CLAIMED'].sum() + d_sub['IPTV_GPON_CLAIMED'].sum() + d_sub['BB_CLAIMED'].sum() + d_sub['PSTN_CLAIMED'].sum() + d_sub['IPTV_CLAIMED'].sum()
        r_denial = d_sub['HSI_OBD_DENIAL'].sum() + d_sub['PSTN_GPON_OBD_DENIAL'].sum() + d_sub['IPTV_GPON_OBD_DENIAL'].sum() + d_sub['BB_OBD_DENIAL'].sum() + d_sub['PSTN_OBD_DENIAL'].sum() + d_sub['IPTV_OBD_DENIAL'].sum()
        r_rep = r_sub['HSI_Repeated'].sum() + r_sub['PSTN_GPON_Repeated'].sum() + r_sub['IPTV_GPON_Repeated'].sum() + r_sub['BB_Repeated'].sum() + r_sub['PSTN_Repeated'].sum() + r_sub['IPTV_Repeated'].sum()
        
        r_mttr = (r_lt / 3600 / r_closed) if r_closed > 0 else 0
        r_denial_pct = (r_denial / r_claim * 100) if r_claim > 0 else 0
        r_rep_pct = (r_rep / r_srs * 100) if r_srs > 0 else 0
        r_100_rate = (r_srs / r_base * 100) if r_base > 0 else 0
        
        reg_summary.append({
            "Region": reg,
            "Active Base": r_base,
            "Total SRs": r_srs,
            "MTTR (Hrs)": round(r_mttr, 2),
            "Denial %": round(r_denial_pct, 2),
            "Repeat %": round(r_rep_pct, 2),
            "100 Per Line": round(r_100_rate, 2)
        })
        
    rdf = pd.DataFrame(reg_summary).sort_values(by="Total SRs", ascending=False)
    st.dataframe(rdf, use_container_width=True, hide_index=True)
    
    # Regional Visual Comparisons
    fig_reg = px.bar(rdf, x="Region", y=["MTTR (Hrs)", "100 Per Line"], barmode="group", title="Regional Comparison: MTTR vs 100 Per Line Rate")
    st.plotly_chart(fig_reg, use_container_width=True)

with tab3:
    st.subheader("🛠️ Granular Service-Wise Breakdown")
    
    # Service Breakdown Dataframe
    svc_data = {
        "Service": ["GPON Broadband (HSI)", "GPON PSTN", "GPON IPTV", "Copper Broadband (BB)", "Copper PSTN", "Copper IPTV"],
        "Active Base": [
            f_base['HSI_GPON_Count'].sum(), f_base['PSTN_GPON_Count'].sum(), f_base['IPTV_GPON_Count'].sum(),
            f_base['Broadband_Count'].sum(), f_base['PSTN_Count'].sum(), f_base['IPTV_Count'].sum()
        ],
        "Complaints (SRs)": [
            f_repeat['HSI'].sum(), f_repeat['PSTN_GPON'].sum(), f_repeat['IPTV_GPON'].sum(),
            f_repeat['BB'].sum(), f_repeat['PSTN'].sum(), f_repeat['IPTV'].sum()
        ],
        "Repeated SRs": [
            f_repeat['HSI_Repeated'].sum(), f_repeat['PSTN_GPON_Repeated'].sum(), f_repeat['IPTV_GPON_Repeated'].sum(),
            f_repeat['BB_Repeated'].sum(), f_repeat['PSTN_Repeated'].sum(), f_repeat['IPTV_Repeated'].sum()
        ],
        "OBD Denials": [
            f_denial['HSI_OBD_DENIAL'].sum(), f_denial['PSTN_GPON_OBD_DENIAL'].sum(), f_denial['IPTV_GPON_OBD_DENIAL'].sum(),
            f_denial['BB_OBD_DENIAL'].sum(), f_denial['PSTN_OBD_DENIAL'].sum(), f_denial['IPTV_OBD_DENIAL'].sum()
        ]
    }
    svc_df = pd.DataFrame(svc_data)
    
    # Calculate Service Level Rates safely
    svc_df['Repeat %'] = (svc_df['Repeated SRs'] / svc_df['Complaints (SRs)'] * 100).fillna(0).round(2)
    svc_df['100 Per Line'] = (svc_df['Complaints (SRs)'] / svc_df['Active Base'] * 100).fillna(0).round(2)
    
    st.dataframe(svc_df, use_container_width=True, hide_index=True)
    
    fig_svc = px.pie(svc_df, values='Complaints (SRs)', names='Service', title='Share of Complaints by Service Category', hole=0.4)
    st.plotly_chart(fig_svc, use_container_width=True)
