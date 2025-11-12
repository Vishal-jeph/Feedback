import streamlit as st
import pandas as pd
import os
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# ===== Page Config =====
st.set_page_config(page_title="Feedback & WordCloud App", layout="centered")
st.markdown("""
    <style>
        .title {
            text-align: center;
            font-size: 42px !important;
            font-weight: 800;
            color: #3b82f6;
            margin-bottom: 5px;
        }
        .subtitle {
            text-align: center;
            font-size: 22px;
            color: #666;
            margin-bottom: 30px;
        }
        .section-title {
            font-size: 26px;
            font-weight: 600;
            color: #10b981;
            margin-top: 40px;
        }
        .chat-box {
            background-color: #f9fafb;
            border-radius: 15px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }
        .feedback-msg {
            background-color: #334d80;
            border-radius: 10px;
            padding: 10px;
            margin: 5px 0;
        }
        .stButton>button {
            border-radius: 10px;
            background-color: #2563eb;
            color: white;
            font-weight: 600;
            transition: 0.3s;
        }
        .stButton>button:hover {
            background-color: #1d4ed8;
        }
    </style>
""", unsafe_allow_html=True)

# ===== Local CSV File =====
FILE_PATH = "feedbacks.csv"
if not os.path.exists(FILE_PATH):
    df = pd.DataFrame(columns=["rating", "comment"])
    df.to_csv(FILE_PATH, index=False)

# ===== Functions =====
def load_feedbacks():
    return pd.read_csv(FILE_PATH)

def save_feedback(rating, comment):
    df = load_feedbacks()
    df = pd.concat([df, pd.DataFrame([{"rating": rating, "comment": comment}])], ignore_index=True)
    df.to_csv(FILE_PATH, index=False)

def generate_wordcloud():
    df = load_feedbacks()
    if df.empty or df["comment"].dropna().empty:
        return None
    text = " ".join(df["comment"].astype(str))
    wc = WordCloud(width=900, height=500, background_color="white", colormap="cool").generate(text)
    return wc

# ===== Header =====
st.markdown("<div class='title'>💬 Feedback Dashboard(It's anonymous)</div>", unsafe_allow_html=True)
st.markdown("""
    <div class='subtitle'>
        As the course is end now I want you all to please
        Share your thoughts and help us improve! 🌟  
        Every feedback you give shapes the experience for everyone.
    </div>
""", unsafe_allow_html=True)

# ===== WordCloud Section =====
st.markdown("<div class='section-title'>🌀 Live Word Cloud</div>", unsafe_allow_html=True)
wordcloud = generate_wordcloud()
if wordcloud:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.imshow(wordcloud, interpolation='bilinear')
    ax.axis("off")
    st.pyplot(fig)
else:
    st.info("No feedback yet — be the first to share something!")

# ===== Feedback Form =====
st.markdown("<div class='section-title'>📝 Give Your Feedback</div>", unsafe_allow_html=True)
with st.form("feedback_form", clear_on_submit=True):
    rating = st.slider("Rate your experience (1 = Poor, 5 = Excellent)", 1, 5, 3)
    comment = st.text_area("Your thoughts:", placeholder="Type your feedback here...")
    submit = st.form_submit_button("Submit Feedback")
    if submit:
        if comment.strip():
            save_feedback(rating, comment)
            st.success("✅ Feedback submitted successfully!")
            st.rerun()  # <-- Updated for latest Streamlit
        else:
            st.warning("⚠️ Please write a comment before submitting.")

# ===== Feedback Display =====
st.markdown("<div class='section-title'>💭 Recent Feedback</div>", unsafe_allow_html=True)
feedbacks = load_feedbacks()
if not feedbacks.empty:
    st.markdown("<div class='chat-box'>", unsafe_allow_html=True)
    for _, row in feedbacks[::-1].iterrows():
        st.markdown(f"""
            <div class='feedback-msg'>
                ⭐ <b>Rating:</b> {int(row['rating'])}/5<br>
                💬 {row['comment']}
            </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No feedbacks yet!")
