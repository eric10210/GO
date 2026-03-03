import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.subplots as sp
import requests
from datetime import datetime, timedelta
import time

# ==============================================================================
# 1. CONFIGURATION & CONSTANTS
# ==============================================================================

APP_TITLE = "🚀 Crypto Watch Pro"
APP_ICON = "📈"
DEFAULT_SYMBOL = "BTCUSDT"
DEFAULT_TIMEFRAME = "1h"
DEFAULT_LIMIT = 200

# Indicator Settings
RSI_PERIOD = 14
SMA_SHORT = 20
SMA_LONG = 50
EMA_PERIOD = 20
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD = 2.0

# Signal Thresholds
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30

# Watchlist
WATCHLIST = ["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT"]

# Binance API Base URL (Public)
BINANCE_BASE_URL = "https://api.binance.com/api/v3"

# ==============================================================================
# 2. HELPER FUNCTIONS & LOGGING
# ==============================================================================

def log_error(message):
    """Simple error logger that prints to console and shows in Streamlit."""
    print(f"[ERROR] {datetime.now()} - {message}")
    # We rely on st.error for UI feedback

def format_currency(value):
    """Formats number as USD currency."""
    return f"${value:,.2f}"

def format_number(value):
    """Formats number with commas."""
    return f"{value:,.0f}"

# ==============================================================================
# 3. DATA FETCHING LAYER (Binance Public API)
# ==============================================================================

