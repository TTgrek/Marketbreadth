import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# Hämta QQQ-data
@st.cache_data
def load_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    data.reset_index(inplace=True)
    
    # Beräkna MA20
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # Identifiera toppar och bottnar baserat på High och Low
    window = 20
    data["Cycle Peak"] = data["High"][(data["High"] == data["High"].rolling(window, center=True).max())]
    data["Cycle Bottom"] = data["Low"][(data["Low"] == data["Low"].rolling(window, center=True).min())]

    return data

# Ladda data
data = load_data()

# Vänd på datan så senaste datum är överst
data_sorted = data.sort_values(by="Date", ascending=False)

# Skapa Streamlit-app
st.set_page_config(page_title="Market Sentiment", layout="wide")

st.markdown("## 📊 Market Sentiment")

# Visa tabell för felsökning
st.markdown("### Debug: Data Preview (första raderna)")
st.dataframe(data_sorted.head(10))  # Visa de 10 senaste datumen

# Skapa Candlestick-graf
fig = go.Figure()

fig.add_trace(go.Candlestick(
    x=data["Date"],
    open=data["Open"],
    high=data["High"],
    low=data["Low"],
    close=data["Close"],
    increasing_line_color="green",
    decreasing_line_color="red",
    name="Candlestick"
))

# Lägg till MA20 som blå linje
fig.add_trace(go.Scatter(
    x=data["Date"],
    y=data["MA20"],
    mode="lines",
    line=dict(color="blue", width=2),
    name="MA20"
))

# Lägg till markeringar för toppar (röda trianglar) och bottnar (blå trianglar)
fig.add_trace(go.Scatter(
    x=data["Date"],
    y=data["Cycle Peak"],
    mode="markers",
    marker=dict(color="red", size=7, symbol="triangle-up"),
    name="Topp"
))

fig.add_trace(go.Scatter(
    x=data["Date"],
    y=data["Cycle Bottom"],
    mode="markers",
    marker=dict(color="blue", size=7, symbol="triangle-down"),
    name="Botten"
))

# Layout
fig.update_layout(
    title="QQQ Candlestick Chart med MA20 & Cykler",
    xaxis_title="Datum",
    yaxis_title="Pris",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    legend=dict(x=0, y=1.05, orientation="h")
)

# Visa graf
st.plotly_chart(fig, use_container_width=True)

# Visa bredare tabell med alla kolumner
st.markdown("### 📅 Fullständig Data (senaste 100 dagarna)")
st.dataframe(data_sorted.head(100))
