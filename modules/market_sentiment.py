import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

def show():
    st.title("📈 Market Sentiment")

    # 🔹 Hämta QQQ-data
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")

    # 🔹 Kontrollera att data hämtas korrekt
    if data.empty:
        st.error("❌ Ingen data kunde hämtas för QQQ. Kolla internetanslutning och försök igen.")
        return

    # 🔹 Lägg till MA20
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # 🔹 Identifiera cykeltoppar & bottnar
    window = 20
    data["Cycle Peak"] = data["High"] == data["High"].rolling(window, center=True).max()
    data["Cycle Bottom"] = data["Low"] == data["Low"].rolling(window, center=True).min()

    # 🔹 Skapa Candlestick-graf
    fig = go.Figure()

    # 📌 Candlestick med korrekt OHLC-data
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing=dict(line=dict(color="green"), fillcolor="green"),
        decreasing=dict(line=dict(color="red"), fillcolor="red"),
        name="Candlestick"
    ))

    # 📌 Lägg till MA20 som blå linje
    fig.add_trace(go.Scatter(
        x=data.index, 
        y=data["MA20"], 
        mode="lines", 
        line=dict(color="blue", width=2),
        name="MA20"
    ))

    # 📌 Lägg till cykeltoppar och bottnar
    fig.add_trace(go.Scatter(
        x=data.index[data["Cycle Peak"]], 
        y=data["High"][data["Cycle Peak"]], 
        mode="markers",
        marker=dict(color="red", size=10, symbol="triangle-up"),
        name="Topp"
    ))

    fig.add_trace(go.Scatter(
        x=data.index[data["Cycle Bottom"]], 
        y=data["Low"][data["Cycle Bottom"]], 
        mode="markers",
        marker=dict(color="blue", size=10, symbol="triangle-down"),
        name="Botten"
    ))

    # 🔹 Layout-inställningar för en tydlig graf
    fig.update_layout(
        title="QQQ Candlestick Chart med MA20 & Cykler",
        xaxis_title="Datum",
        yaxis_title="Pris",
        xaxis_rangeslider_visible=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=700,
        font=dict(family="Arial", size=14, color="black"),
        xaxis=dict(
            showgrid=True,
            gridcolor="lightgrey",
            tickformat="%Y-%m-%d",
            tickangle=45
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor="lightgrey"
        ),
        legend=dict(
            x=0.01,
            y=0.99,
            bgcolor="rgba(255,255,255,0.7)"
        )
    )

    # 🔹 Visa grafen i Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # 🔹 Sortera data (nyaste datum överst)
    data_sorted = data[::-1]

    # 🔹 Visa tabellen korrekt
    required_cols = ["Date", "Close", "High", "Low", "Open", "Volume", "MA20"]
    available_cols = [col for col in required_cols if col in data_sorted.columns]

    if available_cols:
        st.dataframe(
            data_sorted[available_cols],
            height=600,
            width=1200
        )
    else:
        st.error("❌ Ingen data tillgänglig för tabellen. Kolla kolumnnamnen.")

