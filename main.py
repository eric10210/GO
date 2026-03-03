import streamlit as st
import pandas as pd
import time
from src.utils.config_loader import load_config
from src.utils.logger import get_logger
from src.data import get_klines, get_ticker_price, get_crypto_news, clear_data_cache
from src.analysis import add_technical_indicators, generate_trade_signals, analyze_news_sentiment
from src.ui import (
    setup_page, render_sidebar, render_header,
    create_multi_chart, create_rsi_chart,
    render_signal_card, render_sentiment_card,
    render_watchlist_table, render_portfolio_table
)
from src.portfolio import get_portfolio, add_to_portfolio, clear_portfolio, update_portfolio_prices

# --- Initialization ---
logger = get_logger("main")
config = load_config()

# Setup Page Config & CSS
setup_page()

# --- Main Logic ---
def main():
    # 1. Render Sidebar & Get Settings
    settings = render_sidebar()
    symbol = settings['symbol']
    timeframe = settings['timeframe']
    limit = settings['limit']
    refresh_clicked = settings['refresh']
    auto_refresh = settings['auto_refresh']
    page = settings['page']
    
    # 2. Handle Refresh Logic
    if refresh_clicked:
        clear_data_cache()
        st.rerun()
        
    if auto_refresh:
        time.sleep(30)
        clear_data_cache()
        st.rerun()
    
    # 3. Page Routing
    if page == "📊 Dashboard":
        render_dashboard(symbol, timeframe, limit)
    elif page == "👁️ Watchlist":
        render_watchlist_page()
    elif page == "💼 Portfolio":
        render_portfolio_page(symbol)
    elif page == "⚙️ Settings":
        render_settings_page()

# --- Page Renderers ---

def render_dashboard(symbol, timeframe, limit):
    """Main Dashboard View"""
    render_header(f"{symbol} Dashboard", f"Timeframe: {timeframe}")
    
    # A. Fetch Data
    with st.spinner(f"Fetching data for {symbol}..."):
        df = get_klines(symbol, timeframe, limit)
        news_df = get_crypto_news(limit=5)
    
    if df.empty:
        st.error(f"Failed to load data for {symbol}. Please check the symbol name.")
        return

    # B. Analyze Data
    df_ind = add_technical_indicators(df)
    signal_data = generate_trade_signals(df_ind)
    sentiment_data = analyze_news_sentiment(news_df)
    
    # Get Current Price
    current_price = get_ticker_price(symbol)
    prev_close = df_ind['close'].iloc[-2] if len(df_ind) > 1 else df_ind['close'].iloc[-1]
    price_change = ((current_price - prev_close) / prev_close) * 100
    
    # C. Top Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Current Price", f"${current_price:,.2f}", f"{price_change:.2f}%")
    with col2:
        st.metric("RSI (14)", f"{df_ind['RSI'].iloc[-1]:.2f}")
    with col3:
        st.metric("Volume (24h)", f"{df_ind['volume'].sum():,.0f}")
    with col4:
        st.metric("Sentiment", sentiment_data['label'])
    
    st.markdown("---")
    
    # D. Signal & Charts
    col_chart, col_signal = st.columns([2, 1])
    
    with col_chart:
        # Multi-chart (Candle + Volume + RSI + MACD)
        fig = create_multi_chart(df_ind, symbol)
        st.plotly_chart(fig, use_container_width=True)
        
    with col_signal:
        render_signal_card(signal_data)
        st.markdown("---")
        render_sentiment_card(sentiment_data)
        
    # E. News Section
    with st.expander("📰 Latest News Headlines"):
        if not news_df.empty:
            for _, row in news_df.iterrows():
                st.markdown(f"**[{row['title']}]({row['url']})** - {row['source']}")
        else:
            st.write("No news available.")

def render_watchlist_page():
    """Watchlist Scanner View"""
    render_header("👁️ Market Watchlist", "Scanning top configured coins")
    
    watchlist = config.get('app', {}).get('watchlist', ['BTCUSDT', 'ETHUSDT'])
    data = []
    
    progress_bar = st.progress(0)
    
    for i, symbol in enumerate(watchlist):
        try:
            # Fetch quick data (only last 50 candles for speed)
            df = get_klines(symbol, '1h', 50)
            if not df.empty:
                df_ind = add_technical_indicators(df)
                signal = generate_trade_signals(df_ind)
                price = get_ticker_price(symbol)
                
                data.append({
                    'Symbol': symbol,
                    'Price': price,
                    'RSI': df_ind['RSI'].iloc[-1],
                    'Signal': signal['signal'],
                    'Confidence': signal['confidence']
                })
        except Exception as e:
            logger.warning(f"Failed to scan {symbol}: {e}")
            
        progress_bar.progress((i + 1) / len(watchlist))
        
    if data:
        df_watch = pd.DataFrame(data)
        render_watchlist_table(df_watch)
    else:
        st.warning("No data available for watchlist coins.")

def render_portfolio_page(current_symbol):
    """Portfolio Management View"""
    render_header("💼 Portfolio Tracker", "Manage your holdings")
    
    # Add Holding Form
    with st.expander("➕ Add / Update Holding"):
        with st.form("add_holding"):
            col1, col2, col3 = st.columns(3)
            p_symbol = col1.text_input("Symbol", value=current_symbol)
            p_amount = col2.number_input("Amount", min_value=0.0, step=0.0001)
            p_price = col3.number_input("Avg Buy Price ($)", min_value=0.0, step=0.01)
            
            submitted = st.form_submit_button("Add to Portfolio")
            if submitted:
                add_to_portfolio(p_symbol, p_amount, p_price)
                st.success(f"Added {p_amount} {p_symbol}")
                st.rerun()
    
    # Display Portfolio
    df_portfolio = get_portfolio()
    
    if not df_portfolio.empty:
        # Update current prices
        symbols = df_portfolio['symbol'].unique()
        prices = {s: get_ticker_price(s) for s in symbols}
        df_updated = update_portfolio_prices(prices)
        render_portfolio_table(df_updated)
        
        # Clear Button
        if st.button("🗑️ Clear Portfolio"):
            clear_portfolio()
            st.rerun()
    else:
        st.info("Your portfolio is empty. Add holdings above.")

def render_settings_page():
    """Settings & Info View"""
    render_header("⚙️ Settings", "App Configuration")
    
    st.subheader("Configuration")
    st.json(config)
    
    st.subheader("System")
    if st.button("🗑️ Clear All Cache"):
        clear_data_cache()
        st.success("Cache cleared! Please refresh page.")
        
    st.subheader("About")
    st.markdown("""
    **Crypto Watch Pro v1.0.0**
    
    Built with Streamlit, Pandas, and Plotly.
    Data provided by Binance Public API.
    News provided by CryptoPanic (or Mock).
    
    **Disclaimer:** This app is for educational purposes only. Not financial advice.
    """)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Critical Application Error: {e}")
        logger.critical(f"Critical Error: {e}")