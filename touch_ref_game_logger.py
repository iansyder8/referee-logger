import streamlit as st
import pandas as pd
from pytube import YouTube
from streamlit_player import st_player
from streamlit_javascript import st_javascript
from streamlit_keypress import key_press_events


def format_seconds(total_seconds: float) -> str:
    """Return ``HH:MM:SS`` formatted string for the given ``total_seconds``."""
    total_seconds = int(total_seconds)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


st.set_page_config(page_title="Touch Ref Game Logger", layout="wide")

# Expand the main container to the full screen width
st.markdown(
    """
    <style>
        .stApp .block-container {
            padding-top: 1rem;
            padding-left: 0;
            padding-right: 0;
            max-width: 100%;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Instructions
# -----------------------------------------------------------------------------

st.title("Touch Ref Game Logger")
st.markdown(
"""
**Hotkeys**

- `A`, `S`, `D`, `F` – select a referee
- `1` / `2` / `3` / `4` / `5` / `6` / `7` / `8` / `9` / `0` – log the matching event type

**Workflow**
1. Enter referee names below.
2. Paste a YouTube URL to load the video.
3. Use the hotkeys above to log events as the video plays.
4. Download the logged events as a CSV when finished.

Click anywhere on the page to ensure it has focus before using the hotkeys.
"""
)

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Available event types mapped to hotkeys 1-0
EVENT_TYPES = [
    "Short 7M",
    "Long 7M",
    "Incorrect IC",
    "Avoidable Penalty",
    "Penalty Missed",
    "Control Issue",
    "Turnover Missed",
    "Sideline Issue",
    "Dis-interested",
    "Other",
]

# Numeric hotkeys corresponding to event types
EVENT_HOTKEYS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "0"]

# Referee setup
# Arrange referee name inputs in columns for a cleaner layout
name_cols = st.columns(4)
name_labels = [
    "Referee 1 Name",
    "Referee 2 Name",
    "Referee 3 Name",
    "Referee 4 Name",
]
name_keys = ["referee_a", "referee_s", "referee_d", "referee_f"]
for col, label, key in zip(name_cols, name_labels, name_keys):
    with col:
        st.text_input(label, key=key)

# Tidy up the appearance of the name inputs
st.markdown(
    """
    <style>
        div[data-testid="column"] div[data-testid="stTextInput"] > div > input {
            padding: 4px;
            height: 2rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

if "current_referee" not in st.session_state:
    st.session_state["current_referee"] = ""
if "ref_key" not in st.session_state:
    st.session_state["ref_key"] = ""
if "last_key" not in st.session_state:
    st.session_state["last_key"] = ""

ref_map = {
    "a": st.session_state.get("referee_a", ""),
    "s": st.session_state.get("referee_s", ""),
    "d": st.session_state.get("referee_d", ""),
    "f": st.session_state.get("referee_f", ""),
}

# Session state to store events
if "event_log" not in st.session_state:
    st.session_state.event_log = []


# Global key listener for referee and event hotkeys
key_pressed = key_press_events()


def log_event(event_name: str) -> None:
    """Log an event with the currently selected referee."""
    if not st.session_state.get("ref_key"):
        st.warning("Press A, S, D, or F to select a referee before logging.")
        return
    referee_name = st.session_state.get(
        f"referee_{st.session_state['ref_key']}", ""
    )
    current_seconds = st.session_state.get("current_time", 0)
    formatted_time = format_seconds(current_seconds)
    st.session_state.event_log.append(
        {
            "Timestamp": formatted_time,
            "Event": event_name,
            "Referee": referee_name,
        }
    )
    st.success(f"Event '{event_name}' logged!")


# Handle hotkeys
if key_pressed and key_pressed != st.session_state.get("last_key"):
    st.session_state["last_key"] = key_pressed
    key_val = key_pressed.lower()
    # Preserve the current playback time so the video resumes after rerun
    st.session_state["resume_time"] = st.session_state.get("current_time", 0)
    if key_val in ["a", "s", "d", "f"]:
        st.session_state["ref_key"] = key_val
        st.session_state["current_referee"] = ref_map.get(key_val, "")
    elif key_val in EVENT_HOTKEYS[: len(EVENT_TYPES)]:
        event_index = EVENT_HOTKEYS.index(key_val)
        event_name = EVENT_TYPES[event_index]
        log_event(event_name)

# Input: YouTube URL
youtube_url = st.text_input("Enter YouTube Video URL:", "")

if youtube_url:
    viewport_width = st_javascript("window.innerWidth", key="viewport_width") or 0
    col1, col2 = st.columns([3, 2])
    with col1:
        # Maintain a 16:9 aspect ratio based on the available width
        player_height = int(viewport_width * 9 / 16) if viewport_width else 405
        start_time = st.session_state.pop("resume_time", None)
        player_kwargs = {
            'events': ['onProgress'],
            'progress_interval': 1000,
            'height': player_height,
            'key': 'youtube_player',
            'playing': True,
        }
        if start_time is not None:
            player_kwargs['start'] = start_time
        player_event = st_player(
            youtube_url,
            **player_kwargs,
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
    with col2:
        st.markdown("#### Log Event")
        ref_cols = st.columns(4)
        for col, key in zip(ref_cols, ["a", "s", "d", "f"]):
            with col:
                button_label = f"{key.upper()}: {ref_map[key]}" if ref_map[key] else key.upper()
                button_type = "primary" if st.session_state.get("ref_key") == key else "secondary"
                if st.button(button_label, key=f"select_ref_{key}", type=button_type):
                    st.session_state["ref_key"] = key
                    st.session_state["current_referee"] = ref_map[key]
        st.markdown(f"**Current Referee:** {st.session_state.get('current_referee', '')}")
        current_seconds = st.session_state.get("current_time", 0)
        formatted_time = format_seconds(current_seconds)
        st.markdown(f"**Current Video Time:** {formatted_time}")
        event_cols = st.columns(3)
        for idx, (hotkey, event_name) in enumerate(zip(EVENT_HOTKEYS, EVENT_TYPES)):
            col = event_cols[idx % 3]
            with col:
                if st.button(f"{hotkey}. {event_name}", key=f"event_btn_{hotkey}"):
                    log_event(event_name)

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
