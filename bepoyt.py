import streamlit as st 
from pytrends.request import TrendReq
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
import numpy as np
import random
import backoff

@backoff.on_exception(backoff.expo, Exception, max_tries=5)
def create_pytrends_session():
    """Create a PyTrends session with improved error handling and backoff"""
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

def get_cached_data(keyword):
    """Get data from cache or fetch new data"""
    cache_key = f"trends_{keyword}_{datetime.now().strftime('%Y%m%d')}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]
    return None

def save_to_cache(keyword, data):
    """Save data to cache"""
    cache_key = f"trends_{keyword}_{datetime.now().strftime('%Y%m%d')}"
    st.session_state[cache_key] = data

@st.cache_data(ttl=3600)
def get_best_time_for_keyword(keyword):
    """Fetch and analyze the best posting time with improved error handling"""
    try:
        if not keyword.strip():
            st.error("الرجاء إدخال كلمة مفتاحية صالحة")
            return None, None, None

        # Check cache first
        cached_data = get_cached_data(keyword)
        if cached_data:
            return cached_data

        # Add delay between requests
        time.sleep(random.uniform(2, 4))

        pytrends = create_pytrends_session()
        
        # Fetch data with multiple retries
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
                    st.warning(f"لا توجد بيانات متاحة للكلمة '{keyword}'. جرب كلمة مفتاحية أخرى.")
                    return None, None, None
                
                break
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(5, 8))
                    continue
                raise e

        # Process data
        data = data.reset_index()
        data['hour'] = data['date'].dt.hour
        hourly_interest = data.groupby('hour').mean()[keyword]
        
        # Smooth the data
        hourly_interest = hourly_interest.rolling(
            window=3, 
            center=True, 
            min_periods=1
        ).mean()

        best_hour = hourly_interest.idxmax()
        confidence_score = min(100, (1 - hourly_interest.std() / hourly_interest.mean()) * 100)
        
        result = (hourly_interest, best_hour, confidence_score)
        save_to_cache(keyword, result)
        return result

    except Exception as e:
        error_msg = str(e).lower()
        if "429" in error_msg:
            st.error("عدد كبير من الطلبات. الرجاء الانتظار بضع دقائق قبل المحاولة مرة أخرى.")
        elif "authentication" in error_msg or "unauthorized" in error_msg:
            st.error("مشكلة مؤقتة في الوصول إلى API. الرجاء المحاولة مرة أخرى بعد قليل.")
        else:
            st.error(f"حدث خطأ: {str(e)}. الرجاء المحاولة مرة أخرى لاحقاً.")
        return None, None, None
    
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