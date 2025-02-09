import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc  # För modaler
import yfinance as yf
import pandas as pd
import plotly.express as px
from pandas.tseries.offsets import BDay  # För att räkna handelsdagar
import pandas_market_calendars as mcal  # För att få exakta handelsdagar

# --- Lista på ETF:er/sektorer ---
SECTOR_TICKERS = [
    "LIT", "TAN", "ARKK", "FINX", "BOTZ", "SMH", "XLK", "ROKT", "XSW", "FNGS",
    "CIBR", "SKYY", "QTUM", "IYZ", "UFO", "XLE", "XOP", "URA", "URNM", "BATT",
    "XLU", "ICLN", "USO", "KIE", "XLF", "KBE", "KRE", "IYR", "XLRE", "IBB",
    "ARKG", "XBI", "XLV", "ITB", "XHB", "JETS", "XTN", "IYT", "XLB", "XLI",
    "ITA", "COPX", "SLX", "GDX", "SLV", "GLD", "IAU", "CWEB", "KWEB", "FXI",
    "MCHI", "EWH", "EWJ", "EEM", "EWW", "ARGT", "ECH", "EWZ", "MSOS", "MJ",
    "BITO", "IYC", "XLP", "XLY", "KARS", "DRIV", "XLC"
]

# --- Handelsdagsintervall ---
INTERVAL_DAYS = {
    "1D": 1,
    "1V": 5,    # 1 vecka = 5 handelsdagar
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252
}

# --- Hämta NYSE-handelskalender ---
nyse = mcal.get_calendar("NYSE")

