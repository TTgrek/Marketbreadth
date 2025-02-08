import dash
from dash import dcc, html
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
from dash_extensions import EventListener  # Lyssnar på DOM-händelser

def fetch_data():
    ticker = "QQQ"
    data = yf.download(ticker, start="1999-03-10")
    data.reset_index(inplace=True)
    
    # Platta ut MultiIndex om det behövs
    if isinstance(data.columns, pd.MultiIndex):
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
    
    # Beräkna MA20 (20-dagars glidande medelvärde)
    data["MA20"] = data["Close"].rolling(window=20).mean()
    
    # Initiera kolumner för Cycle Bottom och Cycle Top
    data["Cycle Bottom"] = np.nan
    data["Cycle Top"] = np.nan

    # Tröskelvärden för att undvika "choppy" marknad
    MIN_DURATION = 3      # Minsta antal dagar som perioden måste pågå
    MIN_DEVIATION = 0.01  # Minsta relativa avvikelse (exempelvis 1 %)

    # Variabler för perioder under MA20 (potentiell botten)
    in_below = False
    min_price = None
    below_start_index = None

    # Variabler för perioder över MA20 (potentiell topp)
    in_above = False
    max_price = None
    above_start_index = None

    # Variabel för att hålla reda på senaste vändpunkten: "top" eller "bottom"
    last_turning_type = None

    # Iterera genom datan (förutsatt att data är sorterad efter datum)
    for i, row in data.iterrows():
        # Hoppa över rader där MA20 inte är beräknat (t.ex. de första dagarna)
        if pd.isna(row["MA20"]):
            continue
        
        close = row["Close"]
        ma = row["MA20"]
        
        # --- Hantera period då priset ligger UNDER MA20 (potentiell botten) ---
        if close < ma:
            # Starta en ny underperiod endast om den senaste vändpunkten INTE redan var en botten
            if not in_below and last_turning_type != "bottom":
                in_below = True
                min_price = close
                below_start_index = i
            elif in_below:
                if close < min_price:
                    min_price = close
        else:
            # Vi lämnar en period under MA20
            if in_below:
                if (i - below_start_index) >= MIN_DURATION:
                    # Endast om avvikelsen från MA20 är tillräcklig
                    if (ma - min_price) / ma >= MIN_DEVIATION:
                        # Registrera botten bara om den senaste vändpunkten inte redan var en botten
                        if last_turning_type != "bottom":
                            data.at[i, "Cycle Bottom"] = min_price
                            last_turning_type = "bottom"
                in_below = False
                min_price = None
                below_start_index = None
        
        # --- Hantera period då priset ligger ÖVER MA20 (potentiell topp) ---
        if close > ma:
            # Starta en ny överperiod endast om den senaste vändpunkten INTE redan var en topp
            if not in_above and last_turning_type != "top":
                in_above = True
                max_price = close
                above_start_index = i
            elif in_above:
                if close > max_price:
                    max_price = close
        else:
            # Vi lämnar en period över MA20
            if in_above:
                if (i - above_start_index) >= MIN_DURATION:
                    if (max_price - ma) / ma >= MIN_DEVIATION:
                        # Registrera topp bara om den senaste vändpunkten inte redan var en topp
                        if last_turning_type != "top":
                            data.at[i, "Cycle Top"] = max_price
                            last_turning_type = "top"
                in_above = False
                max_price = None
                above_start_index = None
                
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
    
    # Cycle Bottom – markeras med gröna trianglar
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Bottom"],
        mode="markers",
        marker=dict(symbol="triangle-up", size=10, color="green"),
        name="Cycle Bottom"
    ))
    
    # Cycle Top – markeras med röda trianglar
    fig.add_trace(go.Scatter(
        x=data["Date"],
        y=data["Cycle Top"],
        mode="markers",
        marker=dict(symbol="triangle-down", size=10, color="red"),
        name="Cycle Top"
    ))
    
    # --- Bearbeta vändpunkterna för att "ta ut" tidigare vändpunkter ---
    # Gruppera på varandra följande vändpunkter av samma typ och behåll den sista
    turning_points = data[(~data["Cycle Bottom"].isna()) | (~data["Cycle Top"].isna())].copy()
    if not turning_points.empty:
        turning_points["Type"] = turning_points.apply(
            lambda row: "bottom" if not pd.isna(row["Cycle Bottom"]) else "top", axis=1)
        turning_points["Group"] = (turning_points["Type"] != turning_points["Type"].shift()).cumsum()
        filtered_tp = turning_points.groupby("Group").last().reset_index()
        
        # Beräkna cykellängder med de filtrerade vändpunkterna
        tp_list = filtered_tp
        up_cycles = []   # Uppgångscykel: från botten till nästa topp
        down_cycles = [] # Nedgångscykel: från topp till nästa botten
        for i in range(len(tp_list) - 1):
            current_type = tp_list.loc[i, "Type"]
            next_type = tp_list.loc[i+1, "Type"]
            if current_type == "bottom" and next_type == "top":
                cycle_length = (tp_list.loc[i+1, "Date"] - tp_list.loc[i, "Date"]).days
                up_cycles.append(cycle_length)
            elif current_type == "top" and next_type == "bottom":
                cycle_length = (tp_list.loc[i+1, "Date"] - tp_list.loc[i, "Date"]).days
                down_cycles.append(cycle_length)
                
        avg_up = np.mean(up_cycles) if up_cycles else None
        avg_down = np.mean(down_cycles) if down_cycles else None
        
        # Aktuell cykeldag: antal dagar sedan den senaste vändpunkten (enligt de filtrerade)
        last_turning = tp_list.iloc[-1]
        current_date = data.iloc[-1]["Date"]
        current_cycle_day = (current_date - last_turning["Date"]).days + 1
    else:
        avg_up = avg_down = current_cycle_day = None

    annotation_text = (
        "Snittcykel Uppgång: " + (f"{avg_up:.1f} dagar" if avg_up is not None else "N/A") +
        ", Nedgång: " + (f"{avg_down:.1f} dagar" if avg_down is not None else "N/A") +
        "<br>Dag i cykeln: " + (f"{current_cycle_day}" if current_cycle_day is not None else "N/A")
    )
    
    fig.update_layout(
        title="Market Sentiment - QQQ",
        xaxis_title="Datum",
        yaxis_title="Pris",
        dragmode="pan",
        template="plotly_white",
        xaxis=dict(
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

# Startvärde på grafens höjd (i pixlar)
initial_height = 800

# Layout med EventListener för interaktiv höjdjustering
layout = html.Div([
    html.H1("Market Sentiment", style={"textAlign": "center"}),
    dcc.Store(id="resize-store", data={"resizing": False, "startY": None, "startHeight": initial_height}),
    EventListener(
        id="resizable-container",
        events=[
            {"event": "mousedown"},
            {"event": "mousemove"},
            {"event": "mouseup"}
        ],
        children=html.Div(
            id="graph-container",
            children=[
                dcc.Graph(
                    id="candlestick-graph",
                    figure=create_candlestick_chart(data),
                    config={
                        "displayModeBar": True,
                        "scrollZoom": True,
                        "doubleClick": "reset"
                    },
                    style={"width": "100%", "height": "100%"}
                )
            ],
            style={
                "height": f"{initial_height}px",
                "width": "80%",
                "margin": "auto",
                "border": "1px solid #ccc",
                "position": "relative"
            }
        )
    )
])
