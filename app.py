import streamlit as st
import pandas as pd
import os

EXCEL_PATH = "/mnt/data/XY.xlsx"
SHEET_NAME = "XY"   # adjust if needed

st.title("🔎 OTA Knowledge Search Tool (debug friendly)")

# --- Debug: show files present in /mnt/data to confirm upload ---
st.write("Checking for Excel file at:", EXCEL_PATH)
if st.checkbox("List files in /mnt/data (debug)", value=False):
    try:
        files = os.listdir("/mnt/data")
        st.write(files)
    except Exception as e:
        st.write("Could not list /mnt/data:", e)

# --- Robust loader with helpful messages ---
def read_excel_safe(path: str, sheet_name=None):
    """Try to read the Excel file and raise a clear error message if not found."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found at {path}")
    # read with fallback sheet handling
    try:
        if sheet_name is None:
            return pd.read_excel(path)
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        # surface a clear message (but don't leak secrets in production)
        raise RuntimeError(f"Error reading Excel file: {e}") from e

# Try to load file, otherwise let user upload via widget
df = None
try:
    # only cache after successful file check (so cache doesn't hide missing file)
    if os.path.exists(EXCEL_PATH):
        @st.cache_data
        def load_df(path, sheet_name):
            return read_excel_safe(path, sheet_name)
        df = load_df(EXCEL_PATH, SHEET_NAME)
    else:
        st.warning("Excel file not found at the default path.")
        uploaded = st.file_uploader("Upload XY.xlsx (fallback)", type=["xlsx"])
        if uploaded is not None:
            # read uploaded file directly (no need for path)
            df = pd.read_excel(uploaded, sheet_name=SHEET_NAME if SHEET_NAME in pd.ExcelFile(uploaded).sheet_names else 0)
except FileNotFoundError as e:
    st.error(str(e))
except RuntimeError as e:
    st.error(str(e))
except Exception as e:
    st.error("Unexpected error: " + str(e))

if df is None:
    st.stop()

st.success("Excel loaded OK — continuing with UI...")
# ... rest of your app code that uses df ...
