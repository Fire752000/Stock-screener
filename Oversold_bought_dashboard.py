import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Oversold & Overbought Screener", layout="wide")
st.title("📊 Oversold & Overbought Stock Screener")
st.markdown("**RSI + Stochastic Scanner** (Lightweight Version)")

# Sidebar
st.sidebar.header("Settings")

period = st.sidebar.selectbox("Data Period", ["3mo", "6mo", "1y", "2y"], index=1)
rsi_length = st.sidebar.slider("RSI Period", 7, 21, 14)
oversold_threshold = st.sidebar.slider("Oversold Threshold", 20, 40, 30)
overbought_threshold = st.sidebar.slider("Overbought Threshold", 60, 80, 70)

# Watchlists
watchlist_options = {
    "Major Tech": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
    "Broad Market": ['SPY', 'QQQ', 'IWM', 'DIA'],
    "Semiconductors": ['NVDA', 'AMD', 'AVGO', 'TSM', 'ASML'],
    "Financials": ['JPM', 'BAC', 'V', 'MA'],
    "Custom": []
}

selected_list = st.sidebar.selectbox("Select Watchlist", options=list(watchlist_options.keys()))

if selected_list == "Custom":
    custom = st.sidebar.text_input("Enter tickers (comma separated)", "AAPL, MSFT, NVDA")
    tickers = [t.strip().upper() for t in custom.split(",") if t.strip()]
else:
    tickers = watchlist_options[selected_list]

extra = st.sidebar.text_input("Add extra tickers", "")
if extra:
    extra_list = [t.strip().upper() for t in extra.split(",") if t.strip()]
    tickers = list(dict.fromkeys(tickers + extra_list))

# Manual RSI Calculation
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_stoch(data, k=14, d=3):
    low_min = data['Low'].rolling(window=k).min()
    high_max = data['High'].rolling(window=k).max()
    stoch_k = 100 * (data['Close'] - low_min) / (high_max - low_min)
    stoch_d = stoch_k.rolling(window=d).mean()
    return stoch_k, stoch_d

def get_indicators(ticker):
    try:
        data = yf.download(ticker, period=period, progress=False)
        if len(data) < 30:
            return None

        data['RSI'] = calculate_rsi(data, rsi_length)
        data['Stoch_K'], data['Stoch_D'] = calculate_stoch(data)

        latest = data.iloc[-1]
        prev = data.iloc[-2]

        change_pct = round((latest['Close'] - prev['Close']) / prev['Close'] * 100, 2)

        if pd.isna(latest['RSI']):
            return None

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
            'Change%': change_pct,
            'RSI': round(latest['RSI'], 2),
            'Stoch_K': round(latest['Stoch_K'], 2),
            'Status': status,
            'Color': color,
            'Volume': int(latest['Volume'])
        }
    except:
        return None

# Run Button
if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner(f"Scanning {len(tickers)} stocks..."):
        results = []
        for ticker in tickers:
            result = get_indicators(ticker)
            if result:
                results.append(result)

        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('RSI')

            # Display
            st.subheader(f"Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

            def highlight(row):
                if row['Color'] == 'green':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Color'] == 'red':
                    return ['background-color: #f8d7da'] * len(row)
                return [''] * len(row)

            st.dataframe(df.style.apply(highlight, axis=1), use_container_width=True, hide_index=True)

            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 Oversold", len(df[df['RSI'] < oversold_threshold]))
            with col2:
                st.metric("🔴 Overbought", len(df[df['RSI'] > overbought_threshold]))
            with col3:
                st.metric("Total Scanned", len(df))

            # Top Signals
            if not df[df['RSI'] < oversold_threshold].empty:
                st.write("**🟢 Oversold Opportunities**")
                st.dataframe(df[df['RSI'] < oversold_threshold][['Ticker', 'Price', 'Change%', 'RSI', 'Stoch_K']])

            if not df[df['RSI'] > overbought_threshold].empty:
                st.write("**🔴 Overbought Warnings**")
                st.dataframe(df[df['RSI'] > overbought_threshold][['Ticker', 'Price', 'Change%', 'RSI', 'Stoch_K']])
        else:
            st.error("No data retrieved. Try different tickers.")

st.caption("Lightweight version • No pandas_ta • Works on Python 3.14")
