import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/Contact")

layout = dbc.Card(
    [
        dbc.CardBody(
            [
                html.Div(
                    children=[
                        html.H1(children="Contact us"),
                        html.P(
                            [
                                """
                            Thank you for using our tool! We would love to get your feedback and improve over time.
                            Please don't hesitate to contact us per e-mail using the following address: """,
                                dcc.Link(
                                    html.A("FuchsS@rki.de"),
                                    href=("mailto:FuchsS@rki.de"),
                                    target="_blank",
                                ),
                            ]
                        ),
                        html.P(
                            [
                                "If you have any questions or wishes regarding the functionalities of the website, please open an issue on our GitHub repository: ",
                                html.Ul(
                                    [
                                        html.Li(
                                            dcc.Link(
                                                html.A(" Link to MpoxRadar Github "),
                                                href=(
                                                    "https://github.com/rki-mf1/MpoxRadar"
                                                ),
                                                target="_blank",
                                            )
                                        ),
                                        html.Li(
                                            dcc.Link(
                                                html.A(" Link to MpoxSonar Github "),
                                                href=(
                                                    "https://github.com/rki-mf1/MpoxSonar"
                                                ),
                                                target="_blank",
                                            )
                                        ),
                                    ]
                                ),
                            ]
                        ),
                    ],
                ),
            ]
        ),
    ]
)
