import base64

from dash import html
import dash_bootstrap_components as dbc

from pages.app_controller import count_unique_MutRef
from pages.app_controller import get_all_country
from pages.app_controller import get_all_unique_sample
from pages.app_controller import get_newlyadded_sample
from pages.app_controller import get_top3_country

image_filename = "assets/virus.svg"
encoded_image = base64.b64encode(open(image_filename, "rb").read()).decode()

sequences_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(html.I(className="bi bi-body-text", style={})),
                    ],
                    className="col-md-1 col-xs-1 mx-2",
                    style={},
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H5("Number of sequences", className="card-title"),
                            html.H6(
                                f"Total sample: {get_all_unique_sample()}",
                                className="card-text",
                                id="number_seqs",
                            ),
                            html.Small(
                                f"Newly added (last 30 days): {get_newlyadded_sample()}",
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
    style={"maxWidth": "400px"},
)

mutation_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(
                            html.Img(
                                src="data:image/svg+xml;base64,{}".format(encoded_image)
                            )
                        ),
                    ],
                    className="col-md-1 col-xs-1 mx-2",
                    style={},
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H5(
                                [
                                    "Number of mutations ",
                                    dbc.Button(
                                        id="popover-target",
                                        className="me-1 btn-sm bi bi-info-lg fa-xs",
                                        style={"width": "auto", "height": "25x"},
                                    ),
                                ],
                                className="card-title",
                            ),
                            html.H6(
                                f"MIN - MAX: {count_unique_MutRef()}",
                                className="card-text",
                                id="number_seqs",
                            ),
                            html.Small("", className="card-text text-muted"),
                            dbc.Popover(
                                dbc.PopoverBody(
                                    "min and max of number of unique mutations (compared to each reference genome). So if with ref-genome-1, there are 100 mutations and with ref-2, there are 220 and with ref-3 there are 60 mutation, then this field will show: '60 - 220'"
                                ),
                                target="popover-target",
                                trigger="click",
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
    style={"maxWidth": "400px"},
)

country_card = dbc.Card(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.Div(html.I(className="bi bi-dribbble fa-3x", style={})),
                    ],
                    className="col-md-1 col-xs-1 mx-2",
                    style={},
                ),
                dbc.Col(
                    dbc.CardBody(
                        [
                            html.H5("Number of countries", className="card-title"),
                            html.H6(
                                f"Total country: {get_all_country()}",
                                className="card-text",
                                id="number_seqs",
                            ),
                            html.Small(
                                f"Top 3: {get_top3_country()}",
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
    style={"maxWidth": "400px"},
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
                dbc.Col(
                    [
                        country_card,
                    ]
                ),
            ]
        ),
        dbc.Row([]),
    ]
)
