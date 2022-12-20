import dash
from dash import Dash
from dash import html
import dash_bootstrap_components as dbc

from pages.util_footer_table import row1

app = Dash(__name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP])

table_body = [html.Tbody([row1])]

table = dbc.Table(table_body, bordered=True)

app.layout = html.Div(
    [
        html.H1("MPoxRadar", style={"display": "inline-block"}),
        html.Img(
            src=r"assets/hpi_logo.png",
            alt="Img_HPI",
            style={"float": "right", "height": "10%", "width": "10%"},
            className="responsive",
        ),
        html.Img(
            src=r"assets/rki_logo.png",
            alt="Img_RKI",
            style={
                "float": "right",
                "height": "10%",
                "width": "10%",
                "margin-top": "50px",
                "margin-right": "20px",
            },
            className="responsive",
        ),
        html.Img(
            src=r"assets/DAKI-FWS_logo.png",
            alt="Img_DAKI-FWS",
            style={"float": "right", "height": "10%", "width": "10%"},
            className="responsive",
        ),
        html.Div("An interactive dashboard for genomic surveillance of the mpox."),
        html.Br(),
        html.Div(
            [
                dbc.Button(
                    "About",
                    href="About",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    "Tool", href="Tool", outline=True, color="primary", className="me-1"
                ),
                dbc.Button(
                    "Help", href="Help", outline=True, color="primary", className="me-1"
                ),
                dbc.Button(
                    "Imprint & Privacy Policy",
                    href="Imprint",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    "Contact",
                    href="Contact",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
            ]
        ),
        html.Br(),
        html.Br(),
        dash.page_container,
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(["Version = v1.3.5"]),
        html.Div([html.Hr(), html.Footer([dbc.Table(table)])], className="app_footer"),
    ]
)

app.title = "MPox Report"

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
