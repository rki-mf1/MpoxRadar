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
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from data import load_all_sql_files  # noqa: I100 I101
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pages.checklist_filter import get_all_frequency_sorted_seqtech
from pages.checklist_filter import get_all_references
from pages.checklist_filter import get_frequency_sorted_mutation_by_filters
from pages.checklist_filter import get_frequency_sorted_seq_techs_by_filters
from pages.checklist_filter import get_html_elem_checklist_aa_mutations
from pages.checklist_filter import get_html_elem_checklist_seq_tech
from pages.checklist_filter import get_html_elem_method_radioitems
from pages.checklist_filter import get_html_elem_reference_radioitems
from pages.checklist_filter import get_html_interval
from pages.config import color_schemes
from pages.config import location_coordinates
from pages.html_data_explorer import create_table_explorer
from pages.html_data_explorer import create_worldMap_explorer
from pages.util_tool_mpoxsonar import Output_mpxsonar
from pages.util_tool_mpoxsonar import query_card
from pages.util_tool_summary import descriptive_summary_panel
from pages.utils_worldMap_filter import DateSlider
from pages.utils_worldMap_filter import TableFilter
from pages.utils_worldMap_filter import WorldMap
from .app_controller import get_freq_mutation
from .app_controller import match_controller
from .app_controller import sonarBasicsChild
from .libs.mpxsonar.src.mpxsonar.sonar import parse_args

# dash.register_page(__name__, path="/DataExplorer")
df_dict = load_all_sql_files()
reference_options = get_all_references(df_dict["variantView"])
seq_tech_options = get_all_frequency_sorted_seqtech(df_dict["propertyView"])
world_map = WorldMap(
    df_dict["propertyView"], df_dict["variantView"], location_coordinates
)
date_slider = DateSlider(df_dict["propertyView"]["COLLECTION_DATE"].tolist())
df_mut = df_dict["variantView"][df_dict["variantView"]["element.type"] == "cds"]
table_filter = TableFilter(df_dict["propertyView"], df_dict["variantView"])


dash.register_page(__name__, path="/Tool")


# example data for example map
# note_data = pd.read_csv("data/Data.csv")

tab_explored_tool = html.Div(
    [
        html.Div(id="alertmsg"),
        html.Div(
            [
                html.Div(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        get_html_elem_reference_radioitems(
                                            reference_options
                                        )
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_checklist_aa_mutations(
                                            df_dict["variantView"], reference_id=2
                                        )
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_checklist_seq_tech(
                                            seq_tech_options
                                        )
                                    ],
                                    width=2,
                                ),
                                dbc.Col(
                                    [
                                        get_html_elem_method_radioitems(),
                                        get_html_interval(),
                                    ],
                                    width=2,
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

"""

tab_explored_tool = [
    dbc.Container(
        [
            dbc.Row(
                html.H2(
                    [
                        "Filter",
                    ],
                    style={"textAlign": "center"},
                )
            ),
            html.Div(id="alertmsg"),
            html.Div(
                [
                    dbc.Row(
                        [
                            dbc.Col(
                                [checklist_1, html.Div(id="selected-ref-values")],
                                style={
                                    "display": "inline-block",
                                    "width": "23%",
                                    "marginRight": "3%",
                                },
                                className="relative",
                            ),
                            dbc.Form(
                                [checklist_2],
                                style={
                                    "display": "inline-block",
                                    "width": "23%",
                                    "marginRight": "3%",
                                },
                                className="relative",
                            ),
                            dbc.Form(
                                [checklist_3],
                                style={
                                    "display": "inline-block",
                                    "width": "23%",
                                    "marginRight": "3%",
                                },
                                className="relative",
                            ),
                            dbc.Form(
                                [checklist_4],
                                style={"display": "inline-block", "width": "22%"},
                                className="relative",
                            ),
                        ]
                    ),
                ]
            ),
            html.Br(style={"lineHeight": "10"}),
            html.Div(
                [
                    html.Br(),
                    html.H1("Here is a map"),
                    dbc.Spinner(
                        dcc.Graph(id="my-map"),
                        color="info",
                        type="grow",
                        spinner_style={"width": "3rem", "height": "3rem"},
                    ),
                    html.Br(),
                ]
            ),
        ]
    )
]
"""
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
                            ]
                        ),  # end tabs
                    ]
                ),
            ]
        ),
    ]
)

