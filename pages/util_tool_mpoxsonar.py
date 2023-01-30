from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

custom_cmd_cards = html.Div(
    [
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                dcc.Input(
                                                    id="my-input",
                                                    value="match -r NC_063383.1 --COUNTRY USA",
                                                    type="text",
                                                    size="100",
                                                ),
                                                dbc.FormText(
                                                    "Type the sonar command here and press submit (no need to put 'sonar' at the begining).",
                                                    color="info",
                                                ),
                                                html.Br(),
                                                dbc.Row(
                                                    [
                                                        dbc.Col([]),
                                                    ]  # row
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    [
                                        html.Div(
                                            [
                                                dbc.Button(
                                                    children=[
                                                        html.I(
                                                            className="bi bi-bullseye me-1"
                                                        ),
                                                        "Submit",
                                                    ],
                                                    id="submit-button-state",
                                                    n_clicks=0,
                                                    outline=True,
                                                    color="primary",
                                                    className="mb-2",
                                                ),
                                            ]
                                        ),
                                    ]
                                ),
                            ]
                        ),  # end row
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        dbc.Spinner(
                                            dbc.Toast(
                                                [
                                                    dbc.Row(
                                                        html.Div(
                                                            id="my-command", children=""
                                                        )
                                                    ),
                                                    dbc.Row(
                                                        html.P(
                                                            "----  Argument check ----",
                                                            className="mb-0",
                                                        )
                                                    ),
                                                    dbc.Row(
                                                        html.Div(
                                                            id="command-valid-badge"
                                                        )
                                                    ),
                                                ],
                                                header="Translate into Sonar command",
                                                style={"marginTop": "15px"},
                                            ),
                                        ),
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        dbc.Accordion(
                                            [
                                                dbc.AccordionItem(
                                                    [
                                                        html.Ul(
                                                            "1.The output will be showed in the below section."
                                                        ),
                                                        html.Ul(
                                                            "2. Available reference: NC_063383.1, ON563414.3 and MT903344.1"
                                                        ),
                                                    ],
                                                    title="Note>",
                                                ),
                                                dbc.AccordionItem(
                                                    [
                                                        html.P(
                                                            "Currenlty we allow only 'match' and 'list-prop' commands."
                                                        ),
                                                        dbc.Badge(
                                                            "match -r NC_063383.1 --COUNTRY USA",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-1",
                                                        ),
                                                        dbc.Badge(
                                                            "match --profile del:1-60",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-3",
                                                        ),
                                                        dbc.Badge(
                                                            "match --profile ^C162331T",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-4",
                                                        ),
                                                        dbc.Badge(
                                                            "match --profile OPG188:L246F --profile MPXV-UK_P2-164:L246F ",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-5",
                                                        ),
                                                        dbc.Badge(
                                                            "match --profile A151461C del:=1-=6",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-8",
                                                        ),
                                                        dbc.Badge(
                                                            "match --LENGTH >197120 <197200",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-2",
                                                        ),
                                                        dbc.Badge(
                                                            "match --sample ON585033.1",
                                                            color="white",
                                                            text_color="primary",
                                                            className="border me-1",
                                                            id="cmd-9",
                                                        ),
                                                        dbc.Badge(
                                                            "list-prop",
                                                            color="blue",
                                                            text_color="secondary",
                                                            className="border me-1",
                                                            id="cmd-7",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Select all samples from reference 'NC_063383.1' and in USA",
                                                            target="cmd-1",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Select all samples from sequence length in a range between 197120 and 197200 bp",
                                                            target="cmd-2",
                                                        ),
                                                        dbc.Tooltip(
                                                            "List all properties",
                                                            target="cmd-7",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Select all samples that have or in range 1-60 deletion mutation (e.g., del:1-60, del:1-6, del:11-20)",
                                                            target="cmd-3",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Select all samples except samples contain C162331T mutation (^ = exclude)",
                                                            target="cmd-4",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Combine with 'OR'; for example, get all samples that have mutation at 'OPG188:L246F' OR 'MPXV-UK_P2-164:L246F' (format, GENE/TAG:protien mutation)",
                                                            target="cmd-5",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Get all samples ",
                                                            target="cmd-6",
                                                        ),
                                                        dbc.Tooltip(
                                                            "'AND' operation; for example, get all samples that have mutation at A151461C and exact 1-6 deletion",
                                                            target="cmd-8",
                                                        ),
                                                        dbc.Tooltip(
                                                            "Get sample by name",
                                                            target="cmd-9",
                                                        ),
                                                    ],
                                                    title="Example commands...",
                                                ),
                                                dbc.AccordionItem(
                                                    html.Label(
                                                        [
                                                            "We are currently working to resolve bugs :)..Thank you for your understanding and patience while we work on solutions! "
                                                            "Please visit ",
                                                            html.A(
                                                                "MpoxSonar",
                                                                href="https://github.com/rki-mf1/MpoxSonar",
                                                            ),
                                                            " for more usage and detail.",
                                                        ]
                                                    ),
                                                    title="FMI",
                                                ),
                                            ],
                                            style={"marginTop": "15px"},
                                        )
                                    ],
                                    width=8,
                                ),
                            ]
                        ),  # end row
                    ]
                ),  # end card body
            ],
            className="mb-3",
        ),
    ]
)


