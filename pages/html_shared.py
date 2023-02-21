from dash import dcc
from dash import html
import dash_bootstrap_components as dbc


def get_html_elem_reference_radioitems(reference_options, start_ref_id, radio_id=0):
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


def get_html_elem_dropdown_genes(gene_options, g_id=0):
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
                                value=[c["value"] for c in gene_options],
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


def get_html_elem_dropdown_aa_mutations_without_max(mutation_options, title, aa_id):
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
                    dbc.Label(
                        "Number mutations",
                        id=f"max_nb_txt_{aa_id}",
                    ),
                ),
            ),
        ]
    )
    return checklist_aa_mutations


def get_html_elem_checklist_seq_tech(seq_tech_options, s_id=0):
    checklist_seq_tech = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label("Sequencing Technology: "),
                    dbc.Spinner(
                        dbc.Checklist(
                            options=seq_tech_options,
                            value=[
                                tech_dict["value"] for tech_dict in seq_tech_options
                            ],
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
def get_html_elem_dropdown_countries(countries, c_id=0):
    checklist_aa_mutations = dbc.Card(
        [
            dbc.CardBody(
                [
                    dbc.Label("Country: "),
                    html.Br(),
                    dbc.Spinner(
                        dcc.Dropdown(
                            options=countries,
                            value=[c["value"] for c in countries],
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


def get_html_complete_partial_radio(tab):
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
                            {"label": "Complete & partial genomes", "value": "partial"},
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