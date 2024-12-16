import streamlit as st 
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import numpy as np
import random
import backoff

# Page configuration
st.set_page_config(
    page_title="YouTube Best Posting Time",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .main-container {
        padding: 2rem;
    }
    .main-title {
        text-align: center;
        color: #1E88E5;
        font-size: 2.5rem;
        margin-bottom: 1rem;
        padding: 1rem;
    }
    .sub-title {
        text-align: center;
        color: #424242;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stButton > button {
        background-color: #1E88E5;
        color: white;
        padding: 0.5rem 2rem;
        font-size: 1.1rem;
        border-radius: 5px;
        border: none;
        margin: 0 auto;
        display: block;
    }
    .stButton > button:hover {
        background-color: #1976D2;
    }
    .metrics-container {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    div[data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #1E88E5;
    }
    /* Center the form */
    div[data-testid="stForm"] {
        max-width: 600px;
        margin: 0 auto;
    }
    </style>
""", unsafe_allow_html=True)

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def create_pytrends_session():
    """Create a PyTrends session with improved error handling"""
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ]
    
    session = TrendReq(
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
        }
    )
    return session

@st.cache_data(ttl=3600)
def get_best_time_for_keyword(keyword):
    """Fetch and analyze the best posting time with improved error handling"""
    try:
        if not keyword.strip():
            st.error("Please enter a valid keyword")
            return None, None, None

        time.sleep(random.uniform(2, 4))

        pytrends = create_pytrends_session()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                pytrends.build_payload(
                    [keyword], 
                    cat=0, 
                    timeframe='now 1-d', 
                    geo='', 
                    gprop='youtube'
                )
                data = pytrends.interest_over_time()
                
                if data is None or data.empty:
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(5, 8))
                        continue
                    st.warning(f"No data available for '{keyword}'. Try a different keyword.")
                    return None, None, None
                
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 8))
                    continue
                raise e

        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]
        
        hourly_interest = hourly_interest.rolling(
            window=3, 
            center=True, 
            min_periods=1
        ).mean()

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
            st.error(f"An error occurred: {str(e)}. Please try again later.")
        return None, None, None

def main():
    # App header
    st.markdown("<h1 class='main-title'>📊 YouTube Best Posting Time Analyzer</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Find the optimal time to post your YouTube content based on search trends</p>", unsafe_allow_html=True)

    # Center-aligned form
    with st.form("search_form"):
        keyword = st.text_input(
            "Enter your video topic or keyword:",
            help="Enter a topic related to your video content (e.g., 'cooking', 'gaming', 'tutorial')"
        )
        submitted = st.form_submit_button("Analyze Trends")

    if submitted:
        if not keyword.strip():
            st.error("Please enter a keyword to analyze")
            return

        with st.spinner('Analyzing trends... Please wait'):
            hourly_interest, best_hour, confidence_score = get_best_time_for_keyword(keyword)

            if hourly_interest is not None and best_hour is not None:
                # Results section
                st.markdown("---")
                st.markdown(f"### 📈 Analysis Results for '{keyword}'")
                
                # Convert to 12-hour format
                am_pm = "AM" if best_hour < 12 else "PM"
                display_hour = best_hour if best_hour <= 12 else best_hour - 12
                if display_hour == 0:
                    display_hour = 12

                # Metrics container
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    st.metric("Best Posting Time", f"{display_hour}:00 {am_pm}")
                
                with metrics_col2:
                    st.metric("Confidence Score", f"{confidence_score:.1f}%")

                # Visualization section
                st.markdown("### 📊 Trend Analysis")
                viz_col1, viz_col2 = st.columns(2)

                with viz_col1:
                    # Interest curve
                    fig = px.line(
                        x=hourly_interest.index,
                        y=hourly_interest.values,
                        title="24-Hour Interest Distribution",
                    )
                    fig.update_layout(
                        xaxis_title="Hour of Day",
                        yaxis_title="Interest Level",
                        showlegend=False,
                        title_x=0.5,
                        title_font_size=20,
                        plot_bgcolor='white'
                    )
                    fig.update_traces(line_color='#1E88E5')
                    st.plotly_chart(fig, use_container_width=True)

                with viz_col2:
                    # Hourly breakdown table
                    st.subheader("Hourly Breakdown")
                    table_data = pd.DataFrame({
                        "Hour": [f"{h:02d}:00" for h in hourly_interest.index],
                        "Interest Level": np.round(hourly_interest.values, 2)
                    })
                    st.dataframe(
                        table_data.style.highlight_max(
                            subset=["Interest Level"],
                            color="#E3F2FD"
                        ),
                        hide_index=True,
                        use_container_width=True
                    )

if __name__ == "__main__":
    main()

# Disable Streamlit links in footer
hide_links_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    a {text-decoration: none}
    </style>
"""
st.markdown(hide_links_style, unsafe_allow_html=True)