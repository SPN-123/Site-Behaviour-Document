# app.py
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]  # repo path first, session path fallback
SHEET_NAME = "Sheet1"  # prefer this sheet silently if present

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")
st.title("🔎 OTA Knowledge Search Tool")
st.write("Type an OTA name in the box, choose the match, then select a category button for that OTA.")

# ---------- Helpers ----------
def find_excel(paths: List[str]):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

def read_excel_safe(path: str, sheet_name=None) -> pd.DataFrame:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found at: {path}")
    try:
        if sheet_name is None:
            return pd.read_excel(path)
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file: {e}") from e

@st.cache_data
def load_df_cached(path: str, sheet_name: str = None) -> pd.DataFrame:
    return read_excel_safe(path, sheet_name)

def extract_key_values(text: str) -> dict:
    """
    Extract key:value pairs from a free-text detail string.
    Returns dict {lower_key: value}.
    Pattern matches 'Key: Value' until next separator (; , or newline) or end.
    """
    results = {}
    if not isinstance(text, str):
        return results
    pattern = re.compile(r"([A-Za-z0-9_\- ]+?)\s*:\s*([^;\n\r,]+)")
    for m in pattern.finditer(text):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        results[key] = val
    return results

# ---------- Load Data (prefer repo, else uploader) ----------
df = None
found_path = find_excel(EXCEL_PATHS)

if found_path:
    # silently pick preferred sheet (no banner / selectbox shown)
    try:
        xls = pd.ExcelFile(found_path)
    except Exception as e:
        st.error(f"Error reading workbook: {e}")
        st.stop()
    sheet_list = xls.sheet_names
    chosen_sheet = SHEET_NAME if SHEET_NAME in sheet_list else sheet_list[0]
    try:
        df = load_df_cached(found_path, chosen_sheet)
    except Exception as e:
        st.error(f"Failed to load sheet '{chosen_sheet}': {e}")
        st.stop()
else:
    # fallback uploader (visible)
    uploaded = st.file_uploader("Upload XY.xlsx (fallback)", type=["xlsx"])
    if uploaded is None:
        st.info("Please upload the XY.xlsx file or place it in the repo root as 'XY.xlsx'.")
        st.stop()
    try:
        xls = pd.ExcelFile(uploaded)
    except Exception as e:
        st.error(f"Error reading uploaded workbook: {e}")
        st.stop()
    sheet_list = xls.sheet_names
    chosen_sheet = SHEET_NAME if SHEET_NAME in sheet_list else sheet_list[0]
    try:
        df = pd.read_excel(xls, sheet_name=chosen_sheet)
    except Exception as e:
        st.error(f"Error reading uploaded file sheet '{chosen_sheet}': {e}")
        st.stop()

# Basic validation
if df is None or df.empty:
    st.error("Loaded dataframe is empty. Check the Excel file and sheet name.")
    st.stop()

# ---------- Detect structure ----------
cols = list(df.columns)
lower_map = {c.lower(): c for c in cols}

# OTA column detection
if "otaname" in lower_map:
    ota_col = lower_map["otaname"]
elif "ota name" in lower_map:
    ota_col = lower_map["ota name"]
else:
    ota_col = cols[0]

# Detail column detection
if "detail" in lower_map:
    detail_col = lower_map["detail"]
elif "details" in lower_map:
    detail_col = lower_map["details"]
else:
    # fallback to second column if present
    if len(cols) >= 2:
        detail_col = cols[1] if cols[1] != ota_col else cols[0]
    else:
        detail_col = ota_col

# normalize strings used for matching
df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str)

# Build OTA list
ota_list = sorted(df[ota_col].dropna().unique(), key=str.lower)

# ---------- UI: Search & select OTA ----------
st.subheader("Search OTA")
query = st.text_input("OTA name (type part or full name):").strip()

matches = [o for o in ota_list if query.lower() in o.lower()] if query else ota_list

if not matches:
    st.warning("No matching OTA found. Try a different search term.")
    st.stop()

# keep the OTA selectbox visible (as you requested)
selected_ota = st.selectbox("Select OTA from matches", matches)

# ---------- Show details & second search box ----------
rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]

st.markdown(f"### Details for **{selected_ota}**")

if rows.empty:
    st.info("No details found for the selected OTA.")
else:
    # gather detail texts from all matching rows
    detail_texts = rows[detail_col].fillna("").astype(str).tolist()

    # show raw detail rows collapsed (keeps previous behavior)
    with st.expander("Show raw Detail rows"):
        for i, t in enumerate(detail_texts, start=1):
            st.write(f"**{i}.** {t}")

    # second search box: user enters the key name (text before ':')
    st.subheader("Search detail key")
    key_query = st.text_input("Enter detail key (e.g. ChannelId, Allocation, Sell Code):").strip().lower()

    if key_query:
        extracted = []
        for t in detail_texts:
            kv = extract_key_values(t)
            if key_query in kv:
                extracted.append(kv[key_query])
        if not extracted:
            st.info(f"No value found for key '{key_query}' in the Detail column for this OTA.")
        else:
            st.markdown(f"**Values for '{key_query}':**")
            # show unique values preserving order
            seen = set()
            uniq = []
            for v in extracted:
                if v not in seen:
                    uniq.append(v)
                    seen.add(v)
            for i, v in enumerate(uniq, start=1):
                st.write(f"{i}. {v}")
    else:
        st.info("Enter a detail key in the second search box to extract its value from the Detail column.")

# ---------- Raw rows expander ----------
with st.expander("Show raw rows for selected OTA"):
    st.dataframe(rows.reset_index(drop=True))

# ---------- Footer guidance ----------
st.markdown("---")
st.caption("If you deploy from GitHub, ensure 'XY.xlsx' is in the repo root or update EXCEL_PATHS accordingly.")
