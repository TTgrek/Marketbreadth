import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from modules import market_sentiment, sector_leaders, risk_on_off  # Importera den nya modulen

# Skapa Dash-applikation
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # För att kunna deploya på en server

# 🔹 Huvudlayout med navigering
app.layout = html.Div([
    # Navigeringsmeny
    html.Div([
        dcc.Link("📊 Market Sentiment", href="/market_sentiment", style={"padding": "20px", "fontSize": "18px"}),
        dcc.Link("📈 Sektorledare", href="/sector_leaders", style={"padding": "20px", "fontSize": "18px"}),
        dcc.Link("🚦 Risk ON/OFF", href="/risk_on_off", style={"padding": "20px", "fontSize": "18px"})
    ], style={"textAlign": "center", "marginBottom": "20px", "backgroundColor": "#f8f9fa", "padding": "10px"}),

    # Routing-system
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# 🔹 Registrera callback-funktioner innan servern startas
sector_leaders.register_callbacks(app)
risk_on_off.register_callbacks(app)  # Registrera risk_on_off callbacks

# 🔹 Callback för att växla mellan sidor
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname in ["/", "/market_sentiment"]:
        return market_sentiment.layout
    elif pathname == "/sector_leaders":
        return sector_leaders.layout
    elif pathname == "/risk_on_off":
        return risk_on_off.layout  # Lägg till Risk ON/OFF layout
    else:
        return html.H1("❌ 404 - Sidan hittades inte", style={"textAlign": "center", "color": "red"})

# 🔹 Starta Dash-applikationen
if __name__ == "__main__":
    app.run_server(debug=True)
