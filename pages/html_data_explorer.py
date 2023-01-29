from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


def create_worldMap_explorer(date_slider):
    """
    contain layout page
    """

    world_map_with_slider = html.Div(
        [
            dbc.FormText(
                "Only once occurring mutations removed from map and plots.",
                color="primary",
            ),
            dcc.Graph(animate=False, id="world_map_explorer"),
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
                                        interval=500,  # time between steps, this component will increment the counter n_intervals every interval milliseconds, 300 to fast for processing
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

    map_chart_header = html.Div([html.H5(id="chosen_location")])

    map_charts = (
        html.Div(
            [
                html.Div(
                    [
                        html.H6(id="header_upper_plot"),
                        dcc.Graph(id="results_per_location"),
                    ]
                ),
                html.Div(
                    [
                        html.H6("Mutation Development", id="header_lower_plot"),
                        dcc.Graph(id="mutation_development"),
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
            html.H3("Output result from filter options."),
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


def get_html_interval(interval=50):
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
            ]
        )
    )
    return interval_card


def get_html_elem_reference_radioitems(reference_options):
    checklist_reference = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Reference genome: "),
                dbc.RadioItems(
                    options=reference_options,
                    value=2,
                    id="reference_radio",
                ),
                dbc.FormText(
                    "Only one reference allowed.",
                    color="secondary",
                ),
            ]
        )
    )
    return checklist_reference


# TODO : max for input field?
# TODO design dropdown
def get_html_elem_dropdown_aa_mutations(mutation_options):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("AA mutations: "),
                html.Br(),
                dcc.Dropdown(
                    options=mutation_options,
                    value=[mut_dict["value"] for mut_dict in mutation_options[0:20]],
                    id="mutation_dropdown",
                    maxHeight=300,
                    optionHeight=50,
                    multi=True,
                    searchable=True,
                    style={"overflow-y": "scroll", "maxHeight": 120},
                ),
                html.Br(),
                dbc.Label(
                    f"Select x most frequent sequences. Maximum number of non-unique mutations: "
                    f"{len(mutation_options)}",
                    id="max_nb_txt",
                ),
                html.Br(),
                dcc.Input(
                    id="select_x_frequent_mut",
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


# TODO design dropdown
def get_html_elem_dropdown_countries(countries):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Country: "),
                html.Br(),
                dcc.Dropdown(
                    options=countries,
                    value=[c["value"] for c in countries],
                    id="country_dropdown",
                    maxHeight=100,
                    optionHeight=50,
                    multi=True,
                    searchable=True,
                    style={"overflow-y": "auto", "maxHeight": 120},
                ),
                html.Br(),
                dcc.Checklist(
                    id="select_all_countries",
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
                        {"label": "Increasing Trend", "value": "Increase"},
                    ],
                    value="Frequency",
                    id="method_radio",
                ),
            ],
        )
    )
    return checklist_methode


def get_html_elem_checklist_seq_tech(seq_tech_options):
    checklist_seq_tech = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Sequencing Technology: "),
                dbc.Checklist(
                    options=seq_tech_options,
                    value=[tech_dict["value"] for tech_dict in seq_tech_options],
                    id="seq_tech_dropdown",
                    labelStyle={"display": "block"},
                    style={
                        "maxHeight": 120,
                        "overflowY": "scroll",
                    },
                ),
                html.Br(),
                dcc.Checklist(
                    id="select_all_seq_tech",
                    options=[{"label": "Select All", "value": 1}],
                    value=[1],
                ),
            ],
        )
    )
    return checklist_seq_tech
