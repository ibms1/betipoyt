import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
from datetime import datetime
import pytz
import time
import numpy as np

# Page configuration must be the first Streamlit command
st.set_page_config(layout="wide")

def get_best_time_for_keyword(keyword):
    try:
        # Setup pytrends
        pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5, timeout=30)

        # Set keyword and timeframe
        kw_list = [keyword]
        pytrends.build_payload(kw_list, cat=0, timeframe='now 1-d', geo='', gprop='youtube')

        # Get search data
        data = pytrends.interest_over_time()

        if data.empty:
            st.error(f"No data found for keyword: {keyword}. Please try again later.")
            return None, None

        # Clean and analyze data
        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]

        # Find best time
        best_hour = hourly_interest.idxmax()
        
        return hourly_interest, best_hour

    except Exception as e:
        st.error("An error occurred. Please try again later.")
        return None, None

def main():
    # Custom CSS
    st.markdown("""
        <style>
        .main {
            padding: 2rem;
        }
        .stButton > button {
            display: block;
            margin: 0 auto;
            background-color: #FF4B4B;
            color: white;
            padding: 0.5rem 2rem;
        }
        .title {
            text-align: center;
            margin-bottom: 2rem;
        }
        .subtitle {
            text-align: center;
            margin-bottom: 2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # Title and description
    st.markdown("<h1 class='title'>🎯 Best Time to Post on YouTube</h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>This tool helps you find the optimal posting time on YouTube based on search trends analysis</p>", unsafe_allow_html=True)

    # Center the input field
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        keyword = st.text_input("Enter your keyword:")
        analyze_button = st.button("Analyze")

    if analyze_button:
        # Add delay to prevent rate limiting
        time.sleep(1)
        
        with st.spinner('Analyzing data...'):
            hourly_interest, best_hour = get_best_time_for_keyword(keyword)

            if hourly_interest is not None and best_hour is not None:
                # Show results
                st.markdown(f"<h3 style='text-align: center'>🎉 Best time to post content about '{keyword}' is at {best_hour}:00</h3>", unsafe_allow_html=True)

                # Create columns for chart and table
                col1, col2 = st.columns(2)

                with col1:
                    # Create graph
                    fig = px.line(
                        x=hourly_interest.index,
                        y=hourly_interest.values,
                        title=f"Search Activity Throughout the Day for '{keyword}'",
                        labels={'x': 'Hour', 'y': 'Interest Level'}
                    )
                    fig.update_layout(
                        xaxis_title="Hour",
                        yaxis_title="Interest Level",
                        hovermode='x',
                        title_x=0.5
                    )
                    st.plotly_chart(fig)

                with col2:
                    # Display data in table
                    st.subheader("Hourly Activity Details:")
                    df_display = pd.DataFrame({
                        'Hour': hourly_interest.index,
                        'Interest Level': np.round(hourly_interest.values, 2)  # Using numpy's round function
                    })
                    st.table(df_display.style.highlight_max(subset=['Interest Level']))

    # Hide links
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

if __name__ == "__main__":
    main()