@st.cache_data(ttl=60)
def get_klines(symbol, interval, limit):
    """
    Fetches candlestick data from Binance Public API.
    No API key required.
    """
    try:
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        response = requests.get(f"{BINANCE_BASE_URL}/klines", params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            return pd.DataFrame()
        
        df = pd.DataFrame(data, columns=[
            'timestamp', 'open', 'high', 'low', 'close', 'volume',
            'close_time', 'quote_av', 'trades', 'tb_base_av', 'tb_quote_av', 'ignore'
        ])
        
        # Process Data
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        numeric_cols = ['open', 'high', 'low', 'close', 'volume']
        df[numeric_cols] = df[numeric_cols].astype(float)
        df.set_index('timestamp', inplace=True)
        
        return df
    except requests.exceptions.RequestException as e:
        log_error(f"Request failed for {symbol}: {e}")
        return pd.DataFrame()
    except Exception as e:
        log_error(f"Unexpected error fetching {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=10)
def get_ticker_price(symbol):
    """
    Fetches current price from Binance.
    """
    try:
        response = requests.get(f"{BINANCE_BASE_URL}/ticker/price", params={"symbol": symbol}, timeout=5)
        response.raise_for_status()
        data = response.json()
        return float(data['price'])
    except Exception as e:
        log_error(f"Price fetch failed for {symbol}: {e}")
        return 0.0

# ==============================================================================
# 4. TECHNICAL ANALYSIS LAYER
# ==============================================================================

def calculate_rsi(series, period):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calculate_sma(series, period):
    return series.rolling(window=period).mean()

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def calculate_macd(df):
    ema_fast = calculate_ema(df['close'], MACD_FAST)
    ema_slow = calculate_ema(df['close'], MACD_SLOW)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, MACD_SIGNAL)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram

def calculate_bollinger_bands(df):
    sma = calculate_sma(df['close'], BB_PERIOD)
    std = df['close'].rolling(window=BB_PERIOD).std()
    upper = sma + (std * BB_STD)
    lower = sma - (std * BB_STD)
    return upper, sma, lower

def add_indicators(df):
    """
    Adds all technical indicators to the DataFrame.
    Handles errors gracefully if data is insufficient.
    """
    if df.empty or len(df) < SMA_LONG:
        return df
    
    try:
        df['RSI'] = calculate_rsi(df['close'], RSI_PERIOD)
        df['SMA_20'] = calculate_sma(df['close'], SMA_SHORT)
        df['SMA_50'] = calculate_sma(df['close'], SMA_LONG)
        df['EMA_20'] = calculate_ema(df['close'], EMA_PERIOD)
        
        macd, signal, hist = calculate_macd(df)
        df['MACD'] = macd
        df['MACD_Signal'] = signal
        df['MACD_Hist'] = hist
        
        bb_upper, bb_mid, bb_lower = calculate_bollinger_bands(df)
        df['BB_Upper'] = bb_upper
        df['BB_Lower'] = bb_lower
        
        # Drop NaN values generated by rolling windows
        df.dropna(inplace=True)
        return df
    except Exception as e:
        log_error(f"Indicator calculation failed: {e}")
        return df

# ==============================================================================
# 5. SIGNAL ENGINE
# ==============================================================================

def generate_signal(df):
    """
    Generates a trade signal based on the latest candle data.
    """
    if df.empty:
        return {"signal": "NEUTRAL", "confidence": 0, "reasons": ["No data"]}
    
    try:
        last = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else last
        
        signal = "NEUTRAL"
        strength = 0
        reasons = []
        
        # 1. RSI Logic
        if pd.notna(last['RSI']):
            if last['RSI'] < RSI_OVERSOLD:
                reasons.append(f"RSI Oversold ({last['RSI']:.2f})")
                strength += 30
            elif last['RSI'] > RSI_OVERBOUGHT:
                reasons.append(f"RSI Overbought ({last['RSI']:.2f})")
                strength -= 30
        
        # 2. MA Crossover
        if pd.notna(last['EMA_20']) and pd.notna(last['SMA_50']):
            if last['EMA_20'] > last['SMA_50'] and prev['EMA_20'] <= prev['SMA_50']:
                reasons.append("EMA crossed above SMA (Bullish)")
                strength += 40
            elif last['EMA_20'] < last['SMA_50'] and prev['EMA_20'] >= prev['SMA_50']:
                reasons.append("EMA crossed below SMA (Bearish)")
                strength -= 40
        
        # 3. MACD
        if pd.notna(last['MACD']) and pd.notna(last['MACD_Signal']):
            if last['MACD'] > last['MACD_Signal'] and prev['MACD'] <= prev['MACD_Signal']:
                reasons.append("MACD Bullish Crossover")
                strength += 30
            elif last['MACD'] < last['MACD_Signal'] and prev['MACD'] >= prev['MACD_Signal']:
                reasons.append("MACD Bearish Crossover")
                strength -= 30
        
        # 4. Trend
        if pd.notna(last['SMA_50']):
            if last['close'] > last['SMA_50']:
                strength += 10
            else:
                strength -= 10
        
        # Determine Final Signal
        if strength >= 50:
            signal = "STRONG BUY"
        elif strength >= 20:
            signal = "BUY"
        elif strength <= -50:
            signal = "STRONG SELL"
        elif strength <= -20:
            signal = "SELL"
        
        confidence = min(abs(strength), 100)
        
        return {
            "signal": signal,
            "confidence": confidence,
            "reasons": reasons if reasons else ["No strong signals detected"],
            "rsi": last['RSI'] if pd.notna(last['RSI']) else 0
        }
    except Exception as e:
        log_error(f"Signal generation failed: {e}")
        return {"signal": "ERROR", "confidence": 0, "reasons": [str(e)]}

# ==============================================================================
# 6. UI COMPONENTS
# ==============================================================================

def render_css():
    """Injects custom CSS for styling."""
    st.markdown("""
    <style>
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Metric Cards */
    div[data-testid="stMetricValue"] { font-size: 24px; font-weight: bold; }
    
    /* Signal Colors */
    .signal-buy { color: #00FF00; }
    .signal-sell { color: #FF0000; }
    .signal-neutral { color: #FFFF00; }
    
    /* Chart Containers */
    div.stPlotlyChart { border: 1px solid #333; border-radius: 10px; padding: 10px; background-color: #0e1117; }
    
    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #0e0e0e; }
    </style>
    """, unsafe_allow_html=True)

def create_main_chart(df, symbol):
    """Creates the main candlestick chart with indicators."""
    if df.empty:
        return go.Figure()
    
    fig = sp.make_subplots(rows=4, cols=1, shared_xaxes=True, 
                           vertical_spacing=0.02, 
                           row_heights=[0.5, 0.15, 0.15, 0.2],
                           subplot_titles=(f"{symbol} Price", "Volume", "RSI", "MACD"))
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'], low=df['low'], close=df['close'],
        name='Price', increasing_line_color='#00FF00', decreasing_line_color='#FF0000'
    ), row=1, col=1)
    
    # Moving Averages
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], line=dict(color='#FFA500', width=1), name='SMA 20'), row=1, col=1)
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], line=dict(color='#00BFFF', width=1), name='SMA 50'), row=1, col=1)
    
    # Volume
    colors = ['#00FF00' if df['close'].iloc[i] >= df['open'].iloc[i] else '#FF0000' for i in range(len(df))]
    fig.add_trace(go.Bar(x=df.index, y=df['volume'], marker_color=colors, name='Volume'), row=2, col=1)
    
    # RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='#9370DB', width=2), name='RSI'), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#FF0000", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00FF00", row=3, col=1)
    
    # MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='#00BFFF', width=2), name='MACD'), row=4, col=1)
        fig.add_trace(go.Scatter(x=df.index, y=df['MACD_Signal'], line=dict(color='#FFA500', width=2), name='Signal'), row=4, col=1)
        # Histogram
        hist_colors = ['#00FF00' if val > 0 else '#FF0000' for val in df['MACD_Hist']]
        fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=hist_colors, name='Hist', opacity=0.5), row=4, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        height=800,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=30, b=10)
    )
    return fig

