import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ------------------------------------------
# PAGE CONFIG & STYLING
# ------------------------------------------
st.set_page_config(
    page_title="PTCL Executive SSC Dashboard",
    page_icon="🇵🇰",
    layout="wide"
)

st.title("🇵🇰 PTCL Daily SSC Complaint & Quality Analytics Dashboard")
st.caption("Granular Product-Wise & Technology Tracking | MTTR, Denial %, Repeat %, & 100 Per Line Rate")

# ------------------------------------------
# FILE UPLOADER & DATA LOAD
# ------------------------------------------
st.sidebar.header("📁 Data Source")
uploaded_file = st.sidebar.file_uploader("Upload Excel Dashboard File", type=["xlsx"])

if uploaded_file is None:
    st.info("👈 Please upload the 'Daily SSC Dashboard Data' Excel file from the sidebar to launch the dashboard.")
    st.stop()

@st.cache_data(show_spinner="Processing Dashboard Data...")
def load_data(file_bytes):
    xls = pd.ExcelFile(file_bytes)
    base_df = pd.read_excel(xls, sheet_name='Base')
    denial_df = pd.read_excel(xls, sheet_name='Denial')
    repeat_df = pd.read_excel(xls, sheet_name='Repeat')
    mttr_df = pd.read_excel(xls, sheet_name='MTTR')

    for df in [base_df, denial_df, repeat_df, mttr_df]:
        # Standardize Date Columns
        d_cols = [c for c in df.columns if 'date' in str(c).lower() or 'dt' in str(c).lower() or 'state' in str(c).lower()]
        if d_cols:
            df.rename(columns={d_cols[0]: 'Date_Col_Standard'}, inplace=True)
            df['Date_Col_Standard'] = pd.to_datetime(df['Date_Col_Standard'], errors='coerce').dt.strftime('%Y-%m-%d')

        # Clean Numeric Columns
        numeric_keywords = ['Repeated', 'leadtime', 'SRs', 'HSI', 'BB', 'PSTN', 'IPTV', 'Count', 'DENIAL', 'CLAIMED', 'Broadband']
        for col in df.columns:
            if any(k in str(col) for k in numeric_keywords):
                df[col] = pd.to_numeric(df[col].replace('?', 0), errors='coerce').fillna(0)

    return base_df, denial_df, repeat_df, mttr_df

base_df, denial_df, repeat_df, mttr_df = load_data(uploaded_file)

summary_names = ['NATIONAL', 'CENTRAL', 'NORTH', 'SOUTH', 'TOTAL', 'NATIONAL TOTAL']

# Filtered list for UI dropdowns
valid_base = base_df[~base_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)].copy()

# ------------------------------------------
# FILTERS: DATE, ZONE & REGION
# ------------------------------------------
st.sidebar.header("🔍 Dynamic Filters")

if 'Date_Col_Standard' in base_df.columns:
    available_dates = sorted(base_df['Date_Col_Standard'].dropna().unique(), reverse=True)
    selected_date = st.sidebar.selectbox("Select Date", available_dates)
else:
    selected_date = None

# Zone Selector
zones = ["All"] + sorted([str(z) for z in valid_base['Zone_Region'].dropna().unique() if pd.notna(z)])
selected_zone = st.sidebar.selectbox("Select Zone", zones)

# Region Selector
if selected_zone != "All":
    available_regions = sorted([str(r) for r in valid_base[valid_base['Zone_Region'] == selected_zone]['CRM_REGION_NM'].dropna().unique() if pd.notna(r)])
else:
    available_regions = sorted([str(r) for r in valid_base['CRM_REGION_NM'].dropna().unique() if pd.notna(r)])

regions = ["All"] + available_regions
selected_region = st.sidebar.selectbox("Select Region", regions)

