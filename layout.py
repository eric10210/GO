import streamlit as st
from src.utils.config_loader import load_config

config = load_config()

def setup_page():
    """
    Configures the Streamlit page settings.
    """
    app_cfg = config.get('app', {})
    
    st.set_page_config(
        page_title=app_cfg.get('title', 'Crypto Watch'),
        page_icon=app_cfg.get('icon', '📈'),
        layout=app_cfg.get('layout', 'wide'),
        initial_sidebar_state='expanded'
    )
    
    # Inject custom CSS
    with open('assets/styles.css', 'r') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def render_sidebar() -> dict:
    """
    Renders the sidebar with navigation and settings.
    Returns user selections as a dictionary.
    """
    st.sidebar.title("⚙️ Settings")
    
    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        ["📊 Dashboard", "👁️ Watchlist", "💼 Portfolio", "⚙️ Settings"],
        index=0
    )
    
    st.sidebar.markdown("---")
    
    # Trading Pair Selection
    st.sidebar.subheader("Trading Pair")
    symbol = st.sidebar.text_input(
        "Symbol",
        value=config.get('app', {}).get('default_symbol', 'BTCUSDT')
    ).upper()
    
    # Timeframe Selection
    timeframe = st.sidebar.selectbox(
        "Timeframe",
        ['15m', '1h', '4h', '1d', '1w'],
        index=1
    )
    
    # Candle Limit
    limit = st.sidebar.slider(
        "Candle Limit",
        min_value=50,
        max_value=500,
        value=config.get('app', {}).get('candle_limit', 200)
    )
    
    st.sidebar.markdown("---")
    
    # Refresh Button
    refresh = st.sidebar.button("🔄 Refresh Data", use_container_width=True)
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.caption(f"Data: Binance API")
    st.sidebar.caption(f"Version: 1.0.0")
    
    return {
        "page": page,
        "symbol": symbol,
        "timeframe": timeframe,
        "limit": limit,
        "refresh": refresh,
        "auto_refresh": auto_refresh
    }

def render_header(title: str, subtitle: str = ""):
    """
    Renders a consistent header across all pages.
    """
    col1, col2 = st.columns([4, 1])
    
    with col1:
        st.title(title)
        if subtitle:
            st.caption(subtitle)
    
    with col2:
        # Live status indicator
        st.markdown("""
        <div style="background-color: #00FF00; padding: 5px 10px; 
                    border-radius: 5px; text-align: center; color: black; 
                    font-weight: bold; margin-top: 25px;">
            ● LIVE
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")