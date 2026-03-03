import streamlit as st

def render_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal"):
    """
    Renders a styled metric card.
    """
    st.metric(
        label=title,
        value=value,
        delta=delta,
        delta_color=delta_color
    )

def render_signal_card(signal_data: dict):
    """
    Renders a prominent signal card with color coding.
    """
    signal = signal_data.get('signal', 'NEUTRAL')
    confidence = signal_data.get('confidence', 0)
    reasons = signal_data.get('reasons', [])
    
    # Determine color based on signal
    if 'BUY' in signal:
        color = "#00FF00"
        bg_color = "rgba(0, 255, 0, 0.1)"
    elif 'SELL' in signal:
        color = "#FF0000"
        bg_color = "rgba(255, 0, 0, 0.1)"
    else:
        color = "#FFFF00"
        bg_color = "rgba(255, 255, 0, 0.1)"
    
    st.markdown(f"""
    <div style="background-color: {bg_color}; 
                border: 2px solid {color};
                border-radius: 10px;
                padding: 20px;
                margin: 10px 0;">
        <h2 style="color: {color}; margin: 0;">🎯 {signal}</h2>
        <p style="color: white; margin: 5px 0;">Confidence: <strong>{confidence}%</strong></p>
        <hr style="border-color: {color}; opacity: 0.3;">
        <p style="color: #CCCCCC; font-size: 14px;">
            <strong>Reasons:</strong><br>
            {'<br>'.join(['• ' + r for r in reasons]) if reasons else '• No strong signals detected'}
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_sentiment_card(sentiment_data: dict):
    """
    Renders a sentiment analysis card.
    """
    score = sentiment_data.get('score', 0)
    label = sentiment_data.get('label', 'NEUTRAL')
    count = sentiment_data.get('count', 0)
    
    # Color based on sentiment
    if label == "POSITIVE":
        color = "#00FF00"
        icon = "😊"
    elif label == "NEGATIVE":
        color = "#FF0000"
        icon = "😟"
    else:
        color = "#FFFF00"
        icon = "😐"
    
    st.markdown(f"""
    <div style="background-color: #1e1e1e; 
                border-left: 4px solid {color};
                border-radius: 5px;
                padding: 15px;
                margin: 10px 0;">
        <h3 style="color: white; margin: 0;">📰 News Sentiment {icon}</h3>
        <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 10px 0;">
            {label} ({score:.2f})
        </p>
        <p style="color: #888888; font-size: 12px;">
            Analyzed {count} headlines
        </p>
    </div>
    """, unsafe_allow_html=True)

def render_price_card(price: float, change: float, symbol: str):
    """
    Renders a price display card with percentage change.
    """
    delta_color = "normal" if change >= 0 else "inverse"
    change_str = f"{change:+.2f}%"
    
    st.markdown(f"""
    <div style="background-color: #1e1e1e; 
                border-radius: 10px;
                padding: 20px;
                text-align: center;">
        <h3 style="color: #888888; margin: 0;">{symbol} Price</h3>
        <h1 style="color: white; margin: 10px 0;">${price:,.2f}</h1>
        <p style="color: {'#00FF00' if change >= 0 else '#FF0000'}; 
                    font-size: 18px; font-weight: bold;">
            {change_str}
        </p>
    </div>
    """, unsafe_allow_html=True)