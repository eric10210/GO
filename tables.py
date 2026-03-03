import streamlit as st
import pandas as pd

def render_watchlist_table(df: pd.DataFrame):
    """
    Renders a styled watchlist table with conditional formatting.
    """
    if df.empty:
        st.warning("No watchlist data available")
        return
    
    # Format the dataframe
    styled_df = df.style.format({
        'price': '${:,.2f}',
        'change_24h': '{:.2f}%',
        'rsi': '{:.2f}',
        'volume': '{:,.0f}'
    }).applymap(
        lambda v: 'color: #00FF00' if v > 0 else 'color: #FF0000',
        subset=['change_24h']
    ).applymap(
        lambda v: 'background-color: rgba(255, 0, 0, 0.3)' if v > 70 
                  else ('background-color: rgba(0, 255, 0, 0.3)' if v < 30 else ''),
        subset=['rsi']
    )
    
    st.dataframe(styled_df, use_container_width=True)

def render_portfolio_table(df: pd.DataFrame):
    """
    Renders a portfolio holdings table with PnL calculations.
    """
    if df.empty:
        st.info("No holdings in portfolio. Add coins in Settings.")
        return
    
    # Calculate PnL
    df['pnl'] = (df['current_price'] - df['avg_buy_price']) * df['amount']
    df['pnl_percent'] = ((df['current_price'] - df['avg_buy_price']) / df['avg_buy_price']) * 100
    df['value'] = df['current_price'] * df['amount']
    
    # Format and style
    styled_df = df.style.format({
        'avg_buy_price': '${:,.2f}',
        'current_price': '${:,.2f}',
        'amount': '{:.4f}',
        'value': '${:,.2f}',
        'pnl': '${:,.2f}',
        'pnl_percent': '{:.2f}%'
    }).applymap(
        lambda v: 'color: #00FF00' if v > 0 else 'color: #FF0000',
        subset=['pnl', 'pnl_percent']
    )
    
    st.dataframe(styled_df, use_container_width=True)
    
    # Summary metrics
    total_value = df['value'].sum()
    total_pnl = df['pnl'].sum()
    
    col1, col2 = st.columns(2)
    col1.metric("Total Portfolio Value", f"${total_value:,.2f}")
    col2.metric(
        "Total PnL", 
        f"${total_pnl:,.2f}", 
        f"{(total_pnl / (total_value - total_pnl) * 100):.2f}%" if total_value > 0 else "0%",
        delta_color="normal" if total_pnl >= 0 else "inverse"
    )

def render_news_table(df: pd.DataFrame):
    """
    Renders a news headlines table with clickable links.
    """
    if df.empty:
        st.info("No news available")
        return
    
    # Create clickable links
    df['link'] = df.apply(
        lambda row: f'<a href="{row["url"]}" target="_blank">🔗 Read</a>', 
        axis=1
    )
    
    st.markdown(df[['published_at', 'source', 'title', 'link']].to_html(
        escape=False, index=False
    ), unsafe_allow_html=True)