import argparse
import shlex
import time

import dash
from dash import callback
from dash import html
from dash import Input
from dash import no_update
from dash import Output
from dash import State
import dash_bootstrap_components as dbc
from data import load_all_sql_files
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pages.config import color_schemes
from pages.config import location_coordinates
from pages.html_data_explorer import create_table_compare
from pages.html_data_explorer import create_table_explorer
from pages.html_data_explorer import create_worldMap_explorer
from pages.html_data_explorer import get_html_elem_checklist_seq_tech
from pages.html_data_explorer import get_html_elem_dropdown_aa_mutations
from pages.html_data_explorer import get_html_elem_dropdown_countries
from pages.html_data_explorer import get_html_elem_dropdown_genes
from pages.html_data_explorer import get_html_elem_method_radioitems
from pages.html_data_explorer import get_html_elem_reference_radioitems
from pages.html_data_explorer import get_html_interval
from pages.util_tool_mpoxsonar import Output_mpxsonar
from pages.util_tool_mpoxsonar import query_card
from pages.util_tool_summary import descriptive_summary_panel
from pages.utils_explorer_filter import get_all_frequency_sorted_countries
from pages.utils_explorer_filter import get_all_frequency_sorted_mutation
from pages.utils_explorer_filter import get_all_frequency_sorted_seqtech
from pages.utils_explorer_filter import get_all_genes_per_reference
from pages.utils_explorer_filter import get_all_references
from pages.utils_worldMap_explorer import DateSlider
from pages.utils_worldMap_explorer import TableFilter
from pages.utils_worldMap_explorer import WorldMap
from .app_controller import get_freq_mutation
from .app_controller import match_controller
from .app_controller import sonarBasicsChild
from .compare_callbacks import get_compare_callbacks
from .explore_callbacks import get_explore_callbacks
from .libs.mpxsonar.src.mpxsonar.sonar import parse_args

df_dict = load_all_sql_files()
world_map = WorldMap(
    df_dict["propertyView"], df_dict["variantView"], location_coordinates
)
date_slider = DateSlider(df_dict["propertyView"]["COLLECTION_DATE"].tolist())
variantView_cds = df_dict["variantView"][
    df_dict["variantView"]["element.type"] == "cds"
]
table_filter = TableFilter(df_dict["propertyView"], df_dict["variantView"])
all_reference_options = get_all_references(df_dict["variantView"])
all_seq_tech_options = get_all_frequency_sorted_seqtech(df_dict["propertyView"])
all_country_options = get_all_frequency_sorted_countries(df_dict["propertyView"])
all_mutation_options = get_all_frequency_sorted_mutation(
    world_map.df_all_dates_all_voc, 2, world_map.color_dict
)
all_gene_options = get_all_genes_per_reference(
    df_dict["variantView"], 2, world_map.color_dict
)

dash.register_page(__name__, path="/Tool")

tab_explored_tool = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        get_html_elem_reference_radioitems(
                                            all_reference_options
                                        )
                                    ],
                                ),
                                dbc.Col(
                                    [get_html_elem_dropdown_genes(all_gene_options)],
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_checklist_seq_tech(
                                            all_seq_tech_options
                                        )
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_dropdown_countries(
                                            all_country_options
                                        )
                                    ],
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_method_radioitems(),
                                        get_html_interval(),
                                    ],
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        get_html_elem_dropdown_aa_mutations(
                                            all_mutation_options
                                        )
                                    ],
                                    width=12,
                                ),
                            ]
                        ),
                    ]
                ),
                html.Div(create_worldMap_explorer(date_slider)),
                html.Div(create_table_explorer(table_filter)),
            ],
            id="div_elem_standard",
        ),
    ]
)

