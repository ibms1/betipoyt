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
    .title {
        text-align: center;
        font-size: 36px;
        color: #D50000;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .subtitle {
        text-align: center;
        font-size: 18px;
        color: #777;
        margin-bottom: 30px;
    }
    .text-input {
        margin: 0 auto;
        display: block;
        width: 80%;
        height: 40px;
        padding: 10px;
        border-radius: 5px;
        border: 1px solid #ddd;
    }
    .button-container {
        display: flex;
        justify-content: center;
        margin-top: 20px;
    }
    .button {
        background-color: #D50000;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .button:hover {
        background-color: #FF5252;
    }
    .result {
        text-align: center;
        font-size: 24px;
        color: #333;
        font-weight: bold;
        margin-top: 20px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Header
st.markdown("<div class='title'>YouTube Best Time Analyzer</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Find the best time to publish your YouTube videos based on your niche</div>", unsafe_allow_html=True)

# Input
keyword = st.text_input("Enter your niche keyword (e.g., cooking, gaming, fitness):", key="keyword")

# Button
if st.markdown(
    """
    <div class='button-container'>
        <button class='button' onclick="window.location.reload();">Analyze Timing</button>
    </div>
    """,
    unsafe_allow_html=True
):
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
            st.markdown(f"<div class='result'>The best time to publish videos for this niche is: {best_hour}:00 UTC.</div>", unsafe_allow_html=True)
        except Exception as e:
            st.error(f"An error occurred: {e}")

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