from dash import dash_table
from dash import dcc
from dash import html
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
                    style={
                        "font-size": 20,
                        "align-itmes": "center",
                        "margin": "auto"
                    },
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


def html_elem_dropdown_aa_mutations_without_max(mutation_options, title, elem_id):
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
                            id=f"mutation_dropdown_{elem_id}",
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
            dbc.CardFooter([
                dbc.Row(
                    [
                        dbc.Label(
                            "Number mutations",
                            id=f"max_nb_txt_{elem_id}",
                        ),
                        dcc.Checklist(
                            id=f"select_all_mutations_{elem_id}",
                            options=[{"label": "Select All", "value": 1}],
                            value=[1],
                        ),
                    ]
                ),
                html.Br(),
                dbc.Row(
                    [
                        dbc.Label(
                            "Select minimum variant frequency. Highest frequency in selection: 0",
                            id=f"min_nb_freq_{elem_id}",
                        ),
                        html.Br(),
                        dcc.Input(
                            id=f"select_min_nb_frequent_mut_{elem_id}",
                            type="number",
                            placeholder=1,
                            value=1,
                            className="input_field",
                            min=1,
                        ),
                        html.Br(),
                        dbc.Tooltip(
                            "Specifies the minimum number of sequences in which the variant must occur to be listed "
                            "here. Highest frequency represents the highest number of sequences sharing the same "
                            "variant. E.g., a minimum variant frequency of 2 remove all variants detected "
                            "only once.",
                            target=f"min_nb_freq_{elem_id}",
                        ),
                    ]
                ),
            ]
            ),
            dcc.Store(id='compare_shared_dict'),
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
                            value=[c["value"] for c in countries if not c["disabled"]],
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
                            'overflowX': 'auto'
                        },
                        id=f"complete_partial_radio_{tab}",
                    ),
                ],
            ),
        ],
    )
    return item


def html_disclaimer_seq_errors(tool, only_cds=False):
    t = ""
    if not only_cds:
        t = ", nucleotide mutations containing N"
    disclaimer = dbc.Alert(
        [
            html.I(className="bi bi-info-circle-fill me-2"),
            f"Sequencing errors are not shown. \n Amino acids mutations containing X{t} are excluded.",
        ],
        className="d-flex align-items-center",
        color="#FFCC00",
        id=f"disclaimer_mutation_{tool}",
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
                                            "minWidth": "100%",
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


def small_table(df, title, tool):
    Output_table_standard = (
        dbc.Col(
            xs=12, sm=12, md=3, lg=3, xl=3,  # This sets the column width for different screen sizes
        ),
        dbc.Col(
            dbc.Card(
                [
                    html.H3(title),
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
                            "minWidth": "100%",
                            "width": "400px",
                            "maxWidth": "750px",
                        },
                        style_cell={"fontSize": 12},
                        style_table={"overflowX": "auto"},
                        export_format="csv",
                    ),
                ],
                body=True,
                className="mx-1 my-1",
            ),
            xs=12, sm=12, md=7, lg=7, xl=7,  # This sets the column width for different screen sizes
        ),
        dbc.Col(
            xs=12, sm=12, md=2, lg=2, xl=2,
        ),
    )
    return Output_table_standard
