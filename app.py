# app.py
import streamlit as st
import pandas as pd
import os
from typing import List

# ----------------- CONFIG -----------------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]
DEFAULT_SHEET = "Sheet1"

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")
st.title("🔎 OTA Knowledge Search Tool")
st.write("Enter an OTA name in the search box, choose the match, and view the details from the 'Detail' column.")

# ----------------- Helpers -----------------
def find_excel(paths: List[str]):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

@st.cache_data
def load_excel(path_or_file, sheet_name=None):
    if isinstance(path_or_file, str):
        if not os.path.exists(path_or_file):
            raise FileNotFoundError(f"File not found: {path_or_file}")
        if sheet_name is None:
            return pd.read_excel(path_or_file)
        return pd.read_excel(path_or_file, sheet_name=sheet_name)
    else:
        xls = pd.ExcelFile(path_or_file)
        if sheet_name and sheet_name in xls.sheet_names:
            return pd.read_excel(xls, sheet_name=sheet_name)
        return pd.read_excel(xls, sheet_name=0)

# ----------------- Load workbook -----------------
found = find_excel(EXCEL_PATHS)

if found:
    st.success(f"Using Excel file: `{found}`")
    try:
        xls = pd.ExcelFile(found)
    except Exception as e:
        st.error(f"Error reading workbook: {e}")
        st.stop()
else:
    st.warning("Excel file not found in repo or /mnt/data. You can upload the XY.xlsx file below.")
    uploaded = st.file_uploader("Upload XY.xlsx", type=["xlsx"])
    if uploaded is None:
        st.info("Please upload the XY.xlsx file or place it in the repo root as 'XY.xlsx'.")
        st.stop()
    xls = pd.ExcelFile(uploaded)
    found = uploaded

# ----------------- Sheet selection and load -----------------
sheet_names = xls.sheet_names
default_index = sheet_names.index(DEFAULT_SHEET) if DEFAULT_SHEET in sheet_names else 0
chosen_sheet = st.selectbox("Select sheet to use", options=sheet_names, index=default_index)

try:
    df = load_excel(found, sheet_name=chosen_sheet)
except Exception as e:
    st.error(f"Failed to load sheet '{chosen_sheet}': {e}")
    st.stop()

if df is None or df.empty:
    st.error("Selected sheet is empty. Please check the Excel file.")
    st.stop()

# ----------------- Validate expected columns -----------------
cols = list(df.columns)
lower_map = {c.lower(): c for c in cols}

if "otaname" in lower_map:
    ota_col = lower_map["otaname"]
elif "ota name" in lower_map:
    ota_col = lower_map["ota name"]
else:
    ota_col = cols[0]

if "detail" in lower_map:
    detail_col = lower_map["detail"]
else:
    if len(cols) >= 2:
        detail_col = cols[1] if cols[1] != ota_col else cols[0]
    else:
        detail_col = ota_col

# NOTE: Removed the st.caption(...) line that previously displayed the detected columns.

# Normalize strings for matching
df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str).str.strip()

# Build OTA list
ota_list = sorted(df[ota_col].dropna().unique(), key=str.lower)

# ----------------- Search UI -----------------
st.subheader("Search OTA")
query = st.text_input("OTA name (type part or full name):").strip()

if query:
    matches = [o for o in ota_list if query.lower() in o.lower()]
else:
    matches = ota_list

if not matches:
    st.warning("No matching OTA found. Try a different search term.")
    st.stop()

selected_ota = st.selectbox("Select OTA from matches", matches)

# ----------------- Show details -----------------
st.markdown(f"### Details for **{selected_ota}**")

rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]

if rows.empty:
    st.info("No details found for the selected OTA.")
else:
    details = rows[detail_col].fillna("").tolist()
    for i, d in enumerate(details, start=1):
        st.write(f"**{i}.** {d}")

with st.expander("Show raw rows for this OTA"):
    st.dataframe(rows.reset_index(drop=True))
