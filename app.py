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
.block-container {padding-top: 1rem;}
.selected-box {
    background:#ecfdf5;
    padding:8px 12px;
    border-radius:6px;
    border:1px solid #a7f3d0;
    margin-bottom:8px;
}
.section-box {
    background:#f9fafb;
    padding:12px 16px;
    border-radius:8px;
    border:1px solid #e5e7eb;
}
</style>
""", unsafe_allow_html=True)

# ================= TITLE =================
st.markdown("## 🔎 OTA Behaviour Search Tool")
st.caption("Text or Voice Search → Select category → Search inside details")
st.markdown("---")

# ================= LOAD EXCEL =================
df = pd.read_excel(EXCEL_PATH, sheet_name=SHEET_NAME)
df.columns = df.columns.str.strip()

col_map = {c.lower(): c for c in df.columns}

def col(name):
    return col_map[name.lower()]

OTA_COL   = col("ota name")
SETUP_COL = col("set up details")
ARI_COL   = col("ari behaviour")
RES_COL   = col("reservation behaviour")
OTHER_COL = col("other important points")

# ================= HELPERS =================
def clean_text(t):
    t = str(t).strip()
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r":\s*", ": ", t)
    return t[0].upper() + t[1:] if t else ""

def normalize_ota(t):
    t = t.lower().strip()
    t = t.replace(" dot ", ".")
    t = t.replace(" dotcom", ".com")
    t = t.replace(" dot com", ".com")
    t = t.replace(" con", ".com")
    t = t.replace(" ", "")
    return t

# ================= VOICE SEARCH =================
components.html("""
<script>
function startVoice(){
  const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
  rec.lang = 'en-US';
  rec.onresult = e => {
    const txt = e.results[0][0].transcript;
    const otaInput = window.parent.document.querySelector('input[data-testid="ota-input"]');
    otaInput.value = txt;
    otaInput.dispatchEvent(new Event('input', {bubbles:true}));
  }
  rec.start();
}
</script>

<button onclick="startVoice()"
 style="padding:8px 12px;border-radius:6px;border:1px solid #ccc;background:#fff;">
🎤 Voice Search
</button>
""", height=60)

# ================= LAYOUT =================
left, right = st.columns([3,7])

# ================= LEFT =================
with left:
    st.markdown("### Search OTA")

    ota_query = st.text_input(
        "OTA Name",
        key="ota_input",
        placeholder="Type or speak OTA name"
    )
    st.markdown(
        "<script>document.querySelector('input').setAttribute('data-testid','ota-input')</script>",
        unsafe_allow_html=True
    )

    if ota_query:
        nq = normalize_ota(ota_query)
        matches = df[
            df[OTA_COL].astype(str).str.lower().apply(normalize_ota).str.contains(nq)
        ]
    else:
        matches = pd.DataFrame()

    if not matches.empty:
        selected_ota = matches[OTA_COL].iloc[0]
        st.markdown(
            f"<div class='selected-box'><b>Selected OTA:</b> {selected_ota}</div>",
            unsafe_allow_html=True
        )

        option = st.radio(
            "Information Type",
            ["Setup Details", "ARI Behaviour", "Reservation Behaviour", "Other Important Points"]
        )
    else:
        option = None
        selected_ota = None

# ================= RIGHT =================
with right:
    if selected_ota:
        ota_df = df[
            df[OTA_COL].astype(str).str.lower().apply(normalize_ota)
            == normalize_ota(selected_ota)
        ]

        col_map_opt = {
            "Setup Details": SETUP_COL,
            "ARI Behaviour": ARI_COL,
            "Reservation Behaviour": RES_COL,
            "Other Important Points": OTHER_COL,
        }

        active_col = col_map_opt[option]

        st.markdown(f"### 📄 {option}")

        detail_search = st.text_input(
            "Search inside details",
            placeholder="payment, cvv, allocation..."
        ).lower()

        st.markdown("<div class='section-box'>", unsafe_allow_html=True)

        shown = False
        for v in ota_df[active_col].dropna().unique():
            txt = clean_text(v)
            if not detail_search or detail_search in txt.lower():
                st.markdown(f"- {txt}")
                shown = True

        if not shown:
            st.info("No matching details found.")

        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Enter or speak an OTA name to see details.")