tab_compare_tool = (
    html.Div(
        [
            html.Div(
                [
                    html.Div(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            get_html_elem_reference_radioitems(
                                                all_reference_options, radio_id=1
                                            ),
                                            get_html_elem_dropdown_genes(
                                                all_gene_options, g_id=1
                                            ),
                                            get_html_elem_checklist_seq_tech(
                                                all_seq_tech_options, s_id=1
                                            ),
                                            get_html_elem_dropdown_countries(
                                                all_country_options, c_id=1
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            get_html_elem_reference_radioitems(
                                                all_reference_options, radio_id=2
                                            ),
                                            get_html_elem_dropdown_genes(
                                                all_gene_options, g_id=2
                                            ),
                                            get_html_elem_checklist_seq_tech(
                                                all_seq_tech_options, s_id=2
                                            ),
                                            get_html_elem_dropdown_countries(
                                                all_country_options, c_id=2
                                            ),
                                        ]
                                    ),
                                ]
                            ),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Button(
                                        "Compare",
                                        id="compare_button",
                                        size="lg",
                                        className="me-1",
                                        color="primary",
                                        n_clicks=0,
                                    )
                                ]
                            ),
                            html.Br(),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            get_html_elem_dropdown_aa_mutations(
                                                all_mutation_options,
                                                title="AA Mutations unique for left selection",
                                                aa_id=1,
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            get_html_elem_dropdown_aa_mutations(
                                                all_mutation_options,
                                                title="AA Mutations unique for right selection",
                                                aa_id=2,
                                            ),
                                        ]
                                    ),
                                    dbc.Col(
                                        [
                                            get_html_elem_dropdown_aa_mutations(
                                                all_mutation_options,
                                                title="AA Mutations in both selections",
                                                aa_id=3,
                                            )
                                        ],
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    create_table_compare(
                                        title="unique for left selection", table_id=1
                                    ),
                                    create_table_compare(
                                        title="unique for right selection", table_id=2
                                    ),
                                    create_table_compare(
                                        title="in both selection", table_id=3
                                    ),
                                ]
                            ),
                        ]
                    ),
                ]
            ),
        ],
        id="compare_elem",
    ),
)

tab_advanced_tool = html.Div(
    [
        dbc.Row(
            dbc.Col(
                html.H2(
                    [
                        "MpoxSonar Tool",
                        # dbc.Badge(
                        #     "Test", className="ms-1", color="warning"
                        # ),
                    ],
                    style={"textAlign": "center"},
                )
            )
        ),
        dbc.Row(dbc.Col(query_card)),
        dbc.Row(dbc.Col(Output_mpxsonar)),
        # html.Button("Download CSV", id="csv-download"),
        # dcc.Download(id="df-download"),
    ]
)

layout = html.Div(
    [
        html.Div(descriptive_summary_panel),
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.Tabs(
                            [
                                dbc.Tab(tab_explored_tool, label="Explore Tool"),
                                dbc.Tab(tab_advanced_tool, label="Advanced Tool"),
                                dbc.Tab(tab_compare_tool, label="Compare Tool"),
                            ]
                        ),  # end tabs
                    ]
                ),
            ]
        ),
    ]
)


def calculate_coordinate(ouput_df, selected_column):
    """
    TODO:     1. improve performance of map
    """
    # concate the coordinate
    ouput_df = ouput_df[selected_column]
    result = pd.merge(
        ouput_df, location_coordinates, left_on="COUNTRY", right_on="name"
    )
    result.drop(columns=["location_ID", "name"], inplace=True)

    # result["number"] = [
    #    len(x.split(",")) for x in result["NUC_PROFILE"]
    # ]  # just count all mutation occur in each sample.
    # new_res = result.groupby(['COUNTRY', 'lon', 'lat', 'RELEASE_DATE'])['number'].sum().reset_index()
    return result


def calculate_accumulator(ouput_df, column_profile="NUC_PROFILE"):
    # NOTE: Now we change the CaseNumber to MutationNumber

    # NOTE: add Date for accumulation?

    # FIXME: Remove emtpy mutation profile, please disable this IF needed,
    ouput_df.drop(ouput_df[ouput_df[column_profile] == "-"].index, inplace=True)
    # convert to list of string.
    ouput_df[column_profile] = (
        ouput_df[column_profile]
        .str.split(",")
        .map(lambda elements: [e.strip() for e in elements])
    )
    # explode the column_profile
    ouput_df = ouput_df.explode(column_profile)

    # add a new column containing the groups counts
    ouput_df["Case"] = ouput_df.groupby(["COUNTRY", column_profile, "RELEASE_DATE"])[
        column_profile
    ].transform("count")

    # print(len(ouput_df))
    # ouput_df.to_csv("test.csv")
    # TODO: Check the Drop duplication
    ouput_df.drop_duplicates(
        subset=[
            "COUNTRY",
            "RELEASE_DATE",
            column_profile,
            "REFERENCE_ACCESSION",
            "country_ID",
        ],
        keep="last",
        inplace=True,
    )
    # print(len(ouput_df))
    # a = ouput_df[column_profile].unique()
    # logging_radar.debug(a)
    # ouput_df.to_csv("test-after.csv")
    ouput_df.reset_index(drop=True, inplace=True)
    return ouput_df


"""
@callback(Output("query_output", "children"), [Input("query_input", "value")])
def output_text(value):
    return value
"""


