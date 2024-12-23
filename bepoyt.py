import streamlit as st
from googleapiclient.discovery import build
from datetime import datetime
from collections import Counter
from dotenv import load_dotenv
import os

# Load API key from .env file
load_dotenv()
API_KEY = os.getenv("YOUTUBE_API_KEY")

# Check if API_KEY is loaded
if not API_KEY:
    raise ValueError("YouTube API key not found. Please set it in the .env file.")

# Build YouTube API
youtube = build('youtube', 'v3', developerKey=API_KEY)

def search_channels_by_keyword(keyword, max_results=10):
    """
    Search for channels based on a keyword
    """
    request = youtube.search().list(
        part="snippet",
        q=keyword,
        type="channel",
        maxResults=max_results
    )
    response = request.execute()
    
    channels = []
    for item in response.get("items", []):
        channels.append({
            "channel_id": item["id"]["channelId"],
            "channel_title": item["snippet"]["title"]
        })
    return channels

def get_recent_videos(channel_id):
    """
    Get a list of the most recent videos published by a channel
    """
    request = youtube.search().list(
        part="snippet",
        channelId=channel_id,
        maxResults=50,
        order="date"
    )
    response = request.execute()
    
    videos = []
    for item in response.get("items", []):
        if item["id"]["kind"] == "youtube#video":
            videos.append({
                "video_id": item["id"]["videoId"],
                "published_at": item["snippet"]["publishedAt"]
            })
    return videos

def analyze_best_time(videos):
    """
    Analyze the best time based on the timing of previously uploaded videos
    """
    times = [datetime.fromisoformat(video["published_at"].replace("Z", "+00:00")) for video in videos]
    hours = [time.hour for time in times]
    return hours

# Streamlit interface
st.markdown(
    """
    <style>
    .center-button {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 20px;
    }
    .blue-button {
        background-color: #007BFF !important;
        color: white !important;
        border-radius: 8px !important;
        padding: 10px 20px !important;
        border: none !important;
    }
    .bold-text {
        font-weight: bold;
        color: #000;
        font-size: 18px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.title("Best Time to Publish Videos on YouTube")
st.write("This app helps you find the best time to publish videos on YouTube for a specific niche.")

keyword = st.text_input("Enter a niche keyword:")
button_placeholder = st.empty()

with button_placeholder.container():
    button_clicked = st.markdown(
        """
        <div class="center-button">
            <button class="blue-button" onclick="window.location.reload();">
                Analyze
            </button>
        </div>
        """,
        unsafe_allow_html=True
    )

if st.button("Analyze"):
    if not keyword.strip():
        st.error("Please enter a valid keyword.")
    else:
        try:
            # Search for channels
            channels = search_channels_by_keyword(keyword, max_results=5)
            all_hours = []

            for channel in channels:
                videos = get_recent_videos(channel["channel_id"])
                all_hours.extend(analyze_best_time(videos))

            # Analyze most common hours
            hour_counter = Counter(all_hours)
            best_hour = hour_counter.most_common(1)[0][0]

            # Display the result
            st.markdown(
                f"<p class='bold-text'>The best time to publish videos for this niche is: {best_hour}:00 UTC.</p>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"Please Try in Few Moment")

hide_links_style = """
        <style>
        a {
            pointer-events: none;
            cursor: default;
            text-decoration: none;
            color: inherit;
        }
        </style>
        """
st.markdown(hide_links_style, unsafe_allow_html=True)