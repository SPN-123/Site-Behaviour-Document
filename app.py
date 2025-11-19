import streamlit as st
import pandas as pd
import os
from typing import List

# ---------- CONFIG ----------
EXCEL_PATH = "XY.xlsx"   # <--- path to your uploaded Excel (from your session)
SHEET_NAME = "XY"                   # change if your sheet name is different

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")
st.title("🔎 OTA Knowledge Search Tool")
st.write("Type an OTA name in the box, choose the match, then select a category button for that OTA.")

# ---------- Helpers ----------

def read_excel_safe(path: str, sheet_name=None) -> pd.DataFrame:
    """Read excel with clear errors."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Excel file not found at: {path}")
    try:
        if sheet_name is None:
            return pd.read_excel(path)
        # if sheet name not present pandas will raise — let it bubble as helpful error
        return pd.read_excel(path, sheet_name=sheet_name)
    except Exception as e:
        raise RuntimeError(f"Failed to read Excel file: {e}") from e

@st.cache_data
def load_df_cached(path: str, sheet_name: str = None) -> pd.DataFrame:
    return read_excel_safe(path, sheet_name)


# ---------- Load Data (with fallback uploader) ----------
uploaded_df = None

try:
    if os.path.exists(EXCEL_PATH):
        df = load_df_cached(EXCEL_PATH, SHEET_NAME)
    else:
        st.warning(f"Default Excel not found at {EXCEL_PATH}.")
        uploaded = st.file_uploader("Upload XY.xlsx (fallback)", type=["xlsx"])
        if uploaded is None:
            st.info("Please upload the XY.xlsx file or place it at the path: /mnt/data/XY.xlsx")
            st.stop()
        else:
            # read uploaded file
            try:
                # If provided sheet name exists use it, else use first sheet
                xls = pd.ExcelFile(uploaded)
                sheet_to_read = SHEET_NAME if SHEET_NAME in xls.sheet_names else 0
                df = pd.read_excel(xls, sheet_name=sheet_to_read)
            except Exception as e:
                st.error(f"Error reading uploaded file: {e}")
                st.stop()

except FileNotFoundError as e:
    st.error(str(e))
    st.stop()
except RuntimeError as e:
    st.error(str(e))
    st.stop()
except Exception as e:
    st.error(f"Unexpected error: {e}")
    st.stop()

# Basic validation
if df is None or df.empty:
    st.error("Loaded dataframe is empty. Check the Excel file and sheet name.")
    st.stop()

# ---------- Detect structure ----------
cols = [c for c in df.columns]
# Try detect OTA column
possible_ota_cols = [c for c in cols if c.lower() in ("ota", "ota name", "ota_name", "channel", "channel name")]
ota_col = possible_ota_cols[0] if possible_ota_cols else cols[0]

has_category_col = any(c.lower() == "category" for c in cols)
category_col = [c for c in cols if c.lower() == "category"][0] if has_category_col else None

if not has_category_col:
    # treat other columns (except ota_col) as category columns
    category_cols = [c for c in cols if c != ota_col]
else:
    category_cols = None

# Build ota list
ota_list = sorted(df[ota_col].dropna().astype(str).unique(), key=str.lower)

# ---------- UI: Search & select OTA ----------
query = st.text_input("Search OTA name (type part of the OTA name):").strip()

if query:
    matches = [o for o in ota_list if query.lower() in o.lower()]
else:
    matches = ota_list

if not matches:
    st.warning("No OTA matches found. Try a different search term or upload a different file.")
    st.stop()

selected_ota = st.selectbox("Select OTA from matches", matches)

# ---------- Determine available categories for selected OTA ----------
FIXED_CATEGORIES = ["Setup details", "ARI", "Reservations"]


def get_available_categories_for_ota(ota: str) -> List[str]:
    ota = str(ota).strip()
    if has_category_col:
        rows = df[df[ota_col].astype(str).str.strip().str.lower() == ota.lower()]
        if rows.empty:
            return []
        cats = rows[category_col].dropna().astype(str).str.strip().unique().tolist()
        return cats
    else:
        # one-row-per-OTA expected
        rows = df[df[ota_col].astype(str).str.strip().str.lower() == ota.lower()]
        if rows.empty:
            return []
        row = rows.iloc[0]
        available = []
        for c in category_cols:
            val = row.get(c)
            if pd.notna(val):
                sval = str(val).strip().lower()
                if sval not in ("", "na", "n/a", "none", "no", "0"):
                    available.append(c)
        return available

available_categories = get_available_categories_for_ota(selected_ota)

# Normalize available categories to match fixed names when possible
# (so e.g. 'Setup detail' or 'Setup details' both map)
normalized_available = set()
for a in available_categories:
    a_low = a.strip().lower()
    if "setup" in a_low:
        normalized_available.add("Setup details")
    elif a_low in ("ari", "a.r.i"):
        normalized_available.add("ARI")
    elif "reserv" in a_low:
        normalized_available.add("Reservations")
    else:
        # keep the original
        normalized_available.add(a)

# ---------- Show category buttons (only those relevant to selected OTA) ----------
st.markdown(f"**Available categories for**: `{selected_ota}`")
cols_btn = st.columns(len(FIXED_CATEGORIES))
showed_any = False
for i, cat in enumerate(FIXED_CATEGORIES):
    with cols_btn[i]:
        if cat in normalized_available:
            showed_any = True
            if st.button(cat):
                # Show details for this category
                if has_category_col:
                    subset = df[
                        (df[ota_col].astype(str).str.strip().str.lower() == selected_ota.lower()) &
                        (df[category_col].astype(str).str.strip().str.lower().str.contains(cat.split()[0].lower()))
                    ]
                    if subset.empty:
                        st.info("No details found for this OTA/category.")
                    else:
                        details_df = subset.drop(columns=[ota_col, category_col], errors="ignore")
                        if details_df.shape[1] == 0:
                            st.write("Row data:")
                            st.write(subset)
                        else:
                            st.write(f"Details for **{cat}**:")
                            st.dataframe(details_df)
                else:
                    # category columns layout: read the column value
                    rows = df[df[ota_col].astype(str).str.strip().str.lower() == selected_ota.lower()]
                    if rows.empty:
                        st.info("No row found for this OTA.")
                    else:
                        # try to find the original column that matched this fixed category
                        # prefer exact match else fuzzy substring
                        matched_cols = [c for c in category_cols if c.strip().lower() == cat.lower() or cat.split()[0].lower() in c.strip().lower()]
                        if not matched_cols:
                            matched_cols = [c for c in category_cols if cat.split()[0].lower() in c.strip().lower()]
                        if not matched_cols:
                            st.info("No column found for this category in the sheet.")
                        else:
                            for mc in matched_cols:
                                val = rows.iloc[0].get(mc)
                                if pd.isna(val) or str(val).strip() == "":
                                    st.info(f"No content in column {mc} for this OTA.")
                                else:
                                    st.write(f"**{mc}**:")
                                    st.write(val)
        else:
            st.markdown(f"<div style='opacity:0.45;padding:8px;border-radius:6px;border:1px solid #eee;text-align:center'>{cat} (not available)</div>", unsafe_allow_html=True)

if not showed_any:
    # If none of the fixed categories matched, show other available categories (if any)
    if len(available_categories) > 0:
        st.subheader("Other categories available for this OTA")
        for c in available_categories:
            if st.button(c):
                if has_category_col:
                    subset = df[
                        (df[ota_col].astype(str).str.strip().str.lower() == selected_ota.lower()) &
                        (df[category_col].astype(str).str.strip().str.lower() == c.strip().lower())
                    ]
                    if subset.empty:
                        st.info("No details found for this OTA/category.")
                    else:
                        st.dataframe(subset.drop(columns=[ota_col, category_col], errors="ignore"))
                else:
                    rows = df[df[ota_col].astype(str).str.strip().str.lower() == selected_ota.lower()]
                    if rows.empty:
                        st.info("No row found for this OTA.")
                    else:
                        val = rows.iloc[0].get(c)
                        st.write(val)
    else:
        st.info("No categories found for the selected OTA.")

# ---------- Optional: show raw row ----------
with st.expander("Show raw row for selected OTA"):
    st.write(df[df[ota_col].astype(str).str.strip().str.lower() == selected_ota.lower()])

# ---------- Footer guidance ----------
st.markdown("---")
st.caption(f"Using Excel path: `{EXCEL_PATH}`. If you deploy from GitHub, change EXCEL_PATH to 'XY.xlsx' (file in same folder as app.py).")
