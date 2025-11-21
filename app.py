import streamlit as st
import pandas as pd
import re

# ---------- Configuration ----------
HEADER_IMAGE = "/mnt/data/750844b1-1540-4977-a219-0b2e2d3a5b56.png"  # provided screenshot path
PAGE_TITLE = "OTA Knowledge Search Tool"

# ---------- Utility helpers ----------
def strip_leading_number(text: str) -> str:
    """Remove leading numbers and punctuation (e.g. "1.EXPG" -> "EXPG")."""
    return re.sub(r"^\s*\d+[\s\.-:_]*", "", str(text)).strip()


def load_data():
    """Replace this with your actual data-loading logic.
    For demo, we create a small DataFrame similar to what your app expects.
    """
    data = {
        "OTA": ["Booking.com", "Booking.com", "Agoda", "MakeMyTrip"],
        "Detail": [
            "1.EXPG: channelid=123; available=10",
            "2.RATE: sell_code=ABC; allocation=5",
            "1.EXPG: channelid=777; available=3",
            "3.INFO: sell_code=ZZZ; allocation=1",
        ],
    }
    df = pd.DataFrame(data)
    return df


# ---------- Streamlit page config ----------
st.set_page_config(page_title=PAGE_TITLE, layout="wide")

# Small CSS to improve visuals
st.markdown(
    """
    <style>
    .header-row {display:flex; align-items:center; gap:16px}
    .logo-img {height:68px; border-radius:8px}
    .big-title {font-size:32px; font-weight:700; margin:0}
    .muted {color: #6b7280}
    .pill {background:#f3f4f6; padding:6px 10px; border-radius:999px; margin-right:6px}
    .det-chip {display:inline-block; padding:6px 10px; border-radius:999px; background:#eef2ff; margin:4px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Header ----------
col1, col2 = st.columns([6, 4])
with col1:
    st.markdown(f"<div class='header-row'>"
                f"<img src='{HEADER_IMAGE}' class='logo-img'/>"
                f"<div><h1 class='big-title'>{PAGE_TITLE}</h1>"
                f"<div class='muted'>Search OTA entries and inspect values inside the Detail column.</div></div>"
                f"</div>", unsafe_allow_html=True)
with col2:
    # Right side small info cards
    sheet_info_box = st.container()
    with sheet_info_box:
        st.markdown("**Sheet:** Sheet1  
**Rows:** 38")

st.markdown("---")

# ---------- Controls row ----------
controls_col, results_col = st.columns([4, 8])

with controls_col:
    # Search box (partial matching) — user requested a search text box instead of a long dropdown
    ota_search = st.text_input("Search OTA name", value="", placeholder="Type partial OTA name (e.g. 'book')")

    # Optional: a compact select of detected OTAs matching input
    df = load_data()
    all_otas = sorted(df['OTA'].unique())
    # Filter OTAs by search
    matching_otas = [o for o in all_otas if ota_search.lower() in o.lower()] if ota_search else all_otas

    selected_ota = st.selectbox("Select OTA", options=matching_otas)

    st.markdown("---")
    st.markdown("**Options**")
    show_raw = st.checkbox("Show raw Detail rows", value=False)

with results_col:
    st.subheader(f"Details for {selected_ota}")

    # Filter rows for selected OTA
    ota_rows = df[df['OTA'] == selected_ota]

    # Collect detected keys heuristically from Detail column
    detected_keys = set()
    details_parsed = []
    for idx, row in ota_rows.iterrows():
        detail = row['Detail']
        # naive split on semicolon and equal sign
        parts = [p.strip() for p in re.split(r"[;|,]", detail) if p.strip()]
        for p in parts:
            # take left of '=' or ':' if present
            key = re.split(r"[:=]", p)[0].strip()
            if key:
                detected_keys.add(key)
        details_parsed.append(detail)

    # Show chips for detected keys
    if detected_keys:
        st.markdown("**Detected keys:**")
        key_row = "".join([f"<span class='det-chip'>{strip_leading_number(k)}</span>" for k in sorted(detected_keys)])
        st.markdown(key_row, unsafe_allow_html=True)
    else:
        st.info("No keys detected for the selected OTA.")

    st.markdown("---")

    # Show parsed details inline (no page jump)
    for i, detail in enumerate(details_parsed, start=1):
        clean = strip_leading_number(detail)
        with st.expander(f"Detail row {i}: {clean.split(':')[0]}", expanded=False):
            st.write(clean)

    # Optionally show raw rows in a compact table
    if show_raw:
        st.markdown("**Raw Detail rows**")
        st.dataframe(ota_rows.reset_index(drop=True))

# Footer / small help
st.markdown("---")
st.caption("Tip: Use the search box and then pick the OTA from the compact list. Leading numbers in keys are automatically removed for display.")

# End of file
