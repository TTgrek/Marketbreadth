import dash
from dash import dcc, html
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go

#############################
# Data & Preprocessing
#############################

def fetch_data():
    ticker = "QQQ"
    # Hämtar data för perioden 20242-01-01 till 2025-12-31 (anpassa vid behov)
    data = yf.download(ticker, start="2022-01-01", end="2025-12-31")
    data.reset_index(inplace=True)
    
    # Om datan har MultiIndex plattas den ut
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    
    # Beräkna MA200 för långsiktig trendbedömning
    data["MA200"] = data["Close"].rolling(window=200).mean()
    # Beräkna MA20 för kortsiktiga signaler
    data["MA20"] = data["Close"].rolling(window=20).mean()
    # Beräkna relativ avvikelse (absolut procentuell skillnad mellan Close och MA20)
    data["Deviation"] = np.where(data["MA20"].notna(),
                                 abs(data["Close"] - data["MA20"]) / data["MA20"],
                                 np.nan)
    # Långsiktig trend: bull om Close >= MA200, annars bear
    data["LongTermTrend"] = np.where(data["Close"] >= data["MA200"], "bull", "bear")
    return data

def process_market_phase(data):
    # Tröskelvärden för att bekräfta fasen
    MIN_CONFIRMED_DAYS = 6    # Signal måste vara konsekvent i minst 6 dagar
    THRESHOLD = 0.02          # Minsta avvikelse från MA20 (2%)

    # Skapa nya kolumner
    data["MarketPhase"] = None   # "uptrend", "downtrend", "choppy" eller "undefined"
    data["CycleDay"] = 0         # Antal dagar i den aktuella fasen
    data["CycleEvent"] = None    # "top" (vid uptrend) eller "bottom" (vid downtrend)
    # Här skapar vi även de saknade kolumnerna för att spara det faktiska Close-värdet vid vändpunkten
    data["Cycle Top"] = np.nan
    data["Cycle Bottom"] = np.nan

    current_phase = None
    phase_start_index = None

    for i, row in data.iterrows():
        if pd.isna(row["MA20"]) or pd.isna(row["Deviation"]):
            data.at[i, "MarketPhase"] = "undefined"
            data.at[i, "CycleDay"] = 0
            data.at[i, "CycleEvent"] = None
            continue

        if row["Close"] > row["MA20"] and row["Deviation"] >= THRESHOLD:
            signal = "uptrend"
        elif row["Close"] < row["MA20"] and row["Deviation"] >= THRESHOLD:
            signal = "downtrend"
        else:
            signal = "choppy"

        if current_phase is None:
            current_phase = signal
            phase_start_index = i
            data.at[i, "MarketPhase"] = current_phase
            data.at[i, "CycleDay"] = 1
        else:
            if signal == current_phase:
                data.at[i, "MarketPhase"] = current_phase
                data.at[i, "CycleDay"] = i - phase_start_index + 1
            else:
                duration = i - phase_start_index
                if duration < MIN_CONFIRMED_DAYS:
                    current_phase = "choppy"
                    data.at[i, "MarketPhase"] = current_phase
                    data.at[i, "CycleDay"] = duration + 1
                else:
                    phase_data = data.loc[phase_start_index:i-1]
                    if current_phase == "uptrend":
                        idx = phase_data["Close"].idxmax()
                        data.at[idx, "CycleEvent"] = "top"
                        data.at[idx, "Cycle Top"] = data.at[idx, "Close"]
                    elif current_phase == "downtrend":
                        idx = phase_data["Close"].idxmin()
                        data.at[idx, "CycleEvent"] = "bottom"
                        data.at[idx, "Cycle Bottom"] = data.at[idx, "Close"]
                    current_phase = signal
                    phase_start_index = i
                    data.at[i, "MarketPhase"] = current_phase
                    data.at[i, "CycleDay"] = 1
    return data

# Hämta och processa data
data = fetch_data()
data = process_market_phase(data)

#######################################
# Visualization: Candlestick Chart med fasmarkeringar
#######################################

