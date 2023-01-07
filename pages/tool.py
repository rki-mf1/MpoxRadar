import argparse
import shlex

import dash
from dash import callback
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import State
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from pages.config import logging_radar
from pages.util_tool_checklists import checklist_1
from pages.util_tool_checklists import checklist_2
from pages.util_tool_checklists import checklist_3
from pages.util_tool_checklists import checklist_4
from pages.util_tool_mpoxsonar import Output_mpxsonar
from pages.util_tool_mpoxsonar import query_card
from .app_controller import get_freq_mutation
from .app_controller import get_value_by_filter
from .app_controller import match_controller
from .app_controller import sonarBasicsChild
from .libs.mpxsonar.src.mpxsonar.sonar import parse_args

dash.register_page(__name__, path="/Tool")


# example data for example map
# note_data = pd.read_csv("data/Data.csv")

# predefine
coord_data = pd.read_csv("data/location_coordinates.csv")

# 56 colors
color_schemes = (
    px.colors.cyclical.Twilight
    + px.colors.cyclical.IceFire
    + px.colors.cyclical.Phase
    + px.colors.cyclical.Edge
)

layout = html.Div(
    [
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
        html.Div(
            [
                dbc.Row(
                    dbc.Col(
                        html.H1(
                            [
                                "MpoxSonar Tool!",
                                # dbc.Badge(
                                #     "Test", className="ms-1", color="warning"
                                # ),
                            ]
                        )
                    )
                ),
                dbc.Row(dbc.Col(query_card)),
                dbc.Row(dbc.Col(Output_mpxsonar)),
                # html.Button("Download CSV", id="csv-download"),
                # dcc.Download(id="df-download"),
            ]
        ),
    ]
)


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

    output_df = get_value_by_filter(ref_checklist, mut_checklist, seqtech_checklist)
    output_df = calculate_coordinate(output_df)
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


def calculate_coordinate(ouput_df):
    """
    TODO:
    1. improve performance of map
    """

    # concate the coordinate
    result = pd.merge(ouput_df, coord_data, left_on="COUNTRY", right_on="name")
    result.drop(columns=["location_ID", "name"], inplace=True)

    # result["number"] = [
    #    len(x.split(",")) for x in result["NUC_PROFILE"]
    # ]  # just count all mutation occur in each sample.
    # new_res = result.groupby(['COUNTRY', 'lon', 'lat', 'RELEASE_DATE'])['number'].sum().reset_index()

    # sort DATE
    result["RELEASE_DATE"] = pd.to_datetime(result["RELEASE_DATE"]).dt.date
    result.sort_values(by="RELEASE_DATE", inplace=True)
    return result


def calculate_accumulator(ouput_df, column_profile="NUC_PROFILE"):
    # NOTE: Now we change the CaseNumber to MutationNumber

    # NOTE: add Date for accumulation?

    # FIXME: Remove emtpy mutation profile, please note disable this IF needed,
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
    # Drop duplication
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
    a = ouput_df[column_profile].unique()
    logging_radar.debug(a)
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
        badge = html.Div([dbc.Badge("Look ok!", color="success", className="me-1")])
        _list = shlex.split(input_value)
        args = parse_args(_list)
        print(args)

    except Exception:
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

    return toggle_value, output, data, columns


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
    """
    Callback handle sonar ouput to map.
    """
    hidden_state = {"display": "none"}
    if not rows:
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
        return fig, "", hidden_state

    table_df = pd.DataFrame(rows, columns=[c["name"] for c in columns])
    selected_column = [
        "COUNTRY",
        "COLLECTION_DATE",
        "RELEASE_DATE",
        "AA_PROFILE",
        "REFERENCE_ACCESSION",
    ]
    table_df = table_df[selected_column]
    table_df = calculate_coordinate(table_df)
    table_df = calculate_accumulator(table_df, "AA_PROFILE")
    fig = px.scatter_mapbox(
        table_df,
        lat="lat",
        lon="lon",
        size="Case",
        animation_frame="RELEASE_DATE",
        animation_group="AA_PROFILE",
        size_max=20,
        height=800,
        zoom=3,
        hover_data={
            "lat": False,
            "lon": False,
            "RELEASE_DATE": True,
            "Case": True,
            "COUNTRY": True,
        },  # ["NUC_PROFILE", "COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=53, lon=9),
        mapbox_style="carto-positron",
        color="AA_PROFILE",
        color_discrete_sequence=color_schemes,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig, hidden_state


@callback(
    Output("4_checklist_input", "value"),
    [Input("seqtech_all-or-none", "value")],
    [State("4_checklist_input", "options")],
)
def seqtech_select_all_none(all_selected, options):
    """
    Callback handle select all seq tech
    """
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none


@callback(
    Output("2_checklist_input", "value"),
    [Input("mutation_all-or-none", "value")],
    [State("2_checklist_input", "options")],
)
def mutation_select_all_none(all_selected, options):
    """
    Callback handle select all NT mutation
    """
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none
