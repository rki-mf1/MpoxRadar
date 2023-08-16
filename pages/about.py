import dash
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

dash.register_page(__name__, path="/")

card_style = {
    "box-shadow": "4px 4px 4px",
    "width": "15rem",
    "display": "inline-block",
}
img_style = {"width": "170px", "height": "180px"}


layout = html.Div(
    [
        dbc.Card(
            dbc.CardBody(
                [
                    html.H2(children="Project Description"),
                    dbc.Row(
                        dbc.Col(
                            html.Div(
                                [
                                    dbc.Row(
                                        dbc.Col(
                                            [
                                                """
                                            MonkeyPox (Mpox) is an infectious disease caused by a smallpox virus, recently spreading in multiple countries with over 86,000 cases and declared a global emergency by the World Health Organization """,
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
                                                """ - a database framework developed at the RKI for SARS-CoV-2. below is a graphical abstract of our work.""",
                                            ]
                                        ),
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col("", width=2),
                                            dbc.Col(
                                                html.Div(
                                                    dbc.Card(
                                                        [
                                                            dbc.CardBody(
                                                                [
                                                                    html.Div(
                                                                        html.Img(
                                                                            src="assets/graphicalAbstract.png",
                                                                            # style=img_style,
                                                                            style={
                                                                                "width": "75%",
                                                                                "height": "60%",
                                                                            },
                                                                            className="",
                                                                        ),
                                                                        className="card-body text-center",
                                                                    ),
                                                                    html.Div(
                                                                        html.P(
                                                                            "Graphical Abstract.",
                                                                            className="card-text",
                                                                        ),
                                                                        className="card-body text-center",
                                                                    ),
                                                                ]
                                                            ),
                                                        ],
                                                        className="ma-2",
                                                        style={
                                                            "box-shadow": "4px 4px 4px",
                                                        },
                                                    ),
                                                    className="text-center",
                                                ),
                                                className="col-md-8",
                                            ),
                                            dbc.Col("", width=2),
                                        ],
                                    ),
                                ]
                            ),
                        ),
                    ),
                    html.Br(),
                    html.H2(children="What is this?"),
                    html.Div(
                        [
                            dbc.Row(
                                dbc.Col(
                                    """With this web server, we provide tools to explore and comapre metadata from Mpox sequences available from our data sources (listed below).
                                Furthermore, we provide an advanced tool for more detailed searches. The chosen data using our tools is visualised and presented in downloadable tables.
                                As Mpox does not have one defined reference genome, we provide multiple reference genomes to choose between. All sample genomes are pre-processed, aligned to multiple reference genomes, followed by variant calling on our servers to enable quick analysis and searches for our users. We confirm that this website is free and open to all users and there is no login requirement. Below is a simplified overview of our tool:
                                """,
                                ),
                            ),
                            dbc.Row(
                                [
                                    dbc.Col("", width=2),
                                    dbc.Col(
                                        html.Div(
                                            dbc.Card(
                                                [
                                                    dbc.CardBody(
                                                        [
                                                            html.Div(
                                                                html.Img(
                                                                    src="assets/mpoxOverview.png",
                                                                    # style=img_style,
                                                                    style={
                                                                        "width": "75%",
                                                                        "height": "60%",
                                                                    },
                                                                    className="",
                                                                ),
                                                                className="card-body text-center",
                                                            ),
                                                            html.Div(
                                                                html.P(
                                                                    "Simplified Technical Overview.",
                                                                    className="card-text",
                                                                ),
                                                                className="card-body text-center",
                                                            ),
                                                        ]
                                                    ),
                                                ],
                                                className="ma-2",
                                                style={
                                                    "box-shadow": "4px 4px 4px",
                                                },
                                            ),
                                            className="text-center",
                                        ),
                                        className="col-md-8",
                                    ),
                                    dbc.Col("", width=2),
                                ],
                            ),
                            dbc.Row(
                                dbc.Col(
                                    [
                                        """
                                    For more information on the tool, we re-direct you to our paper (below under "How to cite?"), and to our GitHub README pages (below under "Link to code").
                                    We have described the functionalities of our tools in detail in the """,
                                        dcc.Link(
                                            html.A("help page"),
                                            href=("https://mpoxradar.net/Help"),
                                            target="_blank",
                                        ),
                                        " and provide exemplified ways of how to use our page with step-by-step guides available on the ",
                                        dcc.Link(
                                            html.A("GitHub wiki"),
                                            href=(
                                                "https://github.com/rki-mf1/MpoxRadar/wiki"
                                            ),
                                            target="_blank",
                                        ),
                                        ". ",
                                    ],
                                    className="mt-2",
                                ),
                            ),
                        ]
                    ),
                    html.Br(),
                    html.H2(children="Who are we?"),
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
                                                        html.P(
                                                            "Prof. Dr. Bernhard Renard"
                                                        ),
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
                                                            style={
                                                                "fontSize": "0.82em"
                                                            },
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
                                ],
                                className="mb-4",
                            ),
                            dbc.Row(
                                [
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
                                                        html.P(
                                                            "Kunaphas Kongkitimanon"
                                                        ),
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
                                ],
                                className="mb-4",
                            ),  # end ROw
                            dbc.Row(
                                [
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
                                    dbc.Col(
                                        dbc.Card(
                                            [
                                                dbc.CardImg(
                                                    src="assets/image_placeholder.jpg",
                                                    top=True,
                                                    style=img_style,
                                                    className="align-self-center mt-2",
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        html.P("Annika Brinkmann"),
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
                                                    src="assets/image_placeholder.jpg",
                                                    top=True,
                                                    style=img_style,
                                                    className="align-self-center mt-2",
                                                ),
                                                dbc.CardBody(
                                                    [
                                                        html.P("Andreas Nitsche"),
                                                    ]
                                                ),
                                            ],
                                            className="mb-2",
                                            style=card_style,
                                        ),
                                    ),
                                ],
                                className="mb-4",
                            ),
                        ],
                        className="dbc_card",
                        style={"text-align": "center"},
                    ),
                    html.H2(children="Data source:"),
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
                    html.H2(children="Link to code:"),
                    html.Div(
                        [
                            "Our code is open source and shared under the ",
                            dcc.Link(
                                html.A("GNU GPL license. "),
                                href="https://choosealicense.com/licenses/gpl-3.0/",
                                target="_blank",
                            ),
                        ]
                    ),
                    html.Div(
                        [
                            """There are two actively moderated repositories for this project.
                        One mainly containing the backend named MpoxSonar,
                        while the other is for the developement of the front-end named MpoxRadar.
                        Link to the repositories: """,
                            dcc.Link(
                                html.A("Link to MpoxSonar"),
                                href=("https://github.com/rki-mf1/MpoxSonar"),
                                target="_blank",
                            ),
                            " and ",
                            dcc.Link(
                                html.A("Link to MpoxRadar"),
                                href=("https://github.com/rki-mf1/MpoxRadar"),
                                target="_blank",
                            ),
                        ]
                    ),
                    html.Br(),
                    html.H2(children="How to cite?"),
                    html.Div(
                        [
                            """
                                MpoxRadar: a worldwide Mpox genomic surveillance dashboard
                                Ferdous Nasri, Alice Wittig, Kunaphas Kongkitimanon, Jorge Sánchez Cortés, Annika Brinkmann, Andreas Nitsche, Anna-Juliane Schmachtenberg, Bernhard Y. Renard, Stephan Fuchs
                                bioRxiv 2023.02.03.526935;(""",
                            dcc.Link(
                                html.A(
                                    "doi: https://doi.org/10.1101/2023.02.03.526935 "
                                ),
                                href="https://www.biorxiv.org/content/10.1101/2023.02.03.526935v1",
                                target="_blank",
                            ),
                        ]
                    ),
                    html.Br(),
                    html.H2(children="Acknowledgements:"),
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
            ),
            className="mb-1",
        ),
    ]
)
