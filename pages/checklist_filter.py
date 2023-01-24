from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
import pandas as pd


def get_all_frequency_sorted_seqtech(propertyView):
    df_grouped_by_seqtech = (
        propertyView[["sample.id", "SEQ_TECH"]]
        .groupby(["SEQ_TECH"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_seqtech = df_grouped_by_seqtech["SEQ_TECH"].tolist()
    sorted_seqtech = [
        "not defined" if seqtech == "" else seqtech for seqtech in sorted_seqtech
    ]
    sorted_seqtech_dict = [
        {"label": seqtech, "value": seqtech} for seqtech in sorted_seqtech
    ]
    return sorted_seqtech_dict


def get_all_frequency_sorted_mutation(variantView, reference_id):
    df_grouped_by_mutation = (
        variantView[
            (variantView["element.type"] == "cds")
            & (variantView["reference.id"] == int(reference_id))
        ][["sample.id", "variant.label"]]
        .groupby(["variant.label"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_mutations = df_grouped_by_mutation["variant.label"].tolist()
    sorted_mutations_dict = [{"label": mut, "value": mut} for mut in sorted_mutations]
    return sorted_mutations_dict


# TODO check when reference.accession = NA, ""
def get_all_references(variantView):
    references = (
        variantView[["reference.accession", "reference.id"]]
        .dropna()
        .drop_duplicates()
        .values.tolist()
    )
    references.sort(key=lambda x: x[1])
    references = [{"label": x[0], "value": x[1], "disabled": False} for x in references]
    return references


def get_frequency_sorted_mutation_by_filters(df_mut_ref_select, df_seq_tech):
    df_merge = pd.merge(df_mut_ref_select, df_seq_tech, how="left", on="sample.id")[
        ["sample.id", "variant.label"]
    ]
    df_grouped_by_mutation = (
        df_merge.groupby(["variant.label"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_mutations = df_grouped_by_mutation["variant.label"].tolist()
    sorted_mutations_dict = [{"label": mut, "value": mut} for mut in sorted_mutations]
    return sorted_mutations_dict


# def get_reference_options_by_filters(df_mut_select, df_seq_tech, reference_opt):
#     """
#         variantView contains selected mutations rows
#     """
#     df_merge =  pd.merge(df_mut_select, df_seq_tech,
#                          how="left",
#                          on="sample.id")
#     df_merge = df_merge[['reference.id', "reference.accession"]].drop_duplicates()
#     for ref_opt in reference_opt:
#         if not ref_opt['value'] in df_merge['reference.id'].tolist():
#             ref_opt['disabled'] = True
#     print(reference_opt)
#     return reference_opt


def get_frequency_sorted_seq_techs_by_filters(df_mut_ref_select, propertyView):
    df = pd.merge(df_mut_ref_select, propertyView, how="left", on="sample.id")
    df_grouped_by_seq_tech = (
        df[["sample.id", "SEQ_TECH"]]
        .groupby(["SEQ_TECH"])
        .count()
        .reset_index()
        .sort_values(["sample.id"], ascending=False)
    )
    sorted_seq_tech_list = df_grouped_by_seq_tech["SEQ_TECH"].tolist()
    sorted_seq_tech_list = [
        "not defined" if seqtech == "" else seqtech for seqtech in sorted_seq_tech_list
    ]
    sorted_seq_tech_dict = [
        {"label": seqtech, "value": seqtech} for seqtech in sorted_seq_tech_list
    ]
    return sorted_seq_tech_dict


def get_html_interval(interval=100):
    interval_card = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Interval: "),
                dcc.Input(
                    id="selected_interval",
                    type="number",
                    placeholder=interval,
                    value=interval,
                    className="input_field",
                    min=1,
                ),
            ]
        )
    )
    return interval_card


def get_html_elem_reference_radioitems(reference_options):
    checklist_reference = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Reference genome: "),
                dbc.RadioItems(
                    options=reference_options,
                    value=2,
                    id="reference_radio",
                ),
                dbc.FormText(
                    "Only one reference allowed.",
                    color="secondary",
                ),
            ]
        )
    )
    return checklist_reference


# TODO : checklist not searchable, change to dropdown?
def get_html_elem_checklist_aa_mutations(df_variantView, reference_id):
    checklist_aa_mutations = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("AA mutations: "),
                html.Br(),
                dcc.Dropdown(
                    options=get_all_frequency_sorted_mutation(
                        df_variantView, reference_id
                    ),
                    value=[
                        mut_dict["value"]
                        for mut_dict in get_all_frequency_sorted_mutation(
                            df_variantView, reference_id
                        )[0:20]
                    ],
                    id="mutation_dropdown",
                    multi=True,
                    searchable=True,
                    style={"overflow-y": "auto", "max-height": "200px"},
                ),
                dcc.Checklist(
                    id="select_all_mut",
                    options=[{"label": "Select All", "value": 1}],
                    value=[],
                ),
                html.Br(),
                # dbc.Checklist(
                #     id="mutation_all-or-none",
                #     options=[{"label": "Select All", "value": "All"}],
                #     value=["All"],
                #     labelStyle={"display": "inline-block"},
                # ),
                dbc.FormText(
                    "sorted by most common mutations",
                    color="secondary",
                ),
            ],
        )
    )
    return checklist_aa_mutations


def get_html_elem_method_radioitems():
    checklist_methode = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Visualisation method: "),
                dbc.RadioItems(
                    options=[
                        {"label": "Frequencies", "value": "Frequency"},
                        {"label": "Increasing Trend", "value": "Increase"},
                    ],
                    value="Frequency",
                    id="method_radio",
                ),
            ],
        )
    )
    return checklist_methode


def get_html_elem_checklist_seq_tech(seq_tech_options):
    checklist_seq_tech = dbc.Card(
        dbc.CardBody(
            [
                dbc.Label("Sequencing Technology used: "),
                dbc.Checklist(
                    options=seq_tech_options,
                    value=[tech_dict["value"] for tech_dict in seq_tech_options],
                    id="seq_tech_dropdown",
                    labelStyle={"display": "block"},
                    style={
                        "height": 120,
                        "overflowY": "scroll",
                    },
                ),
                html.Br(),
                dcc.Checklist(
                    id="select_all_seq_tech",
                    options=[{"label": "Select All", "value": 1}],
                    value=[1],
                ),
            ],
        )
    )
    return checklist_seq_tech
