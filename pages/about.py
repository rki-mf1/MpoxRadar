import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/About")

card_style = {
    "box-shadow": "4px 4px 4px",
    "width": "15rem",
    "display": "inline-block",
}
img_style = {"width": "170px", "height": "180px"}


layout = html.Div(
    [
        html.H1(children="Project Description"),
        html.Div(
            [
                """
                        Mpox is an infectious disease caused by a smallpox virus, recently spreading in multiple countries with over 83,000 cases and declared a global emergency by the World Health Organization """,
                dcc.Link(
                    html.A("[1]"),
                    href="https://worldhealthorg.shinyapps.io/mpx_global/",
                    target="_blank",
                ),
                """. Normally, the virus is rarely observed outside of Africa, but in recent months it has occurred in over 110 countries """,
                dcc.Link(
                    html.A("[1]"),
                    href="https://worldhealthorg.shinyapps.io/mpx_global/",
                    target="_blank",
                ),
                """. This alarming behavior demands action and highlights the need for genomic surveillance and spatio-temporal analyses.
                        Therefore, the Robert Koch Institute (RKI) together with the Hasso Platter Institute (HPI), joined forces to produce such a dashboard with a strong database background, inspired by their earlier work
                        on """,
                dcc.Link(
                    html.A("CovSonar"),
                    href="https://github.com/rki-mf1/covsonar",
                    target="_blank",
                ),
                """ - a database framework developed at the RKI for SARS-CoV-2.""",
            ]
        ),
        html.Br(),
        html.H1(children="Who are we?"),
        html.Div(
            [
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/Prof.Dr.BR.jpeg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Prof. Dr. Bernhard Renard"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/Dr.SF.png",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Dr. Stephan Fuchs"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/Dr.AJS.jpeg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P(
                                                "Dr. Anna-Juliane Schmachtenberg",
                                                style={"font-size": "0.82em"},
                                            ),
                                        ],
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/AW.jpeg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Alice Wittig"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/FN.jpeg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Ferdous Nasri"),
                                        ]
                                    ),
                                ],
                                style=card_style,
                                className="mb-2",
                            ),
                        ),
                    ],
                    className="mb-4",
                ),
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/K2.jpg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Kunaphas Kongkitimanon"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/JSC.png",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Jorge Sánchez Cortés"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/IP.jpeg",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Injun Park"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/IT.png",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Ivan Tunov"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                        dbc.Col(
                            dbc.Card(
                                [
                                    dbc.CardImg(
                                        src="assets/PK.png",
                                        top=True,
                                        style=img_style,
                                        className="align-self-center mt-2",
                                    ),
                                    dbc.CardBody(
                                        [
                                            html.P("Pavlo Konoplev"),
                                        ]
                                    ),
                                ],
                                className="mb-2",
                                style=card_style,
                            ),
                        ),
                    ]
                ),
            ],
            className="dbc_card",
            style={"text-align": "center"},
        ),
        html.H1(children="Data source:"),
        html.Div(
            [
                """
                The genomic and metadata stem from publicly available data submitted to NCBI (""",
                dcc.Link(
                    html.A("Link"),
                    href="https://www.ncbi.nlm.nih.gov/labs/virus/vssi/#/",
                    target="_blank",
                ),
                ").",
            ]
        ),
        html.Br(),
        html.H1(children="Link to code:"),
        html.Div(
            [
                """
                        Our code is open source and shared under the """,
                dcc.Link(
                    html.A("GNU GPL license. "),
                    href="https://choosealicense.com/licenses/gpl-3.0/",
                    target="_blank",
                ),
            ]
        ),
        html.Div(
            [
                """There are two actively moderated repositories for this project. One mainly containing the backend named MpoxSonar, while the other is for the developement of the front-end named MpoxRadar. Link to the repositories: """,
                dcc.Link(
                    html.A("Link to MpoxSonar"),
                    href=("https://github.com/rki-mf1/MpoxSonar"),
                    target="_blank",
                ),
                dcc.Link(
                    html.A("Link to MpoxRadar"),
                    href=("https://github.com/rki-mf1/MpoxRadar"),
                    target="_blank",
                ),
            ]
        ),
        html.Br(),
        html.H1(children="Acknowledgements:"),
        html.Div(
            [
                """
                        We want to give a big thanks to all our test users, especially in the central German Public Health institute, for giving us their valuable feedback and helping us better our tool. Furthermore, we want to thank the creators of """,
                dcc.Link(
                    html.A("CovRadar"),
                    href=("https://doi.org/10.1093/bioinformatics/btac411"),
                    target="_blank",
                ),
                """ and """,
                dcc.Link(
                    html.A("CovSonar"),
                    href=("https://github.com/rki-mf1/covsonar"),
                    target="_blank",
                ),
                """ for showing the need for genomic surveillance dashboard and database for SARS-CoV-2, therefore inspiring the initiation of this project. We are always open to feedback and promise a continued support and developement of our tool. """,
                dcc.Link(
                    html.A("Don't hesitate to get in touch."),
                    href=("Contact"),
                    target="_blank",
                ),
            ]
        ),
    ]
)