Output_mpxsonar = [
    dbc.Row(html.H4("Output result from MpoxSonar command.")),
    dbc.Row(
        [
            dbc.Toast(
                "The map and table are updated!",
                id="mpoxsonar-updated-noti",
                header="MpoxSonar Tool",
                is_open=False,
                duration=5000,
                icon="info",
                # top: 66 positions the toast below the navbar
                style={
                    "position": "fixed",
                    "top": "5px",
                    "right": "40%",
                    "width": "250px",
                    "z-index": 9990,
                },
            ),
        ]
    ),
    dbc.Accordion(
        [
            dbc.AccordionItem(
                [
                    dbc.Spinner(
                        [
                            html.Div(id="my-output", children=""),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        id="my-output-df",
                                        page_current=0,
                                        page_size=10,
                                        style_data={
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "lineHeight": "15px",
                                            # all three widths are needed
                                            "minWidth": "50px",
                                            "width": "400px",
                                            "maxWidth": "750px",
                                        },
                                        fixed_rows={"headers": True},
                                        style_cell={"fontSize": 12},
                                        style_table={"overflowX": "auto"},
                                        export_format="csv",
                                        filter_action="native",
                                    ),
                                ],
                                id="my-div-table",
                            ),
                            dbc.Badge(
                                "Duration for query: 0 sec",
                                color="white",
                                text_color="muted",
                                className="border me-1",
                                id="exe_time-table",
                            ),
                        ],
                        color="success",
                        type="grow",
                        spinner_style={"width": "3rem", "height": "3rem"},
                    ),
                ],
                title="Result:",
            ),
            dbc.AccordionItem(
                [
                    dbc.Spinner(
                        [
                            dbc.Row(
                                html.Div(
                                    dbc.Alert(
                                        "Note: the count and list-prop command cannot be used with map.",
                                        color="warning",
                                        id="alert-msg-map",
                                    )
                                ),
                                id="alert-msg-map-div",
                            ),
                            dbc.Row(dbc.Col(dcc.Graph(id="mysonar-map"))),
                        ],
                        color="warning",
                        type="grow",
                        spinner_style={"width": "3rem", "height": "3rem"},
                    ),
                    dbc.Row(
                        html.Div(
                            [
                                html.Hr(className="my-2"),
                                dbc.Button(
                                    "Note",
                                    id="simple-toast-toggle",
                                    color="primary",
                                    className="mb-3",
                                    n_clicks=0,
                                ),
                                dbc.Toast(
                                    [
                                        html.P(
                                            "1. Map will be updated when the table result gets an update.",
                                            className="mb-0",
                                        ),
                                        html.P(
                                            "2. Map legends display mutations in accordance with their sizes.",
                                            className="mb-0",
                                        ),
                                        html.P(
                                            "3. For more flexibility in map rendering, mutations with frequencies less than 10 are filtered out (please download the full result from the table for downstream analysis).",
                                            className="mb-0",
                                        ),
                                    ],
                                    id="simple-toast",
                                    header="Mpoxsonar Map...",
                                    icon="primary",
                                    dismissable=True,
                                    is_open=False,
                                    style={
                                        "width": 600,
                                    },
                                ),
                            ]
                        )
                    ),
                ],
                title="Map:",
            ),
        ],
        style={"z-index": 1230},
    ),  # Accordion
]

query_card = dbc.Card(
    [
        dbc.CardHeader(
            [
                html.Div(
                    [
                        "Specialized searches with MpoxSonar command",
                        # dbc.Badge(
                        #     "Alpha-Test", className="ms-1", color="warning"
                        # ),
                    ]
                )
            ]
        ),
        dbc.CardBody(
            [
                html.Div([]),
                custom_cmd_cards,
            ]
        ),
    ],
    style={"width": "100%"},
    className="relative mb-2",
)