@callback(
    Output(component_id="my-command", component_property="children"),
    Output(component_id="command-valid-badge", component_property="children"),
    Input(component_id="my-input", component_property="value"),
)
def update_output_div(input_value):
    """
    This function will developed for validation of sonar command
    """
    try:
        badge = html.Div([dbc.Badge("Looks OK!", color="success", className="me-1")])
        _list = shlex.split(input_value)
        args = parse_args(_list)
        print(args)

    except:  # noqa: E722
        badge = html.Div(
            [
                dbc.Badge(
                    "Warning, please check the command",
                    color="danger",
                    className="me-1",
                )
            ]
        )

    return f"sonar {input_value}", badge


@callback(
    Output(component_id="my-div-table", component_property="style"),
    Output(component_id="my-output", component_property="children"),
    Output(component_id="my-output-df", component_property="data"),
    Output(component_id="my-output-df", component_property="columns"),
    Output(component_id="exe_time-table", component_property="children"),
    Input("submit-button-state", "n_clicks"),
    State("my-input", "value"),
    running=[(Output("submit-button-state", "disabled"), True, False)],
    # background=True,
    # prevent_initial_call=True
)
def update_output_sonar(n_clicks, commands):  # noqa: C901
    """
    Callback handle mpxsonar commands to output table/Div
    """
    # calls backend
    _list = shlex.split(commands)
    # print(_list)
    # need to implement mini parser
    data = None
    columns = None
    toggle_value = {"display": "none"}
    # get the start time
    st = time.time()
    try:
        args = parse_args(_list)
        output = ""
        if args.tool == "list-prop":
            df = sonarBasicsChild.list_prop()
            columns = [{"name": col, "id": col} for col in df.columns]
            data = df.to_dict(orient="records")
            toggle_value = {"display": "block"}
        elif args.tool == "match":
            _tmp_output = match_controller(args)
            if type(_tmp_output) == int:
                output = _tmp_output
            elif type(_tmp_output) == str:
                output = _tmp_output
            else:
                df = _tmp_output
                # Drop columns
                if len(df) > 0:
                    df = df.drop(
                        columns=["AA_X_PROFILE", "NUC_N_PROFILE"], errors="ignore"
                    )
                # reorder column
                if "AA_PROFILE" in df:
                    # shift column 'C' to first position
                    first_column = df.pop("AA_PROFILE")
                    # insert column using insert(position,column_name,first_column) function
                    df.insert(1, "AA_PROFILE", first_column)
                if "NUC_PROFILE" in df:
                    first_column = df.pop("NUC_PROFILE")
                    df.insert(1, "NUC_PROFILE", first_column)

                columns = [{"name": col, "id": col} for col in df.columns]
                data = df.to_dict(orient="records")
                toggle_value = {"display": "block"}

        elif args.tool == "dev":
            get_freq_mutation(args)
        else:
            output = "This command is not available."

    except argparse.ArgumentError as exc:
        output = exc.message
    except SystemExit:
        output = "error: unrecognized arguments/commands or it is not a valid variant definition."
    # get the end time
    et = time.time()
    # get the execution time
    elapsed_time = et - st
    execution_time = f"Duration for query: {elapsed_time:.3f} sec"
    return toggle_value, output, data, columns, execution_time


