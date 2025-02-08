import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from modules import market_sentiment

# Skapa Dash-appen
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # För deployment

# Huvudlayout med navigation
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Div(id="page-content")
])

# Callback för att hantera navigering
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname")]
)
def display_page(pathname):
    if pathname == "/" or pathname == "/market_sentiment":
        return market_sentiment.layout
    else:
        return html.H1("404 - Sida hittades inte", style={"textAlign": "center"})

# Clientside callback med extra kontroller för undefined värden
app.clientside_callback(
    """
    function(event, storeData, currentStyle) {
        if (typeof storeData === "undefined" || storeData === null) {
            storeData = {"resizing": false, "startY": null, "startHeight": 800};
        }
        if (typeof currentStyle === "undefined" || currentStyle === null) {
            currentStyle = {"height": "800px"};
        }
        if (typeof event === "undefined" || event === null || typeof event.type === "undefined") {
            return [currentStyle, storeData];
        }
        let newStore = Object.assign({}, storeData);
        let newStyle = Object.assign({}, currentStyle);
        
        if (event.type === "mousedown") {
            newStore.resizing = true;
            newStore.startY = event.clientY;
            newStore.startHeight = parseInt(currentStyle.height.replace("px", ""));
            return [currentStyle, newStore];
        }
        if (event.type === "mousemove" && storeData.resizing) {
            let delta = event.clientY - storeData.startY;
            let newHeight = storeData.startHeight + delta;
            newHeight = Math.max(500, Math.min(newHeight, 1200));
            newStyle.height = newHeight + "px";
            return [newStyle, storeData];
        }
        if (event.type === "mouseup" && storeData.resizing) {
            newStore.resizing = false;
            return [currentStyle, newStore];
        }
        return [currentStyle, storeData];
    }
    """,
    [Output("graph-container", "style"), Output("resize-store", "data")],
    [Input("resizable-container", "event")],
    [State("resize-store", "data"), State("graph-container", "style")]
)

if __name__ == "__main__":
    app.run_server(debug=True)
