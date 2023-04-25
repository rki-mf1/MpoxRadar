import datetime
import pandas as pd

from pages.utils_filters import select_propertyView_dfs, get_frequency_sorted_mutation_by_df
from pages.utils_filters import select_variantView_dfs
from pages.utils_tables import TableFilter, OverviewTable
from pages.utils_worldMap_explorer import DateSlider


def merge_df(
    variantView: pd.DataFrame,
    propertyView: pd.DataFrame,
    aa_nt_radio: str
) -> pd.DataFrame:
    """
    :return: variantView, propertyView merged df 
        with columns ["sample.id", "variant.label"] for "source" or
        ["sample.id", "variant.label", "element.symbol", "gene:variant"] for "cds"
    """
    df = pd.merge(variantView, propertyView, how="inner", on="sample.id")
    if aa_nt_radio == "cds":
        return df[["sample.id", "variant.label", "element.symbol", "gene:variant"]]
    else:
        return df[["sample.id", "variant.label"]]


def filter_propertyView(
    df: pd.DataFrame,
    seqtech_value: list[str],
    country_value: list[str],
    start_date: str,
    end_date: str
) -> pd.DataFrame:
    """
    :return: filtered df by user selected sequencing technologies, countries and dates
    """
    date_list = DateSlider.get_all_dates(
        datetime.datetime.strptime(start_date, "%Y-%m-%d").date(),
        datetime.datetime.strptime(end_date, "%Y-%m-%d").date(),
    )
    return df[
        (df["SEQ_TECH"].isin(seqtech_value))
        & (df["COUNTRY"].isin(country_value))
        & (df["COLLECTION_DATE"].isin(date_list))
    ]


def select_min_x_frequent_mut(mut_options: list[dict], min_nb_freq: int) -> list:
    """
    :return: mutation values occuring >= user given minimum number of freuquency
    """
    df = pd.DataFrame.from_records(mut_options)
    df = df[df['freq'] >= min_nb_freq]
    return df['value']


def set_difference(set1, set2):
    return set1 - set2


def set_intersection(set1, set2):
    return set1 & set2


def find_unique_and_shared_variants(
        df_dict: pd.DataFrame,
        color_dict: dict,
        complete_partial_radio: str,
        reference_value: int,
        aa_nt_radio: str,
        gene_value_1: list[str],
        seqtech_value_1: list[str],
        country_value_1: list[str],
        start_date_1: str,
        end_date_1: str,
        gene_value_2: list[str],
        seqtech_value_2: list[str],
        country_value_2: list[str],
        start_date_2: str,
        end_date_2: str,
) -> (list[dict], list[dict], list[dict], list[str], list[str], list[str], int, int, int):
    """
    :return: mutation options, mutation values and maximum number of mutation frequency 
        for unique mutation of left selection, right selection and shared mutations in both selections
        based on user selection
    """
    if aa_nt_radio == "cds":
        variant_columns = ["gene:variant", "element.symbol"]
    else:
        variant_columns = ["variant.label"]
    variantView_dfs = select_variantView_dfs(df_dict, complete_partial_radio, reference_value,
                                             aa_nt_radio)
    propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)

    # LEFT OPTIONS
    df_mutations_1 = create_mutation_dfs_for_comparison(aa_nt_radio,
                                                        gene_value_1,
                                                        seqtech_value_1,
                                                        country_value_1,
                                                        start_date_1,
                                                        end_date_1,
                                                        variantView_dfs,
                                                        propertyView_dfs,
                                                        )
    df_mutations_1 = df_mutations_1[['sample.id'] + variant_columns]
    # RIGHT OPTIONS
    df_mutations_2 = create_mutation_dfs_for_comparison(aa_nt_radio,
                                                        gene_value_2,
                                                        seqtech_value_2,
                                                        country_value_2,
                                                        start_date_2,
                                                        end_date_2,
                                                        variantView_dfs,
                                                        propertyView_dfs,
                                                        )
    df_mutations_2 = df_mutations_2[['sample.id'] + variant_columns]

    # DIFFERENCES
    mut_left = set_difference(set(df_mutations_1[variant_columns[0]]), set(
        df_mutations_2[variant_columns[0]]))
    gene_mutations_df_left = df_mutations_1[df_mutations_1[variant_columns[0]].isin(
        mut_left)]
    mut_options_left, max_freq_nb_left, min_nb_freq = get_frequency_sorted_mutation_by_df(
        gene_mutations_df_left, color_dict, variant_columns, aa_nt_radio
    )
    mut_value_left = [v["value"] for v in mut_options_left]

    mut_right = set_difference(set(df_mutations_2[variant_columns[0]]), set(
        df_mutations_1[variant_columns[0]]))
    gene_mutations_df_right = df_mutations_2[df_mutations_2[variant_columns[0]].isin(
        mut_right)]
    mut_options_right, max_freq_nb_right, min_nb_freq = get_frequency_sorted_mutation_by_df(
        gene_mutations_df_right, color_dict, variant_columns, aa_nt_radio
    )
    mut_value_right = [v["value"] for v in mut_options_right]

    mut_both = set_intersection(set(df_mutations_2[variant_columns[0]]), set(
        df_mutations_1[variant_columns[0]]))
    gene_mutations_df_both = pd.concat(
        [
            df_mutations_1[df_mutations_1[variant_columns[0]].isin(mut_both)],
            df_mutations_2[df_mutations_2[variant_columns[0]].isin(mut_both)]
        ],
        ignore_index=True, axis=0
    )
    mut_options_both, max_freq_nb_both, min_nb_freq = get_frequency_sorted_mutation_by_df(
        gene_mutations_df_both, color_dict, variant_columns, aa_nt_radio
    )
    mut_value_both = [v["value"] for v in mut_options_both]
    return mut_options_left, mut_options_right, mut_options_both, \
        mut_value_left, mut_value_right, mut_value_both, \
        max_freq_nb_left, max_freq_nb_right, max_freq_nb_both


