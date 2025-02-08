import dash
from dash import dcc, html
import yfinance as yf
import pandas as pd
import plotly.express as px

# 🔹 Lista över sektorer/ETF:er
SECTOR_TICKERS = [
    "LIT", "TAN", "ARKK", "FINX", "BOTZ", "SMH", "XLK", "ROKT", "XSW",
    "FNGS", "CIBR", "SKYY", "QTUM", "IYZ", "UFO", "XLE", "XOP", "URA",
    "URNM", "BATT", "XLU", "ICLN", "USO", "KIE", "XLF", "KBE", "KRE",
    "IYR", "XLRE", "IBB", "ARKG", "XBI", "XLV", "ITB", "XHB", "JETS",
    "XTN", "IYT", "XLB", "XLI", "ITA", "COPX", "SLX", "GDX", "SLV",
    "GLD", "IAU", "CWEB", "KWEB", "FXI", "MCHI", "EWH", "EWJ", "EEM",
    "EWW", "ARGT", "ECH", "EWZ", "MSOS", "MJ", "BITO", "IYC", "XLP",
    "XLY", "KARS", "DRIV", "XLC"
]

# 🔹 Funktion för att hämta sektordata
def fetch_sector_data():
    print("📥 Hämtar sektordata från Yahoo Finance...")
    raw_data = yf.download(SECTOR_TICKERS, period="6mo")  # Hämta senaste 6 månaderna

    # Kontrollera om "Adj Close" finns, annars använd "Close"
    if "Adj Close" in raw_data:
        data = raw_data["Adj Close"]
    else:
        print("⚠️ 'Adj Close' saknas, använder 'Close' istället.")
        data = raw_data["Close"]

    # Omformatera data: Skapa en procentuell förändring och rangordna sektorer
    returns = data.pct_change().dropna()
    performance = returns.sum().sort_values(ascending=False).reset_index()
    performance.columns = ["Ticker", "Total Return"]
    
    return performance

# 🔹 Hämta data
sector_performance = fetch_sector_data()

# 🔹 Skapa layout och visualisering
def create_sector_performance_chart():
    fig = px.bar(
        sector_performance,
        x="Ticker",
        y="Total Return",
        text="Total Return",
        title="Sektorprestanda - Senaste 6 månaderna",
        color="Total Return",
        color_continuous_scale="bluered",
    )
    fig.update_traces(texttemplate="%{text:.2%}", textposition="outside")
    fig.update_layout(
        xaxis_title="Sektor/ETF",
        yaxis_title="Total Avkastning",
        yaxis_tickformat=".2%",
        template="plotly_white"
    )
    return fig

# 🔹 Layout för Dash-applikationen
layout = html.Div([
    html.H1("Sektorledare", style={"textAlign": "center"}),
    dcc.Graph(id="sector-performance-chart", figure=create_sector_performance_chart())
])
