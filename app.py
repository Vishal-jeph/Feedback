# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from streamlit_autorefresh import st_autorefresh
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ----------------------
# CONFIG
# ----------------------
st.set_page_config(page_title="Course Feedback (Google Sheets)", layout="centered")

# Auto-refresh every 6 seconds so multiple users see updates live
st_autorefresh(interval=6_000, limit=None, key="autorefresh")

# CSS
st.markdown("""
<style>
    .title {text-align:center; font-size:38px; font-weight:800; color:#0ea5a4; margin-bottom:6px;}
    .subtitle {text-align:center; color:#64748b; margin-bottom:18px;}
    .section {background:white; padding:18px; border-radius:12px; box-shadow:0 6px 18px rgba(2,6,23,0.06); margin-top:18px;}
    .chat-box {background:#f8fafc; border-radius:12px; padding:12px; max-height:420px; overflow-y:auto;}
    .feedback-msg {background:#e5e7eb; padding:10px; border-radius:8px; margin:8px 0;}
    .stButton>button {border-radius:10px; background-color:#0ea5a4; color:white; font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# HELPER: Google Sheets
# ----------------------
# We expect two secrets on Streamlit Cloud:
#  - st.secrets["gcp_service_account"]  -> the SERVICE ACCOUNT JSON string
#  - st.secrets["gsheet_id"]            -> the Google Sheet ID (the part between /d/.../ in sheet URL)

def init_gs_client():
    """
    Initialize gspread client using the service account JSON stored in st.secrets["gcp_service_account"].
    """
    if "gcp_service_account" not in st.secrets:
        st.error("Missing GCP service account in Streamlit secrets. Add 'gcp_service_account' (JSON) to your app secrets.")
        st.stop()

    # The secret is expected to be a JSON string; parse it into a dict
    sa_info = json.loads(st.secrets["gcp_service_account"])
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    client = gspread.authorize(creds)
    return client

def get_worksheet():
    """
    Return the first worksheet object. Expects st.secrets['gsheet_id'] to be present.
    """
    if "gsheet_id" not in st.secrets:
        st.error("Missing 'gsheet_id' in Streamlit secrets. Add your Google Sheet ID as 'gsheet_id'.")
        st.stop()
    client = init_gs_client()
    sheet_id = st.secrets["gsheet_id"]
    sh = client.open_by_key(sheet_id)
    worksheet = sh.sheet1
    return worksheet

def read_feedbacks_from_sheet() -> pd.DataFrame:
    """
    Read all feedback rows from the sheet and return a DataFrame with columns ['timestamp','rating','comment'].
    If the sheet is empty / only headers, returns empty DataFrame.
    """
    ws = get_worksheet()
    all_values = ws.get_all_values()
    if not all_values or len(all_values) <= 1:
        return pd.DataFrame(columns=["timestamp", "rating", "comment"])
    df = pd.DataFrame(all_values[1:], columns=all_values[0])
    # Normalize columns if someone changed order
    expected = ["timestamp", "rating", "comment"]
    for col in expected:
        if col not in df.columns:
            df[col] = ""
    # Convert rating column to numeric if possible
    df["rating"] = pd.to_numeric(df["rating"], errors="coerce").fillna(0).astype(int)
    return df[expected]

def append_feedback_to_sheet(rating: int, comment: str):
    """
    Append a feedback row to the Google Sheet.
    Format: timestamp(ISO), rating (int), comment (string)
    """
    ws = get_worksheet()
    ts = datetime.utcnow().isoformat()
    ws.append_row([ts, int(rating), comment], value_input_option="USER_ENTERED")

# ----------------------
# UI
# ----------------------
st.markdown("<div class='title'>🎓 Semester Feedback Dashboard</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Please give honest feedback — it helps improve the course for everyone.</div>", unsafe_allow_html=True)

# Wordcloud
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### ☁️ Live WordCloud")
try:
    df_all = read_feedbacks_from_sheet()
except Exception as e:
    st.exception(e)
    st.stop()

if df_all.shape[0] == 0 or df_all["comment"].str.strip().replace("", pd.NA).dropna().empty:
    st.info("No comments yet. WordCloud will appear after the first comment.")
else:
    all_text = " ".join(df_all["comment"].astype(str).tolist())
    wc = WordCloud(width=900, height=400, background_color="white", stopwords=None, max_words=200).generate(all_text)
    fig, ax = plt.subplots(figsize=(10,4.5))
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    st.pyplot(fig, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Feedback form
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### ✍️ Submit Feedback")
with st.form("feedback_form", clear_on_submit=True):
    rating = st.slider("Rating (1 = Poor, 5 = Excellent)", 1, 5, 5)
    comment = st.text_area("Comments (please be constructive)", height=140)
    submitted = st.form_submit_button("Submit")
    if submitted:
        if not comment.strip():
            st.warning("Please enter a short comment before submitting.")
        else:
            try:
                append_feedback_to_sheet(rating, comment.strip())
                st.success("Thank you! Your feedback was saved ✅")
                # No need to call st.rerun(); the st_autorefresh will pick it up soon.
            except Exception as e:
                st.error("Failed to save feedback. See error message below.")
                st.exception(e)
st.markdown("</div>", unsafe_allow_html=True)

# Recent feedbacks (chat style)
st.markdown("<div class='section'>", unsafe_allow_html=True)
st.markdown("### 💬 Recent Feedbacks")
if df_all.shape[0] == 0:
    st.info("No feedbacks yet.")
else:
    # show newest first
    df_show = df_all.sort_values(by="timestamp", ascending=False).reset_index(drop=True)
    st.markdown("<div class='chat-box'>", unsafe_allow_html=True)
    for _, row in df_show.head(50).iterrows():
        ts = row["timestamp"]
        rating = int(row["rating"])
        comment = row["comment"]
        st.markdown(f"<div class='feedback-msg'><b>⭐ {rating}/5</b> — <i>{ts}</i><br>{st.session_state.get('highlight', '')}{comment}</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# footer
st.caption("Data stored in Google Sheets. If you update the sheet externally, the app will refresh automatically every few seconds.")

