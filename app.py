# app.py (UI-tidy version)
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]  # repo path first, session path fallback
SHEET_NAME = "Sheet1"  # prefer this sheet silently if present

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")

# ---------- Small styling to reduce whitespace and align content ----------
st.markdown(
    """
    <style>
    /* Tighten global paddings */
    .css-12oz5g7 {padding-top: 0rem;}  /* page top gap */
    .css-1d391kg {padding: 0.5rem 1rem;} /* main container padding */
    /* Header and small title */
    .small-title {font-size:20px; font-weight:700; margin:0; padding-bottom:4px;}
    .muted {color:#6b7280; margin-top:0;}
    /* Compact controls */
    .stTextInput>div>div>input, .stSelectbox>div>div>div>select {height:38px;}
    /* Chips */
    .det-chip {display:inline-block; padding:5px 10px; border-radius:999px; background:#eef2ff; margin:4px; font-size:13px;}
    /* Reduce expander padding */
    .streamlit-expanderHeader {padding: 6px 12px;}
    /* Dataframe compact */
    .stDataFrame {padding:6px 0;}
    </style>
    """,
    unsafe_allow_html=True,
)

# Small header (keeps things compact)
st.markdown("<div class='small-title'>🔎 OTA Knowledge Search Tool</div>", unsafe_allow_html=True)
st.markdown("<div class='muted'>Type an OTA name, choose the match, then search inside details.</div>", unsafe_allow_html=True)
st.markdown("---")

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

# ---------- Compact two-column layout: controls left, results right ----------
left_col, right_col = st.columns([3, 7])

with left_col:
    st.markdown("**Search OTA**")
    query = st.text_input("OTA name (type part or full):", value="").strip()
    matches = [o for o in ota_list if query.lower() in o.lower()] if query else ota_list

    if not matches:
        st.warning("No matching OTA found. Try a different search term.")
        st.stop()

    # keep the OTA selectbox visible (as you requested)
    selected_ota = st.selectbox("Select OTA from matches", matches, index=0)

    st.markdown("---")
    st.markdown("**Search inside details**")
    key_query = st.text_input("Detail key (e.g. ChannelId, Allocation):").strip().lower()

    st.markdown("---")
    show_raw_toggle = st.checkbox("Show raw Detail rows (expanded below)", value=False)
    st.markdown("")  # tiny spacer to keep compact

with right_col:
    rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]
    st.markdown(f"### Details for **{selected_ota}**")

    if rows.empty:
        st.info("No details found for the selected OTA.")
    else:
        # gather detail texts from all matching rows
        detail_texts = rows[detail_col].fillna("").astype(str).tolist()

        # Parse and optionally filter by key_query
        parsed_results = []
        shown_rows = []
        for t in detail_texts:
            kv = extract_key_values(t)
            parsed_results.append((t, kv))
            shown_rows.append(t)

        # If user searched a key, gather matches and show compact list
        if key_query:
            extracted = []
            for t, kv in parsed_results:
                if key_query in kv:
                    extracted.append(kv[key_query])
            if not extracted:
                st.info(f"No value found for key '{key_query}' in the Detail column for this OTA.")
            else:
                st.markdown(f"**Values for '{key_query}':**")
                seen = set()
                uniq = []
                for v in extracted:
                    if v not in seen:
                        uniq.append(v)
                        seen.add(v)
                # show values in a compact bulleted list
                for i, v in enumerate(uniq, start=1):
                    st.write(f"{i}. {v}")

        else:
            # No key search — show short chips for detected keys across matching rows
            all_keys = []
            for _, kv in parsed_results:
                for k in kv.keys():
                    if k not in all_keys:
                        all_keys.append(k)
            if all_keys:
                st.markdown("**Detected keys:**")
                chips_html = "".join([f"<span class='det-chip'>{k}</span>" for k in all_keys])
                st.markdown(chips_html, unsafe_allow_html=True)
            else:
                st.info("No structured keys were detected in the Detail column for this OTA.")

        # Compact inline raw rows expander (preserve previous behavior)
        with st.expander("Show raw Detail rows", expanded=show_raw_toggle):
            for i, t in enumerate(shown_rows, start=1):
                st.write(f"**{i}.** {t}")

# ---------- Raw rows (table) — kept but collapsed by default below main area ----------
with st.expander("Show raw rows for selected OTA (table)"):
    st.dataframe(rows.reset_index(drop=True))

# ---------- Footer guidance ----------
st.markdown("---")
st.caption("If you deploy from GitHub, ensure 'XY.xlsx' is in the repo root or update EXCEL_PATHS accordingly.")
