import streamlit as st
import pandas as pd

def get_portfolio() -> pd.DataFrame:
    """
    Retrieves portfolio from session state.
    """
    if 'portfolio' not in st.session_state:
        st.session_state['portfolio'] = pd.DataFrame(columns=[
            'symbol', 'amount', 'avg_buy_price', 'current_price', 'value', 'pnl'
        ])
    return st.session_state['portfolio']

def add_to_portfolio(symbol: str, amount: float, buy_price: float):
    """
    Adds or updates a holding in the portfolio.
    """
    df = get_portfolio()
    
    # Check if symbol exists
    if symbol in df['symbol'].values:
        # Update existing (average down/up)
        idx = df[df['symbol'] == symbol].index[0]
        old_amount = df.loc[idx, 'amount']
        old_price = df.loc[idx, 'avg_buy_price']
        
        new_amount = old_amount + amount
        new_avg = ((old_amount * old_price) + (amount * buy_price)) / new_amount
        
        df.loc[idx, 'amount'] = new_amount
        df.loc[idx, 'avg_buy_price'] = new_avg
    else:
        # Add new
        new_row = pd.DataFrame([{
            'symbol': symbol,
            'amount': amount,
            'avg_buy_price': buy_price,
            'current_price': buy_price, # Will update on refresh
            'value': 0,
            'pnl': 0
        }])
        df = pd.concat([df, new_row], ignore_index=True)
    
    st.session_state['portfolio'] = df

def clear_portfolio():
    """
    Clears all holdings.
    """
    st.session_state['portfolio'] = pd.DataFrame(columns=[
        'symbol', 'amount', 'avg_buy_price', 'current_price', 'value', 'pnl'
    ])

def update_portfolio_prices(prices: dict):
    """
    Updates current prices for all holdings.
    """
    df = get_portfolio()
    if df.empty:
        return df
        
    for index, row in df.iterrows():
        if row['symbol'] in prices:
            df.loc[index, 'current_price'] = prices[row['symbol']]
            df.loc[index, 'value'] = row['amount'] * prices[row['symbol']]
            df.loc[index, 'pnl'] = (df.loc[index, 'current_price'] - row['avg_buy_price']) * row['amount']
            
    st.session_state['portfolio'] = df
    return df