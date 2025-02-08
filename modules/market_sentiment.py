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
    data = yf.download(ticker, start="1999-03-10", end="2025-12-31")
    data.reset_index(inplace=True)
    
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    
    data["MA200"] = data["Close"].rolling(window=200).mean()
    data["MA20"] = data["Close"].rolling(window=20).mean()
    data["Deviation"] = np.where(data["MA20"].notna(), abs(data["Close"] - data["MA20"]) / data["MA20"], np.nan)
    data["LongTermTrend"] = np.where(data["Close"] >= data["MA200"], "bull", "bear")
    return data

def process_market_phase(data):
    MIN_CONFIRMED_DAYS = 6    
    THRESHOLD = 0.02         

    data["MarketPhase"] = None   
    data["CycleDay"] = 0         
    data["CycleEvent"] = None    
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

data = fetch_data()
data = process_market_phase(data)

#############################
# Visualization: Candlestick Chart med fasmarkeringar
#############################

def create_candlestick_chart(data):
    fig = go.Figure()
    
    hover_text = [
        f"Date: {d.strftime('%Y-%m-%d')}<br>Close: {c:.2f}"
        for d, c in zip(data["Date"], data["Close"])
    ]
    
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
    
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["MA20"],
        mode="lines",
        line=dict(color="blue", width=1),
        name="MA20"
    ))
    
    fig.update_layout(
        title="Market Cycle - QQQ",
        xaxis_title="Date",
        yaxis_title="Price",
        dragmode="pan",
        template="plotly_dark",
        xaxis=dict(
            rangeslider_visible=False,
            type="linear",
            showgrid=False,
            showline=True,
            mirror=True,
            linecolor="white"
        ),
        yaxis=dict(
            showgrid=False,
            showline=True,
            mirror=True,
            linecolor="white"
        )
    )
    return fig

candlestick_chart = create_candlestick_chart(data)

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.H1("TradingView Styled QQQ Chart", style={"textAlign": "center", "color": "white"}),
    dcc.Graph(id="cycle-chart", figure=candlestick_chart, config={
        "scrollZoom": True, 
        "displayModeBar": True, 
        "modeBarButtonsToRemove": ["pan2d", "lasso2d"]
    })
])

if __name__ == "__main__":
    app.run_server(debug=True)
