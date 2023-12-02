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
from pages.config import logging_radar
from pages.html_compare import html_aa_nt_radio
from pages.html_compare import html_compare_button
from pages.html_compare import html_date_picker
from pages.html_compare import overview_table
from pages.html_data_explorer import create_world_map_explorer
from pages.html_data_explorer import html_elem_dropdown_aa_mutations
from pages.html_data_explorer import html_elem_method_radioitems
from pages.html_data_explorer import html_interval
from pages.html_more_viz import tab_more_tool
from pages.html_shared import html_complete_partial_radio
from pages.html_shared import html_disclaimer_seq_errors
from pages.html_shared import html_elem_checklist_seq_tech
from pages.html_shared import html_elem_dropdown_aa_mutations_without_max
from pages.html_shared import html_elem_dropdown_countries
from pages.html_shared import html_elem_dropdown_genes
from pages.html_shared import html_elem_reference_radioitems
from pages.html_shared import html_table
from pages.libs.pathosonar.src.pathosonar.sonar import parse_args
from pages.util_tool_mpoxsonar import Output_mpxsonar
from pages.util_tool_mpoxsonar import query_card
from pages.util_tool_summary import descriptive_summary_panel
from pages.utils_filters import get_all_frequency_sorted_countries_by_filters
from pages.utils_filters import get_all_frequency_sorted_seqtech
from pages.utils_filters import get_all_gene_dict
from pages.utils_filters import get_all_references
from pages.utils_filters import get_frequency_sorted_cds_mutation_by_filters
from pages.utils_filters import get_frequency_sorted_seq_techs_by_filters
from pages.utils_tables import OverviewTable
from pages.utils_tables import TableFilter
from pages.utils_worldMap_explorer import DateSlider
from .app_controller import get_freq_mutation
from .app_controller import match_controller
from .app_controller import sonarBasicsChild
from .compare_callbacks import get_compare_callbacks
from .explore_callbacks import get_explore_callbacks
from .utils import get_color_dict


df_dict = load_all_sql_files()
date_slider = DateSlider(df_dict)
color_dict = get_color_dict(df_dict)

# initialize explore tool
start_cond_ref_id = sorted(list(df_dict["variantView"]["complete"].keys()))[0]
start_cond_complete = "complete"
start_cond_aa_nt = "cds"
start_cond_min_freq = 1
start_cond_len_shown_mut = 20
all_reference_options = get_all_references(df_dict)
all_seq_tech_options = get_all_frequency_sorted_seqtech(df_dict)
start_all_gene_dict = get_all_gene_dict(
    df_dict, start_cond_ref_id, start_cond_complete, color_dict
)
start_all_gene_value = [s["value"] for s in start_all_gene_dict]
start_seq_tech_dict = get_frequency_sorted_seq_techs_by_filters(
    df_dict,
    all_seq_tech_options,
    start_cond_complete,
    start_cond_ref_id,
    start_all_gene_value,
    start_cond_aa_nt,
)
start_seq_tech_values = [s["value"] for s in start_seq_tech_dict if not s["disabled"]]
start_country_options = get_all_frequency_sorted_countries_by_filters(
    df_dict,
    start_seq_tech_values,
    start_cond_complete,
    start_cond_ref_id,
    start_all_gene_value,
    start_cond_aa_nt,
)

start_country_value = [i["value"] for i in start_country_options]
(
    start_colored_mutation_options_dict,
    max_nb_freq,
    min_nb_freq,
) = get_frequency_sorted_cds_mutation_by_filters(
    df_dict,
    start_seq_tech_values,
    start_country_value,
    start_all_gene_value,
    start_cond_complete,
    start_cond_ref_id,
    color_dict,
    start_cond_min_freq,
)
nb_shown_options = (
    len(start_colored_mutation_options_dict)
    if len(start_colored_mutation_options_dict) < start_cond_len_shown_mut
    else start_cond_len_shown_mut
)
logging_radar.info("Prebuilt cache is complete.")
dash.register_page(__name__, path="/Tool")
compare_columns = TableFilter("compare", []).table_columns
explore_columns = TableFilter("explorer", []).table_columns

