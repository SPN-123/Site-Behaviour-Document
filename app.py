# app.py - prettier UI version
import streamlit as st
import pandas as pd
import os
import re
from typing import List

# ---------- CONFIG ----------
EXCEL_PATHS = ["XY.xlsx", "/mnt/data/XY.xlsx"]  # prefer repo file, fallback to session path
SHEET_NAME = "Sheet1"  # used silently if present

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")

# ---------- Minimal CSS for nicer look ----------
st.markdown("""
<style>
.header-row { display:flex; align-items:center; gap:14px; }
.title { font-size:36px; font-weight:800; margin:0; }
.subtitle { color:#555; margin-top:2px; }
.card { background:#fff; border-radius:10px; padding:14px; box-shadow: 0 1px 5px rgba(0,0,0,0.06); }
.kv { font-weight:600; color:#0b6cff; }
.badge { background:#eefaf1; color:#067a46; padding:6px 10px; border-radius:8px; font-weight:600 }
.small-muted { color:#777; font-size:13px; }
.btn-pill { background:#f3f6ff; padding:8px 12px; border-radius:999px; display:inline-block; margin-right:6px; margin-bottom:6px; }
.detail-card { background:#fbfcff; border-left:4px solid #e6eefc; padding:10px; border-radius:8px; margin-bottom:8px; }
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
col1, col2 = st.columns([6,2])
with col1:
    st.markdown('<div class="header-row"><span style="font-size:36px">🔎</span>'
                '<div><h1 class="title">OTA Knowledge Search Tool</h1>'
                '<div class="subtitle">Search OTA entries and inspect values inside the Detail column.</div></div></div>',
                unsafe_allow_html=True)
with col2:
    st.markdown('<div style="text-align:right"><span class="badge">Tip: type partial OTA name</span></div>', unsafe_allow_html=True)

st.write("")  # small spacer

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
    uploaded = st.file_uploader("Upload XY.xlsx", type=["xlsx"], help="Workbook must contain OTAName and Detail columns")
    if uploaded is None:
        st.info("Upload XY.xlsx or place it in the repo root as 'XY.xlsx'.")
        st.stop()
    try:
        xls = pd.ExcelFile(uploaded)
    except Exception as e:
        st.error(f"Error reading uploaded workbook: {e}")
        st.stop()
    sheet_list = xls.sheet_names
    chosen_sheet = SHEET_NAME if SHEET_NAME in sheet_list else sheet_list[0]
    df = pd.read_excel(xls, sheet_name=chosen_sheet)

if df is None or df.empty:
    st.error("Selected sheet is empty. Please check the Excel file.")
    st.stop()

# ---------- Detect columns ----------
cols = list(df.columns)
lower_map = {c.lower(): c for c in cols}
ota_col = lower_map.get("otaname") or lower_map.get("ota name") or cols[0]
detail_col = lower_map.get("detail") or lower_map.get("details") or (cols[1] if len(cols) > 1 and cols[1] != ota_col else ota_col)

# normalize
df[ota_col] = df[ota_col].astype(str).str.strip()
df[detail_col] = df[detail_col].astype(str)

# ---------- Search UI (presentable) ----------
search_col, meta_col = st.columns([3,1])
with search_col:
    search_query = st.text_input("OTA name", placeholder="Type partial OTA name (e.g. Expedia)")
    matches = sorted(df[ota_col].dropna().unique(), key=lambda x: x.lower())
    if search_query:
        matches = [m for m in matches if search_query.lower() in str(m).lower()]
    if not matches:
        st.warning("No matching OTA found.")
        st.stop()
    selected_ota = st.selectbox("Select OTA", options=matches)
with meta_col:
    st.markdown(f"<div class='card small-muted'>Sheet: <span class='kv'>{chosen_sheet}</span><br>Rows: <span class='kv'>{len(df)}</span></div>", unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"### Details for <span style='color:#0b6cff'>{selected_ota}</span>", unsafe_allow_html=True)

# ---------- Show details & detected keys ----------
rows = df[df[ota_col].str.strip().str.lower() == str(selected_ota).strip().lower()]
if rows.empty:
    st.info("No details found for this OTA.")
else:
    detail_texts = rows[detail_col].fillna("").astype(str).tolist()

    # detected keys badges
    detected_keys = []
    for t in detail_texts:
        kv = extract_key_values(t)
        for k in kv.keys():
            if k not in detected_keys:
                detected_keys.append(k)
    if detected_keys:
        st.write("**Detected keys:**")
        badges = "".join([f"<span class='btn-pill'>{k}</span>" for k in detected_keys])
        st.markdown(badges, unsafe_allow_html=True)

    # raw details collapsed
    with st.expander("Show raw Detail rows"):
        st.write(rows[[ota_col, detail_col]].reset_index(drop=True))

    # second search - autocomplete + display
    key_col, val_col = st.columns([2,3])
    with key_col:
        if detected_keys:
            pick = st.selectbox("Choose key (or Custom)", options=["-- Custom --"] + detected_keys)
            if pick == "-- Custom --":
                key_input = st.text_input("Custom key (e.g. ChannelId)").strip().lower()
            else:
                key_input = pick.strip().lower()
        else:
            key_input = st.text_input("Detail key (e.g. ChannelId)").strip().lower()

    with val_col:
        if key_input:
            extracted = []
            for t in detail_texts:
                kv = extract_key_values(t)
                if key_input in kv:
                    extracted.append(kv[key_input])
            if not extracted:
                st.info(f"No value found for key '{key_input}'.")
            else:
                st.markdown("<div class='card'>", unsafe_allow_html=True)
                st.markdown(f"**Values for '{key_input}':**")
                for i, v in enumerate(dict.fromkeys(extracted).keys(), start=1):
                    st.markdown(f"<div class='detail-card'><strong>{i}.</strong> {v}</div>", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='small-muted'>Select or enter a key to extract values.</div>", unsafe_allow_html=True)

# ---------- Footer ----------
st.markdown("---")
st.caption("UI updated — tell me if you want different colors, more compact spacing, or an export button.")
