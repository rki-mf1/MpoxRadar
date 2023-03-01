from dash import callback
from dash import Input
from dash import Output
from dash import State
from dash import ctx
import pandas as pd

from pages.config import cache
from pages.utils_compare import create_mutation_dfs_for_comparison
from pages.utils_compare import select_variantView_dfs
from pages.utils_compare import select_propertyView_dfs
from pages.utils_compare import create_comparison_tables
from pages.utils_filters import actualize_filters
from pages.utils_filters import get_frequency_sorted_mutation_by_df


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
            Input("select_all_mutations_left", "value"),
            Input("select_all_mutations_right", "value"),
            Input("select_all_mutations_both", "value"),
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
            State("mutation_dropdown_left", "options"),
            State("mutation_dropdown_right", "options"),
            State("mutation_dropdown_both", "options"),
            State("mutation_dropdown_left", "value"),
            State("mutation_dropdown_right", "value"),
            State("mutation_dropdown_both", "value"),
        ],
        prevent_initial_call=True,
    )
    @cache.memoize()
    def actualize_mutation_filter(
            compare_button,
            select_all_mutations_left,
            select_all_mutations_right,
            select_all_mutations_both,
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
            mut_options_left,
            mut_options_right,
            mut_options_both,
            mut_value_left,
            mut_value_right,
            mut_value_both
    ):
        if ctx.triggered_id == "select_all_mutations_left":
            if len(select_all_mutations_left) == 1:
                mut_value_left = [i["value"] for i in mut_options_left]
            elif len(select_all_mutations_left) == 0:
                mut_value_left = []
        elif ctx.triggered_id == "select_all_mutations_right":
            if len(select_all_mutations_right) == 1:
                mut_value_right = [i["value"] for i in mut_options_right]
            elif len(select_all_mutations_right) == 0:
                mut_value_right = []
        elif ctx.triggered_id == "select_all_mutations_both":
            if len(select_all_mutations_both) == 1:
                mut_value_both = [i["value"] for i in mut_options_both]
            elif len(select_all_mutations_both) == 0:
                mut_value_both = []
        else:
            variantView_dfs_left = select_variantView_dfs(df_dict, complete_partial_radio, reference_value_1, aa_nt_radio)
            variantView_dfs_right = select_variantView_dfs(df_dict, complete_partial_radio, reference_value_2, aa_nt_radio)
            propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)

            # LEFT OPTIONS
            df_mutations_1 = create_mutation_dfs_for_comparison(aa_nt_radio,
                                                                gene_value_1,
                                                                seqtech_value_1,
                                                                country_value_1,
                                                                start_date_1,
                                                                end_date_1,
                                                                variantView_dfs_left,
                                                                propertyView_dfs)
            # RIGHT OPTIONS
            df_mutations_2 = create_mutation_dfs_for_comparison(aa_nt_radio,
                                                                gene_value_2,
                                                                seqtech_value_2,
                                                                country_value_2,
                                                                start_date_2,
                                                                end_date_2,
                                                                variantView_dfs_right,
                                                                propertyView_dfs)

            # DIFFERENCES
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
            mut_options_left = get_frequency_sorted_mutation_by_df(
                gene_mutations_df_left, color_dict, aa_nt_radio
            )
            mut_options_right = get_frequency_sorted_mutation_by_df(
                gene_mutations_df_right, color_dict, aa_nt_radio
            )
            mut_options_both = get_frequency_sorted_mutation_by_df(
                gene_mutations_df_inner, color_dict, aa_nt_radio
            )
            mut_value_left = [v["value"] for v in mut_options_left]
            mut_value_right = [v["value"] for v in mut_options_right]
            mut_value_both = [v["value"] for v in mut_options_both]

        text_1 = f"Unique number of mutations in left selection: {len(mut_options_left)}"
        text_2 = f"Unique number of mutations in right selection: {len(mut_options_right)}"
        text_3 = f"Number of mutations in both selections: {len(mut_options_both)}"

        return (
            mut_options_left,
            mut_value_left,
            text_1,
            mut_options_right,
            mut_value_right,
            text_2,
            mut_options_both,
            mut_value_both,
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
            State("gene_dropdown_1", "value"),
            State("gene_dropdown_2", "value"),
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
            gene_dropdown_1,
            gene_dropdown_2,
            aa_nt_radio,
            complete_partial_radio,
    ):
        table_df_1, table_df_2, table_df_3 = create_comparison_tables(df_dict,
                                                                      complete_partial_radio,
                                                                      aa_nt_radio,
                                                                      mut_value_1,
                                                                      reference_value_1,
                                                                      seqtech_value_1,
                                                                      country_value_1,
                                                                      start_date_1,
                                                                      end_date_1,
                                                                      gene_dropdown_1,
                                                                      mut_value_2,
                                                                      reference_value_2,
                                                                      seqtech_value_2,
                                                                      country_value_2,
                                                                      start_date_2,
                                                                      end_date_2,
                                                                      gene_dropdown_2,
                                                                      mut_value_3
                                                                      )
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
            Input("seq_tech_dropdown_1", "value"),
            Input("gene_dropdown_1", "value"),
        ],
        [
            State("gene_dropdown_1", "options"),
            State("country_dropdown_1", "options"),
            State("seq_tech_dropdown_1", "options"),
            State("country_dropdown_1", "value"),

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
            seq_tech_value,
            gene_value,
            gene_options,
            country_options,
            seq_tech_options,
            country_value,

    ):
        """
        complete_partial_radio --> trigger new evaluation of gene, seq_tech, countries
        aa_nt_radio --> trigger new evaluation of gene, seq_tech, countries
        reference_value --> trigger new evaluation of gene, seq_tech, countries
        gene_value --> trigger new evaluation of seq_tech, countries
        seq_tech --> trigger new evaluation of countries
        select-all --> triggers only new values of defined, no options
        """
        return actualize_filters(
            df_dict,
            color_dict,
            ctx.triggered_id,
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
            Input("seq_tech_dropdown_2", "value"),
            Input("gene_dropdown_2", "value"),
        ],
        [
            State("gene_dropdown_2", "options"),
            State("country_dropdown_2", "options"),
            State("seq_tech_dropdown_2", "options"),
            State("country_dropdown_2", "value"),

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
            seq_tech_value,
            gene_value,
            gene_options,
            country_options,
            seq_tech_options,
            country_value,

    ):
        """
        complete_partial_radio --> trigger new evaluation of gene, seq_tech, countries
        aa_nt_radio --> trigger new evaluation of gene, seq_tech, countries
        reference_value --> trigger new evaluation of gene, seq_tech, countries
        gene_value --> trigger new evaluation of seq_tech, countries
        seq_tech --> trigger new evaluation of countries
        select-all --> triggers only new values of defined, no options
        """
        return actualize_filters(df_dict,
                                 color_dict,
                                 ctx.triggered_id,
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
