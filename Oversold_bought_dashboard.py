import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Stock Screener", layout="wide")
st.title("📊 Oversold & Overbought Screener")
st.markdown("**RSI-based Stock Scanner**")

# Sidebar settings
st.sidebar.header("Settings")
period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y"], index=2)
rsi_length = st.sidebar.slider("RSI Length", 7, 21, 14)
oversold_level = st.sidebar.slider("Oversold Level", 20, 40, 30)
overbought_level = st.sidebar.slider("Overbought Level", 60, 80, 70)

# Watchlist
watchlists = {
    "Major Tech": ["AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA"],
    "Broad Market": ["SPY", "QQQ", "IWM"],
    "Semiconductors": ["NVDA", "AMD", "AVGO", "TSM"],
    "Custom": []
}

choice = st.sidebar.selectbox("Select Watchlist", list(watchlists.keys()))

if choice == "Custom":
    input_tickers = st.sidebar.text_input("Enter tickers (comma separated)", "AAPL, NVDA, SPY")
    tickers = [t.strip().upper() for t in input_tickers.split(",") if t.strip()]
else:
    tickers = watchlists[choice]

# RSI Function
def calculate_rsi(close_prices, window=14):
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner("Fetching latest market data..."):
        results = []
        
        for ticker in tickers:
            try:
                data = yf.download(ticker, period=period, progress=False, timeout=10)
                if data.empty or len(data) < 20:
                    continue
                
                data['RSI'] = calculate_rsi(data['Close'], rsi_length)
                latest = data.iloc[-1]
                
                if pd.isna(latest['RSI']):
                    continue
                
                change_pct = round(((latest['Close'] - data.iloc[-2]['Close']) / data.iloc[-2]['Close']) * 100, 2)
                
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
            except:
                pass
        
        if results:
            df = pd.DataFrame(results).sort_values("RSI")
            
            def highlight(row):
                if row["Color"] == "green":
                    return ["background-color: #d4edda"] * len(row)
                elif row["Color"] == "red":
                    return ["background-color: #f8d7da"] * len(row)
                return [""] * len(row)
            
            st.subheader(f"Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True, hide_index=True)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("🟢 Oversold", len(df[df["RSI"] < oversold_level]))
            c2.metric("🔴 Overbought", len(df[df["RSI"] > overbought_level]))
            c3.metric("Total", len(df))
        else:
            st.error("No data retrieved. Try again later or use different tickers.")

st.caption("Using: streamlit + yfinance + pandas + plotly")
