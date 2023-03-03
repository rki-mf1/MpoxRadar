from dash import dcc
from dash import html
from dash import dash_table
import dash_bootstrap_components as dbc


def html_elem_reference_radioitems(reference_options, start_ref_id, radio_id=0):
    checklist_reference = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Reference genome: "),
                dbc.RadioItems(
                    options=reference_options,
                    value=start_ref_id,
                    id=f"reference_radio_{radio_id}",
                ),
            ]
        )
    )
    return checklist_reference


def html_elem_dropdown_genes(gene_options, g_id=0):
    checklist_aa_mutations = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label("Gene: "),
                    html.Br(),
                    dbc.Row(
                        dbc.Spinner(
                            dcc.Dropdown(
                                options=gene_options,
                                value=[g['value'] for g in gene_options],
                                id=f"gene_dropdown_{g_id}",
                                # maxHeight=200,  # just height of dropdown not choose option field
                                optionHeight=35,  # height options in dropdown, not chosen options
                                multi=True,
                                searchable=True,
                            ),
                            color="dark",
                            type="grow",
                        ),
                    ),
                ],
                style={
                    "overflow-y": "auto",  # without not scrollable, just cut
                    "maxHeight": 300,
                    "minHeight": 200,
                },  # height field
            ),
            dbc.CardFooter(
                dbc.Row(
                    dcc.Checklist(
                        id=f"select_all_genes_{g_id}",
                        options=[{"label": "Select All", "value": 1}],
                        value=[1],
                    ),
                ),
            ),
        ]
    )
    return checklist_aa_mutations


def html_elem_dropdown_aa_mutations_without_max(mutation_options, title, aa_id):
    checklist_aa_mutations = dbc.Card(
        [
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
                            optionHeight=50,
                            multi=True,
                            searchable=True,
                        ),
                        color="danger",
                        type="grow",
                    ),
                    html.Br(),
                ],
                style={"overflow-y": "auto", "maxHeight": 300, "minHeight": 200},
            ),
            dbc.CardFooter(
                dbc.Row(
                    [
                        dbc.Label(
                            "Number mutations",
                            id=f"max_nb_txt_{aa_id}",
                        ),
                        dcc.Checklist(
                            id=f"select_all_mutations_{aa_id}",
                            options=[{"label": "Select All", "value": 1}],
                            value=[1],
                        ),
                    ]
                ),
            ),
        ]
    )
    return checklist_aa_mutations


def html_elem_checklist_seq_tech(seq_tech_options, s_id=0):
    checklist_seq_tech = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label("Sequencing Technology: "),
                    dbc.Spinner(
                        dbc.Checklist(
                            options=seq_tech_options,
                            value=[s['value'] for s in seq_tech_options if not s['disabled']],
                            id=f"seq_tech_dropdown_{s_id}",
                            labelStyle={"display": "block"},
                            style={
                                "maxHeight": 200,
                                "overflowY": "scroll",
                            },
                        ),
                        color="primary",
                        type="grow",
                    ),
                ],
            ),
            dbc.CardFooter(
                dbc.Row(
                    dcc.Checklist(
                        id=f"select_all_seq_tech_{s_id}",
                        options=[{"label": "Select All", "value": 1}],
                        value=[1],
                    ),
                ),
            ),
        ]
    )
    return checklist_seq_tech


# TODO design dropdown
def html_elem_dropdown_countries(countries, c_id=0):
    checklist_aa_mutations = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label("Country: "),
                    html.Br(),
                    dbc.Spinner(
                        dcc.Dropdown(
                            options=countries,
                            value=[c['value'] for c in countries if not c['disabled']],
                            id=f"country_dropdown_{c_id}",
                            # maxHeight=200,
                            optionHeight=35,
                            multi=True,
                            searchable=True,
                        ),
                        color="danger",
                        type="grow",
                    ),
                ],
                style={
                    "overflow-y": "auto",  # without not scrollable, just cut
                    "maxHeight": 300,
                    "minHeight": 200,
                },  # height field
            ),
            dbc.CardFooter(
                dbc.Row(
                    dcc.Checklist(
                        id=f"select_all_countries_{c_id}",
                        options=[{"label": "Select All", "value": 1}],
                        value=[1],
                    ),
                ),
            ),
        ]
    )
    return checklist_aa_mutations


def html_complete_partial_radio(tab):
    item = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label(
                        "Use all genomes (including partial sequences) or only complete genomes:",
                        color="primary",
                    ),
                    dbc.RadioItems(
                        options=[
                            {"label": "Complete Genomes", "value": "complete"},
                            {"label": "Complete & Partial Genomes", "value": "partial"},
                        ],
                        value="complete",
                        inline=True,
                        style={
                            "font-size": 20,
                            "font-weight": "bold",
                            "align-itmes": "center",
                            "textAlign": "center",
                        },
                        id=f"complete_partial_radio_{tab}",
                    ),
                ],
            ),
        ],
    )
    return item


def html_disclaimer_seq_errors(tool):
    disclaimer = dcc.Markdown(
        "Sequencing errors are not shown. \n Amino acids mutations containing X, nucleotide mutations "
        "containing N are excluded.",
        className="me-1",
        style={
            "font-size": 20,
            "font-weight": "bold",
            "align-itmes": "center",
            "textAlign": "center",
            "color": "white",
            "white-space": "pre",
            "background-color": "#ffbd33"
        },
        id=f"disclaimer_mutation_{tool}"
    )
    return disclaimer


def html_table(df, title, tool):
    Output_table_standard = dbc.Card(
        [
            html.H3(title),
            dbc.Accordion(
                [
                    dbc.AccordionItem(
                        [
                            html.Div(id=f"filter-table-output_{tool}", children=""),
                            html.Div(
                                [
                                    dash_table.DataTable(
                                        data=df.to_dict("records"),
                                        columns=[
                                            {"name": i, "id": i} for i in df.columns
                                        ],
                                        id=f"table_{tool}",
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
