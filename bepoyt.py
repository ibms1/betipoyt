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
st.title("Best Time to Publish Videos on YouTube")
st.write("This app helps you find the best time to publish videos on YouTube for a specific niche.")

keyword = st.text_input("Enter a niche keyword (e.g., travel vlogs):")
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
            st.success(f"The best time to publish videos for this niche is: {best_hour}:00 UTC.")
        except Exception as e:
            st.error(f"An error occurred: {e}")
