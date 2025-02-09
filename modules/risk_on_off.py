import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import pandas_market_calendars as mcal

#############################
# MARKNADSSENTIMENT - DATA & PROCESSING
#############################
def fetch_data():
    ticker = "QQQ"
    # Hämtar data för perioden 2024-01-01 till 2025-12-31 (justera vid behov)
    data = yf.download(ticker, start="2024-01-01", end="2025-12-31")
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
    # Kolumner för att spara Close-värde vid vändpunkter
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

def calculate_market_sentiment_score():
    """
    Baserat på den processade marknadsfasen returneras ett sentimentpoäng.
    Exempelvis:
      - Om senaste fasen är "uptrend" och långsiktigt trend är "bull" → hög sentiment (30)
      - Om "downtrend" och "bear" → låg sentiment (0)
      - Annars → medelhögt (15)
    """
    data = fetch_data()
    data = process_market_phase(data)
    latest = data.iloc[-1]
    if latest["MarketPhase"] == "uptrend" and latest["LongTermTrend"] == "bull":
        sentiment = 30
    elif latest["MarketPhase"] == "downtrend" and latest["LongTermTrend"] == "bear":
        sentiment = 0
    else:
        sentiment = 15
    return sentiment

#############################
# RISK ON/OFF INDICATOR
#############################

# Hämta NYSE-handelskalender (används vid behov)
nyse = mcal.get_calendar("NYSE")

# Tidsintervaller för eventuellt framtida användning
INTERVAL_DAYS = {
    "1D": 1,
    "1V": 5,    # 1 vecka = 5 handelsdagar
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252
}

