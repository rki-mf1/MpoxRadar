import dash_bootstrap_components as dbc
from dash import html

sequences_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.I(className="bi bi-body-text mx-2 fa-3x", style={}),
                    ],
                    className="col-md-1",
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H4("Number of sequences", className="card-title"),
                            html.P(
                                "This is a wider card with supporting text "
                                "below as a natural lead-in to additional "
                                "content. This content is a bit longer.",
                                className="card-text",
                            ),
                            html.Small(
                                "Last updated 3 mins ago",
                                className="card-text text-muted",
                            ),
                        ]
                    ),
                    className="",
                ),
            ],
            className="g-0 d-flex align-items-center",
        )
    ],
    className="mb-3",
    style={"maxWidth": "540px"},
)

mutation_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.CardImg(
                        src="/static/images/portrait-placeholder.png",
                        className="img-fluid rounded-start",
                    ),
                    className="col-md-4",
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H4("Card title", className="card-title"),
                            html.P(
                                "This is a wider card with supporting text "
                                "below as a natural lead-in to additional "
                                "content. This content is a bit longer.",
                                className="card-text",
                            ),
                            html.Small(
                                "Last updated 3 mins ago",
                                className="card-text text-muted",
                            ),
                        ]
                    ),
                    className="col-md-8",
                ),
            ],
            className="g-0 d-flex align-items-center",
        )
    ],
    className="mb-3",
    style={"maxWidth": "540px"},
)

country_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    dbc.CardImg(
                        src="/static/images/portrait-placeholder.png",
                        className="img-fluid rounded-start",
                    ),
                    className="col-md-4",
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H4("Card title", className="card-title"),
                            html.P(
                                "This is a wider card with supporting text "
                                "below as a natural lead-in to additional "
                                "content. This content is a bit longer.",
                                className="card-text",
                            ),
                            html.Small(
                                "Last updated 3 mins ago",
                                className="card-text text-muted",
                            ),
                        ]
                    ),
                    className="col-md-8",
                ),
            ],
            className="g-0 d-flex align-items-center",
        )
    ],
    className="mb-3",
    style={"maxWidth": "540px"},
)

descriptive_summary_panel = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        sequences_card,
                    ]
                ),
                dbc.Col(
                    [
                        mutation_card,
                    ]
                ),
            ]
        ),
        dbc.Row([]),
        dbc.Row(
            [
                dbc.Col([country_card]),
            ]
        ),
    ]
)
