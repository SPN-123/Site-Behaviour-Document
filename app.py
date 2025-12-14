import streamlit as st
import pandas as pd
import os

# ================= CONFIG =================
EXCEL_PATH = "XY.xlsx"      # Excel file must be in repo root
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search Tool", layout="wide")

st.title("🔎 OTA Behaviour Search Tool")
st.caption("Search OTA → Select category → View details")

# ================= LOAD EXCEL =================
if not os.path.exists(EXCEL_PATH):
    st.error("❌ XY.xlsx not found in repository root.")
    st.stop()

try:
    df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
except Exception as e:
    st.error(f"❌ Failed to read Excel file: {e}")
    st.stop()

# ================= NORMALIZE COLUMNS =================
df.columns = df.columns.str.strip()

# Create case-insensitive column map
col_map = {c.lower(): c for c in df.columns}

def get_col(col_name: str):
    key = col_name.lower()
    if key not in col_map:
        st.error(f"❌ Required column not found: {col_name}")
        st.write("📌 Columns detected in Excel:", list(df.columns))
        st.stop()
    return col_map[key]

OTA_COL   = get_col("ota name")
SETUP_COL = get_col("set up details")
ARI_COL   = get_col("ari behaviour")
RES_COL   = get_col("reservation behaviour")
OTHER_COL = get_col("other important points")

# ================= OTA SEARCH =================
st.subheader("Search OTA")

ota_query = st.text_input(
    "Enter OTA Name (e.g. Booking.com, Agoda)",
    placeholder="Type OTA name here..."
).strip()

if not ota_query:
    st.info("ℹ️ Please enter an OTA name to continue.")
    st.stop()

matches = df[df[OTA_COL].astype(str).str.lower().str.contains(ota_query.lower(), na=False)]

if matches.empty:
    st.warning("⚠️ No OTA found matching your search.")
    st.stop()

selected_ota = matches[OTA_COL].iloc[0]

st.success(f"Selected OTA: **{selected_ota}**")

ota_df = df[df[OTA_COL].astype(str).str.lower() == selected_ota.lower()]

# ================= RADIO BUTTON =================
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

st.markdown("---")

# ================= DISPLAY FUNCTION =================
def show_values(column_name):
    values = (
        ota_df[column_name]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    if len(values) == 0:
        st.info("ℹ️ No data available for this section.")
        return

    for v in values:
        st.markdown(f"- {v}")

# ================= OUTPUT =================
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
st.caption("Ensure XY.xlsx is updated in GitHub root for latest data.")