def render_signal_card(signal_data):
    """Renders the signal badge."""
    signal = signal_data.get('signal', 'NEUTRAL')
    confidence = signal_data.get('confidence', 0)
    reasons = signal_data.get('reasons', [])
    
    color = "#FFFF00"
    bg = "rgba(255, 255, 0, 0.1)"
    if "BUY" in signal:
        color = "#00FF00"
        bg = "rgba(0, 255, 0, 0.1)"
    elif "SELL" in signal:
        color = "#FF0000"
        bg = "rgba(255, 0, 0, 0.1)"
        
    st.markdown(f"""
    <div style="background-color: {bg}; border: 2px solid {color}; border-radius: 10px; padding: 20px;">
        <h2 style="color: {color}; margin: 0;">🎯 {signal}</h2>
        <p style="color: white; margin: 5px 0;">Confidence: <strong>{confidence}%</strong></p>
        <hr style="border-color: {color}; opacity: 0.3;">
        <ul style="color: #CCCCCC; font-size: 14px;">
            {''.join([f'<li>{r}</li>' for r in reasons])}
        </ul>
    </div>
    """, unsafe_allow_html=True)

# ==============================================================================
# 7. PORTFOLIO MANAGEMENT (Session State)
# ==============================================================================

def init_portfolio():
    if 'portfolio' not in st.session_state:
        st.session_state['portfolio'] = pd.DataFrame(columns=['symbol', 'amount', 'avg_price', 'current_price', 'pnl'])

def add_to_portfolio(symbol, amount, price):
    df = st.session_state['portfolio']
    if symbol in df['symbol'].values:
        idx = df[df['symbol'] == symbol].index[0]
        old_amt = df.loc[idx, 'amount']
        old_price = df.loc[idx, 'avg_price']
        new_amt = old_amt + amount
        new_avg = ((old_amt * old_price) + (amount * price)) / new_amt
        df.loc[idx, 'amount'] = new_amt
        df.loc[idx, 'avg_price'] = new_avg
    else:
        new_row = pd.DataFrame([{
            'symbol': symbol, 'amount': amount, 'avg_price': price, 
            'current_price': price, 'pnl': 0.0
        }])
        st.session_state['portfolio'] = pd.concat([df, new_row], ignore_index=True)
    
    st.success(f"Added {amount} {symbol} to portfolio")

def update_portfolio_prices():
    df = st.session_state['portfolio']
    if df.empty:
        return df
    
    for index, row in df.iterrows():
        price = get_ticker_price(row['symbol'])
        if price > 0:
            df.loc[index, 'current_price'] = price
            df.loc[index, 'pnl'] = (price - row['avg_price']) * row['amount']
    
    st.session_state['portfolio'] = df
    return df

# ==============================================================================
# 8. MAIN APP LOGIC
# ==============================================================================

