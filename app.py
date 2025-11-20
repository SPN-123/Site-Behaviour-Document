# app.py
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]
DEFAULT_SHEET = "Sheet1"

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")
st.title("🔎 OTA Knowledge Search Tool")
st.write("Enter an OTA name in the search box, choose the match, then filter the Detail values by a key (text before ':') to extract the value.")

# ---------- Helpers ----------
def find_excel(paths: List[str]):
    for p in paths:
        if os.path.exists(p):
            return p
    return None

@st.cache_data
def load_excel(path_or_file, sheet_name=None):
    # accepts path string or uploaded file-like
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

def extract_key_values(text: str) -> dict:
    """Extract key:value pairs from a free-text detail string.
    Returns a dict of {key_lower: value} where key_lower is lowercased and stripped.
    It matches patterns like 'ChannelId:434', 'Allocation:Room', or 'Key : Value'.
    """
    results = {}
    if not isinstance(text, str):
        return results
    # match key : value until next separator (semicolon, comma, newline) or end
    pattern = re.compile(r"([A-Za-z0-9_\- ]+?)\s*:\s*([^;\n\r,]+)")
    for m in pattern.finditer(text):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        results[key] = val
    return results

# ---------- Load workbook ----------
found = find_excel(EXCEL_PATHS)

if found:
    st.success(f"Using Excel file: `{found}`")
    try:
        xls = pd.ExcelFile(found)
    except Exception as e:
        st.error(f"Error reading workbook: {e}")
        st.stop()
else:
    st.warning("Excel file not found in repo or /mnt/data. Use the uploader below to provide XY.xlsx.")
    uploaded = st.file_uploader("Upload XY.xlsx", type=["xlsx"])
    if uploaded is None:
        st.stop()
    xls = pd.ExcelFile(uploaded)
    found = uploaded

# ---------- Sheet selection and load ----------
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

# ---------- Detect expected columns ----------
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
elif "details" in lower_map:
    detail_col = lower_map["details"]
else:
    if len(cols) >= 2:
        detail_col = cols[1] if cols[1] != ota_col else cols[0]
    else:
        detail_col = ota_col

# Normalize strings
df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str)

# Build OTA list
ota_list = sorted(df[ota_col].dropna().unique(), key=str.lower)

# ---------- UI: OTA search & selection ----------
st.subheader("Search OTA")
query = st.text_input("OTA name (type part or full name):").strip()

matches = [o for o in ota_list if query.lower() in o.lower()] if query else ota_list

if not matches:
    st.warning("No matching OTA found. Try a different search term.")
    st.stop()

selected_ota = st.selectbox("Select OTA from matches", matches)

# ---------- After selecting OTA show details and second search box ----------
rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]

st.markdown(f"### Details for **{selected_ota}**")

if rows.empty:
    st.info("No details found for the selected OTA.")
else:
    # Combine detail strings from all matching rows into a list
    detail_texts = rows[detail_col].fillna("").astype(str).tolist()

    # Show original details (optional collapse)
    with st.expander("Show raw Detail rows"):
        for i, t in enumerate(detail_texts, start=1):
            st.write(f"**{i}.** {t}")

    # Second search box: key to extract (text before ':')
    st.subheader("Search detail key")
    key_query = st.text_input("Enter detail key (e.g. ChannelId, Allocation, Sell Code):").strip().lower()

    if key_query:
        # extract values for this key from each detail row
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
st.caption(f"Using workbook: `{found}` — selected sheet: `{chosen_sheet}`. If deployed from GitHub, ensure XY.xlsx is in the repo root.")
