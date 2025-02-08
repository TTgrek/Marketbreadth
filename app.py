import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# 🔹 Importera modulerna
from modules import market_sentiment, risk_on_off, sector_leaders, stats

# 🔹 Skapa Dash-appen
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

# 🔹 Layout med navigeringsmeny
app.layout = html.Div([
    dcc.Tabs(id="tabs", value="market_sentiment", children=[
        dcc.Tab(label="Market Sentiment", value="market_sentiment"),
        dcc.Tab(label="Risk ON/OFF", value="risk_on_off"),
        dcc.Tab(label="Sektor Ledare", value="sector_leaders"),
        dcc.Tab(label="Statistik", value="stats"),
    ]),
    html.Div(id="content")
])

# 🔹 Callback för att växla mellan moduler
@app.callback(
    Output("content", "children"),
    Input("tabs", "value")
)
def display_page(tab):
    if tab == "market_sentiment":
        return market_sentiment.layout
    elif tab == "risk_on_off":
        return risk_on_off.layout
    elif tab == "sector_leaders":
        return sector_leaders.layout
    elif tab == "stats":
        return stats.layout

# 🔹 Starta appen
if __name__ == "__main__":
    app.run_server(debug=True)
