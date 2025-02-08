import yfinance as yf
import pandas as pd
import numpy as np
import dash
from dash import dcc, html
import plotly.graph_objects as go

# 🔹 Funktion för att hämta och förbereda data från Yahoo Finance
def fetch_data():
    ticker = "QQQ"
    try:
        # Hämta data från Yahoo Finance
        data = yf.download(ticker, start="1999-03-10")
        if data.empty:
            print("❌ Ingen data hämtades från Yahoo Finance!")
            return pd.DataFrame()

        data.reset_index(inplace=True)

        # 🔹 Om kolumnnamnen är MultiIndex, ta bara den sista nivån
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [col[1] if col[1] else col[0] for col in data.columns]

        # 🔹 Fixar felaktiga kolumnnamn (t.ex. om de bara innehåller "QQQ")
        rename_dict = {
            "Date": "Date",
            "Open": "Open",
            "High": "High",
            "Low": "Low",
            "Close": "Close",
            "Adj Close": "Adj Close",
            "Volume": "Volume"
        }
        data.rename(columns=rename_dict, inplace=True)

        # Kontrollera om "Close" finns, annars printa ut vilka kolumner som finns
        if "Close" not in data.columns:
            print(f"❌ 'Close' saknas i datan! Här är kolumnerna: {list(data.columns)}")
            return pd.DataFrame()

        # Lägg till indikatorer
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["Cycle Peak"] = np.where(
            (data["High"] == data["High"].rolling(50, center=True).max()), 
            data["High"], 
            np.nan
        )
        data["Cycle Bottom"] = np.where(
            (data["Low"] == data["Low"].rolling(50, center=True).min()), 
            data["Low"], 
            np.nan
        )

        return data.dropna(subset=["Close"])  # Ta bort eventuella NaN-värden

    except Exception as e:
        print(f"⚠️ Fel vid hämtning av data: {e}")
        return pd.DataFrame()

# 🔹 Hämta data
data = fetch_data()

# 🔹 Funktion för att skapa candlestick-graf
def create_candlestick_chart(data):
    if data.empty:
        return go.Figure()

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
