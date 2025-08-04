
import streamlit as st
import pandas as pd
from pytube import YouTube

st.set_page_config(page_title="YouTube Sports Match Logger", layout="wide")
st.title("🎥 Sports Match Event Logger")

# Input: YouTube URL
youtube_url = st.text_input("Enter YouTube Video URL:", "")

if youtube_url:
    try:
        yt = YouTube(youtube_url)
        video_id = yt.video_id
        st.video(f"https://www.youtube.com/embed/{video_id}")
        st.success("YouTube video loaded successfully!")
    except Exception as e:
        st.error(f"Failed to load video: {e}")

# Session state to store events
if "event_log" not in st.session_state:
    st.session_state.event_log = []

st.markdown("---")
st.header("📝 Log Event")
event_type = st.selectbox("Event Type", ["Goal", "Foul", "Substitution", "Injury", "Other"])
description = st.text_input("Description (optional)")
timestamp = st.text_input("YouTube Timestamp (e.g., 00:23:45)", "")

if st.button("Log Event"):
    if timestamp:
        st.session_state.event_log.append({
            "Timestamp": timestamp,
            "Event": event_type,
            "Description": description
        })
        st.success("Event logged!")
    else:
        st.warning("Please enter a timestamp.")

# Display and export table
st.markdown("---")
st.header("📊 Logged Events")
if st.session_state.event_log:
    df = pd.DataFrame(st.session_state.event_log)
    st.dataframe(df, use_container_width=True)

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button("📥 Download CSV", data=csv, file_name="event_log.csv", mime="text/csv")
else:
    st.info("No events logged yet.")
