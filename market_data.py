import requests
import pandas as pd
import streamlit as st
from src.utils.logger import get_logger
from src.utils.config_loader import load_config
from .cache_manager import CACHE_TTL_NORMAL, CACHE_TTL_FAST

logger = get_logger("market_data")
config = load_config()

BINANCE_BASE_URL = "https://api.binance.com/api/v3"

@st.cache_data(ttl=CACHE_TTL_FAST)
def get_ticker_price(symbol: str) -> float:
    """
    Fetches the current price of a symbol.
    """
    try:
        response = requests.get(f"{BINANCE_BASE_URL}/ticker/price", params={"symbol": symbol})
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
    except Exception as e:
        logger.error(f"Error fetching price for {symbol}: {e}")
        return 0.0

@st.cache_data(ttl=CACHE_TTL_NORMAL)
def get_klines(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    """
    Fetches candlestick data (OHLCV) from Binance.
    Returns a cleaned Pandas DataFrame.
    """
    try:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        response = requests.get(f"{BINANCE_BASE_URL}/klines", params=params)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logger.warning(f"No data returned for {symbol}")
            return pd.DataFrame()

        # Create DataFrame
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
        ])
        
        # Data Cleaning
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        
        # Set index
        df.set_index('timestamp', inplace=True)
        
        logger.info(f"Successfully fetched {len(df)} candles for {symbol}")
        return df
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {symbol}: {e}")
        st.error(f"Failed to fetch market data: {e}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error processing data for {symbol}: {e}")
        return pd.DataFrame()