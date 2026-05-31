import streamlit as st
import yfinance as yf
import pandas as pd
import os
from datetime import datetime

# Fix for Streamlit Cloud cache issue
os.environ["YFINANCE_CACHE_DIR"] = "/tmp"

st.set_page_config(page_title="Stock Screener", layout="wide")
st.title("📊 Oversold & Overbought Stock Screener")
st.markdown("**RSI Scanner** - Fixed for Streamlit Cloud")

# Sidebar
st.sidebar.header("Settings")
period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y"], index=2)
rsi_length = st.sidebar.slider("RSI Length", 7, 21, 14)
oversold_level = st.sidebar.slider("Oversold", 20, 40, 30)
overbought_level = st.sidebar.slider("Overbought", 60, 80, 70)

# Watchlists
watchlists = {
    "Major Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "Broad Market": ["SPY", "QQQ", "IWM"],
    "Semiconductors": ["NVDA", "AMD", "AVGO", "TSM"],
    "Custom": []
}

choice = st.sidebar.selectbox("Select Watchlist", list(watchlists.keys()))

if choice == "Custom":
    input_str = st.sidebar.text_input("Tickers (comma separated)", "AAPL, NVDA, SPY, TSLA")
    tickers = [t.strip().upper() for t in input_str.split(",") if t.strip()]
else:
    tickers = watchlists[choice]

def calculate_rsi(close, window=14):
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner("Fetching data from Yahoo Finance..."):
        results = []
        
        for ticker in tickers:
            try:
                # Use Ticker object + cache fix
                stock = yf.Ticker(ticker)
                data = stock.history(period=period)
                
                if data.empty or len(data) < 20:
                    continue
                
                data['RSI'] = calculate_rsi(data['Close'], rsi_length)
                latest = data.iloc[-1]
                
                if pd.isna(latest['RSI']):
                    continue
                
                change_pct = round((latest['Close'] - data.iloc[-2]['Close']) / data.iloc[-2]['Close'] * 100, 2)
                
                if latest['RSI'] < oversold_level:
                    status = "🟢 OVERSOLD"
                    color = "green"
                elif latest['RSI'] > overbought_level:
                    status = "🔴 OVERBOUGHT"
                    color = "red"
                else:
                    status = "⚪ Neutral"
                    color = "gray"
                
                results.append({
                    "Ticker": ticker,
                    "Price": round(latest["Close"], 2),
                    "Change%": change_pct,
                    "RSI": round(latest["RSI"], 2),
                    "Status": status,
                    "Color": color
                })
            except Exception as e:
                st.write(f"⚠️ Failed to load {ticker}")
        
        if results:
            df = pd.DataFrame(results).sort_values("RSI")
            
            def highlight_row(row):
                if row["Color"] == "green":
                    return ["background-color: #d4edda"] * len(row)
                elif row["Color"] == "red":
                    return ["background-color: #f8d7da"] * len(row)
                return [""] * len(row)
            
            st.subheader(f"✅ Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            st.dataframe(df.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)
            
            col1, col2, col3 = st.columns(3)
            col1.metric("🟢 Oversold", len(df[df["RSI"] < oversold_level]))
            col2.metric("🔴 Overbought", len(df[df["RSI"] > overbought_level]))
            col3.metric("Total", len(df))
        else:
            st.error("Still no data. Try refreshing the page or use fewer tickers.")

st.caption("Fixed version with cache patch for Streamlit Cloud")
