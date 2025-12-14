import streamlit as st
import pandas as pd
import os

# ---------------- CONFIG ----------------
EXCEL_PATH = "XY.xlsx"   # Excel must be in repo root
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search", layout="wide")

st.title("🔎 OTA Behaviour Search Tool")
st.caption("Search OTA → Choose behaviour type → View details")

# ---------------- LOAD EXCEL ----------------
if not os.path.exists(EXCEL_PATH):
    st.error("XY.xlsx not found in repository root.")
    st.stop()

df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)

# Normalize column names
df.columns = [c.strip() for c in df.columns]

OTA_COL = "OTA Name"
SETUP_COL = "Set Up Details"
ARI_COL = "ARI Behaviour"
RES_COL = "Reservation Behaviour"
OTHER_COL = "Other Important points"

# ---------------- OTA SEARCH ----------------
st.subheader("Search OTA")

ota_query = st.text_input("Enter OTA Name (e.g. Booking.com, Agoda)").strip()

if not ota_query:
    st.info("Please enter an OTA name to begin.")
    st.stop()

matches = df[df[OTA_COL].str.lower().str.contains(ota_query.lower(), na=False)]

if matches.empty:
    st.warning("No OTA found matching your search.")
    st.stop()

selected_ota = matches[OTA_COL].iloc[0]

st.success(f"Selected OTA: **{selected_ota}**")

# Filter rows for selected OTA
ota_df = df[df[OTA_COL].str.lower() == selected_ota.lower()]

# ---------------- RADIO BUTTON ----------------
st.subheader("Select Information Type")

option = st.radio(
    "",
    (
        "Setup Details",
        "ARI Behaviour",
        "Reservation Behaviour",
        "Other Important Points",
    ),
    horizontal=True,
)

# ---------------- DISPLAY RESULTS ----------------
st.markdown("---")

def show_values(column_name):
    values = (
        ota_df[column_name]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    if len(values) == 0:
        st.info("No data available for this section.")
        return

    for v in values:
        st.markdown(f"- {v}")

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
