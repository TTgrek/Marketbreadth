import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.graph_objects as go

# 🔹 Hämta QQQ-data från Yahoo Finance
@st.cache_data
def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")

    # 🔹 Kontrollera om data hämtades korrekt
    if data.empty:
        st.error("Kunde inte hämta data från Yahoo Finance.")
        return None

    # 🔹 Konvertera index till kolumn & fixa datumformat
    data.reset_index(inplace=True)
    data["Date"] = pd.to_datetime(data["Date"])  # Säkerställ rätt datumformat

    # 🔹 Lista över numeriska kolumner
    numeric_cols = ["Open", "High", "Low", "Close", "Volume"]

    # 🔹 Kontrollera om alla nödvändiga kolumner finns
    missing_cols = [col for col in numeric_cols if col not in data.columns]
    if missing_cols:
        st.error(f"Saknade kolumner i datan: {missing_cols}")
        return None

    # 🔹 Konvertera numeriska kolumner och fyll NaN med 0
    for col in numeric_cols:
        data[col] = pd.to_numeric(data[col], errors="coerce").fillna(0)

    # 🔹 Beräkna MA20
    data["MA20"] = data["Close"].rolling(window=20).mean()

    # 🔹 Identifiera cykeltoppar och bottnar (med filtrering)
    data["Cycle Peak"] = data["High"][
        (data["High"] == data["High"].rolling(50, center=True).max())
    ].where(data["Close"] > data["MA20"])  # Endast toppar över MA20

    data["Cycle Bottom"] = data["Low"][
        (data["Low"] == data["Low"].rolling(50, center=True).min())
    ].where(data["Close"] < data["MA20"])  # Endast bottnar under MA20

    return data.dropna(subset=["Close"])  # Ta bort rader med NaN i Close

# 🔹 Funktion för att skapa candlestick-grafen
def plot_candlestick_chart(data):
    if data is None or data.empty:
        st.error("Ingen data tillgänglig för att skapa grafen.")
        return go.Figure()

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
    st.markdown("# 📊 Market Sentiment")

    # 🔹 Hämta data
    data = fetch_data()

    if data is None:
        st.error("Ingen data tillgänglig. Kontrollera felmeddelanden ovan.")
        return

    # 🔹 Debugging: Visa första 5 raderna av datan
    st.write("### Debug: Data Preview (första 5 raderna)")
    st.dataframe(data.head())

    # 🔹 Visa Candlestick-grafen
    st.plotly_chart(plot_candlestick_chart(data), use_container_width=True)
