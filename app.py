import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from modules import market_sentiment

app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # För deployment

# Huvudlayout med navigation
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
    if pathname == "/" or pathname == "/market_sentiment":
        return market_sentiment.layout
    else:
        return html.H1("404 - Sida hittades inte", style={"textAlign": "center"})

# Clientside callback för att uppdatera containerns stil (höjd) baserat på mus-händelser
app.clientside_callback(
    """
    function(event, storeData, currentStyle) {
        // Om inget event har skickats, returnera befintlig stil och storeData
        if (!event) {
            return [currentStyle, storeData];
        }
        // Gör en kopia av storeData och currentStyle
        let newStore = Object.assign({}, storeData);
        let newStyle = Object.assign({}, currentStyle);
        
        // Vid mousedown: starta resizing och spara startpositionen samt aktuell höjd
        if (event.type === "mousedown") {
            newStore.resizing = true;
            newStore.startY = event.clientY;
            newStore.startHeight = parseInt(currentStyle.height.replace("px", ""));
            return [currentStyle, newStore];
        }
        // Vid mousemove: om resizing pågår, beräkna nytt höjd-värde
        if (event.type === "mousemove" && storeData.resizing) {
            let delta = event.clientY - storeData.startY;
            let newHeight = storeData.startHeight + delta;
            // Klamp höjden mellan 500 och 1200 pixlar
            newHeight = Math.max(500, Math.min(newHeight, 1200));
            newStyle.height = newHeight + "px";
            return [newStyle, storeData];
        }
        // Vid mouseup: avsluta resizing
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
