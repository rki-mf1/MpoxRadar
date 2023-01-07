from dash import html
import dash_bootstrap_components as dbc

from pages.app_controller import get_all_references
from pages.app_controller import get_all_seqtech
from pages.app_controller import get_high_mutation

# preload reference,
dat_checkbox_list_of_dict = get_all_references()
seqTech_checkbox_list_of_dict = get_all_seqtech()
mutation_checkbox_list_of_dict = get_high_mutation()

checklist_1 = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Reference genome: "),
            dbc.Checklist(
                options=dat_checkbox_list_of_dict,
                value=["NC_063383.1"],
                id="1_checklist_input",
            ),
            dbc.FormText(
                "If checkbox did not checked any reference, it will return all samples.",
                color="secondary",
            ),
        ]
    )
)

checklist_2 = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("NT mutations displayed: "),
            html.Br(),
            dbc.Checklist(
                options=mutation_checkbox_list_of_dict,
                value=[],
                id="2_checklist_input",
                style={
                    "height": 120,
                    "overflowY": "scroll",
                },
            ),
            html.Br(),
            dbc.Checklist(
                id="mutation_all-or-none",
                options=[{"label": "Select All", "value": "All"}],
                value=["All"],
                labelStyle={"display": "inline-block"},
            ),
            dbc.FormText(
                "To select samples that have mutation from the list.",
                color="secondary",
            ),
        ],
    )
)

checklist_3 = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Visualisation method: "),
            dbc.Checklist(
                options=[
                    {"label": "Frequencies", "value": 1},
                    {"label": "Increasing Trend", "value": 2},
                    {"label": "Decreasing Trend", "value": 3},
                    {"label": "Constant Trend", "value": 4},
                ],
                value=[],
                id="3_checklist_input",
            ),
        ],
    )
)

checklist_4 = dbc.Card(
    dbc.CardBody(
        [
            dbc.Label("Sequencing Technology used: "),
            dbc.Checklist(
                options=seqTech_checkbox_list_of_dict,
                value=[],
                id="4_checklist_input",
                labelStyle={"display": "block"},
                style={
                    "height": 120,
                    "overflowY": "scroll",
                },
            ),
            html.Br(),
            dbc.Checklist(
                id="seqtech_all-or-none",
                options=[{"label": "Select All", "value": "All"}],
                value=["All"],
                labelStyle={"display": "inline-block"},
            ),
        ],
    )
)
