# app.py (UI: hide select control, align values above Detail Key)
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")

# ---------- Styling (compact) ----------
st.markdown(
    """
    <style>
    /* tighten and hide select-like UI elements we don't want visible */
    .css-12oz5g7 {padding-top: 0rem;}
    .css-1d391kg {padding: 0.5rem 1rem;}
    .small-title {font-size:20px; font-weight:700; margin:0; padding-bottom:4px;}
    .muted {color:#6b7280; margin-top:0;}
    .stTextInput>div>div>input {height:38px;}
    .det-chip {display:inline-block; padding:5px 10px; border-radius:999px; background:#eef2ff; margin:4px; font-size:13px;}
    .streamlit-expanderHeader {padding: 6px 12px;}
    .stDataFrame {padding:6px 0;}
    /* hide any visible selectbox label/caret area we previously saw */
    .hidden-select {display:none;}
    /* small box to show the auto-selected OTA in a similar visual style to inputs */
    .selected-ota-box {background:#f3f4f6; padding:10px 12px; border-radius:8px; border:1px solid rgba(0,0,0,0.03); margin-bottom:8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

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
    Robust extraction of key/value pairs from a free-text detail string.
    - Extracts key=value pairs anywhere (e.g. channelid=1011)
    - Also extracts Key: value tokens (e.g. EXPG: ...)
    Returns dict mapping lowercase-key -> value (string).
    """
    results = {}
    if not isinstance(text, str):
        return results

    # extract key=value pairs first
    for m in re.finditer(r"([A-Za-z0-9_\-]+)\s*=\s*([^;,\n\r]+)", text):
        k = m.group(1).strip().lower()
        v = m.group(2).strip()
        results[k] = v

    # also extract 'Key: value' tokens (if not overriding existing key=value)
    for m in re.finditer(r"([A-Za-z0-9_\-]+)\s*:\s*([^;\n\r]+)", text):
        primary_key = m.group(1).strip().lower()
        primary_val = m.group(2).strip()
        if primary_key not in results:
            results[primary_key] = primary_val

    return results

# ---------- Load Data ----------
df = None
found_path = find_excel(EXCEL_PATHS)

if found_path:
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

if df is None or df.empty:
    st.error("Loaded dataframe is empty. Check the Excel file and sheet name.")
    st.stop()

# ---------- Detect columns ----------
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

df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str)

ota_list = sorted(df[ota_col].dropna().unique(), key=str.lower)

# ---------- Layout ----------
left_col, right_col = st.columns([3, 7])

with left_col:
    st.markdown("**Search OTA**")
    # OTA search input — user types partial/full name
    query = st.text_input("OTA name (type part or full):", value="").strip()
    matches = [o for o in ota_list if query.lower() in o.lower()] if query else ota_list

    if not matches:
        st.warning("No matching OTA found. Try a different search term.")
        st.stop()

    # Auto-select best match (first match). We do NOT show the select dropdown.
    selected_ota = matches[0]

    # Show selected OTA as a simple readonly-looking box (no caret/dropdown)
    st.markdown(f"<div class='selected-ota-box'>{selected_ota}</div>", unsafe_allow_html=True)

    st.markdown("---")

    # Place where values (for a searched key) will appear BEFORE the detail-key input:
    st.markdown("**Value(s) found (for the key you enter below):**")
    # We'll fill this area after computing below; for now reserve a small placeholder container
    value_container = st.container()

    st.markdown("---")

    st.markdown("**Search inside details**")
    # Detail key input (user asks e.g. channelid or allocation)
    key_query = st.text_input("Detail key (e.g. channelid, allocation):").strip().lower()

    st.markdown("---")
    show_raw_toggle = st.checkbox("Show raw Detail rows (expanded below)", value=False)
    show_debug = st.checkbox("Show debug: row indices for each found value", value=False)

# compute rows and parsed results (available to both columns)
rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]
parsed_results = []
for idx, r in rows.reset_index().iterrows():
    orig_idx = int(r["index"]) if "index" in r else None
    raw_text = r[detail_col]
    kv = extract_key_values(raw_text)
    parsed_results.append((orig_idx, raw_text, kv))

# fill the value container with found values (placed above detail-key input)
with value_container:
    if key_query:
        found_values = []
        for orig_idx, raw_text, kv in parsed_results:
            if key_query in kv:
                found_values.append((orig_idx, kv[key_query], raw_text))
        if not found_values:
            st.write("_No value found yet — enter a key and press Enter._")
        else:
            # show values only (no numbering), each on its own line
            seen = set()
            for orig_idx, val, raw_text in found_values:
                if val in seen:
                    continue
                seen.add(val)
                if show_debug and orig_idx is not None:
                    st.write(f"{val}  (source row: {orig_idx})")
                else:
                    st.write(val)
    else:
        st.write("_Enter a detail key to see values here._")

# Right column: keep details header and raw rows expander
with right_col:
    st.markdown(f"### Details for **{selected_ota}**")

    if not parsed_results:
        st.info("No detail rows found for the selected OTA.")
    else:
        # show detected keys summary on right (no change)
        all_keys = []
        for _, _, kv in parsed_results:
            for k in kv.keys():
                if k not in all_keys:
                    all_keys.append(k)
        if all_keys:
            st.markdown("**Detected keys:**")
            chips_html = "".join([f"<span class='det-chip'>{k}</span>" for k in all_keys])
            st.markdown(chips_html, unsafe_allow_html=True)
        else:
            st.info("No structured keys were detected in the Detail column for this OTA.")

        with st.expander("Show raw Detail rows", expanded=show_raw_toggle):
            for orig_idx, raw_text, kv in parsed_results:
                if show_debug and orig_idx is not None:
                    st.write(f"[row:{orig_idx}] {raw_text}")
                else:
                    st.write(raw_text)

with st.expander("Show raw rows for selected OTA (table)"):
    st.dataframe(rows.reset_index(drop=True))

st.markdown("---")
st.caption("If you deploy from GitHub, ensure 'XY.xlsx' is in the repo root or update EXCEL_PATHS accordingly.")
