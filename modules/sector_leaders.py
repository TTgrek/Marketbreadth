import dash
from dash import dcc, html
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output

#############################
# Hämta & Processa Sektor Data
#############################

tickers = [
    "LIT", "TAN", "ARKK", "FINX", "BOTZ", "SMH", "XLK", "ROKT", "XSW", "FNGS", "CIBR", "SKYY", "QTUM", "IYZ", "UFO",
    "XLE", "XOP", "URA", "URNM", "BATT", "XLU", "ICLN", "USO", "KIE", "XLF", "KBE", "KRE", "IYR", "XLRE", "IBB",
    "ARKG", "XBI", "XLV", "ITB", "XHB", "JETS", "XTN", "IYT", "XLB", "XLI", "ITA", "COPX", "SLX", "GDX", "SLV",
    "GLD", "IAU", "CWEB", "KWEB", "FXI", "MCHI", "EWH", "EWJ", "EEM", "EWW", "ARGT", "ECH", "EWZ", "MSOS", "MJ",
    "BITO", "IYC", "XLP", "XLY", "KARS", "DRIV", "XLC"
]

interval_options = {
    "1D": "1d",
    "5D": "5d",
    "1M": "1mo",
    "3M": "3mo",
    "6M": "6mo",
    "12M": "1y"
}

def fetch_sector_data(period="6mo"):
    print(f"📥 Hämtar sektordata ({period}) från Yahoo Finance...")
    raw_data = yf.download(tickers, period=period)

    # Använd 'Close' om 'Adj Close' saknas
    if "Adj Close" in raw_data.columns:
        data = raw_data["Adj Close"]
    else:
        print("⚠️ 'Adj Close' saknas, använder 'Close' istället.")
        data = raw_data["Close"]

    # Beräkna avkastning
    returns = (data.iloc[-1] / data.iloc[0]) - 1  # Total procentuell förändring
    returns = returns.sort_values(ascending=False)  # Sortera från bäst till sämst

    return returns

# Hämta standarddata (6M)
sector_returns = fetch_sector_data()

#############################
# Skapa Visualisering i Graf
#############################

def create_sector_chart(returns):
    fig = go.Figure()

    # Färggradient från **grönt (topp) till rött (botten)**
    num_colors = len(returns)
    colors = [
        f"rgb({255 * (i / num_colors)}, {255 * ((num_colors - i) / num_colors)}, 0)"
        for i in range(num_colors)
    ]

    fig.add_trace(go.Bar(
        x=returns.index,
        y=returns.values * 100,  # Omvandla till procent
        marker=dict(color=colors),
        text=[f"{round(r * 100, 2)}%" for r in returns.values],  # Visar avkastning i %
        textposition="outside",
        hoverinfo="x+y"
    ))

    fig.update_layout(
        title="Sector Performance",
        xaxis_title="Sektor",
        yaxis_title="Avkastning (%)",
        xaxis=dict(tickangle=-45),
        plot_bgcolor="white",
        template="plotly_white"
    )

    return fig

# Skapa initial graf
sector_chart = create_sector_chart(sector_returns)

#############################
# Dash Layout
#############################

layout = html.Div([
    html.H1("Sector Leaders", style={"textAlign": "center"}),

    # Knappar för att välja tidsintervall
    html.Div([
        html.Button("1D", id="btn-1D", n_clicks=0, className="btn"),
        html.Button("5D", id="btn-5D", n_clicks=0, className="btn"),
        html.Button("1M", id="btn-1M", n_clicks=0, className="btn"),
        html.Button("3M", id="btn-3M", n_clicks=0, className="btn"),
        html.Button("6M", id="btn-6M", n_clicks=0, className="btn"),
        html.Button("12M", id="btn-12M", n_clicks=0, className="btn"),
    ], style={"textAlign": "center", "margin-bottom": "20px"}),

    # Graf
    dcc.Graph(id="sector-chart", figure=sector_chart)
])

#############################
# Callbacks
#############################

def register_callbacks(app):
    @app.callback(
        Output("sector-chart", "figure"),
        [Input("btn-1D", "n_clicks"),
         Input("btn-5D", "n_clicks"),
         Input("btn-1M", "n_clicks"),
         Input("btn-3M", "n_clicks"),
         Input("btn-6M", "n_clicks"),
         Input("btn-12M", "n_clicks")]
    )
    def update_sector_chart(n1, n5, n30, n90, n180, n365):
        ctx = dash.callback_context
        if not ctx.triggered:
            selected_interval = "6mo"
        else:
            button_id = ctx.triggered[0]["prop_id"].split(".")[0]
            selected_interval = interval_options.get(button_id.split("-")[1], "6mo")

        updated_returns = fetch_sector_data(period=selected_interval)
        return create_sector_chart(updated_returns)
