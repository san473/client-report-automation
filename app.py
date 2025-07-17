import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

st.set_page_config(layout="wide")

# File uploader
uploaded_file = st.file_uploader("Upload your Excel file", type=["xlsx"])

if uploaded_file:
    xls = pd.ExcelFile(uploaded_file)

    # Load necessary sheets
    risk_alerts_df = pd.read_excel(xls, "Portfolio Risk Alerts")
    consolidated_df = pd.read_excel(xls, "Consolidated View (Super User)")

    # Ensure consistent column names
    consolidated_df.columns = consolidated_df.columns.str.strip()
    client_names = consolidated_df['Account Name'].dropna().unique().tolist()

    # Remove known asset class names (these should not appear in client dropdown)
    asset_classes = ["Cash Balances", "Alternatives", "Equities", "Fixed Income", "Structured Products"]
    client_names = [name for name in client_names if name not in asset_classes]

    st.header("Client Summary Report")
    selected_client = st.selectbox("Select client for summary report", sorted(client_names))

    # Filter the data for the selected client
    client_df = consolidated_df[consolidated_df['Account Name'] == selected_client].copy()

    if not client_df.empty:
        # Format percentage columns
        percentage_columns = [
            "Return_1D", "Return_1W", "Return_2W", "Return_1M", "Return_3M", "Return_6M", "Return_1Y", "Return_2Y", "Return_inception", "Return_ytd",
            "Volatility_1W", "Volatility_2W", "Volatility_1M", "Volatility_3M", "Volatility_6M", "Volatility_1Y", "Volatility_2Y", "Volatility_inception", "Volatility_ytd",
            "Current Drawdown", "Loan to Value"
        ]

        for col in percentage_columns:
            if col in client_df.columns:
                client_df[col] = (client_df[col].astype(float) * 100).round(2).astype(str) + "%"

        st.subheader("Summary Table")
        st.dataframe(client_df.set_index("Account Name"))

        # Recalculate numeric values for plotting
        numeric_values = {}
        if 'Risk Tolerance' in client_df.columns:
            numeric_values['Risk Tolerance'] = float(client_df['Risk Tolerance'].iloc[0])
        if 'Loan to Value' in consolidated_df.columns:
            ltv_raw = consolidated_df[consolidated_df['Account Name'] == selected_client]['Loan to Value'].iloc[0]
            numeric_values['Loan to Value'] = float(ltv_raw)

        if numeric_values:
            st.subheader("Summary Graph (% values)")
            metrics = list(numeric_values.keys())
            values = list(numeric_values.values())

            fig, ax = plt.subplots(figsize=(10, 6))
            bars = ax.barh(metrics, values, color='crimson')
            ax.set_title(f"{selected_client} - Summary Metrics")
            ax.set_xlabel("Value (%)")
            ax.xaxis.set_major_formatter(mtick.PercentFormatter())

            for bar, value in zip(bars, values):
                ax.text(bar.get_width(), bar.get_y() + bar.get_height()/2,
                        f"{value:.2f}%", va='center', ha='left')

            st.pyplot(fig)

    else:
        st.warning("No data found for selected client.")
