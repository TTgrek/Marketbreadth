# modules/market_sentiment.py

import dash
from dash import dcc, html
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np

def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    data.reset_index(inplace=True)
    # Hantera MultiIndex om det behövs
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    # Beräkna MA20 (20-dagars glidande medelvärde)
    data["MA20"] = data["Close"].rolling(window=20).mean()
    return data

# Hämta data en gång (global variabel)
data = fetch_data()

def create_candlestick_chart(data, graph_height=800):
    fig = go.Figure()
    
    # Candlestick-spår
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
        name="Candlesticks"
    ))
    
    # MA20-linje (tunnare linje)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        line=dict(color="blue", width=1),
        name="MA20"
    ))
    
    fig.update_layout(
        title="Market Sentiment - QQQ",
        xaxis_title="Datum",
        yaxis_title="Pris",
        dragmode="pan",
        height=graph_height,
        template="plotly_white",
        xaxis=dict(
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
    )
    return fig

# Definiera layout med en graf och en slider för att ändra grafens höjd
layout = html.Div([
    html.H1("Market Sentiment", style={"textAlign": "center"}),
    dcc.Graph(
        id='candlestick-graph',
        config={
            'displayModeBar': True,
            'scrollZoom': True,
            'doubleClick': 'reset'
        }
    ),
    html.Div([
        html.Label("Justera grafens höjd (pixlar):"),
        dcc.Slider(
            id='height-slider',
            min=500,
            max=1200,
            step=50,
            value=800,
            marks={i: str(i) for i in range(500, 1250, 50)}
        )
    ], style={'width': '80%', 'margin': 'auto', 'padding': '20px 0'})
])
