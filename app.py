# app.py
import streamlit as st
import pandas as pd
from typing import List

# === CONFIG ===
EXCEL_PATH = "/mnt/data/XY.xlsx"   # <- your uploaded file path
SHEET_NAME = "XY"                 # change if your sheet name is different

st.set_page_config(page_title="OTA Knowledge Search Tool", layout="wide")

st.title("🔎 OTA Knowledge Search Tool")
st.write("Type an OTA name in the box, choose the match, then select a category button for that OTA.")

@st.cache_data
def load_df(path: str, sheet_name: str = None) -> pd.DataFrame:
    # Try reading specified sheet, fallback to first sheet if error
    try:
        if sheet_name:
            df = pd.read_excel(path, sheet_name=sheet_name)
        else:
            df = pd.read_excel(path)
    except Exception:
        df = pd.read_excel(path, sheet_name=0)
    return df

df = load_df(EXCEL_PATH, SHEET_NAME)

# Normalize columns and show them for debugging (optional)
# st.write("Columns:", list(df.columns))

# Try to detect OTA column automatically
possible_ota_cols = [c for c in df.columns if c.lower() in ("ota", "ota name", "ota_name", "channel")]
if possible_ota_cols:
    ota_col = possible_ota_cols[0]
else:
    # fallback to first column if we can't detect
    ota_col = df.columns[0]

# Identify category columns:
# If the sheet has a single 'Category' column with multiple rows per OTA, we handle that.
# Otherwise assume the categories are column names (like 'Setup details','ARI','Reservations').
has_category_col = any(c.lower() == "category" for c in df.columns)

if has_category_col:
    # Expect rows like: OTA | Category | Details (optional)
    category_col = [c for c in df.columns if c.lower() == "category"][0]
    detail_cols = [c for c in df.columns if c not in (ota_col, category_col)]
else:
    # Assume other columns besides ota_col are categories (boolean/text)
    category_cols = [c for c in df.columns if c != ota_col]

# Build list of OTAs
ota_list = sorted(df[ota_col].dropna().astype(str).unique(), key=str.lower)

# === SEARCH BOX ===
query = st.text_input("Search OTA name (type part of the OTA name):").strip().lower()

# Show suggestions when user types
if query:
    matches = [o for o in ota_list if query in o.lower()]
else:
    matches = ota_list  # show all if no query

if not matches:
    st.warning("No OTA matches found.")
    st.stop()

selected_ota = st.selectbox("Select OTA from matches", matches)

# === Determine categories for the selected OTA ===
def get_categories_for_ota(ota: str) -> List[str]:
    if has_category_col:
        # Rows where OTA matches and category not null
        rows = df[df[ota_col].astype(str).str.lower() == ota.lower()]
        cats = rows[category_col].dropna().astype(str).unique().tolist()
        return cats
    else:
        # Keep columns where the selected OTA has a non-empty / truthy value
        row = df[df[ota_col].astype(str).str.lower() == ota.lower()]
        if row.empty:
            return []
        row = row.iloc[0]
        cats = []
        for c in category_cols:
            val = row[c]
            # treat booleans, non-empty strings, and nonzero numbers as available categories
            if pd.notna(val) and not (isinstance(val, float) and pd.isna(val)):
                # If column value is something like 'No'/'0' treat as not available
                sval = str(val).strip().lower()
                if sval in ("", "na", "n/a", "none", "no", "0"):
                    continue
                cats.append(c)
        return cats

categories = get_categories_for_ota(selected_ota)

if not categories:
    st.info("No categories found for this OTA.")
    st.stop()

st.markdown("**Available categories for**: `" + selected_ota + "`")
cols = st.columns(len(categories))
for i, cat in enumerate(categories):
    with cols[i]:
        if st.button(cat):
            # Show details depending on sheet structure
            if has_category_col:
                # show all matching rows for that OTA and category
                subset = df[
                    (df[ota_col].astype(str).str.lower() == selected_ota.lower()) &
                    (df[category_col].astype(str).str.lower() == cat.lower())
                ]
                if subset.empty:
                    st.write("No details found for this category.")
                else:
                    # Show any additional detail columns if present
                    details_df = subset.drop(columns=[ota_col, category_col], errors="ignore")
                    if details_df.shape[1] == 0:
                        st.write("No extra detail columns. Row data:")
                        st.write(subset)
                    else:
                        st.write(f"Details for **{cat}**:")
                        st.dataframe(details_df)
            else:
                # If categories are columns, display the cell(s) content for this OTA and column
                row = df[df[ota_col].astype(str).str.lower() == selected_ota.lower()]
                if row.empty:
                    st.write("No row for selected OTA.")
                else:
                    value = row.iloc[0].get(cat, "")
                    if pd.isna(value) or str(value).strip() == "":
                        st.write("No content available for this category.")
                    else:
                        st.write(f"**{cat}** content:")
                        st.write(value)

# Optional: show raw row for debugging
with st.expander("Show raw row for selected OTA"):
    st.write(df[df[ota_col].astype(str).str.lower() == selected_ota.lower()])