# Layout för Risk On/Off-modulen
layout = html.Div([
    html.H1("Risk On/Off Indicator", style={"textAlign": "center"}),
    html.Div([
        html.Button("1D", id="risk-btn-1D", n_clicks=0, style={"margin": "5px"}),
        html.Button("1V", id="risk-btn-1V", n_clicks=0, style={"margin": "5px"}),
        html.Button("1M", id="risk-btn-1M", n_clicks=0, style={"margin": "5px"}),
        html.Button("3M", id="risk-btn-3M", n_clicks=0, style={"margin": "5px"}),
        html.Button("6M", id="risk-btn-6M", n_clicks=0, style={"margin": "5px"}),
        html.Button("12M", id="risk-btn-12M", n_clicks=0, style={"margin": "5px"})
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"}),
    html.H3(id="selected-interval-risk", style={"textAlign": "center"}),
    dcc.Loading(
        id="loading-risk-graph",
        type="default",
        children=[dcc.Graph(id="risk-graph")]
    ),
    html.Div(id="risk-indicator", style={"textAlign": "center", "fontSize": "24px", "marginTop": "20px", "padding": "10px", "color": "white"})
])

# Funktioner för att hämta marknadsdata som bidrar till riskbedömningen
def fetch_qqq_trend():
    qqq = yf.download("QQQ", period="1y", auto_adjust=True)
    if qqq.empty:
        return None, None, None
    close_data = qqq["Close"]
    if isinstance(close_data, pd.DataFrame):
        close_data = close_data.squeeze()
    ma200 = close_data.rolling(window=200).mean()
    latest_price = close_data.iloc[-1]
    latest_ma200 = ma200.iloc[-1]
    qqq["MA200"] = ma200
    return qqq, latest_price, latest_ma200

def fetch_vix():
    vix = yf.download("^VIX", period="1y", auto_adjust=True)
    if vix.empty:
        return None
    return vix["Close"]

def calculate_nh_nl_score():
    spy = yf.download("SPY", period="1mo", auto_adjust=True)
    if spy.empty:
        return 0
    close_prices = pd.to_numeric(spy["Close"].squeeze(), errors="coerce").dropna()
    new_highs = 0
    new_lows = 0
    current_max = -float('inf')
    current_min = float('inf')
    for price in close_prices:
        if price > current_max:
            new_highs += 1
            current_max = price
        if price < current_min:
            new_lows += 1
            current_min = price
    return 1 if new_highs > new_lows else 0

# Callback: Uppdatera riskindikator, risk-tidsserie och visa graf
def register_callbacks(app):
    @app.callback(
        [Output("risk-graph", "figure"),
         Output("selected-interval-risk", "children"),
         Output("risk-indicator", "children"),
         Output("risk-indicator", "style")],
        [Input("risk-btn-1D", "n_clicks"),
         Input("risk-btn-1V", "n_clicks"),
         Input("risk-btn-1M", "n_clicks"),
         Input("risk-btn-3M", "n_clicks"),
         Input("risk-btn-6M", "n_clicks"),
         Input("risk-btn-12M", "n_clicks")]
    )
    def update_risk_indicator(n1, n1V, n1M, n3M, n6M, n12M):
        ctx = dash.callback_context
        if not ctx.triggered:
            interval = "6M"
        else:
            interval = ctx.triggered[0]["prop_id"].split(".")[0].replace("risk-btn-", "")
        selected_text = f"Valt intervall: {interval}"
        
        # Dynamisk risk-tidsserie: hämta QQQ-data och beräkna komponenter
        qqq = yf.download("QQQ", period="1y", auto_adjust=True)
        if qqq.empty:
            risk_ts = None
        else:
            qqq["MA200"] = qqq["Close"].rolling(window=200).mean()
            # QQQ-komponenten: 1 om Close > MA200, annars 0
            comp = (qqq["Close"].squeeze().values > qqq["MA200"].squeeze().values)
            qqq["QQQ_component"] = pd.Series(comp, index=qqq.index).astype(int)
            
            vix = fetch_vix()
            if vix is None:
                vix_aligned = pd.Series(0, index=qqq.index)
            else:
                vix_aligned = vix.reindex(qqq.index, method="ffill")
            vix_threshold = 20
            qqq["VIX_component"] = (vix_aligned < vix_threshold).astype(int)
            
            spy_component = calculate_nh_nl_score()
            qqq["SPY_component"] = spy_component  # Konstant över perioden
            
            risk_ts = qqq["QQQ_component"] + qqq["VIX_component"] + qqq["SPY_component"]
            risk_ts = risk_ts.fillna(0)
        
        if risk_ts is None or risk_ts.empty:
            fig = px.line(title="Ingen riskdata")
            dynamic_latest = 0
            dynamic_avg = 0
        else:
            fig = px.line(risk_ts.reset_index(), x="Date", y=0,
                          title="Risk Score över Tid", labels={"Date": "Datum", 0: "Risk Score"})
            dynamic_latest = risk_ts.iloc[-1]
            dynamic_avg = risk_ts.mean()
        
        # Använd det beräknade marknadssentimentet (baserat på dina funktioner)
        market_sentiment_score = calculate_market_sentiment_score()  # t.ex. 30 vid uptrend, 0 vid downtrend
        
        # Övriga konstanter (du kan själv justera dessa)
        breakout_score = 20              # 0–20
        relative_strength_score = 10     # 0–10
        sma50_score = 10                 # 0–10
        sma_trend_score = 15             # 0–15
        sector_score = 10                # 0–10
        
        constant_offset = (market_sentiment_score + breakout_score +
                           relative_strength_score + sma50_score +
                           sma_trend_score + sector_score)
        
        latest_total_risk = dynamic_latest + constant_offset
        average_total_risk = dynamic_avg + constant_offset
        
        if latest_total_risk >= 80:
            risk_text = "Risk On: Invest Full"
            indicator_style = {"textAlign": "center", "fontSize": "24px", "marginTop": "20px",
                               "padding": "10px", "color": "white", "backgroundColor": "#006400"}
        elif latest_total_risk >= 50:
            risk_text = "Neutral: Moderate Exposure"
            indicator_style = {"textAlign": "center", "fontSize": "24px", "marginTop": "20px",
                               "padding": "10px", "color": "black", "backgroundColor": "#FFD700"}
        else:
            risk_text = "Risk Off: Hold Cash"
            indicator_style = {"textAlign": "center", "fontSize": "24px", "marginTop": "20px",
                               "padding": "10px", "color": "white", "backgroundColor": "#8B0000"}
        
        indicator_display = f"Total Risk: {latest_total_risk:.2f} (Avg: {average_total_risk:.2f}) => {risk_text}"
        
        return fig, selected_text, indicator_display, indicator_style

if __name__ == "__main__":
    app = dash.Dash(__name__)
    app.layout = layout
    register_callbacks(app)
    app.run_server(debug=True)
