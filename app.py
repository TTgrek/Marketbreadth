import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from modules import market_sentiment, sector_leaders

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Navigation mellan sidor
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname == "/market_sentiment":
        return market_sentiment.layout
    elif pathname == "/sector_leaders":
        return sector_leaders.layout
    else:
        return html.H1("404 - Sida hittades inte", style={"textAlign": "center"})

if __name__ == "__main__":
    app.run_server(debug=True)
