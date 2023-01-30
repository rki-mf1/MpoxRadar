from dash import callback
from dash import Input
from dash import Output
from dash import State
import dash
import pandas as pd
import datetime

from pages.utils_explorer_filter import get_all_frequency_sorted_countries
from pages.utils_explorer_filter import get_all_frequency_sorted_seqtech
from pages.utils_explorer_filter import get_all_genes_per_reference
from pages.utils_explorer_filter import get_frequency_sorted_mutation_by_filters
from pages.utils_worldMap_explorer import DateSlider


def get_compare_callbacks(df_dict, variantView_cds, color_dict):
    @callback(
        [
            Output("mutation_dropdown_1", "options"),
            Output("mutation_dropdown_1", "value"),
            Output('max_nb_txt_1', 'children'),
            Output("mutation_dropdown_2", "options"),
            Output("mutation_dropdown_2", "value"),
            Output('max_nb_txt_2', 'children'),
            Output("mutation_dropdown_3", "options"),
            Output("mutation_dropdown_3", "value"),
            Output('max_nb_txt_3', 'children'),
            Output(component_id="table_compare_1", component_property="data"),
            Output(component_id="table_compare_1", component_property="columns"),
            Output(component_id="table_compare_2", component_property="data"),
            Output(component_id="table_compare_2", component_property="columns"),
            Output(component_id="table_compare_3", component_property="data"),
            Output(component_id="table_compare_3", component_property="columns")
        ],
        [
            Input("compare_button", "n_clicks"),
        ],
        [
            State("gene_dropdown_1", "value"),
            State("gene_dropdown_2", "value"),
            State("reference_radio_1", "value"),
            State("seq_tech_dropdown_1", "value"),
            State("country_dropdown_1", "value"),
            State("reference_radio_2", "value"),
            State("seq_tech_dropdown_2", "value"),
            State("country_dropdown_2", "value"),
            Input("date_picker_range_1", "start_date"),
            Input("date_picker_range_1", "end_date"),
            Input("date_picker_range_2", "start_date"),
            Input("date_picker_range_2", "end_date"),
        ],
        prevent_initial_call=False,
    )
    def actualize_mutation_filter(
            compare_button,
            gene_value_1,
            gene_value_2,
            reference_value_1,
            seqtech_value_1,
            country_value_1,
            reference_value_2,
            seqtech_value_2,
            country_value_2,
            start_date_1,
            end_date_1,
            start_date_2,
            end_date_2):
        date_list_1 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_1, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_1, "%Y-%m-%d").date()
        )
        variantView_cds_ref_1 = variantView_cds[
            (variantView_cds['reference.id'] == reference_value_1)
        ]
        propertyView_seq_country_1 = df_dict['propertyView'][
            (df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value_1)) &
            (df_dict['propertyView']["COUNTRY"].isin(country_value_1)) &
            (df_dict['propertyView']["COLLECTION_DATE"].isin(date_list_1))
            ]
        variantView_cds_ref_gene_1 = variantView_cds_ref_1[
            variantView_cds_ref_1["element.symbol"].isin(gene_value_1)
        ]
        mut_options_1 = get_frequency_sorted_mutation_by_filters(
            variantView_cds_ref_gene_1, propertyView_seq_country_1, color_dict
        )
        mut_value_1 = [i['value'] for i in mut_options_1]

        date_list_2 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_2, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_2, "%Y-%m-%d").date()
        )
        variantView_cds_ref_2 = variantView_cds[
            (variantView_cds['reference.id'] == reference_value_2)
        ]
        propertyView_seq_country_2 = df_dict['propertyView'][
            (df_dict['propertyView']["SEQ_TECH"].isin(seqtech_value_2)) &
            (df_dict['propertyView']["COUNTRY"].isin(country_value_2)) &
            (df_dict['propertyView']["COLLECTION_DATE"].isin(date_list_2))
            ]
        variantView_cds_ref_gene_2 = variantView_cds_ref_2[
            variantView_cds_ref_2["element.symbol"].isin(gene_value_2)
        ]
        mut_options_2 = get_frequency_sorted_mutation_by_filters(
            variantView_cds_ref_gene_2,
            propertyView_seq_country_2,
            color_dict
        )
        mut_value_2 = [i['value'] for i in mut_options_2]

        unique_mutations_value_1 = list(set(mut_value_1).difference(set(mut_value_2)))
        mut_options_1 = [
            {'value': mut, 'label': mut} for mut in unique_mutations_value_1
        ]
        unique_mutations_value_2 = list(set(mut_value_2).difference(set(mut_value_1)))
        mut_options_2 = [
            {'value': mut, 'label': mut} for mut in unique_mutations_value_2
        ]
        intersection_mutation = list(set(mut_value_2).intersection(set(mut_value_1)))
        mut_options_3 = [
            {'value': mut, 'label': mut} for mut in intersection_mutation
        ]

        text_1 = f"Unique number of mutations in left selection: {len(unique_mutations_value_1)}"
        text_2 = f"Unique number of mutations in right selection: {len(unique_mutations_value_2)}"
        text_3 = f"Number of mutations in both selections: {len(intersection_mutation)}"

        df_all = pd.merge(
            df_dict["variantView"],
            df_dict["propertyView"],
            how="inner",
            on=["sample.id", "sample.name"],
        )
        table_columns = [
            "sample.name",
            "reference.accession",
            "element.symbol",
            "variant.label",
            "COUNTRY",
            "SEQ_TECH",
            "GEO_LOCATION",
            "ISOLATE",
        ]
        table_df_1 = df_all[
            df_all['variant.label'].isin(unique_mutations_value_1) &
            (df_all['reference.id'] == reference_value_1) &
            (df_all["SEQ_TECH"].isin(seqtech_value_1)) &
            (df_all["COUNTRY"].isin(country_value_1))
            ][table_columns]
        table_df_2 = df_all[
            df_all['variant.label'].isin(unique_mutations_value_2) &
            (df_all['reference.id'] == reference_value_2) &
            (df_all["SEQ_TECH"].isin(seqtech_value_2)) &
            (df_all["COUNTRY"].isin(country_value_2))
            ][table_columns]
        table_df_3 = df_all[
            df_all['variant.label'].isin(intersection_mutation) &
            (df_all['reference.id'].isin([reference_value_1, reference_value_2])) &
            (df_all["SEQ_TECH"].isin((seqtech_value_1 + seqtech_value_2))) &
            (df_all["COUNTRY"].isin((country_value_1 + seqtech_value_2)))
            ][table_columns]
        table_df_1.rename(columns={"element.symbol": "GENE"})
        table_df_2.rename(columns={"element.symbol": "GENE"})
        table_df_3.rename(columns={"element.symbol": "GENE"})

        table_df_1_records = table_df_1.to_dict('records')
        table_df_2_records = table_df_2.to_dict('records')
        table_df_3_records = table_df_3.to_dict('records')
        column_names_1 = [{"name": i, "id": i} for i in table_df_1.columns]
        column_names_2 = [{"name": i, "id": i} for i in table_df_2.columns]
        column_names_3 = [{"name": i, "id": i} for i in table_df_3.columns]

        return (
            mut_options_1,
            unique_mutations_value_1,
            text_1,
            mut_options_2,
            unique_mutations_value_2,
            text_2,
            mut_options_3,
            intersection_mutation,
            text_3,
            table_df_1_records,
            column_names_1,
            table_df_2_records,
            column_names_2,
            table_df_3_records,
            column_names_3
        )

    @callback(
        [
            Output("gene_dropdown_1", "options"),
            Output("gene_dropdown_1", "value"),
            Output("country_dropdown_1", "options"),
            Output("country_dropdown_1", "value"),
            Output("seq_tech_dropdown_1", "options"),
            Output("seq_tech_dropdown_1", "value"),
        ],
        [
            Input("reference_radio_1", "value"),
            Input("select_all_seq_tech_1", "value"),
            Input("select_all_genes_1", "value"),
            Input("select_all_countries_1", "value"),
        ],
        [
            State("gene_dropdown_1", "options"),
            State("country_dropdown_1", "options"),
            State("seq_tech_dropdown_1", "options"),
            State("gene_dropdown_1", "value"),
            State("country_dropdown_1", "value"),
            State("seq_tech_dropdown_1", "value")
        ],
        prevent_initial_call=False,
    )
    def actualize_filters_1(
            reference_value,
            select_all_seq_techs,
            select_all_genes,
            select_all_countries,
            gene_options,
            country_options,
            seq_tech_options,
            gene_value,
            country_value,
            seq_tech_value
    ):
        if dash.ctx.triggered_id == "select_all_genes_1":
            if len(select_all_genes) == 1:
                gene_value = [i['value'] for i in gene_options]
            elif len(select_all_genes) == 0:
                gene_value = []
        elif dash.ctx.triggered_id == "select_all_countries_1":
            if len(select_all_countries) == 1:
                country_value = [i['value'] for i in country_options]
            elif len(select_all_countries) == 0:
                country_value = []
        elif dash.ctx.triggered_id == "select_all_seq_tech_1":
            if len(select_all_seq_techs) == 1:
                seq_tech_value = [i['value'] for i in seq_tech_options]
            elif len(select_all_seq_techs) == 0:
                seq_tech_value = []
        else:
            gene_options = get_all_genes_per_reference(
                df_dict['variantView'], reference_value, color_dict
            )
            gene_value = [g['value'] for g in gene_options]

            country_options = get_all_frequency_sorted_countries(
                df_dict['propertyView']
            )
            country_value = [c['value'] for c in country_options]

            seq_tech_options = get_all_frequency_sorted_seqtech(
                df_dict['propertyView']
            )
            seq_tech_value = [s['value'] for s in seq_tech_options]

        return (
            gene_options,
            gene_value,
            country_options,
            country_value,
            seq_tech_options,
            seq_tech_value
        )

    @callback(
        [
            Output("gene_dropdown_2", "options"),
            Output("gene_dropdown_2", "value"),
            Output("country_dropdown_2", "options"),
            Output("country_dropdown_2", "value"),
            Output("seq_tech_dropdown_2", "options"),
            Output("seq_tech_dropdown_2", "value"),
        ],
        [
            Input("reference_radio_2", "value"),
            Input("select_all_seq_tech_2", "value"),
            Input("select_all_genes_2", "value"),
            Input("select_all_countries_2", "value")
        ],
        [
            State("gene_dropdown_2", "options"),
            State("country_dropdown_2", "options"),
            State("seq_tech_dropdown_2", "options"),
            State("gene_dropdown_2", "value"),
            State("country_dropdown_2", "value"),
            State("seq_tech_dropdown_2", "value")
        ],
        prevent_initial_call=False,
    )
    def actualize_filters_2(
            reference_value,
            select_all_seq_techs,
            select_all_genes,
            select_all_countries,
            gene_options,
            country_options,
            seq_tech_options,
            gene_value,
            country_value,
            seq_tech_value
    ):

        if dash.ctx.triggered_id == "select_all_genes_2":
            if len(select_all_genes) == 1:
                gene_value = [i['value'] for i in gene_options]
            elif len(select_all_genes) == 0:
                gene_value = []
        elif dash.ctx.triggered_id == "select_all_countries_2":
            if len(select_all_countries) == 1:
                country_value = [i['value'] for i in country_options]
            elif len(select_all_countries) == 0:
                country_value = []
        elif dash.ctx.triggered_id == "select_all_seq_tech_2":
            if len(select_all_seq_techs) == 1:
                seq_tech_value = [i['value'] for i in seq_tech_options]
            elif len(select_all_seq_techs) == 0:
                seq_tech_value = []
        else:
            gene_options = get_all_genes_per_reference(
                df_dict['variantView'], reference_value, color_dict
            )
            gene_value = [g['value'] for g in gene_options]

            country_options = get_all_frequency_sorted_countries(
                df_dict['propertyView']
            )
            country_value = [c['value'] for c in country_options]

            seq_tech_options = get_all_frequency_sorted_seqtech(
                df_dict['propertyView']
            )
            seq_tech_value = [s['value'] for s in seq_tech_options]

        return (gene_options,
                gene_value,
                country_options,
                country_value,
                seq_tech_options,
                seq_tech_value
                )
