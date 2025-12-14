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
/* Reduce top padding */
.block-container {padding-top: 1rem; padding-bottom: 1rem;}

/* Compact headers */
h1 {font-size: 26px; margin-bottom: 4px;}
h2 {font-size: 20px; margin-bottom: 6px;}
h3 {font-size: 18px; margin-bottom: 6px;}

/* Reduce space between widgets */
.stTextInput, .stRadio {margin-bottom: 6px;}
hr {margin: 8px 0;}

/* Bullet list compact */
ul {margin-top: 4px; margin-bottom: 4px;}
li {margin-bottom: 4px;}

/* Highlight selected OTA */
.selected-box {
    background-color: #ecfdf5;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #a7f3d0;
    margin-bottom: 8px;
}

/* Section container */
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
st.caption("Search OTA → Select category → View details (compact view)")
st.markdown("---")

# ================= LOAD EXCEL =================
if not os.path.exists(EXCEL_PATH):
    st.error("❌ XY.xlsx not found in repository root.")
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
    text = re.sub(r"\.\s*(\d)", r". \1", text)
    text = re.sub(r":\s*", ": ", text)
    if text:
        text = text[0].upper() + text[1:]
    return text

# ================= LAYOUT =================
left_col, right_col = st.columns([3, 7], gap="large")

# ================= LEFT PANEL =================
with left_col:
    st.markdown("### Search OTA")

    ota_query = st.text_input(
        "OTA Name",
        placeholder="Booking.com, Agoda"
    ).strip()

    if not ota_query:
        st.info("Enter OTA name")
        st.stop()

    matches = df[df[OTA_COL].astype(str).str.lower().str.contains(ota_query.lower(), na=False)]
    if matches.empty:
        st.warning("No OTA found")
        st.stop()

    selected_ota = matches[OTA_COL].iloc[0]

    st.markdown(f"<div class='selected-box'><strong>Selected OTA:</strong> {selected_ota}</div>",
                unsafe_allow_html=True)

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

    st.markdown(f"### 📄 {option}")
    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    def show_values(column_name):
        values = (
            ota_df[column_name]
            .dropna()
            .astype(str)
            .str.strip()
            .unique()
        )
        if len(values) == 0:
            st.info("No data available.")
            return
        for v in values:
            st.markdown(f"- {clean_text(v)}")

    if option == "Setup Details":
        show_values(SETUP_COL)
    elif option == "ARI Behaviour":
        show_values(ARI_COL)
    elif option == "Reservation Behaviour":
        show_values(RES_COL)
    elif option == "Other Important Points":
        show_values(OTHER_COL)

    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")
st.caption("Compact single-page view • Clean alignment • Meaning preserved")
