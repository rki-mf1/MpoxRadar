from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


def create_world_map_explorer(date_slider):
    world_map_with_slider = html.Div(
        [
            html.H3("Output result from filter options", style={"textAlign": "center"}),
            html.H4("Mutation counts based on filters"),
            # dbc.FormText(
            #     "Note, mutations only occurring once are removed from the map and plots below to allow for an overview. "
            #     "Those are still included in the table of results.",
            #     color="primary",
            # ),
            dbc.Spinner(
                dcc.Graph(animate=False, id="world_map_explorer"),
                color="primary",
                type="grow",
            ),
            html.Div(
                [
                    dbc.Row(
                        [
                            # dbc.Col(
                            #     html.I(
                            #         id="play_button",
                            #         n_clicks=0,
                            #         className="fa-solid fa-circle-play fa-lg",
                            #     ),
                            #     width=1,
                            # ),
                            dbc.Col(
                                [
                                    # dcc.Interval(
                                    #     id="auto_stepper",
                                    #     # TODO this might cause the error: { message: "Circular Dependencies", html: "Error: Dependency Cycle Found: auto_stepper.n_intervals -> auto_stepper.disabled -> auto_stepper.n_intervals" }
                                    #     interval=500,
                                    #     # time between steps, this component will increment the counter n_intervals every interval milliseconds, 300 to fast for processing
                                    #     n_intervals=0,  # Number of times the interval has passed.
                                    #     max_intervals=0,
                                    #     disabled=True,
                                    # ),
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
                "Detailed look at the sequences with the chosen mutations for the selected country",
                id="chosen_location",
            ),
            dbc.Alert(
                id="sequence_information",
                color="info",
                className="border me-1",
            ),
        ]
    )

    map_charts = (
        html.Div(
            [
                html.Div(
                    [
                        html.H5(id="header_upper_plot"),
                        dbc.Spinner(
                            dcc.Graph(id="results_per_location"),
                            color="primary",
                            type="grow",
                        ),
                    ]
                ),
                html.Div(
                    [
                        html.H5("Mutation Development", id="header_lower_plot"),
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
                        dbc.Row(
                            dbc.Col(
                                [
                                    html.I(
                                        className="fa-solid fa-computer-mouse",
                                    ),
                                    dbc.FormText(
                                        " Note: Please click on a country you are interested in on the global map above to see detail plots for that country.\n",
                                        color="primary",
                                    ),
                                ],
                            ),
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


def html_elem_method_radioitems():
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


def html_interval(interval=30):
    interval_card = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Interval (number of days): "),
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
def html_elem_dropdown_aa_mutations(
    mutation_options, nb_shown_options, title="AA mutations: ", elem_id=0
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
                            mut_dict["value"]
                            for mut_dict in mutation_options[0:nb_shown_options]
                        ],
                        id=f"mutation_dropdown_{elem_id}",
                        # maxHeight=300,
                        optionHeight=50,
                        multi=True,
                        searchable=True,
                    ),
                    color="danger",
                    type="grow",
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            f"Select n-th most frequent variants. "
                                            f"Number variants matching filters: {len(mutation_options)}",
                                            id=f"max_nb_txt_{elem_id}",
                                        ),
                                        html.I(
                                            className="bi bi-info-circle ms-1 text-primary"
                                        ),
                                        dbc.Tooltip(
                                            "Selects from frequency sorted variants the specified top n variants."
                                            "E.g. a value of 50 selects the 50 most common variants to be shown in map, "
                                            "plots and tables.",
                                            target=f"max_nb_txt_{elem_id}",
                                        ),
                                    ]
                                ),
                            ),
                            dbc.Row(
                                dbc.Col(
                                    dcc.Input(
                                        id=f"select_x_frequent_mut_{elem_id}",
                                        type="number",
                                        placeholder=20,
                                        value=20,
                                        className="input_field",
                                        min=1,
                                        max=len(mutation_options),
                                    ),
                                ),
                            ),
                        ],
                    ),
                    className="mt-1",
                ),
                dbc.Row(
                    dbc.Col(
                        [
                            dbc.Row(
                                dbc.Col(
                                    [
                                        dbc.Label(
                                            "Select minimum variant frequency. Highest frequency in selection: 0",
                                            id=f"min_nb_freq_{elem_id}",
                                        ),
                                        html.I(
                                            className="bi bi-info-circle ms-1 text-primary"
                                        ),
                                    ]
                                ),
                            ),
                            dbc.Row(
                                dbc.Col(
                                    dcc.Input(
                                        id=f"select_min_nb_frequent_mut_{elem_id}",
                                        type="number",
                                        placeholder=1,
                                        value=1,
                                        className="input_field",
                                        min=1,
                                    ),
                                ),
                            ),
                            dbc.Tooltip(
                                "Specifies the minimum number of sequences in which the variant must occur to be listed "
                                "here. Highest frequency represents the highest number of sequences sharing the same "
                                "variant. E.g., a minimum variant frequency of 2 remove all variants detected "
                                "only once.",
                                target=f"min_nb_freq_{elem_id}",
                            ),
                        ],
                    ),
                    className="mt-1",
                ),
            ],
            style={
                "overflowY": "auto",
                "maxHeight": 450,
                "minHeight": 200,
            },
        )
    )
    return checklist_aa_mutations
