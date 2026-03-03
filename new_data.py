import requests
import pandas as pd
import streamlit as st
import os
from datetime import datetime, timedelta
from src.utils.logger import get_logger
from src.utils.config_loader import load_config
from .cache_manager import CACHE_TTL_SLOW

logger = get_logger("news_data")
config = load_config()

# Try to load API key from .env
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

@st.cache_data(ttl=CACHE_TTL_SLOW)
def get_crypto_news(limit: int = 5) -> pd.DataFrame:
    """
    Fetches crypto news from CryptoPanic API.
    Falls back to mock data if API key is missing or request fails.
    """
    
    # 1. Try Real API
    if NEWS_API_KEY:
        try:
            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                'auth_token': NEWS_API_KEY,
                'filter': 'hot',
                'limit': limit
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for post in data['results']:
                results.append({
                    'title': post['title'],
                    'source': post['source']['title'],
                    'published_at': post['published_at'],
                    'url': post['url'],
                    'sentiment': 'neutral' # Placeholder, actual sentiment calculated in analysis layer
                })
            return pd.DataFrame(results)
        
        except Exception as e:
            logger.warning(f"News API failed, switching to mock data: {e}")
    
    # 2. Fallback Mock Data (For Development/No Key)
    logger.info("Using mock news data")
    mock_data = []
    headlines = [
        "Bitcoin Surges Past Resistance Level",
        "Ethereum Upgrade Scheduled for Next Month",
        "Regulatory Concerns Impact Market Sentiment",
        "Major Exchange Reports Record Volume",
        "DeFi Protocol Launches New Yield Farming"
    ]
    
    now = datetime.now()
    for i, title in enumerate(headlines[:limit]):
        mock_data.append({
            'title': title,
            'source': 'CryptoDaily (Mock)',
            'published_at': (now - timedelta(hours=i)).isoformat(),
            'url': '#',
            'sentiment': 'neutral'
        })
        
    return pd.DataFrame(mock_data)