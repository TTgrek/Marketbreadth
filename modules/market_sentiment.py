import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

def show():
    st.title("📈 Market Sentiment")

    # 🔹 Hämta QQQ-data
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")

    # 🔹 Kontrollera att data laddats korrekt
    if data.empty:
        st.error("❌ Ingen data kunde hämtas för QQQ. Kolla din internetanslutning.")
        return

    # 🔹 Säkra kolumnnamn
    data = data.rename(columns=lambda x: x.strip())  # Tar bort eventuella mellanslag

    # 🔹 Beräkna MA20
    if "Close" in data.columns:
        data["MA20"] = data["Close"].rolling(window=20).mean()
    else:
        st.error("❌ 'Close' saknas i data.")
        return

    # 🔹 Identifiera cykeltoppar och bottnar
    window = 20
    if "High" in data.columns and "Low" in data.columns:
        data["Cycle Peak"] = data["High"] == data["High"].rolling(window, center=True).max()
        data["Cycle Bottom"] = data["Low"] == data["Low"].rolling(window, center=True).min()
    else:
        st.error("❌ 'High' eller 'Low' saknas i data.")
        return

    # 🔹 Skapa Candlestick-graf
    fig = go.Figure()

    # Candlesticks med färger (grön = upp, röd = ner)
    if all(col in data.columns for col in ["Open", "High", "Low", "Close"]):
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
    if "MA20" in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index, 
            y=data["MA20"], 
            mode="lines", 
            line=dict(color="blue", width=1.5),
            name="MA20"
        ))

    # 🔹 Rita ut cykeltoppar & bottnar på grafen
    if "Cycle Peak" in data.columns:
        fig.add_trace(go.Scatter(
            x=data.index[data["Cycle Peak"]], 
            y=data["High"][data["Cycle Peak"]], 
            mode="markers",
            marker=dict(color="red", size=8, symbol="triangle-up"),
            name="Topp"
        ))

    if "Cycle Bottom" in data.columns:
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
    data_sorted = data[::-1]

    # 🔹 Skriv ut kolumnnamn för debugging
    st.write("Kolumner i data_sorted:", list(data_sorted.columns))

    # 🔹 Visa tabellen om kolumnerna finns
    required_cols = ["Close", "High", "Low", "Open", "Volume", "MA20"]
    available_cols = [col for col in required_cols if col in data_sorted.columns]

    if available_cols:
        st.dataframe(
            data_sorted[available_cols],
            height=500,
            width=1200
        )
    else:
        st.error("❌ Ingen data tillgänglig för tabellen.")

