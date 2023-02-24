from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
from datetime import date


def html_date_picker(d_id):
    today = date.today()
    date_picker = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Date interval:"),
                dcc.DatePickerRange(
                    id=f"date_picker_range_{d_id}",
                    start_date="2022-01-01",
                    end_date=today,
                    min_date_allowed=date(2022, 1, 1),
                    max_date_allowed=today,
                    initial_visible_month=date(2022, 1, 1),
                ),
            ]
        )
    )
    return date_picker


def html_aa_nt_radio():
    item = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label(
                        "Compare amino acid  or nucleotide mutations:",
                        color="primary",
                    ),
                    dbc.RadioItems(
                        options=[
                            {"label": "Amino Acids", "value": "cds"},
                            {"label": "Nucleotides", "value": "source"},
                        ],
                        value="cds",
                        inline=True,
                        style={
                            "font-size": 20,
                            "font-weight": "bold",
                            "align-itmes": "center",
                            "textAlign": "center",
                        },
                        id="aa_nt_radio",
                    ),
                    dbc.Badge(
                        "Warning: The nucleotide option might take a long time to compute.",
                        color="warning",
                        className="me-1",
                    ),
                ],
            ),
        ],
    )
    return item


def html_compare_button():
    return dbc.Button(
        [html.I(className="bi bi-file-play me-1"), "Compare"],
        id="compare_button",
        size="lg",
        className="me-1",
        color="primary",
        style={
            "font-weight": "bold",
        },
        n_clicks=0,
    )
