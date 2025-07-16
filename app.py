import streamlit as st
import pandas as pd

st.set_page_config(page_title="Client Report Generator", layout="wide")

st.title("📊 Lighthouse Canton – Client Reporting Tool")

# --- Upload Excel File ---
uploaded_file = st.file_uploader("Upload the Risk Dashboard Excel file (.xlsm)", type=["xlsm"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    # Load relevant sheets
    risk_df = pd.read_excel(xls, sheet_name="Portfolio Risk Alerts")
    cons_df = pd.read_excel(xls, sheet_name="Consolidated View_Super User", header=8, usecols="B:Q")
    position_df = pd.read_excel(xls, sheet_name="Portfolio Position")
    exposure_df = pd.read_excel(xls, sheet_name="Exposure View")

    # Extract client names from each sheet
    clients_risk = risk_df["Client Name"].dropna().astype(str).str.strip()
    clients_cons = cons_df["Account Name"].dropna().astype(str).str.strip()
    clients_position = position_df["Client Name"].dropna().astype(str).str.strip() if "Client Name" in position_df.columns else []
    clients_exposure = exposure_df["Client Name"].dropna().astype(str).str.strip() if "Client Name" in exposure_df.columns else []

    # Combine all client names (normalized) but display original
    all_clients_raw = pd.Series(
        list(clients_risk) + list(clients_cons) + list(clients_position) + list(clients_exposure)
    )
    all_clients = all_clients_raw.drop_duplicates().sort_values()

    # Client dropdown
    selected_client = st.selectbox("Select a client to generate report", all_clients)

    # ---- Filter data for selected client ----
    risk_data = risk_df[risk_df["Client Name"].astype(str).str.strip() == selected_client]
    cons_data = cons_df[cons_df["Account Name"].astype(str).str.strip() == selected_client]
    pos_data = position_df[position_df["Client Name"].astype(str).str.strip() == selected_client]
    exp_data = exposure_df[exposure_df["Client Name"].astype(str).str.strip() == selected_client]

    # --- Display section ---
    st.subheader("📌 Portfolio Risk Alerts")
    st.dataframe(risk_data, use_container_width=True)

    st.subheader("📌 Consolidated Summary")
    st.dataframe(cons_data, use_container_width=True)

    st.subheader("📌 Portfolio Positions")
    st.dataframe(pos_data, use_container_width=True)

    st.subheader("📌 Exposure Overview")
    st.dataframe(exp_data, use_container_width=True)

else:
    st.info("Please upload your Risk Dashboard Excel file to begin.")

import plotly.express as px
import plotly.graph_objects as go

st.markdown("---")
st.header("📊 Client Visual Summary")

# --- Pie Chart: Asset Allocation ---
if not exp_data.empty:
    pie_data = exp_data.groupby("assetClassName")["Sum of marketValueBase"].sum().reset_index()
    pie_fig = px.pie(
        pie_data,
        values="Sum of marketValueBase",
        names="assetClassName",
        title="Asset Allocation by Asset Class",
        color_discrete_sequence=px.colors.sequential.Reds
    )
    st.plotly_chart(pie_fig, use_container_width=True)

# --- Bar Chart: Alerts by Period ---
alert_cols = [col for col in risk_data.columns if "Alert Status" in col and "Return_" in col]
if not risk_data.empty and alert_cols:
    alert_counts = risk_data[alert_cols].apply(lambda x: (x == "Breach").sum(), axis=0)
    alert_chart = px.bar(
        x=alert_counts.index.str.replace("_Alert Status", ""),
        y=alert_counts.values,
        labels={"x": "Return Period", "y": "Breach Count"},
        title="Return Alert Breaches by Period",
        color_discrete_sequence=["#B30000"]
    )
    st.plotly_chart(alert_chart, use_container_width=True)

# --- KPI Metrics from Consolidated View ---
if not cons_data.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Drawdown", f"{cons_data['Actual Drawdown'].values[0]:.2%}")
    col2.metric("YTD Target Return", f"{cons_data['Target Return - ytd'].values[0]:.2%}")
    col3.metric("Net Asset Value", f"{cons_data['Net Asset Value'].values[0]:,.0f}")
