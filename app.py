import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from modules import market_sentiment, sector_leaders, top_50_stocks

# Skapa Dash-applikation
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # För att kunna deploya på en server

# 🔹 Huvudlayout med navigering
app.layout = html.Div([
    # Navigeringsmeny
    html.Div([
        dcc.Link("📊 Market Sentiment", href="/market_sentiment", 
                 style={"padding": "20px", "fontSize": "18px"}),
        dcc.Link("📈 Sektorledare", href="/sector_leaders", 
                 style={"padding": "20px", "fontSize": "18px"}),
        dcc.Link("🚀 Top 50 Stocks", href="/top_50_stocks", 
                 style={"padding": "20px", "fontSize": "18px"})
    ], style={
        "textAlign": "center", 
        "marginBottom": "20px", 
        "backgroundColor": "#f8f9fa", 
        "padding": "10px"
    }),

    # Routing-system
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# 🔹 Callback för att växla mellan sidor
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname in ["/", "/market_sentiment"]:
        return getattr(market_sentiment, "layout", html.H1("Market Sentiment saknas"))
    elif pathname == "/sector_leaders":
        return getattr(sector_leaders, "layout", html.H1("Sector Leaders saknas"))
    elif pathname == "/top_50_stocks":
        return getattr(top_50_stocks, "layout", html.H1("Top 50 Stocks saknas"))
    else:
        return html.H1("❌ 404 - Sidan hittades inte", style={"textAlign": "center", "color": "red"})

# 🔹 Registrera callbacks för moduler som har funktioner för detta
if hasattr(sector_leaders, "register_callbacks"):
    sector_leaders.register_callbacks(app)
if hasattr(top_50_stocks, "register_callbacks"):
    top_50_stocks.register_callbacks(app)

# 🔹 Starta Dash-applikationen
if __name__ == "__main__":
    app.run_server(debug=True)
