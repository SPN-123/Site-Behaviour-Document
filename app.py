import streamlit as st
import pandas as pd
import os
import re

# ================= CONFIG =================
EXCEL_PATH = "XY.xlsx"
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search Tool", layout="wide")

st.title("🔎 OTA Behaviour Search Tool")
st.caption("Search OTA → Select category → View cleaned (meaning-safe) details")

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
    """
    Meaning-safe cleanup:
    - fixes spacing
    - fixes punctuation
    - keeps ALL original words intact
    """
    if not isinstance(text, str):
        return ""

    text = text.strip()
    text = re.sub(r"\s+", " ", text)              # extra spaces
    text = re.sub(r"\.\s*(\d)", r". \1", text)    # spacing after full stop
    text = re.sub(r":\s*", ": ", text)            # spacing after colon
    text = re.sub(r";\s*", "; ", text)

    # Capitalize first letter only (do NOT change words)
    if text:
        text = text[0].upper() + text[1:]

    return text

# ================= OTA SEARCH =================
st.subheader("Search OTA")

ota_query = st.text_input(
    "Enter OTA Name (e.g. Booking.com, Agoda)",
    placeholder="Type OTA name..."
).strip()

if not ota_query:
    st.info("Please enter an OTA name.")
    st.stop()

matches = df[df[OTA_COL].astype(str).str.lower().str.contains(ota_query.lower(), na=False)]

if matches.empty:
    st.warning("No OTA found.")
    st.stop()

selected_ota = matches[OTA_COL].iloc[0]
st.success(f"Selected OTA: **{selected_ota}**")

ota_df = df[df[OTA_COL].astype(str).str.lower() == selected_ota.lower()]

# ================= RADIO BUTTON =================
option = st.radio(
    "Select Information Type",
    (
        "Setup Details",
        "ARI Behaviour",
        "Reservation Behaviour",
        "Other Important Points",
    ),
    horizontal=True,
)

st.markdown("---")

# ================= DISPLAY =================
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
    st.subheader("🛠 Setup Details")
    show_values(SETUP_COL)

elif option == "ARI Behaviour":
    st.subheader("📊 ARI Behaviour")
    show_values(ARI_COL)

elif option == "Reservation Behaviour":
    st.subheader("📑 Reservation Behaviour")
    show_values(RES_COL)

elif option == "Other Important Points":
    st.subheader("📌 Other Important Points")
    show_values(OTHER_COL)

st.markdown("---")
st.caption("Text is cleaned safely. Meaning and brand names are preserved.")
