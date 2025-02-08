import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
import pandas as pd
import plotly.express as px
import pandas_market_calendars as mcal  # För att få exakta handelsdagar

# Lista på ETF:er/sektorer att hämta
SECTOR_TICKERS = [
    "LIT", "TAN", "ARKK", "FINX", "BOTZ", "SMH", "XLK", "ROKT", "XSW", "FNGS",
    "CIBR", "SKYY", "QTUM", "IYZ", "UFO", "XLE", "XOP", "URA", "URNM", "BATT",
    "XLU", "ICLN", "USO", "KIE", "XLF", "KBE", "KRE", "IYR", "XLRE", "IBB",
    "ARKG", "XBI", "XLV", "ITB", "XHB", "JETS", "XTN", "IYT", "XLB", "XLI",
    "ITA", "COPX", "SLX", "GDX", "SLV", "GLD", "IAU", "CWEB", "KWEB", "FXI",
    "MCHI", "EWH", "EWJ", "EEM", "EWW", "ARGT", "ECH", "EWZ", "MSOS", "MJ",
    "BITO", "IYC", "XLP", "XLY", "KARS", "DRIV", "XLC"
]

# Handelsdagsintervall för olika perioder
INTERVAL_DAYS = {
    "1D": 1,
    "5D": 5,
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252
}

#############################
# Hämta sektordata
#############################

def fetch_sector_data(interval="6M"):
    print(f"\nHämtar sektordata för {interval} från Yahoo Finance...")

    # Beräkna exakta handelsdagar för NYSE/Nasdaq
    nyse = mcal.get_calendar("NYSE")
    today = pd.Timestamp.today().normalize()
    trading_days = nyse.valid_days(
        start_date=(today - pd.DateOffset(days=400)).strftime("%Y-%m-%d"),
        end_date=today.strftime("%Y-%m-%d")
    )
    
    if len(trading_days) < INTERVAL_DAYS[interval]:
        print("Otillräckligt med handelsdagar i datan!")
        return pd.DataFrame(columns=["Sector", "Return (%)"])
    
    start_date = pd.Timestamp(trading_days[-INTERVAL_DAYS[interval]]).tz_localize(None)
    print(f"Korrigerat startdatum för {interval}: {start_date}")

    # Hämta data från Yahoo Finance
    raw_data = yf.download(SECTOR_TICKERS, start=start_date.strftime("%Y-%m-%d"), end=today.strftime("%Y-%m-%d"))

    # Om "Adj Close" saknas, använd "Close"
    data = raw_data.get("Adj Close", raw_data.get("Close"))
    
    if data is None:
        print("Ingen giltig data hämtad!")
        return pd.DataFrame(columns=["Sector", "Return (%)"])

    # Ta bort rader med endast NaN
    data.dropna(how="all", inplace=True)

    # Hämta start- och slutpriser
    try:
        latest_prices = data.iloc[-1]
        nearest_start_date = data.index[data.index.get_indexer([start_date], method="nearest")][0]
        start_prices = data.loc[nearest_start_date]
    except KeyError:
        print("Startdatumet saknas i data! Tar närmaste föregående dag.")
        start_prices = data.iloc[0]
    
    # Debugging - Skriv ut start- och slutpriser för validering
    print("\nStart- och slutpriser för de första 10 tickers:")
    for ticker in SECTOR_TICKERS[:10]:
        if ticker in start_prices and ticker in latest_prices:
            print(f"{ticker}: Start={start_prices[ticker]:.2f}, Slut={latest_prices[ticker]:.2f}")
    
    # Beräkna avkastning korrekt
    returns = ((latest_prices - start_prices) / start_prices) * 100
    
    # Skapa DataFrame med sortering
    sector_data = pd.DataFrame({"Sector": returns.index, "Return (%)": returns.values})
    sector_data.dropna(inplace=True)
    sector_data.sort_values("Return (%)", ascending=False, inplace=True)

    return sector_data

#############################
# Skapa layout
#############################

app = dash.Dash(__name__, suppress_callback_exceptions=True)

# Knappalternativ för intervall
interval_buttons = html.Div([
    html.Button("1D", id="btn-1D", n_clicks=0, className="interval-btn"),
    html.Button("5D", id="btn-5D", n_clicks=0, className="interval-btn"),
    html.Button("1M", id="btn-1M", n_clicks=0, className="interval-btn"),
    html.Button("3M", id="btn-3M", n_clicks=0, className="interval-btn"),
    html.Button("6M", id="btn-6M", n_clicks=0, className="interval-btn"),
    html.Button("12M", id="btn-12M", n_clicks=0, className="interval-btn"),
], style={"display": "flex", "justifyContent": "center", "gap": "10px", "marginBottom": "20px"})

layout = html.Div([
    html.H1("Sector Leaders", style={"textAlign": "center"}),
    interval_buttons,
    html.H3("Välj intervall:", id="selected-interval", style={"textAlign": "center"}),
    dcc.Graph(id="sector-performance")
])

# Registrera callbacks

def register_callbacks(app):
    @app.callback(
        [Output("sector-performance", "figure"),
         Output("selected-interval", "children")],
        [Input(f"btn-{key}", "n_clicks") for key in INTERVAL_DAYS.keys()]
    )
    def update_chart(*args):
        ctx = dash.callback_context
        interval = ctx.triggered[0]["prop_id"].split(".")[0].replace("btn-", "") if ctx.triggered else "1M"
        sector_data = fetch_sector_data(interval)
        fig = px.bar(sector_data, x="Sector", y="Return (%)", text="Return (%)", text_auto=".2f",
                     color="Return (%)", color_continuous_scale="RdYlGn", title="Sector Performance")
        fig.update_traces(marker_line_width=0.5, marker_line_color="black")
        fig.update_layout(xaxis_tickangle=-45, xaxis_title="Sektor", yaxis_title="Avkastning (%)")
        return fig, f"Valt intervall: {interval}"

