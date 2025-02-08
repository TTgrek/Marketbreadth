import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from modules import market_sentiment

# Skapa Dash-appen
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Behövs för att köra appen online

# Layout för navigation
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Funktion för att hantera navigation mellan moduler
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname == "/" or pathname == "/market_sentiment":
        return market_sentiment.layout
    else:
        return html.H1("404 - Sida hittades inte", style={"textAlign": "center"})

# Starta appen
if __name__ == "__main__":
    app.run_server(debug=True)
