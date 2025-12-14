import streamlit as st
import pandas as pd
import os
import re
import streamlit.components.v1 as components

# ================= CONFIG =================
EXCEL_PATH = "XY.xlsx"
SHEET_NAME = "Sheet1"

st.set_page_config(page_title="OTA Behaviour Search Tool", layout="wide")

# ================= CSS =================
st.markdown("""
<style>
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
.stTextInput, .stRadio {margin-bottom: 6px;}
.selected-box {
    background-color: #ecfdf5;
    padding: 8px 12px;
    border-radius: 6px;
    border: 1px solid #a7f3d0;
    margin-bottom: 8px;
}
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
st.caption("Text or Voice Search → Select category → Search inside details")
st.markdown("---")

# ================= LOAD EXCEL =================
if not os.path.exists(EXCEL_PATH):
    st.error("❌ XY.xlsx not found in repository root.")
    st.stop()

df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df.columns = df.columns.str.strip()

# ================= COLUMN MAPPING =================
col_map = {c.lower(): c for c in df.columns}

def get_col(name):
    if name.lower() not in col_map:
        st.error(f"Missing column: {name}")
        st.stop()
    return col_map[name.lower()]

OTA_COL   = get_col("ota name")
SETUP_COL = get_col("set up details")
ARI_COL   = get_col("ari behaviour")
RES_COL   = get_col("reservation behaviour")
OTHER_COL = get_col("other important points")

# ================= TEXT CLEANER (SAFE) =================
def clean_text(text):
    if not isinstance(text, str):
        return ""
    text = text.strip()
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r":\s*", ": ", text)
    return text[0].upper() + text[1:] if text else ""

# ================= OTA NORMALIZATION =================
def normalize_ota(text):
    if not text:
        return ""
    t = text.lower().strip()

    replacements = {
        " dot ": ".",
        " dotcom": ".com",
        " dot com": ".com",
        " con": ".com",
        " coma": ".com",
    }

    for k, v in replacements.items():
        t = t.replace(k, v)

    t = t.replace(" ", "")
    return t

# ================= VOICE SEARCH =================
components.html(
    """
    <script>
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = 'en-US';

    function startVoice() {
        recognition.start();
    }

    recognition.onresult = function(event) {
        const text = event.results[0][0].transcript;
        const input = window.parent.document.querySelector('input[type="text"]');
        input.value = text;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }
    </script>

    <button onclick="startVoice()" style="
        padding:8px 12px;
        border-radius:6px;
        border:1px solid #ccc;
        background:#fff;
        cursor:pointer;
        margin-bottom:10px;">
        🎤 Voice Search
    </button>
    """,
    height=60
)

# ================= LAYOUT =================
left_col, right_col = st.columns([3, 7], gap="large")

# ================= LEFT PANEL =================
with left_col:
    st.markdown("### Search OTA")

    ota_query = st.text_input(
        "OTA Name",
        placeholder="Type or speak OTA name (e.g. Booking.com)"
    ).strip()

    if not ota_query:
        st.info("Enter or speak OTA name")
        st.stop()

    normalized_query = normalize_ota(ota_query)

    matches = df[
        df[OTA_COL]
        .astype(str)
        .str.lower()
        .apply(normalize_ota)
        .str.contains(normalized_query, na=False)
    ]

    if matches.empty:
        st.warning("No OTA found")
        st.stop()

    selected_ota = matches[OTA_COL].iloc[0]

    st.markdown(
        f"<div class='selected-box'><strong>Selected OTA:</strong> {selected_ota}</div>",
        unsafe_allow_html=True
    )

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
    ota_df = df[
        df[OTA_COL]
        .astype(str)
        .str.lower()
        .apply(normalize_ota)
        == normalize_ota(selected_ota)
    ]

    option_map = {
        "Setup Details": SETUP_COL,
        "ARI Behaviour": ARI_COL,
        "Reservation Behaviour": RES_COL,
        "Other Important Points": OTHER_COL,
    }

    active_col = option_map[option]

    st.markdown(f"### 📄 {option}")

    detail_search = st.text_input(
        "Search inside details",
        placeholder="payment, cvv, allocation..."
    ).lower()

    st.markdown("<div class='section-box'>", unsafe_allow_html=True)

    values = ota_df[active_col].dropna().unique()

    shown = False
    for v in values:
        cleaned = clean_text(v)
        if not detail_search or detail_search in cleaned.lower():
            st.markdown(f"- {cleaned}")
            shown = True

    if not shown:
        st.info("No matching details found.")

    st.markdown("</div>", unsafe_allow_html=True)

st.caption("Voice search supports: booking.com, booking dot com, booking con, agoda")
