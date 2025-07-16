import streamlit as st
import pandas as pd

# Load Excel file
xls = pd.ExcelFile("Risk Dashboard_Super User_20241031.xlsm")

# Load Portfolio Risk Alerts sheet normally
risk_df = pd.read_excel(xls, sheet_name="Portfolio Risk Alerts")

# Load Consolidated View sheet with correct header row and columns from B onwards
cons_df = pd.read_excel(
    xls,
    sheet_name="Consolidated View_Super User",
    header=8,       # row 9 is the header (0-indexed)
    usecols="B:Q"   # From B (Account Name) to Q (Total Number of Alerts) - adjust if needed
)

# Show the columns to verify
st.write("Columns in Consolidated View:", cons_df.columns.tolist())

# Client dropdown from risk_df
clients = risk_df["Client Name"].dropna().unique()
selected_client = st.selectbox("Select a client", sorted(clients))

# Filter both dataframes by selected client
risk_data = risk_df[risk_df["Client Name"] == selected_client]
cons_data = cons_df[cons_df["Account Name"] == selected_client]

# Display filtered data
st.header(f"Data for {selected_client}")

st.subheader("Portfolio Risk Alerts")
st.dataframe(risk_data)

st.subheader("Consolidated View")
st.dataframe(cons_data)
