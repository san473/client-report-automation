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

# Utility functions to find key columns
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

# Mapping of display labels to exact Excel column names in Portfolio Risk Alerts
risk_col_map = {
    "Risk Tolerance": "Risk Tolerance",
    "1D Return": "Return_1D",
    "1W Return": "Return_1W",
    "2W Return": "Return_2W",
    "1M Return": "Return_1M",
    "3M Return": "Return_3M",
    "6M Return": "Return_6M",
    "1Y Return": "Return_1Y",
    "2Y Return": "Return_2Y",
    "Return since inception": "Return_inception",
    "YTD Return": "Return_ytd",
    "1W Volatility": "Volatility_1W",
    "2W Volatility": "Volatility_2W",
    "1M Volatility": "Volatility_1M",
    "3M Volatility": "Volatility_3M",
    "6M Volatility": "Volatility_6M",
    "1Y Volatility": "Volatility_1Y",
    "2Y Volatility": "Volatility_2Y",
    "Volatility since inception": "Volatility_inception",
    "YTD Volatility": "Volatility_ytd",
    "Current Drawdown": "Current Drawdown",
    "Loan to Value": "Loan to Value",
    "Number of Warnings": "Number of Warnings",
    "Number of Breaches": "Number of Breaches"
}

def generate_client_summary(client, sheets):
    report_data = {}

    risk_df = sheets.get("Portfolio Risk Alerts", pd.DataFrame())
    if risk_df.empty:
        st.warning("Portfolio Risk Alerts sheet is empty or missing.")
        return {}

    risk_client_col = "Client Name"  # From your debug info
    filtered_risk = risk_df[risk_df[risk_client_col] == client]

    if filtered_risk.empty:
        st.warning(f"No Portfolio Risk Alerts data found for client '{client}'.")
        return {}

    first_row = filtered_risk.iloc[0]

    for display_name, col_name in risk_col_map.items():
        report_data[display_name] = first_row.get(col_name, "-")

    # Also include Asset Class Summary from Exposure View for this client
    exposure_df = sheets.get("Exposure View", pd.DataFrame())
    if not exposure_df.empty:
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
    plot_df = summary_df.melt(id_vars=[])
    plot_df["value"] = pd.to_numeric(plot_df["value"], errors='coerce')
    plot_df = plot_df.dropna(subset=["value"])
    if not plot_df.empty:
        fig = px.bar(plot_df, x="variable", y="value", color="variable", title="Client Key Metrics", height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No numeric data available for chart.")

    # Show asset class summary if exists
    if "Asset Class Summary" in report_data:
        st.subheader("📊 Asset Class Breakdown")
        st.dataframe(report_data["Asset Class Summary"])

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

    exposure_filtered = pd.DataFrame()
    if not exposure_df.empty and exposure_client_col and exposure_asset_col:
        exposure_filtered = exposure_df[exposure_df[exposure_asset_col] == asset_class][
            [exposure_client_col, exposure_asset_col, "Market Value", "Quantity"]].copy()

    position_filtered = pd.DataFrame()
    if not position_df.empty and position_client_col and position_asset_col:
        position_filtered = position_df[position_df[position_asset_col] == asset_class][
            [position_client_col, position_asset_col, "Market Value", "Quantity"]].copy()

    combined = pd.concat([exposure_filtered, position_filtered], ignore_index=True)

    if combined.empty:
        st.warning(f"No data found for asset class '{asset_class}'.")
        return

    combined_summary = combined.groupby(combined.columns[0]).agg({
        "Market Value": "sum",
        "Quantity": "sum"
    }).reset_index().rename(columns={combined.columns[0]: "Client / Account"})

    st.subheader(f"📋 Accounts with exposure in '{asset_class}'")
    st.dataframe(combined_summary)

# Main app logic

if selected_client and selected_client != "-- Select Client --":
    client_report = generate_client_summary(selected_client, sheets)
    display_client_summary(client_report)

if selected_asset_class and selected_asset_class != "-- Select Asset Class --":
    display_accounts_by_asset_class(sheets, selected_asset_class)
