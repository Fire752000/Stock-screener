import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="Oversold & Overbought Screener", layout="wide")
st.title("📊 Oversold & Overbought Stock Screener")
st.markdown("**Real-time RSI + Stochastic Scanner**")

# Sidebar
st.sidebar.header("Settings")

period = st.sidebar.selectbox("Data Period", ["3mo", "6mo", "1y", "2y", "5y"], index=1)
rsi_length = st.sidebar.slider("RSI Period", 7, 21, 14)
oversold_threshold = st.sidebar.slider("Oversold Threshold", 20, 40, 30)
overbought_threshold = st.sidebar.slider("Overbought Threshold", 60, 80, 70)

# Predefined watchlists
watchlist_options = {
    "Major Tech": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
    "Broad Market": ['SPY', 'QQQ', 'IWM', 'DIA', 'VTI'],
    "Financials": ['JPM', 'BAC', 'GS', 'V', 'MA', 'AXP'],
    "Healthcare": ['JNJ', 'PFE', 'MRK', 'ABBV', 'LLY'],
    "Semiconductors": ['NVDA', 'AMD', 'AVGO', 'TSM', 'ASML', 'AMAT'],
    "Custom": []
}

selected_list = st.sidebar.selectbox("Select Watchlist", options=list(watchlist_options.keys()))

if selected_list == "Custom":
    custom_tickers = st.sidebar.text_input("Enter tickers (comma separated)", "AAPL, MSFT, NVDA")
    tickers = [t.strip().upper() for t in custom_tickers.split(",")]
else:
    tickers = watchlist_options[selected_list]

# Add extra tickers
extra = st.sidebar.text_input("Add extra tickers (optional)", "")
if extra:
    extra_list = [t.strip().upper() for t in extra.split(",") if t.strip()]
    tickers = list(dict.fromkeys(tickers + extra_list))  # remove duplicates

# Main Function
def get_indicators(ticker):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if len(data) < rsi_length + 10:
            return None
            
        data['RSI'] = ta.rsi(data['Close'], length=rsi_length)
        stoch = ta.stoch(data['High'], data['Low'], data['Close'], k=14, d=3)
        data['Stoch_K'] = stoch['STOCHk_14_3_3']
        data['Stoch_D'] = stoch['STOCHd_14_3_3']
        
        latest = data.iloc[-1]
        
        if latest['RSI'] < oversold_threshold:
            status = "🟢 OVERSOLD"
            color = "green"
        elif latest['RSI'] > overbought_threshold:
            status = "🔴 OVERBOUGHT"
            color = "red"
        else:
            status = "⚪ Neutral"
            color = "gray"
            
        return {
            'Ticker': ticker,
            'Price': round(latest['Close'], 2),
            'Change%': round((latest['Close'] - data.iloc[-2]['Close'])/data.iloc[-2]['Close']*100, 2),
            'RSI': round(latest['RSI'], 2),
            'Stoch_K': round(latest['Stoch_K'], 2),
            'Status': status,
            'Color': color,
            'Volume': int(latest['Volume'])
        }
    except:
        return None

# Run Scanner Button
if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner(f"Scanning {len(tickers)} stocks..."):
        results = []
        for ticker in tickers:
            data = get_indicators(ticker)
            if data:
                results.append(data)
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('RSI')
            
            # Display Results
            st.subheader(f"Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # Color coding
            def highlight_row(row):
                return ['background-color: #d4edda' if row['Color'] == 'green' 
                        else 'background-color: #f8d7da' if row['Color'] == 'red' 
                        else '' for _ in row]
            
            styled_df = df.style.apply(highlight_row, axis=1)
            
            st.dataframe(styled_df, use_container_width=True, hide_index=True)
            
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 Oversold", len(df[df['RSI'] < oversold_threshold]))
            with col2:
                st.metric("🔴 Overbought", len(df[df['RSI'] > overbought_threshold]))
            with col3:
                st.metric("Total Stocks", len(df))
            
            # Detailed Charts for Oversold/Overbought
            st.subheader("Top Signals")
            
            oversold_df = df[df['RSI'] < oversold_threshold]
            overbought_df = df[df['RSI'] > overbought_threshold]
            
            if not oversold_df.empty:
                st.write("**Oversold Opportunities**")
                st.dataframe(oversold_df[['Ticker', 'Price', 'Change%', 'RSI', 'Stoch_K']], use_container_width=True)
            
            if not overbought_df.empty:
                st.write("**Overbought Warnings**")
                st.dataframe(overbought_df[['Ticker', 'Price', 'Change%', 'RSI', 'Stoch_K']], use_container_width=True)
                
        else:
            st.error("No data retrieved. Check ticker symbols.")

# Footer
st.caption("Built with Streamlit • Data from Yahoo Finance • RSI + Stochastic")