tab_explored_tool = html.Div(
    [
        html.Div(
            [
                html.Div(
                    [
                        dbc.Row(html.H2("Filter Panel", style={"textAlign": "center"})),
                        dbc.Row(
                            dbc.Col(
                                dbc.Alert(
                                    [
                                        html.I(className="bi bi-journal-text me-2"),
                                        "For a step-by-step guide on how to use this tool with an example, check out ",
                                        html.A(
                                            "our wiki.",
                                            href="https://github.com/rki-mf1/MpoxRadar/wiki/Explore-Tool",
                                            target="_blank",
                                        ),
                                        " For more detailed information on the features, check out the ",
                                        html.A(
                                            "help page.",
                                            href="Help",
                                        ),
                                    ],
                                    color="info",
                                    dismissable=True,
                                )
                            ),
                        ),
                        dbc.Row(
                            dbc.Col(html_complete_partial_radio("explore")),
                            className="mb-2",
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html_elem_reference_radioitems(
                                            all_reference_options, start_cond_ref_id, 0
                                        )
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [html_elem_dropdown_genes(start_all_gene_dict)],
                                    width=4,
                                ),
                                dbc.Col(
                                    [
                                        html_elem_checklist_seq_tech(
                                            start_seq_tech_dict, 0
                                        )
                                    ],
                                    width=3,
                                ),
                                dbc.Col(
                                    [
                                        html_elem_dropdown_countries(
                                            start_country_options
                                        )
                                    ],
                                    width=3,
                                ),
                            ]
                        ),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html_elem_dropdown_aa_mutations(
                                            start_colored_mutation_options_dict,
                                            nb_shown_options,
                                        )
                                    ],
                                    width=9,
                                ),
                                dbc.Col(
                                    [
                                        html_interval(),
                                        html.Br(),
                                        html_elem_method_radioitems(),
                                    ],
                                    align="center",
                                    width=3,
                                ),
                            ],
                            className="mt-2",
                        ),
                    ],
                ),
                dbc.Row(
                    dbc.Col(html_disclaimer_seq_errors("explorer", only_cds=True)),
                    className="mt-2",
                ),
                html.Hr(),
                html.Div(create_world_map_explorer(date_slider)),
                html.Div(
                    html_table(
                        pd.DataFrame(columns=explore_columns),
                        "Properties of filtered samples.",
                        "explorer",
                    )
                ),
            ],
            id="div_elem_standard",
            className="mt-2",
        ),
    ]
)