def main():
    # Page Config
    st.set_page_config(page_title=APP_TITLE, page_icon=APP_ICON, layout="wide")
    render_css()
    init_portfolio()
    
    # Sidebar
    st.sidebar.title("⚙️ Settings")
    symbol = st.sidebar.text_input("Trading Pair", value=DEFAULT_SYMBOL).upper()
    timeframe = st.sidebar.selectbox("Timeframe", ['15m', '1h', '4h', '1d'], index=1)
    limit = st.sidebar.slider("Candle Limit", 50, 500, DEFAULT_LIMIT)
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["📊 Dashboard", "👁️ Watchlist", "💼 Portfolio"], index=0)
    
    st.sidebar.caption("Data: Binance Public API")
    st.sidebar.caption("v1.0.0 | No API Keys Required")
    
    # Main Content
    if page == "📊 Dashboard":
        st.title(f"{APP_TITLE} - {symbol}")
        
        # Fetch Data
        with st.spinner(f"Fetching {symbol} data..."):
            df = get_klines(symbol, timeframe, limit)
        
        if df.empty:
            st.error(f"Failed to fetch data for {symbol}. Check symbol name or internet connection.")
            st.stop()
        
        # Analyze
        df_ind = add_indicators(df)
        signal_data = generate_signal(df_ind)
        current_price = get_ticker_price(symbol)
        
        # Metrics
        prev_close = df_ind['close'].iloc[-2] if len(df_ind) > 1 else df_ind['close'].iloc[-1]
        change = ((current_price - prev_close) / prev_close) * 100 if prev_close else 0
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price", format_currency(current_price), f"{change:.2f}%", delta_color="normal" if change >=0 else "inverse")
        c2.metric("RSI", f"{signal_data['rsi']:.2f}")
        c3.metric("Volume", format_number(df_ind['volume'].sum()))
        c4.metric("Signal", signal_data['signal'])
        
        st.markdown("---")
        
        # Charts & Signal
        col_chart, col_sig = st.columns([2, 1])
        with col_chart:
            fig = create_main_chart(df_ind, symbol)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_sig:
            render_signal_card(signal_data)
            
            # Quick Add to Portfolio
            st.markdown("### 💼 Quick Add")
            with st.form("quick_add"):
                amt = st.number_input("Amount", min_value=0.0, step=0.0001)
                submitted = st.form_submit_button("Add to Portfolio")
                if submitted and amt > 0:
                    add_to_portfolio(symbol, amt, current_price)
    
    elif page == "👁️ Watchlist":
        st.title("👁️ Market Watchlist")
        st.write("Scanning configured coins for signals...")
        
        data = []
        progress = st.progress(0)
        
        for i, sym in enumerate(WATCHLIST):
            try:
                df = get_klines(sym, '1h', 50)
                if not df.empty:
                    df_ind = add_indicators(df)
                    sig = generate_signal(df_ind)
                    price = get_ticker_price(sym)
                    data.append({
                        "Symbol": sym,
                        "Price": price,
                        "RSI": sig['rsi'],
                        "Signal": sig['signal'],
                        "Confidence": sig['confidence']
                    })
            except Exception:
                continue
            progress.progress((i + 1) / len(WATCHLIST))
        
        if data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)
        else:
            st.warning("No data available for watchlist.")
            
    elif page == "💼 Portfolio":
        st.title("💼 Portfolio Tracker")
        st.info("Portfolio data is stored in session memory and resets when the app closes.")
        
        # Add Manual Holding
        with st.expander("➕ Add Manual Holding"):
            with st.form("add_hold"):
                c1, c2, c3 = st.columns(3)
                p_sym = c1.text_input("Symbol", value="BTCUSDT")
                p_amt = c2.number_input("Amount", min_value=0.0)
                p_price = c3.number_input("Buy Price", min_value=0.0)
                if st.form_submit_button("Add"):
                    add_to_portfolio(p_sym, p_amt, p_price)
                    st.rerun()
        
        # Display
        df_port = update_portfolio_prices()
        if not df_port.empty:
            # Formatting
            display_df = df_port.copy()
            display_df['Value'] = display_df['amount'] * display_df['current_price']
            display_df['PnL %'] = ((display_df['current_price'] - display_df['avg_price']) / display_df['avg_price']) * 100
            
            st.dataframe(display_df.style.format({
                'current_price': '${:.2f}', 'avg_price': '${:.2f}', 
                'Value': '${:.2f}', 'pnl': '${:.2f}', 'PnL %': '{:.2f}%'
            }).applymap(lambda v: 'color: #00FF00' if v > 0 else 'color: #FF0000', subset=['pnl', 'PnL %']), 
            use_container_width=True)
            
            # Totals
            total_val = display_df['Value'].sum()
            total_pnl = display_df['pnl'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Total Value", format_currency(total_val))
            c2.metric("Total PnL", format_currency(total_pnl), delta_color="normal" if total_pnl >=0 else "inverse")
            
            if st.button("🗑️ Clear Portfolio"):
                st.session_state['portfolio'] = pd.DataFrame(columns=['symbol', 'amount', 'avg_price', 'current_price', 'pnl'])
                st.rerun()
        else:
            st.write("No holdings yet.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Critical Application Error: {e}")
        log_error(f"Critical Crash: {e}")