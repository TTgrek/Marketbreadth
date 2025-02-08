import dash
from dash import dcc, html
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
from dash_resizable import Resizable  # Tredjepartskomponent för resizable containers

def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    data.reset_index(inplace=True)
    # Hantera MultiIndex om nödvändigt
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    # Beräkna MA20 (20-dagars glidande medelvärde)
    data["MA20"] = data["Close"].rolling(window=20).mean()
    # Beräkna Cycle Peak (cykeltopp) och Cycle Bottom (cykelbotten)
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
    return data

# Hämta data (global variabel)
data = fetch_data()

def create_candlestick_chart(data):
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
    
    # MA20-linje (tunn linje)
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        line=dict(color="blue", width=1),
        name="MA20"
    ))
    
    # Cycle Top – röda trianglar
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Peak"],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        name="Cycle Peak"
    ))
    
    # Cycle Bottom – gröna trianglar
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
        dragmode="pan",
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

# Här definierar vi layouten – vi omsluter grafen med Resizable
layout = html.Div([
    html.H1("Market Sentiment", style={"textAlign": "center"}),
    Resizable(
        id="resizable-graph-container",
        children=[
            dcc.Graph(
                id="candlestick-graph",
                figure=create_candlestick_chart(data),
                config={
                    'displayModeBar': True,
                    'scrollZoom': True,
                    'doubleClick': 'reset'
                },
                style={"width": "100%", "height": "100%"}  # Grafen fyller containern
            )
        ],
        style={"width": "80%", "margin": "auto", "border": "1px solid #ccc"},
        # Inställningar för resizable (endast vertikal resize aktiverat)
        resizableProps={
            "minHeight": 500,
            "maxHeight": 1200,
            "defaultHeight": 800,
            "defaultWidth": 800,
            "lockAspectRatio": False,
            # Aktivera endast nedre kant för att ändra höjden
            "enable": {
                "top": False,
                "right": False,
                "bottom": True,
                "left": False,
                "topRight": False,
                "bottomRight": True,
                "bottomLeft": True,
                "topLeft": False
            }
        }
    )
])
