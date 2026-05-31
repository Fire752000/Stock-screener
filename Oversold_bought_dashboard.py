import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="Oversold & Overbought Screener", layout="wide")
st.title("📊 Oversold & Overbought Stock Screener")
st.markdown("**RSI Scanner** - Fixed & More Reliable")

# Sidebar
st.sidebar.header("Settings")
period = st.sidebar.selectbox("Data Period", ["1mo", "3mo", "6mo", "1y"], index=2)
rsi_length = st.sidebar.slider("RSI Period", 7, 21, 14)
oversold_threshold = st.sidebar.slider("Oversold Threshold", 20, 40, 30)
overbought_threshold = st.sidebar.slider("Overbought Threshold", 60, 80, 70)

# Watchlists
watchlist_options = {
    "Major Tech": ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA'],
    "Broad Market": ['SPY', 'QQQ', 'IWM'],
    "Semiconductors": ['NVDA', 'AMD', 'AVGO', 'TSM'],
    "Custom": []
}

selected_list = st.sidebar.selectbox("Select Watchlist", options=list(watchlist_options.keys()))

if selected_list == "Custom":
    custom = st.sidebar.text_input("Enter tickers (comma separated)", "AAPL, MSFT, NVDA, SPY")
    tickers = [t.strip().upper() for t in custom.split(",") if t.strip()]
else:
    tickers = watchlist_options[selected_list]

extra = st.sidebar.text_input("Add extra tickers (optional)", "")
if extra:
    extra_list = [t.strip().upper() for t in extra.split(",") if t.strip()]
    tickers = list(dict.fromkeys(tickers + extra_list))

# Manual RSI + Stochastic
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = delta.where(delta > 0, 0).rolling(window=window).mean()
    loss = -delta.where(delta < 0, 0).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def get_indicators(ticker):
    try:
        # Try with longer period first for better data
        data = yf.download(ticker, period=period, progress=False, timeout=10)
        
        if data.empty or len(data) < rsi_length + 5:
            return {'Ticker': ticker, 'Error': f"Insufficient data ({len(data)} rows)"}
        
        data['RSI'] = calculate_rsi(data, rsi_length)
        
        latest = data.iloc[-1]
        
        if pd.isna(latest['RSI']):
            return {'Ticker': ticker, 'Error': "RSI calculation failed"}

        change_pct = round((latest['Close'] - data.iloc[-2]['Close']) / data.iloc[-2]['Close'] * 100, 2)

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
            'Status': status,
            'Color': color,
            'Rows': len(data)
        }
    except Exception as e:
        return {'Ticker': ticker, 'Error': str(e)[:100]}

# Run Scanner
if st.button("🚀 Run Scanner", type="primary"):
    with st.spinner(f"Scanning {len(tickers)} stocks... This may take 10-20 seconds"):
        results = []
        errors = []
        
        for ticker in tickers:
            result = get_indicators(ticker)
            if 'Error' in result:
                errors.append(result)
            else:
                results.append(result)
        
        if results:
            df = pd.DataFrame(results)
            df = df.sort_values('RSI')
            
            st.success(f"✅ Retrieved data for {len(results)}/{len(tickers)} stocks")
            st.subheader(f"Scan Results - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # Color highlighting
            def highlight_row(row):
                if row['Color'] == 'green':
                    return ['background-color: #d4edda'] * len(row)
                elif row['Color'] == 'red':
                    return ['background-color: #f8d7da'] * len(row)
                return [''] * len(row)
            
            st.dataframe(df.style.apply(highlight_row, axis=1), use_container_width=True, hide_index=True)
            
            # Summary Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("🟢 Oversold", len(df[df['RSI'] < oversold_threshold]))
            with col2:
                st.metric("🔴 Overbought", len(df[df['RSI'] > overbought_threshold]))
            with col3:
                st.metric("Total Valid", len(df))
                
        else:
            st.error("❌ No valid data retrieved from any ticker.")
        
        # Show errors if any
        if errors:
            st.subheader("⚠️ Errors")
            st.write(pd.DataFrame(errors))

st.caption("Improved version • Better error handling • Works better on Streamlit Cloud")
