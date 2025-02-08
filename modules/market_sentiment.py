import yfinance as yf
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objects as go

# 🔹 Hämta data från Yahoo Finance och fixa formatet
def fetch_data():
    ticker = "QQQ"
    try:
        # Hämta data
        data = yf.download(ticker, start="1999-03-10")
        if data.empty:
            print("❌ Ingen data hämtades från Yahoo Finance!")
            return pd.DataFrame()

        data.reset_index(inplace=True)

        # 🔹 Fixar problem med extra headers från Yahoo Finance
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(0)

        # 🔹 Rätta kolumnnamn om de har blivit fel
        correct_columns = ["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]
        if len(data.columns) == len(correct_columns):
            data.columns = correct_columns

        # Kontrollera om "Close" finns
        if "Close" not in data.columns:
            print("❌ 'Close' saknas i datan! Här är kolumnerna:", data.columns)
            return pd.DataFrame()

        # Lägg till indikatorer
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["Cycle Peak"] = np.where((data["High"] == data["High"].rolling(50, center=True).max()), data["High"], np.nan)
        data["Cycle Bottom"] = np.where((data["Low"] == data["Low"].rolling(50, center=True).min()), data["Low"], np.nan)

        return data.dropna(subset=["Close"])  # Ta bort eventuella NaN-värden

    except Exception as e:
        print(f"⚠️ Fel vid hämtning av data: {e}")
        return pd.DataFrame()

# 🔹 Hämta data
data = fetch_data()

# 🔹 Skapa en candlestick-graf med Plotly
def create_candlestick_chart(data):
    fig = go.Figure()

    # Candlestick-graf
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        name="Candlesticks",
        increasing_line_color="green",
        decreasing_line_color="red"
    ))

    # MA20-linje
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        line=dict(color="blue", width=2),
        name="MA20"
    ))

    # Cykeltoppar (Röda trianglar)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Peak"],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        name="Cycle Peak"
    ))

    # Cykelbottnar (Gröna trianglar)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Bottom"],
        mode="markers",
        marker=dict(symbol="triangle-up", size=10, color="green"),
        name="Cycle Bottom"
    ))

    fig.update_layout(
        title="Market Sentiment - QQQ",
        xaxis_title="Datum",
        yaxis_title="Pris",
        xaxis_rangeslider_visible=False,
        template="plotly_white"
    )

    return fig

# 🔹 Skapa layout för Dash
layout = html.Div([
    html.H1("Market Sentiment", style={"textAlign": "center"}),
    dcc.Graph(figure=create_candlestick_chart(data))
])
