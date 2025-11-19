import streamlit as st
import pandas as pd
import os
from typing import List

# ------------------------------------------------------------
# CONFIG — DO NOT USE /mnt/data when deploying from GitHub
# ------------------------------------------------------------
EXCEL_PATHS = [
    "XY.xlsx",          # when running from GitHub repository
    "/mnt/data/XY.xlsx" # when uploading manually inside Streamlit session
]

# Default sheet (if exists)
DEFAULT_SHEET = "Sheet1"

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")
st.title("🔎 OTA Knowledge Search Tool")
st.write("Type an OTA name in the box, choose the match, then select a category button for that OTA.")


# ------------------------------------------------------------
# Function to find Excel file
# ------------------------------------------------------------
def find_excel(paths):
    for p in paths:
        if os.path.exists(p):
            return p
    return None


# ------------------------------------------------------------
# Load Excel (repo or session or uploader fallback)
# ------------------------------------------------------------
excel_file = find_excel(EXCEL_PATHS)

if excel_file:
    st.success(f"Using Excel file: `{excel_file}`")
    xls = pd.ExcelFile(excel_file)
else:
    st.warning("Excel file not found at repo or /mnt/data.")
    uploaded = st.file_uploader("Upload XY.xlsx", type=["xlsx"])
    if uploaded is None:
        st.stop()
    xls = pd.ExcelFile(uploaded)
    excel_file = uploaded


# ------------------------------------------------------------
# Sheet Selection
# ------------------------------------------------------------
sheet_names = xls.sheet_names

# If default sheet not found, show first sheet
default_index = sheet_names.index(DEFAULT_SHEET) if DEFAULT_SHEET in sheet_names else 0

chosen_sheet = st.selectbox("Select sheet to use", options=sheet_names, index=default_index)

df = pd.read_excel(excel_file, sheet_name=chosen_sheet)

if df.empty:
    st.error("The selected sheet is empty.")
    st.stop()


# ------------------------------------------------------------
# Detect columns
# ------------------------------------------------------------
cols = list(df.columns)

possible_ota_cols = [c for c in cols if c.lower() in ("ota", "ota name", "ota_name", "channel", "channel name")]
ota_col = possible_ota_cols[0] if possible_ota_cols else cols[0]

has_category_col = "category" in [c.lower() for c in cols]

if has_category_col:
    category_col = [c for c in cols if c.lower() == "category"][0]
    category_cols = None
else:
    category_cols = [c for c in cols if c != ota_col]


# ------------------------------------------------------------
# Build OTA list
# ------------------------------------------------------------
ota_list = sorted(df[ota_col].dropna().astype(str).unique(), key=str.lower)

search = st.text_input("Search OTA name:").strip()

matches = [o for o in ota_list if search.lower() in o.lower()] if search else ota_list

if not matches:
    st.warning("No matching OTA found.")
    st.stop()

selected_ota = st.selectbox("Select OTA", matches)

# ------------------------------------------------------------
# Category Detection
# ------------------------------------------------------------
FIXED_CATEGORIES = ["Setup details", "ARI", "Reservations"]


def get_categories(ota: str) -> List[str]:
    if has_category_col:
        rows = df[df[ota_col].astype(str).str.lower() == ota.lower()]
        if rows.empty:
            return []
        cat_values = rows[category_col].dropna().astype(str).unique().tolist()
        return cat_values
    else:
        row = df[df[ota_col].astype(str).str.lower() == ota.lower()]
        if row.empty:
            return []
        row = row.iloc[0]
        available = []
        for c in category_cols:
            val = row[c]
            if pd.notna(val) and str(val).strip():
                available.append(c)
        return available


available_categories = get_categories(selected_ota)

# Normalize to fixed names
normalized = set()
for cat in available_categories:
    c = cat.lower()
    if "setup" in c:
        normalized.add("Setup details")
    elif "ari" in c:
        normalized.add("ARI")
    elif "reserv" in c:
        normalized.add("Reservations")
    else:
        normalized.add(cat)


# ------------------------------------------------------------
# Button Display
# ------------------------------------------------------------
st.subheader(f"Available categories for `{selected_ota}`:")
cols_btn = st.columns(len(FIXED_CATEGORIES))

for i, cat in enumerate(FIXED_CATEGORIES):
    with cols_btn[i]:
        if cat in normalized:
            if st.button(cat):
                if has_category_col:
                    subset = df[
                        (df[ota_col].astype(str).str.lower() == selected_ota.lower()) &
                        (df[category_col].astype(str).str.lower().str.contains(cat.split()[0].lower()))
                    ]
                    if subset.empty:
                        st.info("No details found.")
                    else:
                        st.dataframe(subset)
                else:
                    row = df[df[ota_col].astype(str).str.lower() == selected_ota.lower()]
                    col_candidates = [c for c in category_cols if cat.split()[0].lower() in c.lower()]
                    for c in col_candidates:
                        st.write(f"### {c}")
                        st.write(row.iloc[0][c])
        else:
            st.write(f"{cat} (not available)")


# ------------------------------------------------------------
# Raw Row
# ------------------------------------------------------------
with st.expander("Show raw data for selected OTA"):
    st.dataframe(df[df[ota_col].astype(str).str.lower() == selected_ota.lower()])