def create_mutation_dfs_for_comparison(
    aa_nt_radio: str,
    gene_value: list[str],
    seqtech_value: list[str],
    country_value: list[str],
    start_date: str,
    end_date: str,
    variantView_dfs: list[pd.DataFrame],
    propertyView_dfs: list[pd.DataFrame],
) -> pd.DataFrame:
    """
    :return: merged variantView and propertyView filtered for seqtech, country, dates, genes
    """
    if aa_nt_radio == 'cds':
        variantView_dfs = [df[df["element.symbol"].isin(
            gene_value)] for df in variantView_dfs]

    propertyView_dfs = [filter_propertyView(df, seqtech_value, country_value, start_date, end_date) 
                        for df in propertyView_dfs]

    merged_dfs = []
    for i, variantView in enumerate(variantView_dfs):
        merged_dfs.append(merge_df(variantView, propertyView_dfs[i], aa_nt_radio))
    df_mutations = pd.concat(merged_dfs, ignore_index=True,
                             axis=0).reset_index(drop=True)
    return df_mutations


def create_comparison_tables(
        df_dict: dict,
        complete_partial_radio: str,
        aa_nt_radio: str,
        mut_value_left: list[str],
        reference_value: int,
        seqtech_value_left: list[str],
        country_value_left: list[str],
        start_date_left: str,
        end_date_left: str,
        mut_value_right: list[str],
        seqtech_value_right: list[str],
        country_value_right: list[str],
        start_date_right: str,
        end_date_right: str,
        mut_value_both: list[str]
) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame):
    """
    create overview table and detail tables for samples with unique mutations for left selection, 
    right selection or table for shared mutations between both selections for compare tool
    based on user selection
    """
    variantView_dfs = select_variantView_dfs(
        df_dict, complete_partial_radio, reference_value, aa_nt_radio)
    propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)

    table_left_ins = TableFilter("compare",
                                 mut_value_left,
                                 aa_nt_radio,
                                 seqtech_value_left,
                                 country_value_left,
                                 start_date_left,
                                 end_date_left,
                                 )
    table_right_ins = TableFilter("compare",
                                  mut_value_right,
                                  aa_nt_radio,
                                  seqtech_value_right,
                                  country_value_right,
                                  start_date_right,
                                  end_date_right,
                                  )
    table_both_ins = TableFilter("compare",
                                 mut_value_both,
                                 aa_nt_radio,
                                 )

    propertyView_dfs_left = [
        table_left_ins.filter_propertyView(df) for df in propertyView_dfs]
    propertyView_dfs_right = [
        table_right_ins.filter_propertyView(df) for df in propertyView_dfs]

    table_df_1 = table_left_ins.create_compare_table_left_and_right(
        variantView_dfs, propertyView_dfs_left)
    table_df_2 = table_right_ins.create_compare_table_left_and_right(
        variantView_dfs, propertyView_dfs_right)
    table_df_3, samples_left_both, samples_right_both = table_both_ins.create_compare_table_both(
        variantView_dfs,
        propertyView_dfs_left,
        propertyView_dfs_right
    )

    overviewTable = OverviewTable(aa_nt_radio)
    variantView_df_overview_both = overviewTable.count_shared_mutation_in_left_and_right_selection(
        mut_value_both,
        samples_left_both,
        samples_right_both,
        variantView_dfs
    )

    return table_df_1, table_df_2, table_df_3, variantView_df_overview_both
