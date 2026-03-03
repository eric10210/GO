import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import requests
import numpy as np
from datetime import datetime

# --- Page Config ---
st.set_page_config(page_title="Crypto Watch & Signals", layout="wide", page_icon="📈")

# --- Custom CSS for Dark Mode & Cards ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #333;
    }
    .signal-buy { color: #00ff00; font-weight: bold; }
    .signal-sell { color: #ff0000; font-weight: bold; }
    .signal-neutral { color: #ffff00; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions (Technical Analysis) ---

def fetch_crypto_data(symbol, interval='1h', limit=200):
    """Fetches kline/candlestick data from Binance Public API"""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        'symbol': symbol,
        'interval': interval,
        'limit': limit
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
        ])
        
        # Convert types
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        cols = ['open', 'high', 'low', 'close', 'volume']
        df[cols] = df[cols].astype(float)
        
        return df.set_index('timestamp')
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

def calculate_sma(df, window):
    return df['close'].rolling(window=window).mean()

def calculate_ema(df, window):
    return df['close'].ewm(span=window, adjust=False).mean()

def calculate_rsi(df, window=14):
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def generate_signal(df):
    """Generates a trade signal based on RSI and Moving Averages"""
    if df.empty:
        return "Neutral", 0
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    rsi = last_row['RSI']
    price = last_row['close']
    sma_50 = last_row['SMA_50']
    ema_20 = last_row['EMA_20']
    
    signal = "Neutral"
    confidence = 50
    
    # Logic Implementation
    if rsi < 30 and price > sma_50:
        signal = "Strong Buy"
        confidence = 90
    elif rsi < 40 or (prev_row['close'] < prev_row['EMA_20'] and price > ema_20):
        signal = "Buy"
        confidence = 75
    elif rsi > 70 and price < sma_50:
        signal = "Strong Sell"
        confidence = 90
    elif rsi > 60 or (prev_row['close'] > prev_row['EMA_20'] and price < ema_20):
        signal = "Sell"
        confidence = 75
        
    return signal, confidence

# --- Sidebar ---
st.sidebar.title("⚙️ Settings")
symbol = st.sidebar.text_input("Trading Pair", "BTCUSDT").upper()
interval = st.sidebar.selectbox("Timeframe", ['15m', '1h', '4h', '1d'], index=1)
refresh = st.sidebar.button("🔄 Refresh Data")

st.sidebar.markdown("---")
st.sidebar.info("Data provided by Binance Public API")

# --- Main App ---
st.title(f"🚀 {symbol} Crypto Watch")

# Fetch Data
@st.cache_data(ttl=60) # Cache for 60 seconds
def get_data(sym, intv):
    return fetch_crypto_data(sym, intv)

if refresh:
    st.cache_data.clear()

df = get_data(symbol, interval)

if not df.empty:
    # Calculate Indicators
    df['SMA_50'] = calculate_sma(df, 50)
    df['EMA_20'] = calculate_ema(df, 20)
    df['RSI'] = calculate_rsi(df, 14)
    
    # Get Signal
    signal, confidence = generate_signal(df)
    
    # --- Top Metrics ---
    c1, c2, c3, c4 = st.columns(4)
    current_price = df['close'].iloc[-1]
    price_change = ((current_price - df['open'].iloc[0]) / df['open'].iloc[0]) * 100
    volume_24h = df['volume'].sum() # Approximate for the fetched limit
    
    # Color for price change
    delta_color = "normal" if price_change >= 0 else "inverse"
    
    c1.metric("Current Price", f"${current_price:,.2f}", f"{price_change:.2f}%", delta_color=delta_color)
    c2.metric("24h Volume (Base)", f"{volume_24h:,.0f}")
    c3.metric("RSI (14)", f"{df['RSI'].iloc[-1]:.2f}")
    
    # Signal Metric
    signal_color = "normal"
    if "Buy" in signal: signal_color = "normal" # Green in streamlit metrics is positive
    if "Sell" in signal: signal_color = "inverse" # Red in streamlit metrics is negative
    
    c4.metric("Signal", signal, f"{confidence}% Conf.", delta_color=signal_color)

    # --- Charts ---
    # Candlestick Chart
    fig_candle = go.Figure()
    fig_candle.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='Price'
    ))
    # Add SMA & EMA
    fig_candle.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='orange', width=1), name='SMA 50'))
    fig_candle.add_trace(go.Scatter(x=df.index, y=df['EMA_20'], line=dict(color='blue', width=1), name='EMA 20'))
    
    fig_candle.update_layout(height=400, margin=dict(l=10, r=10, t=10, b=10), xaxis_rangeslider_visible=False, template="plotly_dark")
    st.plotly_chart(fig_candle, use_container_width=True)

    # RSI Chart
    fig_rsi = go.Figure()
    fig_rsi.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'))
    fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="Overbought")
    fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="Oversold")
    fig_rsi.update_layout(height=200, margin=dict(l=10, r=10, t=10, b=10), showlegend=False, template="plotly_dark")
    st.plotly_chart(fig_rsi, use_container_width=True)

    # --- Trade Idea Box ---
    st.subheader("💡 Automated Trade Idea")
    col_txt, col_act = st.columns([3, 1])
    
    with col_txt:
        if "Buy" in signal:
            st.success(f"**Action:** Consider Long Position on {symbol}")
            st.write(f"**Reasoning:** RSI indicates oversold conditions ({df['RSI'].iloc[-1]:.1f}) and price action is supporting momentum.")
        elif "Sell" in signal:
            st.error(f"**Action:** Consider Short Position or Take Profit on {symbol}")
            st.write(f"**Reasoning:** RSI indicates overbought conditions ({df['RSI'].iloc[-1]:.1f}) and price is rejecting higher levels.")
        else:
            st.warning(f"**Action:** Hold / Wait for confirmation on {symbol}")
            st.write(f"**Reasoning:** Market is ranging. Wait for RSI breakout or MA cross.")
            
    with col_act:
        st.metric("Confidence", f"{confidence}%")

    # --- Recent Data Table ---
    with st.expander("📊 View Recent Candle Data"):
        st.dataframe(df[['open', 'high', 'low', 'close', 'volume', 'RSI']].tail(10).style.format("{:.2f}"))

else:
    st.warning("No data available. Please check the symbol (e.g., BTCUSDT, ETHUSDT).")

# --- Footer ---
st.markdown("---")
st.caption("Disclaimer: This app is for educational purposes only. Not financial advice.")