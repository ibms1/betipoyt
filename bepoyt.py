import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import numpy as np
from requests.exceptions import RequestException
import backoff

# Custom decorator for exponential backoff
@backoff.on_exception(
    backoff.expo,
    (RequestException, Exception),
    max_tries=5,
    max_time=30
)
def fetch_trends_with_retry(pytrends, keyword):
    """Fetch trends data with retry logic"""
    pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='', gprop='youtube')
    return pytrends.interest_over_time()

def get_best_time_for_keyword(keyword):
    """Fetch and analyze the best posting time for a given keyword with improved error handling."""
    try:
        if not keyword.strip():
            st.error("Please enter a valid keyword.")
            return None, None

        # Initialize session state for rate limiting
        if 'last_request_time' not in st.session_state:
            st.session_state.last_request_time = datetime.min

        # Rate limiting - ensure at least 1 second between requests
        time_since_last_request = datetime.now() - st.session_state.last_request_time
        if time_since_last_request.total_seconds() < 1:
            time.sleep(1 - time_since_last_request.total_seconds())

        # Set up Pytrends with increased timeout and custom headers
        pytrends = TrendReq(
            hl='en-US',
            tz=360,
            timeout=30,
            retries=3,
            backoff_factor=1.5,
            requests_args={
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            }
        )

        # Fetch data with retry logic
        with st.spinner('Fetching trend data...'):
            data = fetch_trends_with_retry(pytrends, keyword)
            st.session_state.last_request_time = datetime.now()

        if data is None or data.empty:
            st.warning(f"No trend data available for '{keyword}'. Try a more popular keyword or check your internet connection.")
            return None, None

        # Process data
        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]

        # Add smoothing to reduce noise
        hourly_interest = hourly_interest.rolling(window=3, center=True, min_periods=1).mean()

        # Determine the best hour
        best_hour = hourly_interest.idxmax()
        
        # Get confidence score based on data variance
        confidence_score = min(100, (1 - hourly_interest.std() / hourly_interest.mean()) * 100)
        
        return hourly_interest, best_hour, confidence_score

    except Exception as e:
        error_message = str(e)
        if "429" in error_message:
            st.error("Too many requests. Please wait a few minutes before trying again.")
        elif "method_whitelist" in error_message:
            st.error(" Please try again in a few moments.")
        else:
            st.error(f"Please try again in a few moments.")
        return None, None, None

def main():
    # Set up page configuration
    st.set_page_config(
        page_title="Best Time to Post on YouTube",
        layout="wide",
        initial_sidebar_state="collapsed"
    )

    # Custom CSS with error handling styles
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
            transition: all 0.3s ease;
        }
        .stButton > button:hover {
            background-color: #45a049;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }
        .error-message {
            background-color: #ffebee;
            border-left: 5px solid #f44336;
            padding: 1em;
            margin: 1em 0;
            border-radius: 4px;
        }
        .confidence-meter {
            margin-top: 1em;
            padding: 1em;
            background: #f5f5f5;
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    # App header
    st.markdown("<h1 class='main-title'>🎯 Best Time to Post on YouTube</h1>", unsafe_allow_html=True)
    st.markdown("<p class='description'>Find the optimal posting time for your YouTube content based on search trends.</p>", unsafe_allow_html=True)

    # Input section with better validation
    keyword = st.text_input("Enter your keyword:", help="Enter a topic or theme related to your video content")
    
    col1, col2, col3 = st.columns([1,1,1])
    with col2:
        analyze_button = st.button("Analyze")

    if analyze_button:
        with st.spinner('Analyzing trends...'):
            hourly_interest, best_hour, confidence_score = get_best_time_for_keyword(keyword)

            if hourly_interest is not None and best_hour is not None:
                # Display results
                st.markdown(f"### 🎉 Results for '{keyword}'")
                
                # Convert best hour to 12-hour format
                am_pm = "AM" if best_hour < 12 else "PM"
                display_hour = best_hour if best_hour <= 12 else best_hour - 12
                if display_hour == 0:
                    display_hour = 12
                
                st.markdown(f"#### Best posting time: {display_hour}:00 {am_pm}")
                
                if confidence_score:
                    st.markdown(f"Confidence Score: {confidence_score:.1f}%")
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