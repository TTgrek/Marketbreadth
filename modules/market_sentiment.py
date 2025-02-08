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

        # Återställ index så att datumet blir en kolumn
        data.reset_index(inplace=True)
        print("Kolumner efter reset_index:", list(data.columns))

        # Om data har MultiIndex, platta ut den
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = [
                col[1] if isinstance(col, tuple) and col[1] != "" else col[0]
                for col in data.columns
            ]
        print("Kolumner efter eventuell plattning:", list(data.columns))

        # Om det behövs, justera kolumnnamnen med ett rename_dict
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

        # Kontrollera att "Close" finns i datan
        if "Close" not in data.columns:
            print(f"❌ 'Close' saknas i datan! Här är kolumnerna: {list(data.columns)}")
            return pd.DataFrame()

        # Lägg till indikatorer
        data["MA20"] = data["Close"].rolling(window=20).mean()
        data["Cycle Peak"] = np.where(
            data["High"] == data["High"].rolling(window=50, center=True).max(),
            data["High"],
            np.nan
        )
        data["Cycle Bottom"] = np.where(
            data["Low"] == data["Low"].rolling(window=50, center=True).min(),
            data["Low"],
            np.nan
        )

        # Ta bort rader där "Close" är NaN (om det finns några)
        return data.dropna(subset=["Close"])

    except Exception as e:
        print(f"⚠️ Fel vid hämtning av data: {e}")
        return pd.DataFrame()

# 🔹 Hämta data
data = fetch_data()
print("Första raderna i data:\n", data.head())

# 🔹 Funktion för att skapa candlestick-graf med Plotly
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
