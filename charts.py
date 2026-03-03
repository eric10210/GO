import plotly.graph_objects as go
import plotly.subplots as sp
from src.utils.logger import get_logger

logger = get_logger("charts")

def create_candlestick_chart(df: dict, symbol: str) -> go.Figure:
    """
    Creates an interactive candlestick chart with volume and moving averages.
    """
    fig = go.Figure()
    
    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='Price',
        increasing_line_color='#00FF00',
        decreasing_line_color='#FF0000'
    ))
    
    # Moving Averages (if available)
    if 'SMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_20'],
            line=dict(color='#FFA500', width=1),
            name='SMA 20'
        ))
    
    if 'SMA_50' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['SMA_50'],
            line=dict(color='#00BFFF', width=1),
            name='SMA 50'
        ))
    
    if 'EMA_20' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['EMA_20'],
            line=dict(color='#FF1493', width=1, dash='dash'),
            name='EMA 20'
        ))
    
    # Layout
    fig.update_layout(
        title=f"{symbol} Price Chart",
        xaxis_title="Time",
        yaxis_title="Price (USDT)",
        template="plotly_dark",
        height=500,
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig

def create_rsi_chart(df: dict, period: int = 14) -> go.Figure:
    """
    Creates RSI indicator chart with overbought/oversold zones.
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df.index, y=df['RSI'],
        line=dict(color='#9370DB', width=2),
        name='RSI'
    ))
    
    # Overbought/Oversold lines
    fig.add_hline(y=70, line_dash="dash", line_color="#FF0000", 
                  annotation_text="Overbought (70)")
    fig.add_hline(y=30, line_dash="dash", line_color="#00FF00", 
                  annotation_text="Oversold (30)")
    fig.add_hline(y=50, line_dash="dot", line_color="#888888", opacity=0.5)
    
    fig.update_layout(
        title=f"RSI ({period})",
        yaxis_range=[0, 100],
        template="plotly_dark",
        height=200,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    return fig

def create_macd_chart(df: dict) -> go.Figure:
    """
    Creates MACD indicator chart with histogram.
    """
    fig = go.Figure()
    
    # MACD Line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['MACD'],
        line=dict(color='#00BFFF', width=2),
        name='MACD'
    ))
    
    # Signal Line
    fig.add_trace(go.Scatter(
        x=df.index, y=df['Signal'],
        line=dict(color='#FFA500', width=2),
        name='Signal'
    ))
    
    # Histogram
    colors = ['#00FF00' if val > 0 else '#FF0000' for val in df['Hist']]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Hist'],
        marker_color=colors,
        name='Histogram',
        opacity=0.5
    ))
    
    fig.update_layout(
        title="MACD",
        template="plotly_dark",
        height=200,
        showlegend=True,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    return fig

def create_volume_chart(df: dict) -> go.Figure:
    """
    Creates volume bar chart.
    """
    colors = ['#00FF00' if df['close'].iloc[i] >= df['open'].iloc[i] 
              else '#FF0000' for i in range(len(df))]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=df.index, y=df['volume'],
        marker_color=colors,
        name='Volume',
        opacity=0.7
    ))
    
    fig.update_layout(
        title="Volume",
        template="plotly_dark",
        height=150,
        showlegend=False,
        margin=dict(l=10, r=10, t=30, b=10)
    )
    
    return fig

def create_multi_chart(df: dict, symbol: str) -> go.Figure:
    """
    Creates a subplot with candlestick, volume, RSI, and MACD.
    """
    fig = sp.make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{symbol} Price", "Volume", "RSI", "MACD")
    )
    
    # Row 1: Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['open'], high=df['high'],
        low=df['low'], close=df['close'],
        name='Price',
        increasing_line_color='#00FF00',
        decreasing_line_color='#FF0000'
    ), row=1, col=1)
    
    # Row 2: Volume
    colors = ['#00FF00' if df['close'].iloc[i] >= df['open'].iloc[i] 
              else '#FF0000' for i in range(len(df))]
    fig.add_trace(go.Bar(
        x=df.index, y=df['volume'],
        marker_color=colors, name='Volume'
    ), row=2, col=1)
    
    # Row 3: RSI
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['RSI'],
            line=dict(color='#9370DB', width=2), name='RSI'
        ), row=3, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#FF0000", row=3, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#00FF00", row=3, col=1)
    
    # Row 4: MACD
    if 'MACD' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['MACD'],
            line=dict(color='#00BFFF', width=2), name='MACD'
        ), row=4, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df['Signal'],
            line=dict(color='#FFA500', width=2), name='Signal'
        ), row=4, col=1)
    
    fig.update_layout(
        template="plotly_dark",
        height=800,
        xaxis_rangeslider_visible=False,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    return fig