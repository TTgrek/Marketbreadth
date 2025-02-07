import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

def show():
    st.title("📈 Market Sentiment")

    # 🔹 Hämta QQQ-data
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")

    # 🔹 Beräkna MA20
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # 🔹 Identifiera cykeltoppar och bottnar
    window = 20  # Hur många dagar bakåt vi kollar för toppar/bottnar
    data["Cycle Peak"] = data["High"] == data["High"].rolling(window, center=True).max()
    data["Cycle Bottom"] = data["Low"] == data["Low"].rolling(window, center=True).min()

    # 🔹 Skapa Candlestick-graf
    fig = go.Figure()

    # Candlesticks med färger (grön = upp, röd = ner)
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
        name="Candlestick"
    ))

    # 🔹 Lägg till MA20 (blå linje)
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data["MA20"], 
        mode="lines", 
        line=dict(color="blue", width=1.5),
        name="MA20"
    ))

    # 🔹 Rita ut cykeltoppar & bottnar på grafen
    fig.add_trace(go.Scatter(
        x=data.index[data["Cycle Peak"]], 
        y=data["High"][data["Cycle Peak"]], 
        mode="markers",
        marker=dict(color="red", size=8, symbol="triangle-up"),
        name="Topp"
    ))

    fig.add_trace(go.Scatter(
        x=data.index[data["Cycle Bottom"]], 
        y=data["Low"][data["Cycle Bottom"]], 
        mode="markers",
        marker=dict(color="blue", size=8, symbol="triangle-down"),
        name="Botten"
    ))

    # 🔹 Anpassa grafens layout
    fig.update_layout(
        title="QQQ Candlestick Chart med MA20 & Cykler",
        xaxis_title="Datum",
        yaxis_title="Pris",
        xaxis_rangeslider_visible=False,
        height=600
    )

    # 🔹 Visa grafen i Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # 🔹 Vänd tabellen (nyaste datum överst)
    data_sorted = data[::-1]  # Sorterar i omvänd ordning

    # 🔹 Visa tabellen i bredare format
    st.dataframe(
        data_sorted[["Close", "High", "Low", "Open", "Volume", "MA20"]],
        height=500,
        width=1200
    )
