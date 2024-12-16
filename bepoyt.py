import streamlit as st 
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import numpy as np
from requests.exceptions import RequestException
import random

def create_pytrends_session():
    """Create a PyTrends session with optimized settings for Streamlit Cloud"""
    # List of different user agents to rotate
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    # Try to create a session with different settings
    try:
        return TrendReq(
            hl='en-US',
            tz=360,
            timeout=30,
            retries=5,
            backoff_factor=2,
            requests_args={
                'headers': {
                    'User-Agent': random.choice(user_agents)
                },
                'verify': True,
                'proxies': None  # Let requests handle proxy automatically
            }
        )
    except Exception as e:
        st.error(f"Failed to create session: {str(e)}")
        return None

@st.cache_data(ttl=3600)  # Cache data for 1 hour
def get_best_time_for_keyword(keyword):
    """Fetch and analyze the best posting time for a given keyword."""
    try:
        if not keyword.strip():
            st.error("Please enter a valid keyword.")
            return None, None, None

        # Add delay between requests
        time.sleep(2)

        # Create new session
        pytrends = create_pytrends_session()
        if pytrends is None:
            return None, None, None

        # Fetch data with multiple retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='', gprop='youtube')
                data = pytrends.interest_over_time()
                
                if data is None or data.empty:
                    if attempt < max_retries - 1:
                        time.sleep(5)  # Wait before retry
                        continue
                    st.warning(f"No data available for '{keyword}'. Try a different keyword.")
                    return None, None, None
                
                break  # Success - exit retry loop
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5)  # Wait before retry
                    continue
                raise e

        # Process data
        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]

        # Smooth the data
        hourly_interest = hourly_interest.rolling(window=3, center=True, min_periods=1).mean()

        # Find best hour and calculate confidence
        best_hour = hourly_interest.idxmax()
        confidence_score = min(100, (1 - hourly_interest.std() / hourly_interest.mean()) * 100)
        
        return hourly_interest, best_hour, confidence_score

    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg:
            st.error("Too many requests. Please wait a few minutes before trying again.")
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            st.error("Temporary API access issue. Please try again in a few moments.")
        else:
            st.error(f"An error occurred. Please try again later.")
        return None, None, None

def main():
    st.set_page_config(
        page_title="Best Time to Post on YouTube",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS
    st.markdown("""
        <style>
        .main-title {
            text-align: center;
            color: #333;
            padding: 1em 0;
        }
        .description {
            text-align: center;
            color: #777;
            margin-bottom: 2em;
        }
        .stButton > button {
            display: block;
            margin: 0 auto;
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px 20px;
            border-radius: 5px;
            width: 150px;
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px;
            color: #4CAF50;
        }
        </style>
    """, unsafe_allow_html=True)

    # App header
    st.markdown("<h1 class='main-title'>🎯 Best Time to Post on YouTube</h1>", unsafe_allow_html=True)
    st.markdown("<p class='description'>Find the optimal posting time for your YouTube content based on search trends.</p>", unsafe_allow_html=True)

    # Input section
    with st.form("search_form"):
        keyword = st.text_input("Enter your keyword:", 
                              help="Enter a topic or theme related to your video content")
        submitted = st.form_submit_button("Analyze")

    if submitted:
        with st.spinner('Analyzing trends...'):
            hourly_interest, best_hour, confidence_score = get_best_time_for_keyword(keyword)

            if hourly_interest is not None and best_hour is not None:
                # Display results
                st.markdown(f"### 🎉 Results for '{keyword}'")
                
                # Convert to 12-hour format
                am_pm = "AM" if best_hour < 12 else "PM"
                display_hour = best_hour if best_hour <= 12 else best_hour - 12
                if display_hour == 0:
                    display_hour = 12
                
                st.markdown(f"#### Best posting time: {display_hour}:00 {am_pm}")
                
                if confidence_score:
                    st.metric("Confidence Score", f"{confidence_score:.1f}%")
                    st.progress(confidence_score/100)

                # Display visualization and data
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Hourly Interest Levels")
                    fig = px.line(
                        x=hourly_interest.index,
                        y=hourly_interest.values,
                        labels={"x": "Hour", "y": "Interest Level"},
                        title="Interest Over 24 Hours"
                    )
                    fig.update_layout(
                        xaxis_title="Hour of Day",
                        yaxis_title="Interest Level",
                        title_x=0.5,
                        showlegend=False
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    st.subheader("Hourly Breakdown")
                    table_data = pd.DataFrame({
                        "Hour": [f"{h:02d}:00" for h in hourly_interest.index],
                        "Interest Level": np.round(hourly_interest.values, 2)
                    })
                    st.dataframe(
                        table_data.style.highlight_max(
                            subset=["Interest Level"],
                            color="lightgreen"
                        ),
                        hide_index=True
                    )

if __name__ == "__main__":
    main()


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