@callback(
    Output("mysonar-map", component_property="figure"),
    Output(component_id="alert-msg-map-div", component_property="style"),
    Output("mpoxsonar-updated-noti", "is_open"),
    Input(component_id="my-output-df", component_property="data"),
    Input(component_id="my-output-df", component_property="columns"),
    running=[(Output("submit-button-state", "disabled"), True, False)],
    # background=True,
    # prevent_initial_call=True
)
def update_output_sonar_map(rows, columns):  # noqa: C901

    # Callback handle sonar ouput to map.

    hidden_state = {"display": "none"}

    if rows is None or len(rows) == 0:
        print("empty data")
        hidden_state = {"display": "block"}
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 28},
                }
            ],
        )
        return fig, hidden_state, False

    table_df = pd.DataFrame(rows, columns=[c["name"] for c in columns])
    selected_column = [
        "COUNTRY",
        "AA_PROFILE",
        "REFERENCE_ACCESSION",
    ]
    column_profile = "AA_PROFILE"
    # table_df = table_df[selected_column]
    table_df = calculate_coordinate(table_df, selected_column)
    # table_df["Case"] = table_df.groupby(["COUNTRY","REFERENCE_ACCESSION","AA_PROFILE"])["AA_PROFILE"].transform("count")
    # FIXME: Remove emtpy mutation profile, please disable this IF needed,
    table_df.drop(table_df[table_df[column_profile] == "-"].index, inplace=True)
    # convert to list of string.
    table_df[column_profile] = (
        table_df[column_profile]
        .str.split(",")
        .map(lambda elements: [e.strip() for e in elements])
    )
    # explode the column_profile
    table_df = table_df.explode(column_profile)

    # add a new column containing the groups counts
    table_df["Case"] = table_df.groupby(["COUNTRY", column_profile])[
        column_profile
    ].transform("count")
    # drop duplicate
    table_df.drop_duplicates(
        subset=[
            "COUNTRY",
            "REFERENCE_ACCESSION",
            column_profile,
            "country_ID",
        ],
        keep="last",
        inplace=True,
    )
    # remove mutation case = 1
    table_df = table_df[table_df["Case"] > 10]
    # sort value
    table_df = table_df.sort_values(by=["Case"], ascending=False)
    # print(table_df)
    table_df["mutation_list"] = (
        table_df["AA_PROFILE"] + " " + table_df["Case"].astype(str)
    )
    table_df.reset_index(drop=True, inplace=True)
    fig = px.scatter_mapbox(
        table_df,
        lat="lat",
        lon="lon",
        size="Case",
        # animation_frame="RELEASE_DATE",
        # animation_group="AA_PROFILE",
        size_max=14,
        height=800,
        zoom=1,
        hover_data={
            "lat": False,
            "lon": False,
            "mutation_list": False,
            "AA_PROFILE": True,
            "Case": True,
            "REFERENCE_ACCESSION": True,
            "COUNTRY": True,
        },  # ["NUC_PROFILE", "COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=53, lon=9),
        mapbox_style="carto-positron",
        color="mutation_list",
        color_discrete_sequence=color_schemes,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    # update legend

    # print(table_df)
    # newnames = table_df.set_index('AA_PROFILE').to_dict()['new_name']

    # fig.for_each_trace(lambda t: t.update(name = newnames[t.name]))
    return fig, hidden_state, True


@callback(
    Output("simple-toast", "is_open"),
    [Input("simple-toast-toggle", "n_clicks")],
)
def open_toast(n):
    if n == 0:
        return no_update
    return True


"""
@callback(
    Output("mysonar-map", component_property="figure"),
    Output(component_id="alert-msg-map-div", component_property="style"),
    Input(component_id="my-output-df", component_property="data"),
    Input(component_id="my-output-df", component_property="columns"),
    running=[(Output("submit-button-state", "disabled"), True, False)],
    # background=True,
    # prevent_initial_call=True
)
def update_output_sonar_map(rows, columns):  # noqa: C901

  #  Callback handle sonar ouput to map.

    hidden_state = {"display": "none"}

    if rows is None or len(rows) == 0:
        print("empty data")
        hidden_state = {"display": "block"}
        fig = go.Figure()
        fig.update_layout(
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[
                {
                    "text": "No matching data found",
                    "xref": "paper",
                    "yref": "paper",
                    "showarrow": False,
                    "font": {"size": 28},
                }
            ],
        )
        return fig, hidden_state

    table_df = pd.DataFrame(rows, columns=[c["name"] for c in columns])
    selected_column = [
        "COUNTRY",
        "COLLECTION_DATE",
        "RELEASE_DATE",
        # "AA_PROFILE",
        "REFERENCE_ACCESSION",
    ]
    # table_df = table_df[selected_column]
    table_df = calculate_coordinate(table_df, selected_column)
    # table_df = calculate_accumulator(table_df, "AA_PROFILE")
    table_df["Case"] = table_df.groupby(["COUNTRY"])["COUNTRY"].transform("count")

    print(table_df)
    fig = px.scatter_mapbox(
        table_df,
        lat="lat",
        lon="lon",
        size="Case",
        # animation_frame="RELEASE_DATE",
        # animation_group="AA_PROFILE",
        size_max=14,
        height=800,
        zoom=1,
        hover_data={
            "lat": False,
            "lon": False,
            # "RELEASE_DATE": True,
            # "Case": True,
            "REFERENCE_ACCESSION": True,
            "COUNTRY": True,
        },  # ["NUC_PROFILE", "COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=53, lon=9),
        mapbox_style="carto-positron",
        color=["COUNTRY","REFERENCE_ACCESSION"],
        color_discrete_sequence=color_schemes,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig, hidden_state
"""

# This is the EXPLORE TOOL PART
get_explore_callbacks(
    df_dict,
    world_map,
    date_slider,
    variantView_cds,
    table_filter,
    all_seq_tech_options,
    world_map.color_dict,
)

# COMPARE PART
get_compare_callbacks(df_dict, variantView_cds, world_map.color_dict)
