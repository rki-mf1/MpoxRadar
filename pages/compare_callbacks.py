from dash import callback
from dash import ctx
from dash import Input
from dash import Output
from dash import State

from pages.config import cache
from pages.utils_compare import select_min_x_frequent_mut
from pages.utils_compare import find_unique_and_shared_variants
from pages.utils_compare import create_comparison_tables
from pages.utils_filters import actualize_filters
from pages.utils_tables import OverviewTable


def get_compare_callbacks(df_dict, color_dict):  # noqa: C901
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
            Output("min_nb_freq_left", "children"),
            Output("min_nb_freq_right", "children"),
            Output("min_nb_freq_both", "children")
        ],
        [
            Input("compare_button", "n_clicks"),
            Input("select_all_mutations_left", "value"),
            Input("select_all_mutations_right", "value"),
            Input("select_all_mutations_both", "value"),
            Input("select_min_nb_frequent_mut_left", "value"),
            Input("select_min_nb_frequent_mut_right", "value"),
            Input("select_min_nb_frequent_mut_both", "value"),
        ],
        [
            State("gene_dropdown_1", "value"),
            State("gene_dropdown_2", "value"),
            State("reference_radio_1", "value"),
            State("seq_tech_dropdown_1", "value"),
            State("country_dropdown_1", "value"),
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
            State("min_nb_freq_left", "children"),
            State("min_nb_freq_right", "children"),
            State("min_nb_freq_both", "children"),
        ],
        prevent_initial_call=True,
    )
    @cache.memoize()
    def actualize_mutation_filter(
            compare_button,
            select_all_mutations_left,
            select_all_mutations_right,
            select_all_mutations_both,
            min_nb_freq_left,
            min_nb_freq_right,
            min_nb_freq_both,
            gene_value_1,
            gene_value_2,
            reference_value,
            seqtech_value_1,
            country_value_1,
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
            mut_value_both,
            text_freq_1,
            text_freq_2,
            text_freq_3,

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
        elif ctx.triggered_id == "select_min_nb_frequent_mut_left":
            mut_value_left = select_min_x_frequent_mut(mut_options_left,
                                                       min_nb_freq_left)
        elif ctx.triggered_id == "select_min_nb_frequent_mut_right":
            mut_value_right = select_min_x_frequent_mut(mut_options_right,
                                                        min_nb_freq_right)
        elif ctx.triggered_id == "select_min_nb_frequent_mut_both":
            mut_value_both = select_min_x_frequent_mut(mut_options_both,
                                                       min_nb_freq_both)

        else:
            mut_options_left, mut_options_right, mut_options_both, \
                mut_value_left, mut_value_right, mut_value_both, \
                max_freq_nb_left, max_freq_nb_right, max_freq_nb_both = find_unique_and_shared_variants(
                    df_dict,
                    color_dict,
                    complete_partial_radio,
                    reference_value,
                    aa_nt_radio,
                    gene_value_1,
                    seqtech_value_1,
                    country_value_1,
                    start_date_1,
                    end_date_1,
                    gene_value_2,
                    seqtech_value_2,
                    country_value_2,
                    start_date_2,
                    end_date_2,
                )
            text_freq_1 = f"Select minimum variant frequency. Highest frequency in selection: {max_freq_nb_left}"
            text_freq_2 = f"Select minimum variant frequency. Highest frequency in selection:  {max_freq_nb_right}"
            text_freq_3 = f"Select minimum variant frequency. Highest frequency in selection: {max_freq_nb_both}"

        text_1 = f"Unique number of variants in left selection: {len(mut_value_left)}"
        text_2 = f"Unique number of variants in right selection: {len(mut_value_right)}"
        text_3 = f"Number of variants in both selections: {len(mut_value_both)}"

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
            text_freq_1,
            text_freq_2,
            text_freq_3,
        )

    @callback(
        [
            Output(component_id="table_compare_1", component_property="data"),
            Output(component_id="table_compare_1", component_property="columns"),
            Output(component_id="table_compare_2", component_property="data"),
            Output(component_id="table_compare_2", component_property="columns"),
            Output(component_id="table_compare_3", component_property="data"),
            Output(component_id="table_compare_3", component_property="columns"),
            Output('compare_shared_dict', 'data')
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
            mut_value_left,
            mut_value_right,
            mut_value_both,
            reference_value,
            seqtech_value_1,
            country_value_1,
            seqtech_value_2,
            country_value_2,
            start_date_1,
            end_date_1,
            start_date_2,
            end_date_2,
            aa_nt_radio,
            complete_partial_radio,
    ):
        table_df_1, table_df_2, table_df_3, variantView_df_both = create_comparison_tables(df_dict,
                                                                                           complete_partial_radio,
                                                                                           aa_nt_radio,
                                                                                           mut_value_left,
                                                                                           reference_value,
                                                                                           seqtech_value_1,
                                                                                           country_value_1,
                                                                                           start_date_1,
                                                                                           end_date_1,
                                                                                           mut_value_right,
                                                                                           seqtech_value_2,
                                                                                           country_value_2,
                                                                                           start_date_2,
                                                                                           end_date_2,
                                                                                           mut_value_both
                                                                                           )
        table_df_1_records = table_df_1.to_dict("records")
        table_df_2_records = table_df_2.to_dict("records")
        table_df_3_records = table_df_3.to_dict("records")
        column_names_1 = [{"name": i, "id": i} for i in table_df_1.columns]
        column_names_2 = [{"name": i, "id": i} for i in table_df_2.columns]
        column_names_3 = [{"name": i, "id": i} for i in table_df_3.columns]

        variantView_df_both_json = variantView_df_both.to_json(
            date_format='iso', orient='split')

        return (
            table_df_1_records,
            column_names_1,
            table_df_2_records,
            column_names_2,
            table_df_3_records,
            column_names_3,
            variantView_df_both_json
        )

    @callback(
        [
            Output(component_id="table_compare_0", component_property="data"),
            Output(component_id="table_compare_0", component_property="columns"),
        ],
        [
            Input("mutation_dropdown_left", "value"),
            Input("mutation_dropdown_right", "value"),
            Input("mutation_dropdown_both", "value"),
            Input("mutation_dropdown_left", "options"),
            Input("mutation_dropdown_right", "options"),
            Input('compare_shared_dict', 'data')

        ],
        [
            State("aa_nt_radio", "value"),
        ],
        prevent_initial_call=True,
    )
    @cache.memoize()
    def actualize_overview_table(
            mut_value_left,
            mut_value_right,
            mut_value_both,
            mut_options_left,
            mut_options_right,
            variantView_df_both_json,
            aa_nt_radio
    ):
        overviewTable = OverviewTable(aa_nt_radio)
        df_left = overviewTable.create_df_from_mutation_options(
            mut_options_left, mut_value_left)
        df_right = overviewTable.create_df_from_mutation_options(
            mut_options_right, mut_value_right)
        df_both = overviewTable.create_df_from_json(
            variantView_df_both_json, mut_value_both)
        table_df_records, column_names = overviewTable.create_overview_table(
            df_left, df_both, df_right)

        return (
            table_df_records,
            column_names,
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
            Input("reference_radio_1", "value"),
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
