import streamlit as st
import pandas as pd
from pathlib import Path

# ======================================================
#  CONFIG
# ======================================================
EXCEL_FILE = "XY.xlsx"   # Make sure the Excel file is uploaded in the same repo

# ======================================================
#  LOAD WORKBOOK
# ======================================================
@st.cache_data
def load_excel():
    try:
        xls = pd.ExcelFile(EXCEL_FILE)
        sheets = {s: pd.read_excel(EXCEL_FILE, sheet_name=s) for s in xls.sheet_names}
        return sheets
    except Exception as e:
        st.error(f"❌ Unable to load Excel file: {e}")
        return {}

# ======================================================
#  FIND OTA COLUMN
# ======================================================
def find_ota_column(df):
    possible_cols = ["OTA", "OTA Name", "OTA_Name", "Channel", "OTAName"]
    for col in possible_cols:
        if col in df.columns:
            return col
    # fallback
    for col in df.columns:
        if df[col].nunique() < 50 and df[col].dtype == object:
            return col
    return None

# ======================================================
#  FILTER RESULTS
# ======================================================
def filter_results(sheets, selected_ota, category):
    results = []
    for sname, df in sheets.items():
        df2 = df.copy()
        ota_col = find_ota_column(df2)

        # Filter OTA
        if ota_col:
            mask = df2[ota_col].astype(str).str.lower().str.contains(selected_ota.lower())
            df2 = df2[mask]

        if df2.empty:
            continue

        # Filter by category (simple keyword search)
        category_keywords = [category.lower(), category.replace(" ", "").lower()]

        matched_cols = [c for c in df2.columns if any(k in c.lower() for k in category_keywords)]

        if matched_cols:
            df2 = df2[matched_cols]  # keep only relevant columns

        results.append((sname, df2))

    return results

# ======================================================
#  STREAMLIT UI
# ======================================================
st.title("🔍 OTA Knowledge Search Tool")
st.write("Select OTA → Select Category → View Results from the Excel File")

sheets = load_excel()

if not sheets:
    st.stop()

# Collect all OTA names
ota_values = set()
for df in sheets.values():
    col = find_ota_column(df)
    if col:
        ota_values.update(df[col].dropna().astype(str).unique())

ota_list = sorted(list(ota_values))

# OTA selector
selected_ota = st.selectbox("Select OTA", ota_list)

# Category selector
category = st.radio("Select Category", ["Setup detail", "ARI", "Reservations"])

# Search button
if st.button("Search"):
    results = filter_results(sheets, selected_ota, category)

    if not results:
        st.warning("No matching results found.")
    else:
        st.success(f"Results for **{selected_ota}** → **{category}**")
        for sheet_name, df_res in results:
            st.subheader(f"📄 Sheet: {sheet_name} ({len(df_res)} rows)")
            st.dataframe(df_res)
