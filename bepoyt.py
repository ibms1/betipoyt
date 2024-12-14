import streamlit as st
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
from datetime import datetime
import time
import numpy as np

def get_best_time_for_keyword(keyword):
    """Fetch and analyze the best posting time for a given keyword."""
    try:
        if not keyword.strip():
            st.error("Please enter a valid keyword.")
            return None, None

        # Set up Pytrends
        pytrends = TrendReq(hl='en-US', tz=360, retries=2, backoff_factor=0.5, timeout=30)

        # Fetch data
        pytrends.build_payload([keyword], cat=0, timeframe='now 1-d', geo='', gprop='youtube')
        data = pytrends.interest_over_time()

        if data.empty:
            st.error(f"No data available for keyword: {keyword}. Please try another one.")
            return None, None

        # Process data
        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]

        # Determine the best hour
        best_hour = hourly_interest.idxmax()
        return hourly_interest, best_hour

    except Exception as e:
        st.error("An error occurred while processing the data. Please try again later.")
        st.error(f"Error details: {str(e)}")
        return None, None

def main():
    # Set up page configuration
    st.set_page_config(page_title="Best Time to Post on YouTube", layout="wide")

    # Custom CSS for styling
    st.markdown("""
        <style>
        .main-title {
            text-align: center;
            color: #333;
        }
        .description {
            text-align: center;
            color: #777;
            margin-bottom: 20px;
        }
        .stButton > button {
            display: block;
            margin: 0 auto;
            background-color: #4CAF50;
            color: white;
            font-size: 16px;
            padding: 10px;
            border-radius: 5px;
            width: 150px; /* Set the width of the button */
        }
        </style>
    """, unsafe_allow_html=True)

    # App title and description
    st.markdown("<h1 class='main-title'>🎯 Best Time to Post on YouTube</h1>", unsafe_allow_html=True)
    st.markdown("<p class='description'>Find the optimal posting time for your YouTube content based on search trends.</p>", unsafe_allow_html=True)

    # User input section
    keyword = st.text_input("Enter your keyword:")
    analyze_button = st.button("Analyze")

    if analyze_button:
        # Add delay to avoid rate limiting
        time.sleep(1)

        # Analyze keyword trends
        with st.spinner('Analyzing trends...'):
            hourly_interest, best_hour = get_best_time_for_keyword(keyword)

            if hourly_interest is not None and best_hour is not None:
                # Display best time
                st.markdown(f"<h3 style='text-align: center;'>🎉 The best time to post about '{keyword}' is at {best_hour}:00.</h3>", unsafe_allow_html=True)

                # Display chart and table
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Hourly Interest Levels")
                    fig = px.line(
                        x=hourly_interest.index,
                        y=hourly_interest.values,
                        title=f"Interest Over the Day for '{keyword}'",
                        labels={"x": "Hour", "y": "Interest Level"}
                    )
                    fig.update_layout(xaxis_title="Hour", yaxis_title="Interest Level", title_x=0.5)
                    st.plotly_chart(fig)

                with col2:
                    st.subheader("Interest Level Table")
                    table_data = pd.DataFrame({
                        "Hour": hourly_interest.index,
                        "Interest Level": np.round(hourly_interest.values, 2)
                    })
                    st.dataframe(table_data.style.highlight_max(subset=["Interest Level"], color="lightgreen"))



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