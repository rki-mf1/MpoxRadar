from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc

from pages.app_controller import get_all_references
from pages.app_controller import get_all_seqtech, get_high_mutation

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
                "most common mutations",
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

custom_cmd_cards = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H3(
                            [
                                "MpoxSonar command!",
                                # dbc.Badge(
                                #     "Alpha-Test", className="ms-1", color="warning"
                                # ),
                            ]
                        )
                    ]
                ),
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
                                                    value="match -r NC_063383.1 --COUNTRY USA --SEQ_TECH 'Illumina MiSeq' --RELEASE_DATE 2022-08-01:2022-08-31",
                                                    type="text",
                                                    size="100",
                                                ),
                                                dbc.FormText(
                                                    "type the sonar command here and press submit (no need to put sonar at the begining)",
                                                    color="secondary",
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
                                                    id="submit-button-state",
                                                    n_clicks=0,
                                                    children="Submit",
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
                                        dbc.Toast(
                                            [
                                                html.Div(id="my-command", children=""),
                                                html.P(
                                                    "-------",
                                                    className="mb-0",
                                                ),
                                                html.P(
                                                    "",
                                                    className="mb-0",
                                                ),
                                            ],
                                            header="Translate into Sonar command",
                                            style={"marginTop": "15px"},
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
                                                            color="white",
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
                                                                "MPXSonar",
                                                                href="https://github.com/rki-mf1/covsonar/tree/dev/cov2_mpire",
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


Output_mpxsonar = dbc.Card(  # Output
                    [
                        html.H3("Output result from MpoxSonar command."),
                        dbc.Accordion(
                            [
                                dbc.AccordionItem(
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
                                                        # all three widths are needed
                                                        "minWidth": "300px",
                                                        "width": "300px",
                                                        "maxWidth": "300px",
                                                    },
                                                    style_table={"overflowX": "auto"},
                                                    export_format="csv",
                                                ),
                                            ]
                                        ),
                                    ],
                                    title="Click to hide/show output:",
                                ),
                            ]
                        ),
                    ],
                    body=True,
                    className="mx-1 my-1",
                )  # end of Output

query_card = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    dbc.Checklist(
                        options=[
                            {
                                "label": "Use MpoxSonar query result to map: ",
                                "value": "mpoxsonar_checked",
                            }
                        ],
                        id="mpoxsonar_output_checkbox",
                    )
                ]
            ),
            custom_cmd_cards,
        ]
    ),
    style={"width": "100%"},
    className="relative",
)
