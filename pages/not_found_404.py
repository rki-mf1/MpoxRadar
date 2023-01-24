import dash
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__)

layout = html.Div(
    [
        dbc.Alert(
            [
                "404 Content Not Found ",
            ],
            color="danger",
        ),
    ]
)
