import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Client Risk Report", layout="wide")
st.title("📊 Client Risk Report Dashboard")

FILE_PATH = "Risk Dashboard_Super User_20241031.xlsm"

@st.cache_data
def load_excel(file_path):
    try:
        xls = pd.ExcelFile(file_path)
        sheets = {sheet: xls.parse(sheet) for sheet in xls.sheet_names}
        return sheets
    except Exception as e:
        st.error(f"Error loading file: {e}")
        return {}

sheets = load_excel(FILE_PATH)

def get_client_col(df):
    """Find the first column with 'Client' or 'Account' in its name."""
    for col in df.columns:
        if "Client" in col or "Account" in col:
            return col
    return None

def extract_clients(sheets):
    """Extract unique client names from all relevant sheets."""
    relevant_sheets = ["Portfolio Risk Alerts", "Portfolio Position", "Exposure View", "Consolidated View (Super User)"]
    client_names = set()
    for sheet_name in relevant_sheets:
        df = sheets.get(sheet_name, pd.DataFrame())
        if df.empty:
            continue
        client_col = get_client_col(df)
        if client_col:
            client_names.update(df[client_col].dropna().unique())
    return sorted(client_names)

client_names = extract_clients(sheets)

selected_client = st.selectbox("Select Client", client_names)

def generate_summary(client, sheets):
    report_data = {}

    # Portfolio Risk Alerts summary
    try:
        risk_df = sheets.get("Portfolio Risk Alerts", pd.DataFrame())
        risk_client_col = get_client_col(risk_df)
        filtered_risk = risk_df[risk_df[risk_client_col] == client] if risk_client_col else pd.DataFrame()

        if not filtered_risk.empty:
            first_row = filtered_risk.iloc[0]
            report_data.update({
                "Account Name": client,
                "Risk Tolerance": first_row.get("Risk Tolerance", "-"),
                "1D Return": first_row.get("1D Return", "-"),
                "Target Return - ytd": first_row.get("Target Return - YTD", "-"),
                "Actual Return - inception": first_row.get("Actual Return - Inception", "-"),
                "Actual Volatility - inception": first_row.get("Actual Volatility - Inception", "-"),
                "Drawdown Limit": first_row.get("Drawdown Limit", "-"),
                "Actual Drawdown": first_row.get("Actual Drawdown", "-"),
                "Drawdown Limit Utilization": first_row.get("Drawdown Limit Utilization", "-"),
                "Loan to Value": first_row.get("Loan to Value", "-"),
                "Concentrated Holdings": first_row.get("Concentrated Holdings", "-"),
                "Net Asset Value": first_row.get("Net Asset Value", "-"),
                "No. Portfolio Level Alert": first_row.get("Portfolio Level Alert Count", "-"),
                "No. Instrument Level Alert": first_row.get("Instrument Level Alert Count", "-"),
                "Total Number of Alerts": first_row.get("Total Alert Count", "-")
            })
    except Exception as e:
        st.warning(f"Error extracting risk data: {e}")

    # Asset Class summary from Exposure View
    try:
        exposure_df = sheets.get("Exposure View", pd.DataFrame())
        exposure_client_col = get_client_col(exposure_df)
        if exposure_client_col:
            filtered_exposure = exposure_df[exposure_df[exposure_client_col] == client]
            if not filtered_exposure.empty and "Asset Class" in filtered_exposure.columns:
                asset_summary = filtered_exposure.groupby("Asset Class").agg({
                    "Market Value": "sum",
                    "Quantity": "sum"
                }).reset_index()
                report_data["Asset Class Summary"] = asset_summary
    except Exception as e:
        st.warning(f"Error extracting exposure data: {e}")

    return report_data

def display_report(report_data):
    if not report_data:
        st.warning("No data available for selected client.")
        return

    # Display main summary metrics (excluding Asset Class Summary)
    summary_keys = [k for k in report_data.keys() if k != "Asset Class Summary"]
    summary_df = pd.DataFrame([{k: report_data[k] for k in summary_keys}])
    st.subheader("📄 Summary Report")
    st.dataframe(summary_df.style.set_properties(**{
        'background-color': 'white',
        'color': 'black',
        'border-color': 'gray',
        'border-style': 'solid',
        'border-width': '1px'
    }))

    # Plot key numeric metrics in a bar chart
    plot_df = summary_df.melt(id_vars=["Account Name"])
    try:
        plot_df["value"] = pd.to_numeric(plot_df["value"], errors='coerce')
        plot_df = plot_df.dropna(subset=["value"])
        if not plot_df.empty:
            fig = px.bar(plot_df, x="variable", y="value", color="variable", title="Client Key Metrics", height=500)
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

    # Display asset class summary table if exists
    if "Asset Class Summary" in report_data:
        st.subheader("📊 Asset Class Summary")
        st.dataframe(report_data["Asset Class Summary"])

if selected_client:
    report = generate_summary(selected_client, sheets)
    display_report(report)
