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

from pages.util_tool_checklists import checklist_1
from pages.util_tool_checklists import checklist_2
from pages.util_tool_checklists import checklist_3
from pages.util_tool_checklists import checklist_4
from pages.util_tool_checklists import query_card, Output_mpxsonar
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
sql_query = (
    ""
    "SELECT t6.value_text, t1.label, value_date, count(*)"
    "FROM "
    "variant t1 "
    "JOIN alignment2variant t2 ON t1.id = t2.variant_id "
    "JOIN alignment t3 ON t2.alignment_id = t3.id "
    "JOIN sequence t4 ON t3.seqhash = t4.seqhash "
    "JOIN sample t5 ON t4.seqhash = t5.seqhash"
    "JOIN sample2property t6 ON t5.id = t6.sample_id"
    "WHERE"
    "t1.label LIKE 'del%'"
    "GROUP BY"
    "t6.value_text, t1.label, value_date"
    "limit 250"
    ";"
)
layout = html.Div(
    [      
        html.Div(id= "alertmsg"),
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
        html.P(id="checklist-output"),
        query_card,
        html.Br(style={"lineHeight": "10"}),
        html.Div(
            [
                dbc.Spinner(
                    html.Div(id="loading-output"),
                    fullscreen=True,
                    color="info",
                    type="grow",
                    spinner_style={"width": "3rem", "height": "3rem"},
                ),
                html.Br(),
                html.H1("Here is a map"),
                dcc.Graph(id="my-map"),
                html.Br(),
                html.Div(
                    [
                        # html.Button("Download CSV", id="csv-download"),
                        # dcc.Download(id="df-download"),
                        Output_mpxsonar
                    ]
                ),
            ]
        ),
    ]
)



@callback(
    Output("alertmsg", "children"),
    Output("loading-output", "children"),
    Output("my-map", component_property="figure"),
    [
        Input("1_checklist_input", "value"),
        Input("2_checklist_input", "value"),
        Input("3_checklist_input", "value"),
        Input("4_checklist_input", "value"),
        Input("mpoxsonar_output_checkbox", "value"),
        Input("my-output-df", "data"),
        Input("my-output-df", "columns"),
    ],
)
def update_figure(
    ref_checklist, mut_checklist, viz_checklist, seqtech_checklist, mpoxsonar_check,
    rows, columns
):
    alertmsg = ""
    all_or_none = ref_checklist + mut_checklist + viz_checklist + seqtech_checklist
    output_df = pd.DataFrame(columns=['COUNTRY','RELEASE_DATE', 'lat','lon','CaseNumber'])
    if mpoxsonar_check:
        print(rows)

        print(columns)
        if  rows is not None:
            output_df = pd.DataFrame(rows, columns=[c['name'] for c in columns])
            output_df = calculate_coordinate(output_df)

        else:
            alertmsg= dbc.Alert("Table result is empty, please submit a query", color="warning", dismissable=True)   
    else:
        if len(all_or_none) == 0:
            msg = "All"
        else:
            msg = all_or_none
        print(msg)

        output_df = get_value_by_filter(ref_checklist, mut_checklist, seqtech_checklist)

        output_df = calculate_coordinate(output_df)


    fig = px.scatter_mapbox(
        output_df,
        lat="lat",
        lon="lon",
        size="CaseNumber",
        animation_frame="RELEASE_DATE",
        animation_group="COUNTRY",
        size_max=50,
        zoom=1,
        hover_data=["COUNTRY", "RELEASE_DATE", "CaseNumber"],
        center=dict(lat=8.584314, lon=-75.95781),
        mapbox_style="carto-positron",
        color="CaseNumber",
        color_continuous_scale=px.colors.sequential.Reds,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    return alertmsg, "", fig


def calculate_coordinate(ouput_df):
    # concate the coordinate
    result = pd.merge(ouput_df, coord_data, left_on="COUNTRY", right_on="name")
    result.drop(columns=["location_ID", "name"], inplace=True)
    
    result['number'] = [len(x.split(',')) for x in result['NUC_PROFILE']] # just count all mutation occur in each sample.
    # new_res = result.groupby(['COUNTRY', 'lon', 'lat', 'RELEASE_DATE'])['number'].sum().reset_index()

    # sort DAte
    result["RELEASE_DATE"] = pd.to_datetime(result["RELEASE_DATE"]).dt.date
    result.sort_values(by="RELEASE_DATE", inplace=True)
    result["CaseNumber"] = result.groupby(["COUNTRY", "RELEASE_DATE"])["COUNTRY"].transform(
        "count"
    )

    # change the CaseNumber to MutationNumber

    # add accumulator?

    print(result)
    return result


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
    Input(component_id="my-input", component_property="value"),
)
def update_output_div(input_value):
    return f"sonar {input_value}"


@callback(
    Output(component_id="my-output", component_property="children"),
    Output(component_id="my-output-df", component_property="data"),
    Output(component_id="my-output-df", component_property="columns"),
    Input("submit-button-state", "n_clicks"),
    State("my-input", "value"),
)
def update_output_sonar(n_clicks, commands):
    """
        Callback handle mpxsonar commands
    """
    # calls backend
    _list = shlex.split(commands)
    print(_list)
    # need to implement mini parser
    data = None
    columns = None
    try:
        args = parse_args(_list)
        output = ""
        if args.tool == "list-prop":
            df = sonarBasicsChild.list_prop()
            columns = [{"name": col, "id": col} for col in df.columns]
            data = df.to_dict(orient="records")
        elif args.tool == "match":
            _tmp_output = match_controller(args)
            if type(_tmp_output) == int:
                output = _tmp_output
            elif type(_tmp_output) == str:
                output = _tmp_output
            else:
                df = _tmp_output
                columns = [{"name": col, "id": col} for col in df.columns]
                data = df.to_dict(orient="records")
        elif args.tool == "dev":
            get_freq_mutation(args)
        else:
            output = "This command is not available."

    except argparse.ArgumentError as exc:
        output = exc.message
    except SystemExit:
        output = "error: unrecognized arguments/commands"
    return output, data, columns

@callback(
    Output("4_checklist_input", "value"),
    [Input("seqtech_all-or-none", "value")],
    [State("4_checklist_input", "options")],
)
def seqtech_select_all_none(all_selected, options):
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none

@callback(
    Output("2_checklist_input", "value"),
    [Input("mutation_all-or-none", "value")],
    [State("2_checklist_input", "options")],
)
def mutation_select_all_none(all_selected, options):
    all_or_none = []
    all_or_none = [option["value"] for option in options if all_selected]
    return all_or_none 
  
