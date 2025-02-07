import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# 🔹 Hämta QQQ-data från Yahoo Finance
@st.cache_data
def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")

    # 🔹 Konvertera index till kolumn
    data.reset_index(inplace=True)

    # 🔹 Beräkna glidande medelvärde (MA20)
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # 🔹 Identifiera cykeltoppar och bottnar
    data["Cycle Peak"] = data["High"][(data["High"] == data["High"].rolling(20, center=True).max())]
    data["Cycle Bottom"] = data["Low"][(data["Low"] == data["Low"].rolling(20, center=True).min())]

    return data

# 🔹 Funktion för att skapa candlestick-grafen
def plot_candlestick_chart(data):
    fig = go.Figure()

    # 🔹 Lägg till Candlestick-graf
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Candlestick",
        increasing_line_color="green",
        decreasing_line_color="red"
    ))

    # 🔹 Lägg till MA20-linjen
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        name="MA20",
        line=dict(color="blue", width=1.5)
    ))

    # 🔹 Lägg till cykeltoppar (röda trianglar)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Peak"],
        mode="markers",
        name="Topp",
        marker=dict(color="red", symbol="triangle-down", size=10)
    ))

    # 🔹 Lägg till cykelbottnar (gröna trianglar)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Bottom"],
        mode="markers",
        name="Botten",
        marker=dict(color="green", symbol="triangle-up", size=10)
    ))

    # 🔹 Anpassa layout
    fig.update_layout(
        title="QQQ Candlestick Chart med MA20 & Cykler",
        xaxis_title="Datum",
        yaxis_title="Pris",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )

    return fig

# 🔹 Huvudfunktion som visas i Streamlit
def show():
    st.markdown("## 📊 Market Sentiment")

    # 🔹 Hämta data
    data = fetch_data()

    # 🔹 Visa Candlestick-grafen
    st.plotly_chart(plot_candlestick_chart(data), use_container_width=True)
