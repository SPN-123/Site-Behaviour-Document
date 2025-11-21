# app.py - final corrected version
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]  # prefer repo file, fallback to session upload
SHEET_NAME = "Sheet1"  # default sheet to use silently when available

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")

# ---------- Minimal CSS for nicer look ----------
st.markdown("""
<style>
.header-row { display:flex; align-items:center; gap:14px; }
.title { font-size:36px; font-weight:800; margin:0; }
.subtitle { color:#555; margin-top:2px; }
.card { background:#fff; border-radius:10px; padding:14px; box-shadow: 0 1px 5px rgba(0,0,0,0.06); }
.kv { font-weight:600; color:#0b6cff; }
.badge { background:#eefaf1; color:#067a46; padding:6px 10px; border-radius:8px; font-weight:600; }
.small-muted { color:#777; font-size:13px; }
.btn-pill { background:#f3f6ff; padding:8px 12px; border-radius:999px; display:inline-block; margin-right:6px; margin-bottom:6px; }
.detail-card { background:#fbfcff; border-left:4px solid #e6eefc; padding:10px; border-radius:8px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
col1, col2 = st.columns([6,2])
with col1:
    st.markdown(
        '<div class="header-row"><span style="font-size:36px">🔎</span>'
        '<div><h1 class="title">OTA Knowledge Search Tool</h1>'
        '<div class="subtitle">Search OTA entries and inspect values inside the Detail column.</div></div></div>',
        unsafe_allow_html=True
    )
with col2:
    st.markdown('<div style="text-align:right"><span class="badge">Tip: type partial OTA name</span></div>', unsafe_allow_html=True)

st.write("")  # spacer

# ---------- Helpers ----------
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
        return pd.read_excel(path_or_file, sheet_name=sheet_name)
    else:
        xls = pd.ExcelFile(path_or_file)
        if sheet_name and sheet_name in xls.sheet_names:
            return pd.read_excel(xls, sheet_name=sheet_name)
        return pd.read_excel(xls, sheet_name=0)

def extract_key_values(text: str) -> dict:
    """Return dict of lower_key -> value for patterns like Key: Value"""
    results = {}
    if not isinstance(text, str):
        return results
    # match 'Key : Value' until next separator (; , newline) or end
    pattern = re.compile(r"([A-Za-z0-9_\- ]+?)\s*:\s*([^;\n\r,]+)")
    for m in pattern.finditer(text):
        key = m.group(1).strip().lower()
        val = m.group(2).strip()
        results[key] = val
    return results

# ---------- Load workbook (silently choose sheet) ----------
found = find_excel(EXCEL_PATHS)
if found:
    try:
        xls = pd.ExcelFile(found)
    except Exception as e:
        st.error(f"Error reading workbook: {e}")
        st.stop()
    sheet_list = xls.sheet_names
    chosen_sheet = SHEET_NAME if SHEET_NAME in sheet_list else sheet_list[0]
    try:
        df = load_excel(found, sheet_name=chosen_sheet)
    except Exception as e:
        st.error(f"Failed to load sheet '{chosen_sheet}': {e}")
        st.stop()
else:
    uploaded = st.file_uploader("Upload XY.xlsx (fallback)", type=["xlsx"], help="Workbook must contain OTAName and Detail columns")
    if uploaded is None:
        st.info("Please upload the XY.xlsx file or place it at the path: /mnt/data/XY.xlsx")
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
ota_col = lower_map.get("otaname") or lower_map.get("ota name") or cols[0]
detail_col = lower_map.get("detail") or lower_map.get("details") or (cols[1] if len(cols) > 1 and cols[1] != ota_col else ota_col)

# normalize
df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str)

# ---------- Search UI ----------
search_col, meta_col = st.columns([3,1])
with search_col:
    search_query = st.text_input("OTA name", placeholder="Type partial OTA name (e.g. Expedia)")
    ota_matches = sorted(df[ota_col].dropna().unique(), key=lambda x: x.lower())
    if search_query:
        ota_matches = [m for m in ota_matches if search_query.lower() in str(m).lower()]
    if not ota_matches:
        st.warning("No matching OTA found.")
        st.stop()
    selected_ota = st.selectbox("Select OTA", options=ota_matches)
with meta_col:
    st.markdown(f"<div style='padding:8px;border-radius:6px;background:#f6f9ff;'>Sheet: <b>{chosen_sheet}</b><br/>Rows: <b>{len(df)}</b></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"### Details for **{selected_ota}**")

rows = df[df[ota_col].str.strip().str.lower() == str(selected_ota).strip().lower()]
if rows.empty:
    st.info("No details found for this OTA.")
else:
    detail_texts = rows[detail_col].fillna("").astype(str).tolist()

    # show detected keys as badges (informational)
    detected_keys = []
    for t in detail_texts:
        kv = extract_key_values(t)
        for k in kv.keys():
            if k not in detected_keys:
                detected_keys.append(k)
    if detected_keys:
        st.write("**Detected keys:**")
        # build HTML badges safely
        badge_html_parts = []
        for k in detected_keys:
            # escape minimal HTML sensitive characters in key (simple replace)
            safe_k = str(k).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            badge_html_parts.append(f"<span style='display:inline-block;background:#eef6ff;padding:6px 10px;border-radius:999px;margin-right:6px;margin-bottom:6px'>{safe_k}</span>")
        badges = "".join(badge_html_parts)
        st.markdown(badges, unsafe_allow_html=True)

    with st.expander("Show raw Detail rows"):
        st.write(rows[[ota_col, detail_col]].reset_index(drop=True))

    # ---------- Second search: simple text input (user requested) ----------
    st.subheader("Search detail key")
    key_query = st.text_input("Enter detail key (e.g. ChannelId, Allocation, Sell Code):").strip().lower()

    if key_query:
        extracted = []
        for t in detail_texts:
            kv = extract_key_values(t)
            # exact (case-insensitive) match on key
            if key_query in kv:
                extracted.append(kv[key_query])

        if not extracted:
            st.info(f"No value found for key '{key_query}' in the Detail column for this OTA.")
        else:
            # unique values preserving order, show plain values only (no numbering)
            seen = set()
            uniq = []
            for v in extracted:
                if v not in seen:
                    uniq.append(v)
                    seen.add(v)

            for v in uniq:
                st.write(v)
    else:
        st.info("Enter a detail key in the search box to extract its value from the Detail column.")

# ---------- Raw rows expander ----------
with st.expander("Show raw rows for selected OTA"):
    st.dataframe(rows.reset_index(drop=True))

# ---------- Footer guidance ----------
st.markdown("---")
st.caption("If you deploy from GitHub, ensure 'XY.xlsx' is in the repo root or update EXCEL_PATHS.")