tab_compare_tool = (
    html.Div(
        [
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Row(
                                dbc.Col(
                                    dbc.Alert(
                                        [
                                            html.I(className="bi bi-journal-text me-2"),
                                            "For a step-by-step guide on how to use this tool with an example, check out ",
                                            html.A(
                                                "our wiki.",
                                                href="https://github.com/rki-mf1/MpoxRadar/wiki/Compare-Tool",
                                                target="_blank",
                                            ),
                                            " For more detailed information on the features, check out the ",
                                            html.A(
                                                "help page.",
                                                href="Help",
                                            ),
                                        ],
                                        color="info",
                                        dismissable=True,
                                    )
                                ),
                            ),
                            dbc.Row(
                                dbc.Col(html_complete_partial_radio("compare")),
                            ),
                            dbc.Row(
                                dbc.Col(html_aa_nt_radio()),
                                className="mt-1",
                            ),
                            dbc.Row(
                                dbc.Col(
                                    html_elem_reference_radioitems(
                                        all_reference_options,
                                        start_cond_ref_id,
                                        radio_id=1,
                                    ),
                                ),
                                className="mt-1",
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        [
                                            html.H3(
                                                "Left Filter",
                                                style={
                                                    "textAlign": "center",
                                                    "margin-top": 20,
                                                },
                                            )
                                        ]
                                    ),
                                    html.Div(
                                        html_elem_dropdown_genes(
                                            start_all_gene_dict, g_id=1
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_elem_checklist_seq_tech(
                                            start_seq_tech_dict, s_id=1
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_elem_dropdown_countries(
                                            start_country_options, c_id=1
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_date_picker(d_id=1),
                                        className="mt-1",
                                    ),
                                ]
                            ),
                            html.Hr(
                                className="vr",
                                style={
                                    "border": "none",
                                    "borderColor": "#AB87FF",
                                    "opacity": "unset",
                                    "width": "1px",
                                },
                            ),
                            dbc.Col(
                                [
                                    dbc.Row(
                                        html.H3(
                                            "Right Filter",
                                            style={
                                                "textAlign": "center",
                                                "margin-top": 20,
                                            },
                                        )
                                    ),
                                    html.Div(
                                        html_elem_dropdown_genes(
                                            start_all_gene_dict, g_id=2
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_elem_checklist_seq_tech(
                                            start_seq_tech_dict, s_id=2
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_elem_dropdown_countries(
                                            start_country_options, c_id=2
                                        ),
                                        className="mt-1",
                                    ),
                                    html.Div(
                                        html_date_picker(d_id=2),
                                        className="mt-1",
                                    ),
                                ]
                            ),
                        ]
                    ),
                    html.Br(),
                    dbc.Row([html_compare_button()]),
                ],
                className="mt-2",
            ),
            html.Hr(),
            dbc.Row(dbc.Col(html.H2("Output Section", style={"textAlign": "center"}))),
            dbc.Row(dbc.Col(html_disclaimer_seq_errors("compare", only_cds=False))),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    html_elem_dropdown_aa_mutations_without_max(
                                        [{"value": "no_mutation"}],
                                        title="Mutations unique for left selection",
                                        elem_id="left",
                                    ),
                                ]
                            ),
                            dbc.Col(
                                [
                                    html_elem_dropdown_aa_mutations_without_max(
                                        [{"value": "no_mutation"}],
                                        title="Mutations in both selections",
                                        elem_id="both",
                                    )
                                ],
                            ),
                            dbc.Col(
                                [
                                    html_elem_dropdown_aa_mutations_without_max(
                                        [{"value": "no_mutation"}],
                                        title="Mutations unique for right selection",
                                        elem_id="right",
                                    ),
                                ]
                            ),
                        ]
                    ),
                    dbc.Row(
                        overview_table(
                            pd.DataFrame(columns=OverviewTable.table_columns),
                            OverviewTable.column_names,
                            title="Overview Table",
                            tool="compare_0",
                        ),
                        className="mt-3",
                    ),
                    dbc.Row(
                        [
                            html_table(
                                pd.DataFrame(columns=compare_columns),
                                title="Samples with mutations unique for left selection",
                                tool="compare_1",
                            ),
                            html_table(
                                pd.DataFrame(columns=compare_columns),
                                title="Samples with mutations contained in both selections",
                                tool="compare_3",
                            ),
                            html_table(
                                pd.DataFrame(columns=compare_columns),
                                title="Samples with mutations unique for right selection",
                                tool="compare_2",
                            ),
                        ],
                        className="mt-3",
                    ),
                ],
                className="mt-2",
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
                                dbc.Tab(tab_more_tool, label="More Tools"),
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
    try:
        ouput_df = ouput_df[selected_column]
        result = pd.merge(
            ouput_df, location_coordinates, left_on="COUNTRY", right_on="name"
        )
        result.drop(columns=["location_ID", "name"], inplace=True)
    except Exception as e:
        print(e)
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
        parse_args(_list)
        # print(args)

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
    #   background=True,
    # manager=background_callback_manager
    prevent_initial_call=True,
)
# @cache.cached(key_prefix='adv_sonar_table')
# @cache.memoize()
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
            # print(_tmp_output)
            if type(_tmp_output) is int:
                output = _tmp_output
            elif type(_tmp_output) is str:
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
        "PROTEOMIC_PROFILE",
        "REFERENCE",
    ]
    column_profile = "PROTEOMIC_PROFILE"
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
            "REFERENCE",
            column_profile,
            "country_ID",
        ],
        keep="last",
        inplace=True,
    )
    _tmp_original_df = table_df.copy()
    size_data = len(table_df)
    if size_data > 100:
        # remove mutation case = 1
        table_df = table_df[table_df["Case"] > 10]
        # in case, the filter condition remove all samples.
        if len(table_df) == 0:
            table_df = _tmp_original_df.sample(frac=0.5, random_state=42)
    else:
        pass
        # remove mutation case = 1
        # table_df = table_df[table_df["Case"] > 1]
    # sort value
    table_df = table_df.sort_values(by=["Case"], ascending=False)
    # print(table_df)
    table_df["mutation_list"] = (
        table_df[column_profile] + " " + table_df["Case"].astype(str)
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
            "PROTEOMIC_PROFILE": False,
            "Case": True,
            "REFERENCE": True,
            "COUNTRY": True,
        },  # ["NUC_PROFILE", "COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=53, lon=9),
        mapbox_style="carto-positron",
        color="mutation_list",
        color_discrete_sequence=color_schemes,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0}, showlegend=False)

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
get_explore_callbacks(df_dict, date_slider, color_dict, location_coordinates)

# COMPARE PART
get_compare_callbacks(df_dict, color_dict)

del df_dict
