import streamlit as st
import pandas as pd
import os
from textblob import TextBlob

# ================= CONFIG =================
EXCEL_PATH = "XY.xlsx"
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search Tool", layout="wide")

st.title("🔎 OTA Behaviour Search Tool")
st.caption("Search OTA → Select category → View corrected details")

# ================= LOAD EXCEL =================
if not os.path.exists(EXCEL_PATH):
    st.error("❌ XY.xlsx not found in repository root.")
    st.stop()

df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df.columns = df.columns.str.strip()

# ================= COLUMN SAFE MAPPING =================
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

# ================= TEXT CORRECTION =================
def correct_text(text: str) -> str:
    """
    Fix spelling + basic grammar.
    Safe fallback if correction fails.
    """
    try:
        blob = TextBlob(text)
        corrected = str(blob.correct())
        return corrected
    except Exception:
        return text  # fallback if anything breaks

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
def show_corrected_values(column_name):
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
        corrected = correct_text(v)
        st.markdown(f"- {corrected}")

if option == "Setup Details":
    st.subheader("🛠 Setup Details (Auto-Corrected)")
    show_corrected_values(SETUP_COL)

elif option == "ARI Behaviour":
    st.subheader("📊 ARI Behaviour (Auto-Corrected)")
    show_corrected_values(ARI_COL)

elif option == "Reservation Behaviour":
    st.subheader("📑 Reservation Behaviour (Auto-Corrected)")
    show_corrected_values(RES_COL)

elif option == "Other Important Points":
    st.subheader("📌 Other Important Points (Auto-Corrected)")
    show_corrected_values(OTHER_COL)

st.markdown("---")
st.caption("Text is auto-corrected for spelling and basic grammar.")
