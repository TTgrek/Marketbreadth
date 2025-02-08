import dash
from dash import dcc, html
from dash.dependencies import Input, Output
from modules import market_sentiment

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname in ["/", "/market_sentiment"]:
        # Visa candlestick-chart med marknadsfasindelning
        return html.Div([
            html.H1("Market Cycle - QQQ", style={"textAlign": "center"}),
            dcc.Graph(id="cycle-chart", figure=market_sentiment.candlestick_chart)
        ])
    else:
        return html.H1("404 - Page Not Found", style={"textAlign": "center"})

if __name__ == "__main__":
    app.run_server(debug=True)
