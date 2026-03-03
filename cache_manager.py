import streamlit as st

# Cache TTL settings (in seconds)
CACHE_TTL_FAST = 60      # For prices
CACHE_TTL_NORMAL = 300   # For candles (5 mins)
CACHE_TTL_SLOW = 3600    # For news (1 hour)

def clear_data_cache():
    """
    Clears all cached data functions. 
    Call this when the user clicks a 'Refresh' button.
    """
    st.cache_data.clear()
    st.success("Data cache cleared!")