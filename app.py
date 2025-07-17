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
    for col in df.columns:
        if "Client" in col or "Account" in col:
            return col
    return None

def get_asset_class_col(df):
    for col in df.columns:
        if "Asset Class" in col or "Asset" in col:
            return col
    return None

# Extract unique clients from relevant sheets
def extract_clients(sheets):
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

# Extract unique asset classes from Exposure View and Portfolio Position combined
def extract_asset_classes(sheets):
    asset_classes = set()
    for sheet_name in ["Exposure View", "Portfolio Position"]:
        df = sheets.get(sheet_name, pd.DataFrame())
        if df.empty:
            continue
        asset_col = get_asset_class_col(df)
        if asset_col:
            asset_classes.update(df[asset_col].dropna().unique())
    return sorted(asset_classes)

client_names = extract_clients(sheets)
asset_classes = extract_asset_classes(sheets)

# Dropdowns for Client and Asset Class
selected_client = st.selectbox("Select Client for Summary Report", ["-- Select Client --"] + client_names)
selected_asset_class = st.selectbox("Select Asset Class for Cross-Client View", ["-- Select Asset Class --"] + asset_classes)

# Function to generate client summary report (same as before)
def generate_client_summary(client, sheets):
    report_data = {}

    risk_col_map = {
        "Risk Tolerance": "Risk Tolerance",
        "1D Return": "1D Return",
        "Target Return - ytd": "Target Return - YTD",
        "Actual Return - inception": "Actual Return - Inception",
        "Actual Volatility - inception": "Actual Volatility - Inception",
        "Drawdown Limit": "Drawdown Limit",
        "Actual Drawdown": "Actual Drawdown",
        "Drawdown Limit Utilization": "Drawdown Limit Utilization",
        "Loan to Value": "Loan to Value",
        "Concentrated Holdings": "Concentrated Holdings",
        "Net Asset Value": "Net Asset Value",
        "No. Portfolio Level Alert": "Portfolio Level Alert Count",
        "No. Instrument Level Alert": "Instrument Level Alert Count",
        "Total Number of Alerts": "Total Alert Count"
    }

    try:
        risk_df = sheets.get("Portfolio Risk Alerts", pd.DataFrame())
        risk_client_col = get_client_col(risk_df)
        filtered_risk = risk_df[risk_df[risk_client_col] == client] if risk_client_col else pd.DataFrame()

        if not filtered_risk.empty:
            first_row = filtered_risk.iloc[0]
            for key, col_name in risk_col_map.items():
                report_data[key] = first_row.get(col_name, "-")
    except Exception as e:
        st.warning(f"Error extracting risk data: {e}")

    # Also include Asset Class Summary from Exposure View for this client
    try:
        exposure_df = sheets.get("Exposure View", pd.DataFrame())
        exposure_client_col = get_client_col(exposure_df)
        asset_class_col = get_asset_class_col(exposure_df)
        if exposure_client_col and asset_class_col:
            filtered_exposure = exposure_df[exposure_df[exposure_client_col] == client]
            if not filtered_exposure.empty:
                asset_summary = filtered_exposure.groupby(asset_class_col).agg({
                    "Market Value": "sum",
                    "Quantity": "sum"
                }).reset_index()
                report_data["Asset Class Summary"] = asset_summary
    except Exception as e:
        st.warning(f"Error extracting exposure data: {e}")

    return report_data

def display_client_summary(report_data):
    if not report_data:
        st.warning("No data available for selected client.")
        return

    # Show main summary except Asset Class Summary
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

    # Bar chart of numeric key metrics
    plot_df = summary_df.melt(id_vars=["Account Name"] if "Account Name" in summary_df.columns else [])
    try:
        plot_df["value"] = pd.to_numeric(plot_df["value"], errors='coerce')
        plot_df = plot_df.dropna(subset=["value"])
        if not plot_df.empty:
            fig = px.bar(plot_df, x="variable", y="value", color="variable", title="Client Key Metrics", height=500)
            st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass

    # Show asset class summary if exists
    if "Asset Class Summary" in report_data:
        st.subheader("📊 Asset Class Breakdown")
        st.dataframe(report_data["Asset Class Summary"])

# Function to display accounts grouped by asset class filter (cross-client)
def display_accounts_by_asset_class(sheets, asset_class):
    if asset_class == "-- Select Asset Class --":
        st.info("Select an asset class to see account exposures.")
        return

    exposure_df = sheets.get("Exposure View", pd.DataFrame())
    position_df = sheets.get("Portfolio Position", pd.DataFrame())

    exposure_client_col = get_client_col(exposure_df)
    exposure_asset_col = get_asset_class_col(exposure_df)
    position_client_col = get_client_col(position_df)
    position_asset_col = get_asset_class_col(position_df)

    # Filter and combine Exposure View
    exposure_filtered = pd.DataFrame()
    if not exposure_df.empty and exposure_client_col and exposure_asset_col:
        exposure_filtered = exposure_df[exposure_df[exposure_asset_col] == asset_class][
            [exposure_client_col, exposure_asset_col, "Market Value", "Quantity"]].copy()

    # Filter and combine Portfolio Position
    position_filtered = pd.DataFrame()
    if not position_df.empty and position_client_col and position_asset_col:
        position_filtered = position_df[position_df[position_asset_col] == asset_class][
            [position_client_col, position_asset_col, "Market Value", "Quantity"]].copy()

    combined = pd.concat([exposure_filtered, position_filtered], ignore_index=True)

    if combined.empty:
        st.warning(f"No data found for asset class '{asset_class}'.")
        return

    # Group by client/account and aggregate
    combined_summary = combined.groupby(combined.columns[0]).agg({
        "Market Value": "sum",
        "Quantity": "sum"
    }).reset_index().rename(columns={combined.columns[0]: "Client / Account"})

    st.subheader(f"📋 Accounts with exposure in '{asset_class}'")
    st.dataframe(combined_summary)

# Show reports based on selections
if selected_client and selected_client != "-- Select Client --":
    client_report = generate_client_summary(selected_client, sheets)
    display_client_summary(client_report)

if selected_asset_class and selected_asset_class != "-- Select Asset Class --":
    display_accounts_by_asset_class(sheets, selected_asset_class)
