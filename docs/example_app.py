import argparse
import os

from dash import Dash
from dash import dash_table
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import State
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import pandas as pd

from pages.app_controller import get_all_references
from pages.app_controller import get_freq_mutation
from pages.app_controller import get_value_by_reference
from pages.app_controller import match_controller
from pages.app_controller import sonarBasicsChild
from pages.libs.mpxsonar.src.mpxsonar.sonar import parse_args

load_dotenv()
# stylesheet with the .dbc class
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css])
df = pd.DataFrame(
    {
        "First Name": ["Arthur", "Ford", "Zaphod", "Trillian"],
        "Last Name": ["Dent", "Prefect", "Beeblebrox", "Astra"],
    }
)
# preload
dat_checkbox_list_of_dict = get_all_references()
server = app.server

tool_checkbox_cards = html.Div(
    [
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        dbc.CardHeader("FILTER"),
                        dbc.Row(
                            [
                                html.H3("Reference", className="card-title"),
                                dbc.Col(
                                    [
                                        dcc.Checklist(
                                            id="reference-selection",
                                            options=dat_checkbox_list_of_dict,
                                            labelStyle={"display": "block"},
                                            style={
                                                "height": 100,
                                                "width": 200,
                                                "overflow": "auto",
                                            },
                                        )
                                    ]
                                ),
                                dbc.Spinner(html.Div(id="loading-output")),
                                html.Div(id="display-selected-values"),
                                html.Hr(),
                                html.Div(id="table1-results"),
                            ]
                        ),
                    ]
                ),
            ]
        ),
    ]
)

custom_cmd_cards = html.Div(
    [
        dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H3(
                            [
                                "MPXSonar command!",
                                dbc.Badge(
                                    "Alpha-Test", className="ms-1", color="warning"
                                ),
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
                                                    value="match --count",
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
                dbc.Card(  # Output
                    [
                        html.H4("Output:"),
                        html.Hr(),
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
                    body=True,
                    className="mx-1 my-1",
                ),  # end of Output
            ],
            className="mb-3",
        ),
    ]
)

app.layout = dbc.Container(
    [
        dbc.Row([tool_checkbox_cards]),
        html.Hr(),
        dbc.Row(
            [
                custom_cmd_cards,
                html.Br(),
            ]
        ),
    ]
)


@app.callback(
    Output("loading-output", "children"),
    Output("display-selected-values", "children"),
    Output("table1-results", "children"),
    Input(component_id="reference-selection", component_property="value"),
)
def checkbox(checked_value):
    output_df = ""
    print(checked_value)
    if len(checked_value) == 0:
        return "", "", output_df
    else:
        output_df = get_value_by_reference(checked_value)
    print(len(output_df))
    return (
        "",
        "{}".format(checked_value),
        dbc.Table.from_dataframe(
            output_df[0:5], striped=True, bordered=True, hover=True
        ),
    )


@app.callback(
    Output(component_id="my-command", component_property="children"),
    Input(component_id="my-input", component_property="value"),
)
def update_output_div(input_value):
    return f"sonar {input_value}"


@app.callback(
    Output(component_id="my-output", component_property="children"),
    Output(component_id="my-output-df", component_property="data"),
    Output(component_id="my-output-df", component_property="columns"),
    Input("submit-button-state", "n_clicks"),
    State("my-input", "value"),
)
def update_output_sonar(n_clicks, commands):
    # calls backend
    _list = commands.split()
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


if __name__ == "__main__":
    app.run_server(
        debug=os.getenv("DEBUG"), host=os.getenv("SERVER"), port=os.getenv("PORT")
    )
