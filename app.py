import streamlit as st
import pandas as pd
import re

# ---------- Configuration ----------
HEADER_IMAGE = "/mnt/data/750844b1-1540-4977-a219-0b2e2d3a5b56.png"
PAGE_TITLE = "OTA Knowledge Search Tool"

# ---------- Utility helpers ----------
def strip_leading_number(text: str) -> str:
    """Remove leading numbers and punctuation (e.g. '1.EXPG' -> 'EXPG')."""
    return re.sub(r"^\s*\d+[\s\.-:_]*", "", str(text)).strip()

def load_data():
    """Mock dataset — replace with your actual Excel load."""
    data = {
        "OTA": ["Booking.com", "Booking.com", "Agoda", "MakeMyTrip", "Expedia"],
        "Detail": [
            "1.EXPG: channelid=123; available=10",
            "2.RATE: sell_code=ABC; allocation=5",
            "1.EXPG: channelid=777; available=3",
            "3.INFO: sell_code=ZZZ; allocation=1",
            "1.EXPG: channelid=999; available=7"
        ],
    }
    return pd.DataFrame(data)

# ---------- Streamlit page config ----------
st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# CSS styling
st.markdown("""
<style>
.header-row {display:flex; align-items:center; gap:16px}
.logo-img {height:68px; border-radius:8px}
.big-title {font-size:32px; font-weight:700; margin:0}
.muted {color:#6b7280}
.det-chip {display:inline-block; padding:6px 10px; border-radius:999px; background:#eef2ff; margin:4px;}
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
col1, col2 = st.columns([6, 4])
with col1:
    st.markdown(f"""
    <div class='header-row'>
        <img src='{HEADER_IMAGE}' class='logo-img'/>
        <div>
            <h1 class='big-title'>{PAGE_TITLE}</h1>
            <div class='muted'>Search OTA entries and inspect values inside the Detail column.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("**Sheet:** Sheet1<br>**Rows:** 38", unsafe_allow_html=True)

st.markdown("---")

# ---------- Controls ----------
controls_col, results_col = st.columns([4, 8])

with controls_col:
    # 1) OTA name search (partial match)
    ota_search = st.text_input("Search OTA name", "", placeholder="Type partial OTA name (e.g. 'book')")

    # Load data and derive OTA list
    df = load_data()
    all_otas = sorted(df["OTA"].unique())

    matching_otas = [o for o in all_otas if ota_search.lower() in o.lower()] if ota_search else all_otas
    if not matching_otas:
        matching_otas = all_otas  # fallback

    # 2) OTA select
    selected_ota = st.selectbox("Select OTA", matching_otas)

    st.markdown("---")

    # 3) NEW: Search inside Detail values (filters detected keys + rows)
    detail_search = st.text_input("Search inside details", "", placeholder="Filter detail rows by text (e.g. 'channelid' or 'available')")

    st.markdown("---")
    show_raw = st.checkbox("Show raw Detail rows", False)

with results_col:
    st.subheader(f"Details for {selected_ota}")

    # Filter rows for selected OTA
    ota_rows = df[df["OTA"] == selected_ota].copy()

    # If user provided a detail_search, further filter rows that contain that substring (case-insensitive)
    if detail_search:
        ota_rows = ota_rows[ota_rows["Detail"].str.contains(detail_search, case=False, na=False)]

    # Collect detected keys heuristically from Detail column
    detected_keys = set()
    details_parsed = []
    for _, row in ota_rows.iterrows():
        detail = row["Detail"]
        parts = [p.strip() for p in re.split(r"[;,\|]", detail) if p.strip()]
        for p in parts:
            key = re.split(r"[:=]", p)[0].strip()
            if key:
                detected_keys.add(key)
        details_parsed.append(detail)

    # Show chips for detected keys (strip numbers like '1.EXPG' -> 'EXPG')
    if detected_keys:
        st.markdown("**Detected keys:**")
        chips = "".join([f"<span class='det-chip'>{strip_leading_number(k)}</span>" for k in sorted(detected_keys)])
        st.markdown(chips, unsafe_allow_html=True)
    else:
        st.info("No keys detected for the selected OTA (or no rows match your filters).")

    st.markdown("---")

    # Show parsed details inline (keeps everything on same page)
    if details_parsed:
        for i, detail in enumerate(details_parsed, start=1):
            clean = strip_leading_number(detail)
            with st.expander(f"Detail row {i}: {clean.split(':')[0]}", expanded=False):
                st.write(clean)
    else:
        st.write("_No detail rows to display._")

    # Optionally show raw rows in a compact table
    if show_raw:
        st.markdown("**Raw Detail rows**")
        st.dataframe(ota_rows.reset_index(drop=True))

st.markdown("---")
st.caption("Tip: Use the OTA search to narrow the list, pick an OTA, then use 'Search inside details' to filter specific keys or values.")
