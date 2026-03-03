import pandas as pd
from src.utils.logger import get_logger
from src.utils.config_loader import load_config

logger = get_logger("signals")
config = load_config()

def generate_trade_signals(df: pd.DataFrame) -> dict:
    """
    Analyzes the last row of the DataFrame to generate a trade signal.
    Returns a dictionary with signal, strength, and reasons.
    """
    if df.empty:
        return {"signal": "NEUTRAL", "strength": 0, "reasons": ["No data available"]}

    # Get latest data point
    last = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else last
    
    # Config thresholds
    sig_cfg = config.get('signals', {})
    rsi_overbought = sig_cfg.get('rsi_overbought', 70)
    rsi_oversold = sig_cfg.get('rsi_oversold', 30)
    
    signal = "NEUTRAL"
    strength = 0
    reasons = []
    
    # --- Logic Engine ---
    
    # 1. RSI Logic
    if last['RSI'] < rsi_oversold:
        reasons.append(f"RSI Oversold ({last['RSI']:.2f})")
        strength += 30
    elif last['RSI'] > rsi_overbought:
        reasons.append(f"RSI Overbought ({last['RSI']:.2f})")
        strength -= 30
        
    # 2. Moving Average Crossover (Golden/Death Cross short term)
    if last['EMA_20'] > last['SMA_50'] and prev['EMA_20'] <= prev['SMA_50']:
        reasons.append("EMA crossed above SMA (Bullish)")
        strength += 40
    elif last['EMA_20'] < last['SMA_50'] and prev['EMA_20'] >= prev['SMA_50']:
        reasons.append("EMA crossed below SMA (Bearish)")
        strength -= 40
        
    # 3. MACD Logic
    if last['MACD'] > last['Signal'] and prev['MACD'] <= prev['Signal']:
        reasons.append("MACD Bullish Crossover")
        strength += 30
    elif last['MACD'] < last['Signal'] and prev['MACD'] >= prev['Signal']:
        reasons.append("MACD Bearish Crossover")
        strength -= 30
        
    # 4. Trend Alignment
    if last['close'] > last['SMA_50']:
        reasons.append("Price above SMA 50")
        strength += 10
    else:
        strength -= 10
        
    # --- Determine Final Signal ---
    if strength >= 50:
        signal = "STRONG BUY"
    elif strength >= 20:
        signal = "BUY"
    elif strength <= -50:
        signal = "STRONG SELL"
    elif strength <= -20:
        signal = "SELL"
    else:
        signal = "NEUTRAL"
        
    # Normalize strength to 0-100 for UI
    confidence = min(abs(strength), 100)
    
    result = {
        "signal": signal,
        "strength": strength,
        "confidence": confidence,
        "reasons": reasons,
        "price": last['close'],
        "rsi": last['RSI']
    }
    
    logger.info(f"Signal generated: {signal} (Strength: {strength})")
    return result