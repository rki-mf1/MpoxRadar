import datetime

import dash
from dash import callback
from dash import Input
from dash import Output
from dash import State
import pandas as pd

from pages.config import cache
from pages.utils_explorer_filter import filter_propertyView
from pages.utils_explorer_filter import actualize_filters
from pages.utils_explorer_filter import get_frequency_sorted_mutation_by_df
from pages.utils_explorer_filter import get_mutations_by_filters
from pages.utils_worldMap_explorer import DateSlider


def get_compare_callbacks(  # noqa: C901
        df_dict, color_dict
):
    @callback(
        [
            Output("mutation_dropdown_left", "options"),
            Output("mutation_dropdown_left", "value"),
            Output("max_nb_txt_left", "children"),
            Output("mutation_dropdown_right", "options"),
            Output("mutation_dropdown_right", "value"),
            Output("max_nb_txt_right", "children"),
            Output("mutation_dropdown_both", "options"),
            Output("mutation_dropdown_both", "value"),
            Output("max_nb_txt_both", "children"),
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
            State("date_picker_range_1", "start_date"),
            State("date_picker_range_1", "end_date"),
            State("date_picker_range_2", "start_date"),
            State("date_picker_range_2", "end_date"),
            State("aa_nt_radio", "value"),
            State("complete_partial_radio_compare", "value"),
        ],
        prevent_initial_call=True,
    )
    @cache.memoize()
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
            end_date_2,
            aa_nt_radio,
            complete_partial_radio,
    ):
        variantView_dfs_1 = []
        variantView_dfs_2 = []
        propertyView_dfs = []
        variantView_dfs_1.append(df_dict["variantView"]['complete'][reference_value_1][aa_nt_radio])
        variantView_dfs_2.append(df_dict["variantView"]['complete'][reference_value_2][aa_nt_radio])
        propertyView_dfs.append(df_dict["propertyView"]["complete"])
        if complete_partial_radio == 'partial':
            variantView_dfs_1.append(df_dict["variantView"]['partial'][reference_value_1][aa_nt_radio])
            variantView_dfs_2.append(df_dict["variantView"]['partial'][reference_value_2][aa_nt_radio])
            propertyView_dfs.append(df_dict["propertyView"]["partial"])

        if aa_nt_radio == 'cds':
            variantView_dfs_1 = [df[df["element.symbol"].isin(gene_value_1)] for df in variantView_dfs_1]
            variantView_dfs_2 = [df[df["element.symbol"].isin(gene_value_2)] for df in variantView_dfs_2]

            # LEFT OPTIONS
        date_list_1 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_1, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_1, "%Y-%m-%d").date(),
        )
        propertyView_dfs_1 = [filter_propertyView(df, seqtech_value_1, country_value_1, date_list_1) for df in
                              propertyView_dfs]

        merged_dfs_1 = get_mutations_by_filters(
            variantView_dfs_1, propertyView_dfs_1
        )

        # RIGHT OPTIONS
        date_list_2 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_2, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_2, "%Y-%m-%d").date(),
        )
        # TODO check if working or on same df
        propertyView_dfs_2 = [filter_propertyView(df, seqtech_value_2, country_value_2, date_list_2) for df in
                              propertyView_dfs]

        merged_dfs_2 = get_mutations_by_filters(
            variantView_dfs_2, propertyView_dfs_2
        )

        df_mutations_1 = pd.concat(merged_dfs_1, ignore_index=True, axis=0)
        df_mutations_2 = pd.concat(merged_dfs_2, ignore_index=True, axis=0)
        gene_mutations_df_merge = pd.merge(
            df_mutations_1[["variant.label", "element.symbol"]],
            df_mutations_2[["variant.label", "element.symbol"]],
            how="outer",
            indicator=True,
            on=["variant.label", "element.symbol"],
        )

        gene_mutations_df_left = gene_mutations_df_merge[
            gene_mutations_df_merge["_merge"] == "left_only"
            ][["variant.label", "element.symbol"]]
        gene_mutations_df_right = gene_mutations_df_merge[
            gene_mutations_df_merge["_merge"] == "right_only"
            ][["variant.label", "element.symbol"]]

        gene_mutations_df_inner = gene_mutations_df_merge[
            gene_mutations_df_merge["_merge"] == "both"
            ][["variant.label", "element.symbol"]]
        mut_options_1 = get_frequency_sorted_mutation_by_df(
            gene_mutations_df_left, color_dict, aa_nt_radio
        )
        mut_options_2 = get_frequency_sorted_mutation_by_df(
            gene_mutations_df_right, color_dict, aa_nt_radio
        )
        mut_options_3 = get_frequency_sorted_mutation_by_df(
            gene_mutations_df_inner, color_dict, aa_nt_radio
        )

        text_1 = f"Unique number of mutations in left selection: {len(mut_options_1)}"
        text_2 = f"Unique number of mutations in right selection: {len(mut_options_2)}"
        text_3 = f"Number of mutations in both selections: {len(mut_options_3)}"

        return (
            mut_options_1,
            [v["value"] for v in mut_options_1],
            text_1,
            mut_options_2,
            [v["value"] for v in mut_options_2],
            text_2,
            mut_options_3,
            [v["value"] for v in mut_options_3],
            text_3,
        )

    @callback(
        [
            Output(component_id="table_compare_1", component_property="data"),
            Output(component_id="table_compare_1", component_property="columns"),
            Output(component_id="table_compare_2", component_property="data"),
            Output(component_id="table_compare_2", component_property="columns"),
            Output(component_id="table_compare_3", component_property="data"),
            Output(component_id="table_compare_3", component_property="columns"),
        ],
        [
            Input("mutation_dropdown_left", "value"),
            Input("mutation_dropdown_right", "value"),
            Input("mutation_dropdown_both", "value"),
        ],
        [
            State("reference_radio_1", "value"),
            State("seq_tech_dropdown_1", "value"),
            State("country_dropdown_1", "value"),
            State("reference_radio_2", "value"),
            State("seq_tech_dropdown_2", "value"),
            State("country_dropdown_2", "value"),
            State("date_picker_range_1", "start_date"),
            State("date_picker_range_1", "end_date"),
            State("date_picker_range_2", "start_date"),
            State("date_picker_range_2", "end_date"),
            State("aa_nt_radio", "value"),
            State("complete_partial_radio_compare", "value"),
        ],
        prevent_initial_call=True,
    )
    @cache.memoize()
    def actualize_tables(
            mut_value_1,
            mut_value_2,
            mut_value_3,
            reference_value_1,
            seqtech_value_1,
            country_value_1,
            reference_value_2,
            seqtech_value_2,
            country_value_2,
            start_date_1,
            end_date_1,
            start_date_2,
            end_date_2,
            aa_nt_radio,
            complete_partial_radio,
    ):
        variantView_dfs_1 = []
        variantView_dfs_2 = []
        propertyView_dfs = []
        variantView_dfs_1.append(df_dict["variantView"]['complete'][reference_value_1][aa_nt_radio])
        variantView_dfs_2.append(df_dict["variantView"]['complete'][reference_value_2][aa_nt_radio])
        propertyView_dfs.append(df_dict["propertyView"]["complete"])
        if complete_partial_radio == 'partial':
            variantView_dfs_1.append(df_dict["variantView"]['partial'][reference_value_1][aa_nt_radio])
            variantView_dfs_2.append(df_dict["variantView"]['partial'][reference_value_2][aa_nt_radio])
            propertyView_dfs.append(df_dict["propertyView"]["partial"])

        date_list_1 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_1, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_1, "%Y-%m-%d").date(),
        )
        date_list_2 = DateSlider.get_all_dates(
            datetime.datetime.strptime(start_date_2, "%Y-%m-%d").date(),
            datetime.datetime.strptime(end_date_2, "%Y-%m-%d").date(),
        )
        propertyView_dfs_1 = [filter_propertyView(df, seqtech_value_1, country_value_1, date_list_1) for df in
                              propertyView_dfs]
        propertyView_dfs_2 = [filter_propertyView(df, seqtech_value_2, country_value_2, date_list_2) for df in
                              propertyView_dfs]
        propertyView_dfs_3 = [filter_propertyView(df,
                                                  (seqtech_value_1 + seqtech_value_2),
                                                  (country_value_1 + country_value_2),
                                                  (set(date_list_1).union(set(date_list_2)))
                                                  )
                              for df in propertyView_dfs]
        variantView_dfs_1 = [df.isin(mut_value_1) for df in variantView_dfs_1]
        variantView_dfs_2 = [df.isin(mut_value_2) for df in variantView_dfs_2]
        variantView_3 = pd.concat([df.isin(mut_value_3) for df in variantView_dfs_1] +
                                  [df.isin(mut_value_3) for df in variantView_dfs_2], ignore_index=True, axis=0)

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

        table_df_1 = pd.concat([pd.merge(
            variantView,
            propertyView,
            how="inner",
            on=["sample.id", "sample.name"],
        ) for variantView, propertyView in zip(variantView_dfs_1, propertyView_dfs_1)], ignore_index=True, axis=0)[
            table_columns]

        table_df_2 = pd.concat([pd.merge(
            variantView,
            propertyView,
            how="inner",
            on=["sample.id", "sample.name"],
        ) for variantView, propertyView in zip(variantView_dfs_2, propertyView_dfs_2)], ignore_index=True, axis=0)[
            table_columns]

        table_df_3 = pd.merge(
            variantView_3,
            pd.concat(propertyView_dfs_3, ignore_index=True, axis=0),
            how="inner",
            on=["sample.id", "sample.name"],
        )[table_columns]

        table_df_1 = table_df_1.rename(columns={"element.symbol": "gene.symbol"})
        table_df_2 = table_df_2.rename(columns={"element.symbol": "gene.symbol"})
        table_df_3 = table_df_3.rename(columns={"element.symbol": "gene.symbol"})

        table_df_1_records = table_df_1.to_dict("records")
        table_df_2_records = table_df_2.to_dict("records")
        table_df_3_records = table_df_3.to_dict("records")
        column_names_1 = [{"name": i, "id": i} for i in table_df_1.columns]
        column_names_2 = [{"name": i, "id": i} for i in table_df_2.columns]
        column_names_3 = [{"name": i, "id": i} for i in table_df_3.columns]
        return (
            table_df_1_records,
            column_names_1,
            table_df_2_records,
            column_names_2,
            table_df_3_records,
            column_names_3,
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
            Input("aa_nt_radio", "value"),
            Input("reference_radio_1", "value"),
            Input("select_all_seq_tech_1", "value"),
            Input("select_all_genes_1", "value"),
            Input("select_all_countries_1", "value"),
            Input("complete_partial_radio_compare", "value"),
        ],
        [
            State("gene_dropdown_1", "options"),
            State("country_dropdown_1", "options"),
            State("seq_tech_dropdown_1", "options"),
            State("gene_dropdown_1", "value"),
            State("country_dropdown_1", "value"),
            State("seq_tech_dropdown_1", "value"),
        ],
        prevent_initial_call=True,
    )
    def actualize_filters_left(
            aa_nt_radio,
            reference_value,
            select_all_seq_techs,
            select_all_genes,
            select_all_countries,
            complete_partial_radio,
            gene_options,
            country_options,
            seq_tech_options,
            gene_value,
            country_value,
            seq_tech_value,
    ):
        return actualize_filters(df_dict,
                                 color_dict,
                                 dash.ctx.triggered_id,
                                 aa_nt_radio,
                                 reference_value,
                                 select_all_seq_techs,
                                 select_all_genes,
                                 select_all_countries,
                                 complete_partial_radio,
                                 gene_options,
                                 country_options,
                                 seq_tech_options,
                                 gene_value,
                                 country_value,
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
            Input("aa_nt_radio", "value"),
            Input("reference_radio_2", "value"),
            Input("select_all_seq_tech_2", "value"),
            Input("select_all_genes_2", "value"),
            Input("select_all_countries_2", "value"),
            Input("complete_partial_radio_compare", "value"),
        ],
        [
            State("gene_dropdown_2", "options"),
            State("country_dropdown_2", "options"),
            State("seq_tech_dropdown_2", "options"),
            State("gene_dropdown_2", "value"),
            State("country_dropdown_2", "value"),
            State("seq_tech_dropdown_2", "value"),
        ],
        prevent_initial_call=True,
    )
    def actualize_filters_right(
            aa_nt_radio,
            reference_value,
            select_all_seq_techs,
            select_all_genes,
            select_all_countries,
            complete_partial_radio,
            gene_options,
            country_options,
            seq_tech_options,
            gene_value,
            country_value,
            seq_tech_value,
    ):
        return actualize_filters(df_dict,
                                 color_dict,
                                 dash.ctx.triggered_id,
                                 aa_nt_radio,
                                 reference_value,
                                 select_all_seq_techs,
                                 select_all_genes,
                                 select_all_countries,
                                 complete_partial_radio,
                                 gene_options,
                                 country_options,
                                 seq_tech_options,
                                 gene_value,
                                 country_value,
                                 seq_tech_value
                                 )