#############################
# Funktion: Hämta sektordata
#############################
def fetch_sector_data(interval="6M"):
    print(f"\n📥 Hämtar sektordata för {interval} från Yahoo Finance...")
    today = pd.Timestamp.today()
    all_trading_days = nyse.valid_days(start_date="2020-01-01", end_date=today)

    if interval == "1V":
        # Hitta senaste fredag (weekday == 4)
        friday_date = None
        for d in reversed(all_trading_days):
            if d.weekday() == 4:
                friday_date = d
                break
        if friday_date is None:
            print("❌ Kunde inte hitta en fredag.")
            return pd.DataFrame(columns=["Sector", "Return (%)"])
        week_number = friday_date.isocalendar()[1]
        year = friday_date.year
        week_trading_days = [d for d in all_trading_days if d.isocalendar()[1] == week_number and d.year == year]
        monday_date = min(week_trading_days)
        start_date = monday_date.strftime("%Y-%m-%d")
        # Lägg till en dag efter fredagen så att yfinance inkluderar fredagen
        end_date = (friday_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 För 1V: Måndag: {start_date}, Fredag: {end_date}")
    else:
        if len(all_trading_days) < INTERVAL_DAYS[interval]:
            print("❌ Inte tillräckligt med handelsdagar!")
            return pd.DataFrame(columns=["Sector", "Return (%)"])
        start_date = all_trading_days[-INTERVAL_DAYS[interval]].strftime("%Y-%m-%d")
        end_date = (all_trading_days[-1] + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 Start: {start_date}, Slut: {end_date}")

    raw_data = yf.download(SECTOR_TICKERS, start=start_date, end=end_date)
    if raw_data.empty:
        print("❌ Ingen data hämtades!")
        return pd.DataFrame(columns=["Sector", "Return (%)"])
    print("✅ Data hämtad!")
    if "Adj Close" in raw_data:
        data_adj = raw_data["Adj Close"]
    else:
        data_adj = None
    if "Close" in raw_data:
        data_close = raw_data["Close"]
    else:
        data_close = None

    returns = {}
    desired_start = pd.to_datetime(start_date)
    for ticker in SECTOR_TICKERS:
        if ticker == "BITO":
            try:
                bito_df = yf.Ticker("BITO").history(start=start_date, end=end_date, auto_adjust=False)
                series = bito_df["Close"].dropna()
            except Exception as e:
                print(f"❌ Fel vid BITO: {e}")
                continue
        else:
            if data_adj is not None and ticker in data_adj.columns:
                series = data_adj[ticker].dropna()
            elif data_close is not None and ticker in data_close.columns:
                series = data_close[ticker].dropna()
            else:
                continue
        if series.empty:
            continue
        first_date = series.index[0]
        if first_date.tz is not None:
            first_date = first_date.tz_localize(None)
        if first_date > desired_start:
            continue
        start_price = series.iloc[0]
        end_price = series.iloc[-1]
        if start_price == 0:
            continue
        ticker_return = (end_price - start_price) / start_price * 100
        returns[ticker] = ticker_return
        print(f"{ticker}: start {start_price:.2f}, end {end_price:.2f}, return {ticker_return:.2f}%")
    
    if not returns:
        return pd.DataFrame(columns=["Sector", "Return (%)"])
    
    sector_data = pd.DataFrame({
        "Sector": list(returns.keys()),
        "Return (%)": list(returns.values())
    })
    sector_data.sort_values("Return (%)", ascending=False, inplace=True)
    print(f"📊 Sektoravkastning:\n{sector_data.head()}")
    return sector_data

#############################
# Funktion: Hämta top 5 innehav automatiskt
#############################
def get_top_holdings(ticker):
    try:
        t = yf.Ticker(ticker)
        holdings = getattr(t, 'holdings', None)
        if holdings is None:
            holdings = getattr(t, 'fund_holdings', None)
        if holdings is not None and not holdings.empty:
            if "Symbol" in holdings.columns:
                return holdings.head(5)["Symbol"].tolist()
            elif "Ticker" in holdings.columns:
                return holdings.head(5)["Ticker"].tolist()
            else:
                return holdings.iloc[:5, 0].tolist()
        else:
            return None
    except Exception as e:
        print(f"Fel vid hämtning av holdings för {ticker}: {e}")
        return None

#############################
# Skapa Dash-layout med modal
#############################
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)

layout = html.Div([
    html.H1("📊 Sector Leaders", style={"textAlign": "center"}),
    html.Div([
        html.Button("1D", id="btn-1D", n_clicks=0, className="interval-btn"),
        html.Button("1V", id="btn-1V", n_clicks=0, className="interval-btn"),
        html.Button("1M", id="btn-1M", n_clicks=0, className="interval-btn"),
        html.Button("3M", id="btn-3M", n_clicks=0, className="interval-btn"),
        html.Button("6M", id="btn-6M", n_clicks=0, className="interval-btn"),
        html.Button("12M", id="btn-12M", n_clicks=0, className="interval-btn"),
    ], style={"display": "flex", "justifyContent": "center", "gap": "10px", "marginBottom": "20px"}),
    html.H3("Välj intervall:", id="selected-interval", style={"textAlign": "center"}),
    dcc.Graph(id="sector-performance"),
    dbc.Modal(
        [
            dbc.ModalHeader("Top 5 Aktier"),
            dbc.ModalBody(id="modal-body"),
            dbc.ModalFooter(dbc.Button("Stäng", id="close-modal", className="ml-auto"))
        ],
        id="modal",
        is_open=False,
    )
])

#############################
# Callback: Uppdatera diagram
#############################
@app.callback(
    [Output("sector-performance", "figure"),
     Output("selected-interval", "children")],
    [Input("btn-1D", "n_clicks"),
     Input("btn-1V", "n_clicks"),
     Input("btn-1M", "n_clicks"),
     Input("btn-3M", "n_clicks"),
     Input("btn-6M", "n_clicks"),
     Input("btn-12M", "n_clicks")]
)
def update_chart(n1, n1V, n1M, n3M, n6M, n12M):
    ctx = dash.callback_context
    if not ctx.triggered:
        interval = "6M"
    else:
        interval = ctx.triggered[0]["prop_id"].split(".")[0].replace("btn-", "")
    
    sector_data = fetch_sector_data(interval)
    
    if sector_data.empty:
        fig = px.bar(title="Ingen data tillgänglig", labels={"x": "Sektor", "y": "Avkastning (%)"})
    else:
        fig = px.bar(
            sector_data,
            x="Sector",
            y="Return (%)",
            text="Return (%)",
            text_auto=".2f",
            color="Return (%)",
            color_continuous_scale="RdYlGn",
            title="Sector Performance"
        )
    fig.update_traces(marker_line_width=0.5, marker_line_color="black")
    fig.update_layout(
        xaxis_tickangle=-45,
        xaxis_title="Sektor",
        yaxis_title="Avkastning (%)",
        clickmode="event"  # Se till att klick registreras
    )
    
    return fig, f"Valt intervall: {interval}"

#############################
# Callback: Visa modal vid klick
#############################
@app.callback(
    [Output("modal", "is_open"),
     Output("modal-body", "children")],
    [Input("sector-performance", "clickData"),
     Input("close-modal", "n_clicks")],
    [State("modal", "is_open")]
)
def display_modal(clickData, close_click, is_open):
    ctx = dash.callback_context
    if ctx.triggered and ctx.triggered[0]["prop_id"].split(".")[0] == "close-modal":
        return False, dash.no_update
    if clickData is None:
        return is_open, "Klicka på en sektor för att se top 5 aktier."
    try:
        sector = clickData["points"][0]["x"]
    except (KeyError, IndexError):
        return is_open, "Klicka på en sektor för att se top 5 aktier."
    
    top5 = get_top_holdings(sector)
    if top5 is None:
        content = f"Inga uppgifter om top 5 aktier för {sector} hittades automatiskt."
    else:
        content = f"Top 5 aktier i {sector}: " + ", ".join(top5)
    return True, content

def register_callbacks(app):
    app.callback(
        [Output("sector-performance", "figure"),
         Output("selected-interval", "children")],
        [Input("btn-1D", "n_clicks"),
         Input("btn-1V", "n_clicks"),
         Input("btn-1M", "n_clicks"),
         Input("btn-3M", "n_clicks"),
         Input("btn-6M", "n_clicks"),
         Input("btn-12M", "n_clicks")]
    )(update_chart)

#############################
# Starta applikationen
#############################
if __name__ == "__main__":
    app.layout = layout
    app.run_server(debug=True)