"""
# update map here
@callback(
    Output("alertmsg", "children"),
    Output("my-map", component_property="figure"),
    [
        Input("1_checklist_input", "value"),
        Input("2_checklist_input", "value"),
        Input("3_checklist_input", "value"),
        Input("4_checklist_input", "value"),
    ],
)
def update_figure(
    ref_checklist,
    mut_checklist,
    viz_checklist,
    seqtech_checklist,
):
    alertmsg = ""
    all_or_none = ref_checklist + mut_checklist + viz_checklist + seqtech_checklist
    output_df = pd.DataFrame(
        columns=["COUNTRY", "RELEASE_DATE", "lat", "lon", "CaseNumber"]
    )
    fig = go.Figure()
    if len(all_or_none) == 0:
        msg = "All"
    else:
        msg = all_or_none
    print(msg)
    selected_column = ["COUNTRY", "RELEASE_DATE", "AA_PROFILE", "REFERENCE_ACCESSION"]
    output_df = get_value_by_filter(ref_checklist, mut_checklist, seqtech_checklist)
    output_df = calculate_coordinate(output_df, selected_column)
    # sort DATE
    output_df["RELEASE_DATE"] = pd.to_datetime(output_df["RELEASE_DATE"]).dt.date
    output_df.sort_values(by="RELEASE_DATE", inplace=True)
    output_df = calculate_accumulator(output_df, "AA_PROFILE")

    fig = px.scatter_mapbox(
        output_df,
        lat="lat",
        lon="lon",
        size="Case",
        animation_frame="RELEASE_DATE",
        animation_group="AA_PROFILE",
        size_max=50,
        height=600,
        zoom=3,
        hover_data={
            "lat": False,
            "lon": False,
            "RELEASE_DATE": True,
            "Case": True,
            "COUNTRY": True,
        },  # ["NUC_PROFILE", "COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=8.584314, lon=-75.95781),
        mapbox_style="carto-positron",
        color="AA_PROFILE",
        color_continuous_scale=px.colors.sequential.Reds,
    )
    fig.update_layout(
        legend=dict(
            title=None, orientation="h", y=1, yanchor="bottom", x=0.5, xanchor="center"
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
    )

    return alertmsg, fig
"""


