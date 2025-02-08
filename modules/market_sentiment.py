from dash import dcc, html
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np

# 🔹 Hämta data
def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    data.reset_index(inplace=True)
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["Cycle Peak"] = np.where((data["High"] == data["High"].rolling(50, center=True).max()), data["High"], np.nan)
    data["Cycle Bottom"] = np.where((data["Low"] == data["Low"].rolling(50, center=True).min()), data["Low"], np.nan)
    return data.dropna(subset=["Close"])

# 🔹 Hämta data
data = fetch_data()

# 🔹 Candlestick-graf
fig = go.Figure()
fig.add_trace(go.Candlestick(
    x=data["Date"], open=data["Open"], high=data["High"], low=data["Low"], close=data["Close"],
    name="Candlestick", increasing_line_color="green", decreasing_line_color="red"
))
fig.add_trace(go.Scatter(x=data["Date"], y=data["MA20"], mode="lines", name="MA20", line=dict(color="blue", width=1.5)))
fig.add_trace(go.Scatter(x=data["Date"], y=data["Cycle Peak"], mode="markers", name="Topp",
                         marker=dict(color="red", symbol="triangle-down", size=10)))
fig.add_trace(go.Scatter(x=data["Date"], y=data["Cycle Bottom"], mode="markers", name="Botten",
                         marker=dict(color="green", symbol="triangle-up", size=10)))
fig.update_layout(title="QQQ Candlestick Chart med MA20 & Cykler", xaxis_rangeslider_visible=False, template="plotly_white")

# 🔹 Layout för denna modul
layout = html.Div([
    html.H3("Market Sentiment"),
    dcc.Graph(figure=fig)
])
