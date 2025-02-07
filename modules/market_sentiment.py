import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import yfinance as yf

# 🛠 **Fix: set_page_config måste vara det första Streamlit-kommandot**
st.set_page_config(page_title="Market Sentiment", layout="wide")

# 🔹 **Ladda QQQ-data**
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

# 🔹 **Ladda data**
data = load_data()

# 🔹 **Vänd på datan så senaste datum är överst**
data_sorted = data.sort_values(by="Date", ascending=False)

# 🔹 **Visa titel**
st.markdown("## 📊 Market Sentiment")

# 🔹 **Debug-tabell för att se datan**
st.markdown("### Debug: Data Preview (första raderna)")
st.dataframe(data_sorted.head(10))  # Visa de 10 senaste datumen

# 🔹 **Skapa Candlestick-graf**
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

# 🔹 **Lägg till MA20 som blå linje**
fig.add_trace(go.Scatter(
    x=data["Date"],
    y=data["MA20"],
    mode="lines",
    line=dict(color="blue", width=2),
    name="MA20"
))

# 🔹 **Lägg till markeringar för toppar och bottnar**
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

# 🔹 **Graf-layout**
fig.update_layout(
    title="QQQ Candlestick Chart med MA20 & Cykler",
    xaxis_title="Datum",
    yaxis_title="Pris",
    xaxis_rangeslider_visible=False,
    template="plotly_white",
    legend=dict(x=0, y=1.05, orientation="h")
)

# 🔹 **Visa grafen**
st.plotly_chart(fig, use_container_width=True)

# 🔹 **Visa tabellen bredare**
st.markdown("### 📅 Fullständig Data (senaste 100 dagarna)")
st.dataframe(data_sorted.head(100))
