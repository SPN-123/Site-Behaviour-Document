import streamlit as st
import pandas as pd
import os
import re

# ================= CONFIG =================
EXCEL_PATH = "XY.xlsx"
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search Tool", layout="wide")

# ================= CUSTOM CSS (COMPACT UI) =================
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
h1 {font-size: 26px; margin-bottom: 4px;}
h2 {font-size: 20px; margin-bottom: 6px;}
h3 {font-size: 18px; margin-bottom: 6px;}
.stTextInput, .stRadio {margin-bottom: 6px;}
hr {margin: 8px 0;}
ul {margin-top: 4px; margin-bottom: 4px;}
li {margin-bottom: 4px;}
.selected-box {
    background-color: #ecfdf5;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #a7f3d0;
    margin-bottom: 8px;
}
.section-box {
    background-color: #f9fafb;
    padding: 12px 16px;
    border-radius: 8px;
    border: 1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown("## 🔎 OTA Behaviour Search Tool")
st.caption("Search OTA → Select category → Search inside details")
st.markdown("---")

# ================= LOAD EXCEL =================
if not os.path.exists(EXCEL_PATH):
    st.error("XY.xlsx not found in repository root.")
    st.stop()

df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df.columns = df.columns.str.strip()

# ================= SAFE COLUMN MAPPING =================
col_map = {c.lower(): c for c in df.columns}

def get_col(name):
    if name.lower() not in col_map:
        st.error(f"Missing column: {name}")
        st.write("Detected columns:", list(df.columns))
        st.stop()
    return col_map[name.lower()]

OTA_COL   = get_col("ota name")
SETUP_COL = get_col("set up details")
ARI_COL   = get_col("ari behaviour")
RES_COL   = get_col("reservation behaviour")
OTHER_COL = get_col("other important points")

# ================= SAFE TEXT CLEANER =================
def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r":\s*", ": ", text)
    if text:
        text = text[0].upper() + text[1:]
    return text

# ================= LAYOUT =================
left_col, right_col = st.columns([3, 7], gap="large")

# ================= LEFT PANEL =================
with left_col:
    st.markdown("### Search OTA")

    ota_query = st.text_input("OTA Name", placeholder="Booking.com, Agoda").strip()

    if not ota_query:
        st.info("Enter OTA name")
        st.stop()

    matches = df[df[OTA_COL].astype(str).str.lower().str.contains(ota_query.lower(), na=False)]
    if matches.empty:
        st.warning("No OTA found")
        st.stop()

    selected_ota = matches[OTA_COL].iloc[0]

    st.markdown(
        f"<div class='selected-box'><strong>Selected OTA:</strong> {selected_ota}</div>",
        unsafe_allow_html=True
    )

    option = st.radio(
        "Information Type",
        (
            "Setup Details",
            "ARI Behaviour",
            "Reservation Behaviour",
            "Other Important Points",
        ),
    )

# ================= RIGHT PANEL =================
with right_col:
    ota_df = df[df[OTA_COL].astype(str).str.lower() == selected_ota.lower()]

    # Pick column based on option
    col_map_option = {
        "Setup Details": SETUP_COL,
        "ARI Behaviour": ARI_COL,
        "Reservation Behaviour": RES_COL,
        "Other Important Points": OTHER_COL,
    }
    active_col = col_map_option[option]

    st.markdown(f"### 📄 {option}")

    # 🔍 SEARCH INSIDE DETAILS
    detail_search = st.text_input(
        "Search inside details",
        placeholder="Type keyword e.g. payment, CVV, OPB..."
    ).strip().lower()

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    values = (
        ota_df[active_col]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    filtered = []
    for v in values:
        cleaned = clean_text(v)
        if not detail_search or detail_search in cleaned.lower():
            filtered.append(cleaned)

    if not filtered:
        st.info("No matching details found.")
    else:
        for item in filtered:
            st.markdown(f"- {item}")

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Search works within the selected section only • Compact single-page layout")
