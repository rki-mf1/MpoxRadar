from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd


def create_world_map_explorer(date_slider):
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
    empty_df = pd.DataFrame(columns=tableFilter.table_columns)
    Output_table_standard = dbc.Card(
        [
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(id="filter-table-output", children=""),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        data=empty_df.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i} for i in empty_df.columns
                                        ],
                                        id="table_explorer",
                                        page_current=0,
                                        page_size=5,
                                        style_data={
                                            "whiteSpace": "normal",
                                            "height": "auto",
                                            "lineHeight": "15px",
                                            # all three widths are needed
                                            "minWidth": "50px",
                                            "width": "400px",
                                            "maxWidth": "750px",
                                        },
                                        style_cell={"fontSize": 12},
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
def html_elem_dropdown_aa_mutations(
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
                        # maxHeight=300,
                        optionHeight=50,
                        multi=True,
                        searchable=True,
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
            style={
                "overflow-y": "auto",
                "maxHeight": 300,
                "minHeight": 200,
            },
        )
    )
    return checklist_aa_mutations
