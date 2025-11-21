# app.py (fixed parsing: extracts key=value pairs and Key: value; shows correct values)
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
    .css-12oz5g7 {padding-top: 0rem;}
    .css-1d391kg {padding: 0.5rem 1rem;}
    .small-title {font-size:20px; font-weight:700; margin:0; padding-bottom:4px;}
    .muted {color:#6b7280; margin-top:0;}
    .stTextInput>div>div>input, .stSelectbox>div>div>div>select {height:38px;}
    .det-chip {display:inline-block; padding:5px 10px; border-radius:999px; background:#eef2ff; margin:4px; font-size:13px;}
    .streamlit-expanderHeader {padding: 6px 12px;}
    .stDataFrame {padding:6px 0;}
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
    - Finds all `key=value` pairs anywhere (e.g. channelid=1011, available=3)
    - Also finds `Key: value` style tokens (e.g. EXPG: channelid=777; ...). The left-hand token (EXPG) is included too.
    Returns dict mapping lowercase-key -> string value.
    """
    results = {}
    if not isinstance(text, str):
        return results

    # 1) Extract all key=value pairs (these are the primary source for things like channelid)
    for m in re.finditer(r"([A-Za-z0-9_\-]+)\s*=\s*([^;,\n\r]+)", text):
        k = m.group(1).strip().lower()
        v = m.group(2).strip()
        results[k] = v

    # 2) Extract 'Key: value' tokens (value may contain further key=value pairs)
    #    We include the left label too (lowercased), but do not overwrite existing key=value extractions.
    for m in re.finditer(r"([A-Za-z0-9_\-]+)\s*:\s*([^;\n\r]+)", text):
        primary_key = m.group(1).strip().lower()
        primary_val = m.group(2).strip()
        # If the primary_val itself contains key=value pairs, those are already captured above.
        # Keep primary token only if it doesn't conflict with an extracted key=value.
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
    query = st.text_input("OTA name (type part or full):", value="").strip()
    matches = [o for o in ota_list if query.lower() in o.lower()] if query else ota_list

    if not matches:
        st.warning("No matching OTA found. Try a different search term.")
        st.stop()

    # hide the label text so only the control is visible (but accessible)
    selected_ota = st.selectbox("", matches, index=0, label_visibility="collapsed", key="ota_select")

    st.markdown("---")
    st.markdown("**Search inside details**")
    key_query = st.text_input("Detail key (e.g. channelid, allocation):").strip().lower()

    st.markdown("---")
    show_raw_toggle = st.checkbox("Show raw Detail rows (expanded below)", value=False)
    show_debug = st.checkbox("Show debug: row indices for each found value", value=False)

with right_col:
    rows = df[df[ota_col].str.strip().str.lower() == selected_ota.strip().lower()]
    st.markdown(f"### Details for **{selected_ota}**")

    if rows.empty:
        st.info("No details found for the selected OTA.")
    else:
        # iterate rows, parse kv, gather results
        parsed_results = []  # list of tuples (original_row_index, raw_text, kv_dict)
        for idx, r in rows.reset_index().iterrows():
            orig_idx = int(r["index"]) if "index" in r else None
            raw_text = r[detail_col]
            kv = extract_key_values(raw_text)
            parsed_results.append((orig_idx, raw_text, kv))

        if key_query:
            found_values = []
            for orig_idx, raw_text, kv in parsed_results:
                if key_query in kv:
                    found_values.append((orig_idx, kv[key_query], raw_text))
            if not found_values:
                st.info(f"No value found for key '{key_query}' in the Detail column for this OTA.")
            else:
                st.markdown(f"**Values for '{key_query}':**")
                seen = set()
                for orig_idx, val, raw_text in found_values:
                    if val in seen:
                        continue
                    seen.add(val)
                    # show only the value (no numbering). Optionally show the source row index if debug enabled
                    if show_debug and orig_idx is not None:
                        st.write(f"{val}  (source row: {orig_idx})")
                    else:
                        st.write(val)
        else:
            # show detected keys across matching rows
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
