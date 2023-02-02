import dash
from dash import Dash
from dash import html
import dash_bootstrap_components as dbc

from pages.config import __version__
from pages.config import background_callback_manager
from pages.config import DEBUG
from pages.config import SERVER
from pages.util_footer_table import footer_table


dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP],
    background_callback_manager=background_callback_manager,
)
server = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("MpoxRadar", style={"display": "inline-block"}),
                        html.Div(
                            "An interactive dashboard for genomic surveillance of mpox."
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Img(
                            src=r"assets/hpi_logo.png",
                            alt="Img_HPI",
                            style={"float": "right", "width": "25%", "height": "auto"},
                            className="responsive",
                        ),
                        html.Img(
                            src=r"assets/rki_logo.png",
                            alt="Img_RKI",
                            style={
                                "float": "right",
                                "width": "25%",
                                "height": "auto",
                                "marginTop": "20px",
                                "marginRight": "20px",
                            },
                            className="responsive",
                        ),
                        html.Img(
                            src=r"assets/DAKI-FWS_logo.png",
                            alt="Img_DAKI-FWS",
                            style={"float": "right", "width": "25%", "height": "auto"},
                            className="responsive",
                        ),
                    ]
                ),
            ]
        ),
        html.Hr(className="my-2"),
        html.Div(
            [
                dbc.Button(
                    [html.I(className="bi bi-info-circle-fill me-2"), "About"],
                    href="About",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-file-bar-graph me-2"),
                        "Tool",
                        dbc.Badge(
                            "Click Here",
                            color="info",
                            text_color="white",
                            className="ms-1",
                        ),
                    ],
                    href="Tool",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="bi bi-card-list me-2"), "Help"],
                    href="Help",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-send-check-fill me-2"),
                        "Imprint & Privacy Policy",
                    ],
                    href="Imprint",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-envelope-plus-fill me-2"),
                        "Contact",
                    ],
                    href="Contact",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
            ]
        ),
        html.Br(),
        dash.page_container,
        html.Br(),
        html.Div(
            [
                html.Hr(),
                html.Div(["Version = " + __version__]),
                html.Footer([footer_table]),
            ],
            className="",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=DEBUG, host=SERVER)