# ------------------------------------------
# EXACT BASE & ACTIVITY FILTERING LOGIC
# ------------------------------------------
def get_base_subset(df):
    temp = df.copy()
    if 'Date_Col_Standard' in temp.columns and selected_date:
        temp = temp[temp['Date_Col_Standard'] == selected_date]

    if selected_zone == "All" and selected_region == "All":
        nat_row = temp[temp['CRM_REGION_NM'].astype(str).str.strip().str.upper() == 'NATIONAL']
        if not nat_row.empty:
            return nat_row.iloc[[0]]
        else:
            return temp[~temp['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)]
            
    elif selected_zone != "All" and selected_region == "All":
        zone_row = temp[temp['CRM_REGION_NM'].astype(str).str.strip().str.upper() == selected_zone.upper()]
        if not zone_row.empty:
            return zone_row.iloc[[0]]
        else:
            return temp[temp['Zone_Region'] == selected_zone]
    else:
        return temp[temp['CRM_REGION_NM'] == selected_region]

def get_activity_subset(df):
    temp = df[~df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)].copy()
    if 'Date_Col_Standard' in temp.columns and selected_date:
        temp = temp[temp['Date_Col_Standard'] == selected_date]

    if selected_zone != "All":
        temp = temp[temp['Zone_Region'] == selected_zone]
    if selected_region != "All":
        temp = temp[temp['CRM_REGION_NM'] == selected_region]
    return temp

f_base = get_base_subset(base_df)
f_denial = get_activity_subset(denial_df)
f_repeat = get_activity_subset(repeat_df)
f_mttr = get_activity_subset(mttr_df)

# ------------------------------------------
# PRODUCT-WISE INDIVIDUAL CALCULATIONS
# ------------------------------------------
# GPON Broadband (HSI)
base_hsi = f_base['HSI_GPON_Count'].sum()
srs_hsi = f_repeat['HSI'].sum()
rep_hsi = f_repeat['HSI_Repeated'].sum()
claim_hsi = f_denial['HSI_CLAIMED'].sum()
denial_hsi = f_denial['HSI_OBD_DENIAL'].sum()
closed_hsi = f_mttr['HSI_SRs'].sum()
lt_hsi = f_mttr['HSI_leadtime'].sum()

# GPON PSTN
base_pstn_gpon = f_base['PSTN_GPON_Count'].sum()
srs_pstn_gpon = f_repeat['PSTN_GPON'].sum()
rep_pstn_gpon = f_repeat['PSTN_GPON_Repeated'].sum()
claim_pstn_gpon = f_denial['PSTN_GPON_CLAIMED'].sum()
denial_pstn_gpon = f_denial['PSTN_GPON_OBD_DENIAL'].sum()
closed_pstn_gpon = f_mttr['PSTN_GPON_SRs'].sum()
lt_pstn_gpon = f_mttr['PSTN_GPON_leadtime'].sum()

# GPON IPTV
base_iptv_gpon = f_base['IPTV_GPON_Count'].sum()
srs_iptv_gpon = f_repeat['IPTV_GPON'].sum()
rep_iptv_gpon = f_repeat['IPTV_GPON_Repeated'].sum()
claim_iptv_gpon = f_denial['IPTV_GPON_CLAIMED'].sum()
denial_iptv_gpon = f_denial['IPTV_GPON_OBD_DENIAL'].sum()
closed_iptv_gpon = f_mttr['IPTV_GPON_SRs'].sum()
lt_iptv_gpon = f_mttr['IPTV_GPON_leadtime'].sum()

# Copper Broadband (BB)
base_bb = f_base['Broadband_Count'].sum()
srs_bb = f_repeat['BB'].sum()
rep_bb = f_repeat['BB_Repeated'].sum()
claim_bb = f_denial['BB_CLAIMED'].sum()
denial_bb = f_denial['BB_OBD_DENIAL'].sum()
closed_bb = f_mttr['BB_SRs'].sum()
lt_bb = f_mttr['BB_leadtime'].sum()

# Copper PSTN
base_pstn = f_base['PSTN_Count'].sum()
srs_pstn = f_repeat['PSTN'].sum()
rep_pstn = f_repeat['PSTN_Repeated'].sum()
claim_pstn = f_denial['PSTN_CLAIMED'].sum()
denial_pstn = f_denial['PSTN_OBD_DENIAL'].sum()
closed_pstn = f_mttr['PSTN_SRs'].sum()
lt_pstn = f_mttr['PSTN_leadtime'].sum()

# Copper IPTV
base_iptv = f_base['IPTV_Count'].sum()
srs_iptv = f_repeat['IPTV'].sum()
rep_iptv = f_repeat['IPTV_Repeated'].sum()
claim_iptv = f_denial['IPTV_CLAIMED'].sum()
denial_iptv = f_denial['IPTV_OBD_DENIAL'].sum()
closed_iptv = f_mttr['IPTV_SRs'].sum()
lt_iptv = f_mttr['IPTV_leadtime'].sum()

# ------------------------------------------
# AGGREGATIONS (GPON vs COPPER vs OVERALL)
# ------------------------------------------
base_gpon = base_hsi + base_pstn_gpon + base_iptv_gpon
base_copper = base_bb + base_pstn + base_iptv

srs_gpon = srs_hsi + srs_pstn_gpon + srs_iptv_gpon
srs_copper = srs_bb + srs_pstn + srs_iptv

repeat_gpon = rep_hsi + rep_pstn_gpon + rep_iptv_gpon
repeat_copper = rep_bb + rep_pstn + rep_iptv

claim_gpon = claim_hsi + claim_pstn_gpon + claim_iptv_gpon
claim_copper = claim_bb + claim_pstn + claim_iptv

denial_gpon = denial_hsi + denial_pstn_gpon + denial_iptv_gpon
denial_copper = denial_bb + denial_pstn + denial_iptv

closed_gpon = closed_hsi + closed_pstn_gpon + closed_iptv_gpon
closed_copper = closed_bb + closed_pstn + closed_iptv

lt_gpon = lt_hsi + lt_pstn_gpon + lt_iptv_gpon
lt_copper = lt_bb + lt_pstn + lt_iptv

# Tech Rates
mttr_gpon = (lt_gpon / 3600 / closed_gpon) if closed_gpon > 0 else 0
mttr_copper = (lt_copper / 3600 / closed_copper) if closed_copper > 0 else 0

denial_rate_gpon = (denial_gpon / claim_gpon * 100) if claim_gpon > 0 else 0
denial_rate_copper = (denial_copper / claim_copper * 100) if claim_copper > 0 else 0

repeat_rate_gpon = (repeat_gpon / srs_gpon * 100) if srs_gpon > 0 else 0
repeat_rate_copper = (repeat_copper / srs_copper * 100) if srs_copper > 0 else 0

per_100_gpon = (srs_gpon / base_gpon * 100) if base_gpon > 0 else 0
per_100_copper = (srs_copper / base_copper * 100) if base_copper > 0 else 0

# Grand Totals
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
tab1, tab2, tab3 = st.tabs(["⚡ Technology Comparison (GPON vs Copper)", "🛠️ Product-Wise Granular Breakdown", "🗺️ Region-Wise Deep Dive"])

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
            go.Bar(name='GPON', x=['MTTR (Hours)', '100 Per Line'], y=[mttr_gpon, per_100_gpon], marker_color='#00CC96', texttemplate='%{y:.2f}', textposition='outside'),
            go.Bar(name='Copper', x=['MTTR (Hours)', '100 Per Line'], y=[mttr_copper, per_100_copper], marker_color='#EF553B', texttemplate='%{y:.2f}', textposition='outside')
        ])
        fig1.update_layout(barmode='group', title="MTTR vs 100 Per Line Rate", template="plotly_white")
        st.plotly_chart(fig1, use_container_width=True)

    with c2:
        fig2 = go.Figure(data=[
            go.Bar(name='GPON', x=['Denial %', 'Repeat %'], y=[denial_rate_gpon, repeat_rate_gpon], marker_color='#00CC96', texttemplate='%{y:.2f}%', textposition='outside'),
            go.Bar(name='Copper', x=['Denial %', 'Repeat %'], y=[denial_rate_copper, repeat_rate_copper], marker_color='#EF553B', texttemplate='%{y:.2f}%', textposition='outside')
        ])
        fig2.update_layout(barmode='group', title="Denial % vs Repeat %", template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    st.subheader("🛠️ Product-Wise Complete Performance Matrix")
    
    products_data = [
        {"Product": "GPON Broadband (HSI)", "Tech": "GPON", "Base": base_hsi, "SRs": srs_hsi, "Closed": closed_hsi, "LeadTime": lt_hsi, "Claimed": claim_hsi, "Denials": denial_hsi, "Repeats": rep_hsi},
        {"Product": "GPON PSTN", "Tech": "GPON", "Base": base_pstn_gpon, "SRs": srs_pstn_gpon, "Closed": closed_pstn_gpon, "LeadTime": lt_pstn_gpon, "Claimed": claim_pstn_gpon, "Denials": denial_pstn_gpon, "Repeats": rep_pstn_gpon},
        {"Product": "GPON IPTV", "Tech": "GPON", "Base": base_iptv_gpon, "SRs": srs_iptv_gpon, "Closed": closed_iptv_gpon, "LeadTime": lt_iptv_gpon, "Claimed": claim_iptv_gpon, "Denials": denial_iptv_gpon, "Repeats": rep_iptv_gpon},
        {"Product": "Copper Broadband (BB)", "Tech": "Copper", "Base": base_bb, "SRs": srs_bb, "Closed": closed_bb, "LeadTime": lt_bb, "Claimed": claim_bb, "Denials": denial_bb, "Repeats": rep_bb},
        {"Product": "Copper PSTN", "Tech": "Copper", "Base": base_pstn, "SRs": srs_pstn, "Closed": closed_pstn, "LeadTime": lt_pstn, "Claimed": claim_pstn, "Denials": denial_pstn, "Repeats": rep_pstn},
        {"Product": "Copper IPTV", "Tech": "Copper", "Base": base_iptv, "SRs": srs_iptv, "Closed": closed_iptv, "LeadTime": lt_iptv, "Claimed": claim_iptv, "Denials": denial_iptv, "Repeats": rep_iptv},
    ]
    
    p_df = pd.DataFrame(products_data)
    p_df['MTTR (Hrs)'] = (p_df['LeadTime'] / 3600 / p_df['Closed']).fillna(0).round(2)
    p_df['Denial %'] = (p_df['Denials'] / p_df['Claimed'] * 100).fillna(0).round(2)
    p_df['Repeat %'] = (p_df['Repeats'] / p_df['SRs'] * 100).fillna(0).round(2)
    p_df['100 Per Line'] = (p_df['SRs'] / p_df['Base'] * 100).fillna(0).round(2)
    
    disp_p_df = p_df[['Product', 'Tech', 'Base', 'SRs', 'Repeats', 'Denials', 'MTTR (Hrs)', 'Denial %', 'Repeat %', '100 Per Line']].copy()
    disp_p_df['Base'] = disp_p_df['Base'].map('{:,.0f}'.format)
    disp_p_df['SRs'] = disp_p_df['SRs'].map('{:,.0f}'.format)
    disp_p_df['Repeats'] = disp_p_df['Repeats'].map('{:,.0f}'.format)
    disp_p_df['Denials'] = disp_p_df['Denials'].map('{:,.0f}'.format)
    
    st.dataframe(disp_p_df, use_container_width=True, hide_index=True)

with tab3:
    st.subheader("🗺️ Region-Wise Performance Summary")

    reg_summary = []
    reg_base = base_df[(base_df['Date_Col_Standard'] == selected_date) & (~base_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names))] if selected_date else base_df[~base_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)]
    reg_mttr = mttr_df[(mttr_df['Date_Col_Standard'] == selected_date) & (~mttr_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names))] if selected_date else mttr_df[~mttr_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)]
    reg_repeat = repeat_df[(repeat_df['Date_Col_Standard'] == selected_date) & (~repeat_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names))] if selected_date else repeat_df[~repeat_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)]
    reg_denial = denial_df[(denial_df['Date_Col_Standard'] == selected_date) & (~denial_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names))] if selected_date else denial_df[~denial_df['CRM_REGION_NM'].astype(str).str.strip().str.upper().isin(summary_names)]

    for reg in sorted(reg_base['CRM_REGION_NM'].dropna().unique()):
        b_sub = reg_base[reg_base['CRM_REGION_NM'] == reg]
        m_sub = reg_mttr[reg_mttr['CRM_REGION_NM'] == reg]
        r_sub = reg_repeat[reg_repeat['CRM_REGION_NM'] == reg]
        d_sub = reg_denial[reg_denial['CRM_REGION_NM'] == reg]
        
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
