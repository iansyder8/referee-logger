import streamlit as st
import pandas as pd
from pytube import YouTube
from streamlit_player import st_player
from streamlit_javascript import st_javascript


def format_seconds(total_seconds: float) -> str:
    """Return ``HH:MM:SS`` formatted string for the given ``total_seconds``."""
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


st.set_page_config(page_title="YouTube Sports Match Event Logger", layout="wide")
st.title("🎥 Sports Match Event Logger")

# Referee setup
st.text_input("Referee for A key", key="referee_a")
st.text_input("Referee for S key", key="referee_s")
st.text_input("Referee for D key", key="referee_d")

if "current_referee" not in st.session_state:
    st.session_state["current_referee"] = ""

key_pressed = st_javascript(
    """
if (!window.refKeyListener) {
    document.addEventListener('keydown', (e) => {
        const key = e.key.toLowerCase();
        if (['a', 's', 'd'].includes(key)) {
            Streamlit.setComponentValue(key);
        }
    });
    window.refKeyListener = true;
}
""",
    key="ref_key_listener",
)

if key_pressed:
    mapping = {
        "a": st.session_state.get("referee_a", ""),
        "s": st.session_state.get("referee_s", ""),
        "d": st.session_state.get("referee_d", ""),
    }
    st.session_state["current_referee"] = mapping.get(key_pressed, "")

st.markdown(f"**Current Referee:** {st.session_state.get('current_referee', '')}")

# Input: YouTube URL
youtube_url = st.text_input("Enter YouTube Video URL:", "")

if youtube_url:
    player_event = st_player(
        youtube_url,
        events=["onProgress"],
        progress_interval=1000,
        key="youtube_player",
    )
    if player_event and player_event.name == "onProgress" and player_event.data:
        st.session_state["current_time"] = player_event.data.get("playedSeconds", 0)

    if not st.session_state.get("video_loaded"):
        try:
            YouTube(youtube_url)
            st.success("YouTube video loaded successfully!")
            st.session_state["video_loaded"] = True
        except Exception as e:
            st.error(f"Failed to load YouTube video: {e}")

# Session state to store events
if "event_log" not in st.session_state:
    st.session_state.event_log = []

st.markdown("---")
st.header("📝 Log Event")
st.markdown(f"**Current Referee:** {st.session_state.get('current_referee', '')}")
event_type = st.selectbox(
    "Event Type",
    [
        "Goal",
        "Foul",
        "Substitution",
        "Injury",
        "Other",
        "Try Scored",
        "Penalty - Hard Touch",
        "Penalty - FWD Pass",
        "Penalty - In The Ruck",
        "Penalty - Not Moving Forward",
        "Penalty - Unknown",
        "Turn Over",
        "Penalty Missed",
        "Turn Over Missed",
    ],
)
description = st.text_input("Description (optional)")
current_seconds = st.session_state.get("current_time", 0)
formatted_time = format_seconds(current_seconds)
st.markdown(f"**Current Video Time:** {formatted_time}")

if st.button("Log Event"):
    selected_event = event_type  # preserve the exact selected value
    st.session_state.event_log.append(
        {
            "Timestamp": formatted_time,
            "Event": selected_event,
            "Description": description,
            "Referee": st.session_state.get("current_referee", ""),
        }
    )
    st.success("Event logged!")

# Display and export table
st.markdown("---")
st.header("📊 Logged Events")
if st.session_state.event_log:
    df = pd.DataFrame(st.session_state.event_log)
    st.dataframe(df, use_container_width=True)

    # Write the CSV to a local file and offer it for download
    output_path = "event_log.csv"
    df.to_csv(output_path, index=False)
    with open(output_path, "rb") as file:
        st.download_button(
            "📥 Download CSV", data=file, file_name=output_path, mime="text/csv"
        )
    st.caption(f"CSV saved locally as {output_path}")
else:
    st.info("No events logged yet.")
