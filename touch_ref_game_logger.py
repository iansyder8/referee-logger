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

st.title("🎥 Touch Ref Game Logger")

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

# Available event types mapped to hotkeys 1-9
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
]

# Referee setup
st.text_input("Referee for A key", key="referee_a")
st.text_input("Referee for S key", key="referee_s")
st.text_input("Referee for D key", key="referee_d")

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
}

# Global key listener for referee and event hotkeys
key_pressed = st_javascript(
    """
thvxoy-codex/place-referee-selector-above-event-selector
const root = window.parent || window;
if (!root.globalKeyListener) {
=======
if (!window.globalKeyListener) {
main
    const handler = (e) => {
        let key = e.key || e.keyCode;
        if (typeof key === 'string') {
            key = key.toLowerCase();
        } else {
            key = String.fromCharCode(key).toLowerCase();
        }
        if (['a','s','d','1','2','3','4','5','6','7','8','9'].includes(key)) {
            e.preventDefault();
            Streamlit.setComponentValue(key);
        }
    };
thvxoy-codex/place-referee-selector-above-event-selector
    root.document.addEventListener('keydown', handler, true);
    root.globalKeyListener = true;
=======
    window.addEventListener('keydown', handler, true);
    window.globalKeyListener = true;
main
}
""",
    key="global_key_listener",
)


def log_event(event_name: str) -> None:
    """Log an event with the currently selected referee."""
    if not st.session_state.get("ref_key"):
        st.warning("Press A, S, or D to select a referee before logging.")
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
    if key_pressed in ["a", "s", "d"]:
        st.session_state["ref_key"] = key_pressed
        st.session_state["current_referee"] = ref_map.get(key_pressed, "")
    elif key_pressed in [str(i) for i in range(1, len(EVENT_TYPES) + 1)]:
        event_name = EVENT_TYPES[int(key_pressed) - 1]
        log_event(event_name)

# Input: YouTube URL
youtube_url = st.text_input("Enter YouTube Video URL:", "")

if youtube_url:
    viewport_width = st_javascript("window.innerWidth", key="viewport_width") or 0
    # Maintain a 16:9 aspect ratio based on the available width
    player_height = int(viewport_width * 9 / 16) if viewport_width else 405
    player_event = st_player(
        youtube_url,
        events=["onProgress"],
        progress_interval=1000,
        height=player_height,
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
# Referee selector above event selector
ref_cols = st.columns(3)
for col, key in zip(ref_cols, ["a", "s", "d"]):
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

# Event buttons laid out in a grid
event_cols = st.columns(3)
for i, event_name in enumerate(EVENT_TYPES, start=1):
    col = event_cols[(i - 1) % 3]
    with col:
        if st.button(f"{i}. {event_name}", key=f"event_btn_{i}"):
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
