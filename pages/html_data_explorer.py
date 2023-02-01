from datetime import date

from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd


def create_worldMap_explorer(date_slider):
    """
    contain layout page
    """

    world_map_with_slider = html.Div(
        [
            html.H3("Output result from filter options", style={"textAlign": "center"}),
            html.H4("Mutation counts based on filters"),
            dbc.FormText(
                "Note, mutations only occurring once are removed from the map and plots below to allow for an overview. "
                "Those are still included in the table of results.",
                color="primary",
            ),
            dbc.Spinner(
                dcc.Graph(animate=False, id="world_map_explorer"),
                color="primary",
                type="grow",
            ),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                html.I(
                                    id="play_button",
                                    n_clicks=0,
                                    className="fa-solid fa-circle-play fa-lg",
                                ),
                                width=1,
                            ),
                            dbc.Col(
                                [
                                    dcc.Interval(
                                        id="auto_stepper",
                                        # TODO this might cause the error: { message: "Circular Dependencies", html: "Error: Dependency Cycle Found: auto_stepper.n_intervals -> auto_stepper.disabled -> auto_stepper.n_intervals" }
                                        interval=500,
                                        # time between steps, this component will increment the counter n_intervals every interval milliseconds, 300 to fast for processing
                                        n_intervals=0,  # Number of times the interval has passed.
                                        max_intervals=0,
                                        disabled=True,
                                    ),
                                    dcc.RangeSlider(
                                        id="date_slider",
                                        updatemode="mouseup",
                                        min=date_slider.unix_time_millis(
                                            date_slider.min_date
                                        ),
                                        max=date_slider.unix_time_millis(
                                            date_slider.max_date
                                        ),
                                        marks=date_slider.get_marks_date_range(),
                                        step=86400,  # unix time one day
                                        allowCross=False,
                                        value=[
                                            date_slider.unix_time_millis(
                                                date_slider.get_date_x_days_before(
                                                    date_slider.max_date
                                                )
                                            ),
                                            date_slider.unix_time_millis(
                                                date_slider.max_date
                                            ),
                                        ],
                                    ),
                                ],
                            ),
                        ],
                        justify="center",
                    ),
                ],
                id="slider_box",
            ),
        ],
    )

    map_chart_header = html.Div(
        [
            html.H4(
                "Detailed look at the sequences with the chosen mutations for the selected country"
            ),
            html.H5(id="chosen_location"),
            dbc.FormText(
                "Please click on a country you are interested in on the global map above to see detail plots for that country.",
                color="primary",
            ),
        ]
    )

    map_charts = (
        html.Div(
            [
                html.Div(
                    [
                        html.H6(id="header_upper_plot"),
                        dbc.Spinner(
                            dcc.Graph(id="results_per_location"),
                            color="primary",
                            type="grow",
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.H6("Mutation Development", id="header_lower_plot"),
                        dbc.Spinner(
                            dcc.Graph(id="mutation_development"),
                            color="primary",
                            type="grow",
                        ),
                    ]
                ),
            ]
        ),
    )

    map_slider_and_detail_plots = html.Div(
        [
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    world_map_with_slider,
                                    width=12,
                                    style={"height": "100%"},
                                ),
                            ],
                            align="center",
                        ),
                        html.Br(),
                        dbc.Row(
                            [
                                dbc.Col(
                                    map_chart_header, width=10, style={"height": "100%"}
                                )
                            ],
                            align="center",
                        ),
                        html.Br(),
                        dbc.Row(
                            [
                                #   dbc.Col(info_texts, width=2, style={"height":"100%"}),
                                dbc.Col(map_charts, width=10, style={"height": "100%"}),
                            ],
                            align="center",
                        ),
                        html.Br(),
                    ],
                ),
            )
        ],
        className="page",
        id="map_explorer",
    )
    return map_slider_and_detail_plots


def create_table_explorer(tableFilter):
    df = tableFilter.get_filtered_table()
    Output_table_standard = dbc.Card(  # Output
        [
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(id="filter-table-output", children=""),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        data=df.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i} for i in df.columns
                                        ],
                                        id="table_explorer",
                                        page_current=0,
                                        page_size=20,
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
    )
    return Output_table_standard


def create_table_compare(title, table_id):
    df = pd.DataFrame()
    Output_table_standard = dbc.Card(  # Output
        [
            html.H3(title),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(
                                id=f"compare-table-output_{table_id}", children=""
                            ),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        data=df.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i} for i in df.columns
                                        ],
                                        id=f"table_compare_{table_id}",
                                        page_current=0,
                                        page_size=20,
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
    )
    return Output_table_standard


def get_html_elem_reference_radioitems(reference_options, radio_id=0):
    checklist_reference = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Reference genome: "),
                dbc.RadioItems(
                    options=reference_options,
                    value=2,
                    id=f"reference_radio_{radio_id}",
                ),
                dbc.FormText(
                    "Only one reference allowed.",
                    color="secondary",
                ),
            ]
        )
    )
    return checklist_reference


