import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Upload Excel
st.title("Client Summary Report")

uploaded_file = st.file_uploader("Upload the Excel file", type=["xlsx"])

if uploaded_file:
    # Read sheets
    risk_alerts_df = pd.read_excel(uploaded_file, sheet_name="Portfolio Risk Alerts")
    position_df = pd.read_excel(uploaded_file, sheet_name="Portfolio Position")
    
    # Filter out asset class-like entries from client list
    asset_class_keywords = ["Cash", "Alternatives", "Equities", "Fixed Income", "Private Equity"]
    client_names = risk_alerts_df["Client Name"].dropna().unique()
    clean_client_names = [name for name in client_names if all(keyword.lower() not in str(name).lower() for keyword in asset_class_keywords)]
    
    selected_client = st.selectbox("Select Client for Summary Report", clean_client_names)

    if selected_client:
        # Filter data for selected client
        client_data = risk_alerts_df[risk_alerts_df["Client Name"] == selected_client]

        if not client_data.empty:
            st.subheader(f"Summary Report for {selected_client}")

            # Display relevant fields
            columns_of_interest = [
                "Client Name", "Risk Tolerance", "Return_ytd", "Return_inception",
                "Volatility_inception", "Current Drawdown", "Loan to Value",
                "Number of Warnings", "Number of Breaches"
            ]

            summary_data = client_data[columns_of_interest].copy()

            # Convert relevant columns to percentage format
            percent_cols = ["Return_ytd", "Return_inception", "Volatility_inception", "Current Drawdown", "Loan to Value"]
            for col in percent_cols:
                summary_data[col] = summary_data[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else "N/A")

            st.dataframe(summary_data.set_index("Client Name"))

            # Plotly Graph - Previous working version
            chart_data = client_data.iloc[0]
            labels = ["Return YTD", "Return Inception", "Volatility", "Drawdown", "Loan to Value"]
            values = [
                chart_data["Return_ytd"] * 100 if pd.notnull(chart_data["Return_ytd"]) else 0,
                chart_data["Return_inception"] * 100 if pd.notnull(chart_data["Return_inception"]) else 0,
                chart_data["Volatility_inception"] * 100 if pd.notnull(chart_data["Volatility_inception"]) else 0,
                chart_data["Current Drawdown"] * 100 if pd.notnull(chart_data["Current Drawdown"]) else 0,
                chart_data["Loan to Value"] * 100 if pd.notnull(chart_data["Loan to Value"]) else 0,
            ]

            fig = go.Figure(go.Bar(
                x=labels,
                y=values,
                marker_color='indianred',
                text=[f"{v:.2f}%" for v in values],
                textposition="auto"
            ))

            fig.update_layout(
                title=f"Key Metrics for {selected_client}",
                xaxis_title="Metric",
                yaxis_title="Percentage",
                yaxis_tickformat=".2f",
                template="plotly_white"
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No data available for selected client.")