def create_candlestick_chart(data):
    fig = go.Figure()
    
    # Skapa en lista med egen hovertext för candlesticks (visar datum och Close)
    hover_text = [
        f"Date: {d.strftime('%Y-%m-%d')}<br>Close: {c:.2f}"
        for d, c in zip(data["Date"], data["Close"])
    ]
    
    # Lägg till candlestick-spår
    fig.add_trace(go.Candlestick(
        x=data["Date"],
        open=data["Open"],
        high=data["High"],
        low=data["Low"],
        close=data["Close"],
        increasing_line_color="green",
        decreasing_line_color="red",
        name="Candlesticks",
        hovertext=hover_text,
        hoverinfo="text"
    ))
    
    # Lägg till MA20-linje
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        line=dict(color="blue", width=1),
        name="MA20",
        hovertemplate="MA20: %{y:.2f}<extra></extra>"
    ))
    
    # Lägg till Cycle Top och Cycle Bottom marker
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Top"],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        name="Cycle Top",
        hovertemplate="Cycle Top: %{y:.2f}<extra></extra>"
    ))
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Bottom"],
        mode="markers",
        marker=dict(symbol="triangle-up", size=10, color="green"),
        name="Cycle Bottom",
        hovertemplate="Cycle Bottom: %{y:.2f}<extra></extra>"
    ))
    
    # Lägg till bakgrundsmarkeringar (vrects) för de olika marknadsfaserna
    data["PhaseGroup"] = (data["MarketPhase"] != data["MarketPhase"].shift()).cumsum()
    for _, group in data.groupby("PhaseGroup"):
        phase = group["MarketPhase"].iloc[0]
        start_date = group["Date"].iloc[0]
        end_date = group["Date"].iloc[-1]
        if phase == "uptrend":
            color = "rgba(144,238,144,0.5)"   # ljusgrön med hög opacitet
        elif phase == "downtrend":
            color = "rgba(255,182,193,0.5)"   # ljusröd med hög opacitet
        elif phase == "choppy":
            color = "rgba(211,211,211,0.5)"   # ljusgrå med hög opacitet
        else:
            color = "rgba(255,255,255,0)"
        fig.add_vrect(
            x0=start_date, x1=end_date,
            fillcolor=color, opacity=0.5, layer="below", line_width=0
        )
    
    # Lägg till annotation med aktuell fas och CycleDay
    latest = data.iloc[-1]
    annotation_text = (
        f"Phase: {latest['MarketPhase']}<br>"
        f"CycleDay: {latest['CycleDay']}<br>"
        f"Event: {latest['CycleEvent'] if pd.notna(latest['CycleEvent']) else ''}"
    )
    
    fig.update_layout(
        title="Market Cycle - QQQ",
        xaxis_title="Date",
        yaxis_title="Price",
        dragmode="pan",
        hovermode="x",  # Visar en vertikal linje (crosshair) vid hover
        template="plotly_white",
        xaxis=dict(
            rangeslider_visible=False,  # Ta bort rangeslider
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1m", step="month", stepmode="backward"),
                    dict(count=3, label="3m", step="month", stepmode="backward"),
                    dict(count=6, label="6m", step="month", stepmode="backward"),
                    dict(count=1, label="YTD", step="year", stepmode="todate"),
                    dict(count=1, label="1y", step="year", stepmode="backward"),
                    dict(step="all")
                ]
            )
        ),
        annotations=[
            {
                "xref": "paper",
                "yref": "paper",
                "x": 1,
                "y": 1,
                "xanchor": "right",
                "yanchor": "top",
                "text": annotation_text,
                "font": {"size": 12, "color": "black"},
                "bgcolor": "white",
                "bordercolor": "black",
                "borderwidth": 1
            }
        ]
    )
    return fig
def get_market_trend():
    """
    Analyserar indextrenden och returnerar en poäng mellan 0-30.
    - Använder SMA50, SMA200 och prisets position relativt dessa.
    - Trendpoäng baseras på hur starkt index befinner sig i en uppåtgående trend.
    """
    import yfinance as yf

    # 🔹 Hämta SPY som proxy för marknaden
    spy = yf.download("SPY", period="6mo", interval="1d")["Close"]

    if spy.empty:
        return 0  # Om datan saknas, returnera 0 poäng

    # 🔹 Beräkna glidande medelvärden
    sma50 = spy.rolling(window=50).mean().iloc[-1]
    sma200 = spy.rolling(window=200).mean().iloc[-1]
    price = spy.iloc[-1]

    # 🔹 Poängsystem baserat på SMA och pris
    score = 0
    if price > sma50:
        score += 10  # Priset över SMA50 → stark trend
    if price > sma200:
        score += 10  # Priset över SMA200 → långsiktig bulltrend
    if sma50 > sma200:
        score += 10  # SMA50 över SMA200 → Golden Cross = stark trend

    return score

# För visualisering: skapa figuren
candlestick_chart = create_candlestick_chart(data)
layout = html.Div([
    html.H1("Market Sentiment", style={"textAlign": "center"}),
    dcc.Graph(id="cycle-chart", figure=candlestick_chart)
])
