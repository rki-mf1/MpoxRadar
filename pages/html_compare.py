from datetime import date

from dash import dash_table
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


def html_date_picker(d_id):
    today = date.today()
    date_picker = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Date interval:"),
                dcc.DatePickerRange(
                    id=f"date_picker_range_{d_id}",
                    start_date="1960-01-01",
                    end_date=today,
                    min_date_allowed=date(1960, 1, 1),
                    max_date_allowed=today,
                    initial_visible_month=date(2022, 1, 1),
                ),
            ]
        )
    )
    return date_picker


def html_aa_nt_radio():
    item = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label(
                        "Compare amino acid  or nucleotide mutations:",
                        color="primary",
                    ),
                    dbc.RadioItems(
                        options=[
                            {"label": "Amino Acids", "value": "cds"},
                            {"label": "Nucleotides", "value": "source"},
                        ],
                        value="cds",
                        inline=True,
                        style={
                            "font-size": 20,
                            "font-weight": "bold",
                            "align-itmes": "center",
                            "textAlign": "center",
                        },
                        id="aa_nt_radio",
                    ),
                    dbc.Badge(
                        "Warning: The nucleotide option might take a long time to compute.",
                        color="warning",
                        className="me-1",
                    ),
                ],
            ),
        ],
    )
    return item


def html_compare_button():
    return dbc.Button(
        [
            html.I(className="fa-solid fa-magnifying-glass-chart me-1"),
            "Compare",
        ],
        id="compare_button",
        size="lg",
        className="me-1",
        color="primary",
        style={
            "font-weight": "bold",
        },
        n_clicks=0,
    )


# TODO left column very wide, others to small, I want fill_width=False, but currently with bug, waitinng for update
def overview_table(df, column_names, title, tool):
    Output_table_standard = (
        dbc.Col(
            xs=0,
            sm=0,
            md=1,
            lg=1,
            xl=1,  # This sets the column width for different screen sizes
        ),
        dbc.Col(
            dbc.Card(
                [
                    html.H3(title),
                    dash_table.DataTable(
                        data=df.to_dict("records"),
                        columns=[
                            {"name": column_names[i], "id": j}
                            for i, j in enumerate(df.columns)
                        ],
                        id=f"table_{tool}",
                        page_current=0,
                        page_size=5,
                        style_data={
                            "whiteSpace": "normal",
                            "height": "auto",
                            "lineHeight": "15px",
                            # all three widths are needed
                            "minWidth": "100%",
                            "width": "400px",
                            "maxWidth": "750px",
                            "textAlign": "left",
                        },
                        style_header={
                            "whiteSpace": "pre-line",
                            "height": "auto",
                            "lineHeight": "15px",
                            "fontWeight": "bold",
                            "minWidth": "130px",
                            "width": "auto",
                            "maxWidth": "400px",
                            "textAlign": "center",
                        },
                        style_cell={"fontSize": 12},
                        style_table={"overflowX": "auto"},
                        export_format="csv",
                        # fill_width=False,
                    ),
                ],
                body=True,
                className="mx-1 my-1",
            ),
            xs=12,
            sm=12,
            md=10,
            lg=10,
            xl=10,  # This sets the column width for different screen sizes
        ),
        dbc.Col(
            xs=0,
            sm=0,
            md=1,
            lg=1,
            xl=1,
        ),
    )
    return Output_table_standard
