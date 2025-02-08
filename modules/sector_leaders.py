import dash
from dash import dcc, html
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# 🔹 1. Definiera sektorerna och deras ETF:er
SECTOR_ETFS = {
    "Lithium & Battery Tech": "LIT",
    "Robotics & AI": "BOTZ",
    "Semiconductors": "SMH",
    "Technology": "XLK",
    "Rocket & Space": "ROKT",
    "Software": "XSW",
    "FANG Stocks": "FNGS",
    "Cybersecurity": "CIBR",
    "Cloud Computing": "SKYY",
    "Quantum Computing": "QTUM",
    "Telecom": "IYZ",
    "Space Exploration": "UFO",
    "Energy": "XLE",
    "Oil & Gas": "XOP",
    "Uranium": "URA",
    "Nuclear Energy": "URNM",
    "Battery Metals": "BATT",
    "Utilities": "XLU",
    "Clean Energy": "ICLN",
    "Oil Fund": "USO",
    "Insurance": "KIE",
    "Financials": "XLF",
    "Banks": "KBE",
    "Regional Banks": "KRE",
    "Real Estate": "XLRE",
    "Biotech": "IBB",
    "Genomics": "ARKG",
    "Healthcare": "XLV",
    "Homebuilders": "XHB",
    "Airlines": "JETS",
    "Transportation": "XTN",
    "Industrials": "XLI",
    "Aerospace & Defense": "ITA",
    "Copper": "COPX",
    "Steel": "SLX",
    "Gold Miners": "GDX",
    "Silver": "SLV",
    "Gold": "GLD",
    "China Tech": "CWEB",
    "China Internet": "KWEB",
    "China Large-Cap": "FXI",
    "Emerging Markets": "EEM",
    "Mexico": "EWW",
    "Argentina": "ARGT",
    "Brazil": "EWZ",
    "Cannabis": "MSOS",
    "Marijuana": "MJ",
    "Bitcoin Futures": "BITO",
    "Consumer Discretionary": "XLY",
    "Consumer Staples": "XLP",
    "Communications": "XLC",
    "Electric Vehicles": "KARS",
    "Autonomous & EV": "DRIV"
}

# 🔹 2. Hämta sektordata från Yahoo Finance
def fetch_sector_data():
    tickers = list(SECTOR_ETFS.values()) + ["QQQ", "SPY"]
    data = yf.download(tickers, period="6mo")["Adj Close"]
    returns = data.pct_change().dropna()
    cumulative_returns = (1 + returns).cumprod()  # Ackumulerad avkastning
    return cumulative_returns

# 🔹 3. Skapa en ranking-tabell
def create_sector_ranking_table(data):
    last_returns = data.iloc[-1] / data.iloc[0] - 1
    ranking = last_returns.sort_values(ascending=False).reset_index()
    ranking.columns = ["Ticker", "Performance"]
    ranking["Sector"] = ranking["Ticker"].map({v: k for k, v in SECTOR_ETFS.items()})
    return ranking.dropna()

# 🔹 4. Skapa en interaktiv sektor-graf
def create_sector_chart(data):
    fig = go.Figure()

    for sector, ticker in SECTOR_ETFS.items():
        fig.add_trace(go.Scatter(
            x=data.index,
            y=data[ticker],
            mode="lines",
            name=sector
        ))

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["QQQ"],
        mode="lines",
        line=dict(width=3, dash="dot", color="black"),
        name="QQQ (Benchmark)"
    ))

    fig.update_layout(
        title="Sektorutveckling jämfört med QQQ",
        xaxis_title="Datum",
        yaxis_title="Avkastning (%)",
        template="plotly_white",
        hovermode="x unified"
    )
    
    return fig

# 🔹 5. Hämta data och skapa visualiseringar
data = fetch_sector_data()
ranking_table = create_sector_ranking_table(data)
sector_chart = create_sector_chart(data)

# 🔹 6. Layout för sektormodulen
layout = html.Div([
    html.H1("Sector Leaders", style={"textAlign": "center"}),

    html.H3("Sektor-ranking senaste 6 månaderna"),
    html.Table([
        html.Thead(html.Tr([html.Th("Sector"), html.Th("Performance")]))] +
        [html.Tr([html.Td(row["Sector"]), html.Td(f"{row['Performance']:.2%}")])
         for _, row in ranking_table.iterrows()]
    ),

    html.H3("Sektorprestation jämfört med QQQ"),
    dcc.Graph(id="sector-chart", figure=sector_chart)
])
