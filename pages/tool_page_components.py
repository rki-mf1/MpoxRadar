from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


references_box = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                style={"width": "10%", "height": "100%", "float": "left"},
                children=[
                    dcc.Checklist(
                        className="checkbox_1",
                        id="references-list",
                        options=[
                            {"label": "MT903344.1", "value": "MT903344.1"},
                            {"label": "NC_063383.1", "value": "NC_063383.1"},
                            {"label": "ON563414.3", "value": "ON563414.3"},
                        ],
                        labelStyle={"display": "block"},
                    )
                ],
            )
        ]
    ),
    style={"width": "20rem"},
)


mutations_box = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                style={"width": "10%", "height": "100%", "float": "left"},
                children=[
                    dcc.Checklist(
                        className="checkbox_1",
                        id="mutation-list",
                        options=[
                            {"label": "some mutation", "value": "I1ST2"},
                            {"label": "some mutation", "value": "I2ST2"},
                            {"label": "some mutation", "value": "I3ST2"},
                            {"label": "some mutation", "value": "I4ST2"},
                        ],
                        labelStyle={"display": "block"},
                    )
                ],
            )
        ]
    ),
    style={"width": "20rem"},
)


vizualization_box = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                style={"width": "45%", "height": "100%", "float": "left"},
                children=[
                    dcc.Checklist(
                        className="checkbox_1",
                        id="vizual-method-list",
                        options=[
                            {"label": "Frequencies", "value": "freq"},
                            {"label": "Increasing Trend", "value": "trend-inc"},
                            {"label": "Decreasing Trend", "value": "trend-dec"},
                            {"label": "Constant Trend", "value": "trend-const"},
                        ],
                        value=["I1MT"],
                        labelStyle={"display": "block"},
                    )
                ],
            )
        ]
    ),
    style={"width": "20rem"},
)


user_query_input = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.Div(
                        [
                            "direct MPXSonar query: ",
                            html.Br(),
                            dcc.Input(id="my-input", type="text", size="100"),
                            html.Button(
                                "Run direct MPXSonar query", id="btn-1", n_clicks=0
                            ),
                        ]
                    )
                ]
            )
        ]
    ),
    style={"width": "18rem"},
)
