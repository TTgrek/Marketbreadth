import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import yfinance as yf
import pandas as pd
import plotly.express as px
from pandas.tseries.offsets import BDay  # För att räkna handelsdagar
import pandas_market_calendars as mcal  # För att få exakta handelsdagar för NYSE

# --------------------------------------------------
# Hämta S&P 500-tickers genom att skrapa Wikipedia
# --------------------------------------------------
def get_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df['Symbol'].tolist()
    # Ändra t.ex. BRK.B till BRK-B (anpassat för Yahoo Finance)
    tickers = [ticker.replace('.', '-') for ticker in tickers]
    return tickers

SP500_TICKERS = get_sp500_tickers()
print(f"Hämtade {len(SP500_TICKERS)} tickers från S&P 500.")

# --------------------------------------------------
# Definiera tidsintervaller (samma som i sector leaders)
# --------------------------------------------------
INTERVAL_DAYS = {
    "1D": 1,
    "1V": 5,    # 1 vecka = 5 handelsdagar
    "1M": 21,
    "3M": 63,
    "6M": 126,
    "12M": 252
}

# --------------------------------------------------
# Hämta NYSE-handelskalender
# --------------------------------------------------
nyse = mcal.get_calendar("NYSE")

# --------------------------------------------------
# Funktion: Hämta data och beräkna avkastning för SP500-aktier
# --------------------------------------------------
def fetch_top_stocks_data(interval="6M"):
    print(f"\n📥 Hämtar top stocks data för {interval} från Yahoo Finance...")
    today = pd.Timestamp.today()
    all_trading_days = nyse.valid_days(start_date="2020-01-01", end_date=today)
    
    # Bestäm start- och slutdatum beroende på intervallet
    if interval == "1V":
        # Hitta den senaste fredagen (weekday == 4)
        friday_date = None
        for d in reversed(all_trading_days):
            if d.weekday() == 4:
                friday_date = d
                break
        if friday_date is None:
            print("❌ Kunde inte hitta en fredag.")
            return pd.DataFrame(columns=["Ticker", "Return (%)"])
        week_number = friday_date.isocalendar()[1]
        year = friday_date.year
        week_trading_days = [d for d in all_trading_days if d.isocalendar()[1] == week_number and d.year == year]
        monday_date = min(week_trading_days)
        start_date = monday_date.strftime("%Y-%m-%d")
        # Eftersom yfinance inte inkluderar slutdatumet, lägg till en dag efter fredagen
        end_date = (friday_date + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 För 1V: Måndag: {start_date}, Fredag: {end_date}")
    else:
        if len(all_trading_days) < INTERVAL_DAYS[interval]:
            print("❌ Inte tillräckligt med handelsdagar!")
            return pd.DataFrame(columns=["Ticker", "Return (%)"])
        start_date = all_trading_days[-INTERVAL_DAYS[interval]].strftime("%Y-%m-%d")
        end_date = (all_trading_days[-1] + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        print(f"📅 Start: {start_date}, Slut: {end_date}")
    
    # Ladda ner data för alla S&P 500-aktier
    data = yf.download(SP500_TICKERS, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
    if data.empty:
        print("❌ Ingen data hämtades!")
        return pd.DataFrame(columns=["Ticker", "Return (%)"])
    
    returns = {}
    for ticker in SP500_TICKERS:
        try:
            ticker_data = data[ticker]
        except Exception as e:
            print(f"⚠️ Ingen data för {ticker}: {e}")
            continue
        if ticker_data.empty:
            continue
        # Använd kolumnen "Close" för beräkning
        if "Close" not in ticker_data.columns:
            continue
        series = ticker_data["Close"].dropna()
        if series.empty:
            continue
        start_price = series.iloc[0]
        end_price = series.iloc[-1]
        if start_price == 0:
            continue
        ret = (end_price - start_price) / start_price * 100
        returns[ticker] = ret
    if not returns:
        return pd.DataFrame(columns=["Ticker", "Return (%)"])
    df = pd.DataFrame({"Ticker": list(returns.keys()), "Return (%)": list(returns.values())})
    df.sort_values("Return (%)", ascending=False, inplace=True)
    top50 = df.head(50)
    print("📊 Top 50 aktier:\n", top50)
    return top50

# --------------------------------------------------
# Bygg Dash-layouten för Top 50 Stocks
# --------------------------------------------------
layout = html.Div([
    html.H1("Top 50 Stocks (Most Up)", style={"textAlign": "center"}),
    html.Div([
        html.Button("1D", id="btn-1D", n_clicks=0, style={"margin": "5px"}),
        html.Button("1V", id="btn-1V", n_clicks=0, style={"margin": "5px"}),
        html.Button("1M", id="btn-1M", n_clicks=0, style={"margin": "5px"}),
        html.Button("3M", id="btn-3M", n_clicks=0, style={"margin": "5px"}),
        html.Button("6M", id="btn-6M", n_clicks=0, style={"margin": "5px"}),
        html.Button("12M", id="btn-12M", n_clicks=0, style={"margin": "5px"}),
    ], style={"display": "flex", "justifyContent": "center", "flexWrap": "wrap"}),
    html.H3(id="selected-interval", style={"textAlign": "center"}),
    dcc.Graph(id="top-stocks-graph")
])

# --------------------------------------------------
# Callback: Registrera callbacks med en funktion
# --------------------------------------------------
def register_callbacks(app):
    @app.callback(
        [Output("top-stocks-graph", "figure"),
         Output("selected-interval", "children")],
        [Input("btn-1D", "n_clicks"),
         Input("btn-1V", "n_clicks"),
         Input("btn-1M", "n_clicks"),
         Input("btn-3M", "n_clicks"),
         Input("btn-6M", "n_clicks"),
         Input("btn-12M", "n_clicks")]
    )
    def update_top_stocks(n1, n1V, n1M, n3M, n6M, n12M):
        ctx = dash.callback_context
        if not ctx.triggered:
            interval = "6M"
        else:
            interval = ctx.triggered[0]["prop_id"].split(".")[0].replace("btn-", "")
        
        top50 = fetch_top_stocks_data(interval)
        if top50.empty:
            fig = px.bar(title="Ingen data tillgänglig")
        else:
            fig = px.bar(top50, x="Ticker", y="Return (%)", 
                         text="Return (%)", color="Return (%)",
                         color_continuous_scale="RdYlGn",
                         title="Top 50 Stocks by Return")
            fig.update_traces(texttemplate="%{text:.2f}%", textposition="outside")
            fig.update_layout(xaxis_tickangle=-45, clickmode="event")
        return fig, f"Valt intervall: {interval}"

# --------------------------------------------------
# Om modulen körs direkt (standalone)
# --------------------------------------------------
if __name__ == "__main__":
    # Skapa en egen app-instans om modulen körs direkt
    app = dash.Dash(__name__)
    app.layout = layout
    register_callbacks(app)
    app.run_server(debug=True)