def calculate_coordinate(ouput_df, selected_column):
    """
    TODO:
    1. improve performance of map
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

@callback(
    Output(component_id="selected-ref-values", component_property="children"),
    Input(component_id="1_checklist_input", component_property="value")
)
def reference_text(value):
    print(value)
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
    """
    Callback handle sonar ouput to map.
    """
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
    Output("4_checklist_input", "value"),
    [Input("seqtech_all-or-none", "value")],
    [State("4_checklist_input", "options")],
)
def seqtech_select_all_none(all_selected, options):

    # Callback handle select all seq tech

    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none


@callback(
    Output("2_checklist_input", "value"),
    [Input("mutation_all-or-none", "value")],
    [State("2_checklist_input", "options")],
)
def mutation_select_all_none(all_selected, options):

    # Callback handle select all NT mutation

    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none

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

    Callback handle sonar ouput to map.

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


# @callback(
#     Output("seq_tech_dropdown", "value"),
#     [Input("seqtech_all-or-none", "value")],
#     [State("seq_tech_dropdown", "options")],
# )
# def seqtech_select_all_none(all_selected, options):
#     all_or_none = [option for option in options if all_selected]
#     return all_or_none

# refill filters depending on selected filter
@callback(
    [
        Output("mutation_dropdown", "options"),
        Output("mutation_dropdown", "value"),
        Output("seq_tech_dropdown", "options"),
        Output("seq_tech_dropdown", "value"),
        # Output("reference_radio", "options"),
        # Output("reference_radio", "value"),
    ],
    [
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("mutation_dropdown", "value"),
        Input("select_all_mut", "value"),
        Input("select_all_seq_tech", "value"),
    ],
    [
        State("mutation_dropdown", "options"),
        State("seq_tech_dropdown", "options"),
        #     State("reference_radio", "options")
    ],
    prevent_initial_call=False,
)
def frequency_sorted_mutation_by_filters(
    reference_value,
    seqtech_value,
    mut_value,
    select_all_mut,
    select_all_tech,
    mut_options,
    tech_options,
):
    """
    different filters depending on each other (exception reference genome, do not change)
    """
    if dash.ctx.triggered_id == "select_all_seq_tech":
        if len(select_all_tech) == 1:
            seqtech_value = [i["value"] for i in seq_tech_options]
        elif len(select_all_tech) == 0:
            seqtech_value = []

    if dash.ctx.triggered_id == "select_all_mut":
        if len(select_all_mut) == 1:
            mut_value = [i["value"] for i in mut_options]
        elif len(select_all_mut) == 0:
            mut_value = []

    # mutation_option
    if dash.ctx.triggered_id in [
        "reference_radio",
        "seq_tech_dropdown",
        "select_all_seq_tech",
    ]:
        df_seq_tech = df_dict["propertyView"][
            df_dict["propertyView"]["SEQ_TECH"].isin(seqtech_value)
        ]
        df_mut_ref_select = df_mut[(df_mut["reference.id"] == reference_value)]
        mut_options = get_frequency_sorted_mutation_by_filters(
            df_mut_ref_select, df_seq_tech
        )
        print("mut_option: ", len(mut_options))
        if len(mut_options) > 20:
            mut_value = [
                mut_dict["value"]
                for mut_dict in mut_options[0:20]
                if mut_dict["value"] in mut_value
            ]
        else:
            mut_value = [
                mut_dict["value"]
                for mut_dict in mut_options
                if mut_dict["value"] in mut_value
            ]
        print("mut_value: ", len(mut_value))
    # seq tech
    if dash.ctx.triggered_id in [
        "reference_radio",
        "mutation_dropdown",
        "select_all_mut",
    ]:
        df_mut_ref_mut_select = df_mut[
            (
                df_mut["variant.label"].isin(mut_value)
                & (df_mut["reference.id"] == reference_value)
            )
        ]
        tech_options = get_frequency_sorted_seq_techs_by_filters(
            df_mut_ref_mut_select, df_dict["propertyView"]
        )
        seqtech_value = [
            seq_tech_dict["value"]
            for seq_tech_dict in tech_options
            if seq_tech_dict["value"] in seqtech_value
        ]

    # # reference
    # if dash.ctx.triggered_id in ["seq_tech_dropdown", "mutation_dropdown", "select_all_mut"]:
    #     df_seq_tech = df_dict['propertyView'][df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value)]
    #     df_mut_mut_select = df_mut[df_mut["variant.label"].isin(mut_value)]
    #     ref_options = get_reference_options_by_filters(df_mut_mut_select, df_seq_tech, reference_options)
    #     reference_options_values = [ref_dict['value'] for ref_dict in ref_options]
    #     try:
    #         reference_value = reference_value if reference_value in reference_options_values else \
    #             reference_options_values[0]
    #     except IndexError:
    #         reference_value = 2

    return mut_options, mut_value, tech_options, seqtech_value


# update map by change of filters or moving slider
@callback(
    Output("world_map_explorer", "figure"),
    [
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("method_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("selected_interval", "value"),
        Input("date_slider", "value"),
    ],
    [
        State("world_map_explorer", "figure"),
    ],
    prevent_initial_call=True,
)
def update_world_map_explorer(
    mutation_list, reference_id, method, seqtech_list, interval, dates, map_json
):
    print("trigger new map")
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    if map_json:
        if "zoom" in map_json["layout"]["mapbox"]:
            zoom = map_json["layout"]["mapbox"]["zoom"]
        else:
            zoom = None
        center = map_json["layout"]["mapbox"]["center"]
    else:
        zoom, center = None, None
    # map mutations, reference_id, seq_tech_list, method, dates, mode='absolute frequencies', nth=0
    fig = world_map.get_world_map(
        mutation_list, reference_id, seqtech_list, method, date_list, zoom, center
    )
    print("fig returned")
    return fig


# slider interval updated during drag (drag_value)
# slider interval updated by play-button and Interval
@callback(
    Output("date_slider", "value"),
    [
        Input("date_slider", "drag_value"),
        Input("selected_interval", "value"),
        Input("auto_stepper", "n_intervals"),
    ],
    [
        State("date_slider", "value"),
    ],
    prevent_initial_call=True,
)
def update_slider_interval(drag_value, interval, n_intervals, slider_value):
    """
    slider moved by user drag, changed location of slider with drag_value
    OR
    slider moved by auto_stepper (activated by play-button)
    """
    if interval is None:
        interval = 0
    # if interval changed or slider moved:
    if dash.ctx.triggered_id in ["selected_interval", "date_slider"]:
        if not drag_value:
            return slider_value
        if len(drag_value) == 2:
            second_date = drag_value[-1]
            if (
                DateSlider.get_date_x_days_before(
                    DateSlider.unix_to_date(second_date), interval
                )
                > date_slider.min_date
            ):
                new_first_date = DateSlider.unix_time_millis(
                    DateSlider.get_date_x_days_before(
                        DateSlider.unix_to_date(second_date), interval
                    )
                )
            else:
                new_first_date = DateSlider.unix_time_millis(date_slider.min_date)
            return [new_first_date, second_date]
        else:
            return slider_value
    # if play button starts auto_stepper
    if dash.ctx.triggered_id == "auto_stepper":
        if n_intervals == 0:
            # raise PreventUpdate
            return slider_value
        if interval is None:
            interval = 7
        if n_intervals + interval >= len(date_slider.date_list):
            first_date = DateSlider.unix_time_millis(date_slider.date_list[-interval])
            second_date = DateSlider.unix_time_millis(date_slider.date_list[-1])
        else:
            first_date = DateSlider.unix_time_millis(
                date_slider.date_list[n_intervals - 1]
            )
            second_date = DateSlider.unix_time_millis(
                date_slider.date_list[n_intervals + interval - 1]
            )  # first_date + interval*86400
        return [first_date, second_date]


@callback(
    [
        Output("auto_stepper", "max_intervals"),
        Output("auto_stepper", "disabled"),
        Output("play_button", "className"),
    ],
    [
        Input("play_button", "n_clicks"),
        Input("auto_stepper", "n_intervals"),
    ],
    [State("selected_interval", "value"), State("play_button", "className")],
    prevent_initial_call=True,
)
def stepper_control(n_clicks, n_intervals, interval, button_icon):
    """
    stop and start auto-stepper (disabled value), returns play or stop icon for button
    interval: increment the counter n_intervals every interval milliseconds.
    disabled (boolean; optional): If True, the counter will no longer update.
    n_intervals (number; default 0): Number of times the interval has passed.
    max_intervals (number; default -1): Number of times the interval will be fired. If -1, then the interval has no limit
    (the default) and if 0 then the interval stops running.
    """
    if interval is None:
        interval = 0
    steps = len(date_slider.date_list) - interval
    # stop stepper
    if dash.ctx.triggered_id == "play_button":
        # start stepper
        if button_icon == "fa-solid fa-circle-play fa-lg":
            return steps, False, "fa-solid fa-circle-stop fa-lg"
        # pause stepper
        elif button_icon == "fa-solid fa-circle-stop fa-lg":
            return steps, True, "fa-solid fa-circle-play fa-lg"
    else:
        if n_intervals == steps:
            return 0, True, "fa-solid fa-circle-play fa-lg"
        else:
            raise PreventUpdate


# update plots
@callback(
    [
        Output("results_per_location", "figure"),
        Output("chosen_location", "children"),
        Output("header_upper_plot", "children"),
    ],
    [
        Input("world_map_explorer", "clickData"),
        Input("mutation_dropdown", "value"),
        Input("method_radio", "value"),
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("date_slider", "value"),
        Input("selected_interval", "value"),
        #   Input('yaxis_type', 'value')
    ],
    prevent_initial_call=True,
)
def update_upper_plot(
    click_data, mutations, method, reference_id, seqtech_list, dates, interval
):
    # get click data {'points': [{'curveNumber': 19, 'pointNumber': 3, 'pointIndex': 3, 'lon': 10.451526,
    # 'lat': 51.165691, 'hovertext': 'Germany', 'marker.size': 30,
    # 'bbox': {'x0': 877.5110333644036, 'x1': 919.9374402355966, 'y0': 243.83076680322816, 'y1': 286.257173674421},
    # 'customdata': ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]}]}
    # print(f"start plot: {datetime.now()}")
    try:
        location_name = click_data["points"][0]["hovertext"]
    except TypeError:
        location_name = "Germany"
    # date from slider
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    # title text
    title_text = location_name
    # 1. plot
    if method == "Increase":
        fig = world_map.get_slope_bar_plot(
            date_list, mutations, reference_id, seqtech_list, location_name
        )
        plot_header = "Slope mutations"
    elif method == "Frequency":
        fig = world_map.get_frequency_bar_chart(
            mutations, reference_id, seqtech_list, date_list, location_name
        )
        plot_header = "Number Sequences"
    return fig, title_text, plot_header


@callback(
    Output("mutation_development", "figure"),
    [
        Input("world_map_explorer", "clickData"),
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("date_slider", "value"),
        Input("selected_interval", "value"),
        Input("results_per_location", "clickData"),
        #   Input('yaxis_type', 'value'),
    ],
    prevent_initial_call=True,
)
def update_lower_plot(
    click_data_map,
    mutations,
    reference_id,
    seqtech_list,
    dates,
    interval,
    clickDataBoxPlot,
):
    # get click data {'points': [{'curveNumber': 19, 'pointNumber': 3, 'pointIndex': 3, 'lon': 10.451526,
    # 'lat': 51.165691, 'hovertext': 'Germany', 'marker.size': 30,
    # 'bbox': {'x0': 877.5110333644036, 'x1': 919.9374402355966, 'y0': 243.83076680322816, 'y1': 286.257173674421},
    # 'customdata': ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]}]}
    # click_data['points'][0]['customdata'] = ['V125G', 167, 'Germany', 51.165691, 10.451526, 30]
    # = [mut, nb_seq, location_name, location_ID, lat, lon, size
    # print(f"start plot: {datetime.now()}")
    if dash.ctx.triggered_id == "results_per_location":
        mutations = [clickDataBoxPlot["points"][0]["label"]]
    try:
        location_name = click_data_map["points"][0]["hovertext"]
    except TypeError:
        location_name = "Germany"
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    fig_develop = world_map.get_frequency_development_scatter_plot(
        mutations, reference_id, seqtech_list, date_list, location_name
    )
    return fig_develop


# fill table
@callback(
    [
        Output(component_id="table_explorer", component_property="data"),
        Output(component_id="table_explorer", component_property="columns"),
    ],
    [
        Input("mutation_dropdown", "value"),
        Input("reference_radio", "value"),
        Input("seq_tech_dropdown", "value"),
        Input("selected_interval", "value"),
        Input("date_slider", "value"),
    ],
    prevent_initial_call=True,
)
def update_table_filter(mutation_list, reference_id, seqtech_list, interval, dates):
    date_list = date_slider.get_all_dates_in_interval(dates, interval)
    table_df = table_filter.get_filtered_table(
        mutation_list, seqtech_list, reference_id, date_list
    )
    return table_df.to_dict("records"), [{"name": i, "id": i} for i in table_df.columns]