def get_html_elem_dropdown_genes(gene_options, g_id=0):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Gene: "),
                html.Br(),
                dbc.Spinner(
                    dcc.Dropdown(
                        options=gene_options,
                        value=[c["value"] for c in gene_options],
                        id=f"gene_dropdown_{g_id}",
                        maxHeight=300,  # just height of dropdown not choose option field
                        optionHeight=35,  # height options in dropdown, not chosen options
                        multi=True,
                        searchable=True,
                        style={
                            "overflow-y": "auto",  # without not scrollable, just cut
                            "maxHeight": 200,
                        },  # height field
                    ),
                    color="dark",
                    type="grow",
                ),
                html.Br(),
                dcc.Checklist(
                    id=f"select_all_genes_{g_id}",
                    options=[{"label": "Select All", "value": 1}],
                    value=[1],
                ),
            ],
        )
    )
    return checklist_aa_mutations


def get_html_elem_checklist_seq_tech(seq_tech_options, s_id=0):
    checklist_seq_tech = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Sequencing Technology: "),
                dbc.Spinner(
                    dbc.Checklist(
                        options=seq_tech_options,
                        value=[tech_dict["value"] for tech_dict in seq_tech_options],
                        id=f"seq_tech_dropdown_{s_id}",
                        labelStyle={"display": "block"},
                        style={
                            "maxHeight": 200,
                            "overflowY": "scroll",
                        },
                    ),
                    color="primary",
                    type="grow",
                ),
                html.Br(),
                dcc.Checklist(
                    id=f"select_all_seq_tech_{s_id}",
                    options=[{"label": "Select All", "value": 1}],
                    value=[1],
                ),
            ],
        )
    )
    return checklist_seq_tech


# TODO design dropdown
def get_html_elem_dropdown_countries(countries, c_id=0):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Country: "),
                html.Br(),
                dbc.Spinner(
                    dcc.Dropdown(
                        options=countries,
                        value=[c["value"] for c in countries],
                        id=f"country_dropdown_{c_id}",
                        maxHeight=200,
                        optionHeight=35,
                        multi=True,
                        searchable=True,
                        style={"overflow-y": "auto", "maxHeight": 200},
                    ),
                    color="danger",
                    type="grow",
                ),
                html.Br(),
                dcc.Checklist(
                    id=f"select_all_countries_{c_id}",
                    options=[{"label": "Select All", "value": 1}],
                    value=[1],
                ),
            ],
        )
    )
    return checklist_aa_mutations


def get_html_elem_method_radioitems():
    checklist_methode = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Visualisation method: "),
                dbc.RadioItems(
                    options=[
                        {"label": "Frequencies", "value": "Frequency"},
                        {"label": "Increase/Decrease", "value": "Increase"},
                    ],
                    value="Frequency",
                    id="method_radio",
                ),
            ],
        )
    )
    return checklist_methode


def get_html_interval(interval=30):
    interval_card = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Interval: "),
                dcc.Input(
                    id="selected_interval",
                    type="number",
                    placeholder=interval,
                    value=interval,
                    className="input_field",
                    min=1,
                ),
            ],
        )
    )
    return interval_card


# TODO : max for input field?
# TODO design dropdown
def get_html_elem_dropdown_aa_mutations(
        mutation_options, title="AA mutations: ", aa_id=0
):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label(title),
                html.Br(),
                dbc.Spinner(
                    dcc.Dropdown(
                        options=mutation_options,
                        value=[
                            mut_dict["value"] for mut_dict in mutation_options[0:20]
                        ],
                        id=f"mutation_dropdown_{aa_id}",
                        maxHeight=300,
                        optionHeight=50,
                        multi=True,
                        searchable=True,
                        style={"overflow-y": "auto", "maxHeight": 300},
                    ),
                    color="danger",
                    type="grow",
                ),
                html.Br(),
                dbc.Label(
                    f"Select x most frequent sequences. Maximum number of non-unique mutations: "
                    f"{len(mutation_options)}",
                    id=f"max_nb_txt_{aa_id}",
                ),
                html.Br(),
                dcc.Input(
                    id=f"select_x_frequent_mut_{aa_id}",
                    type="number",
                    placeholder=20,
                    value=20,
                    className="input_field",
                    min=1,
                    max=len(mutation_options),
                ),
                html.Br(),
            ],
        )
    )
    return checklist_aa_mutations


def get_html_date_picker(d_id):
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


def get_html_aa_nt_radio():
    item = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Compare amino acid  or nucleotide mutations:"),
                html.Br(),
                dcc.RadioItems(
                    options=[
                        {'label': 'Amino Acids',
                         'value': 'Amino Acids'},
                        {'label': 'Nucleotides',
                         'value': 'Nucleotides'}
                    ],
                    value='Amino Acids',
                    inline=True,
                    style={
                        'font-size': 20,
                    },
                    id="aa_nt_radio",
                ),
            ],
            style={
                "display": "flex",
                "align-itmes": "center",
            },
        )
    )
    return item
