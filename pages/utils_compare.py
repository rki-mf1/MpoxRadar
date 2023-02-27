import pandas as pd
import datetime

from pages.utils_filters import select_variantView_dfs
from pages.utils_filters import select_propertyView_dfs
from pages.utils_worldMap_explorer import DateSlider


def merge_df(variantView, propertyView):
    return pd.merge(
        variantView, propertyView, how="inner", on="sample.id"
    )[["sample.id", "variant.label", "element.symbol"]]


def merge_tables(variantView, propertyView):
    return pd.merge(
        variantView,
        propertyView,
        how="inner",
        on=["sample.id", "sample.name"],
    )


def filter_propertyView(df, seqtech_value, country_value, start_date, end_date):
    date_list = DateSlider.get_all_dates(
        datetime.datetime.strptime(start_date, "%Y-%m-%d").date(),
        datetime.datetime.strptime(end_date, "%Y-%m-%d").date(),
    )
    return df[
        (df["SEQ_TECH"].isin(seqtech_value))
        & (df["COUNTRY"].isin(country_value))
        & (df["COLLECTION_DATE"].isin(date_list))
        ]


def get_filtered_samples(propertyView_dfs, variantView_dfs, mut_value, gene_dropdown=None):
    new_samples = set()
    for i, df in enumerate(variantView_dfs):
        samples = set(propertyView_dfs[i]["sample.id"])
        if gene_dropdown:
            new_samples = new_samples.union(set(df[df["sample.id"].isin(samples)
                                           & df["variant.label"].isin(mut_value)
                                           & df["element.symbol"].isin(gene_dropdown)
                                           ]["sample.id"]))
        else:
            new_samples = new_samples.union(set(df[df["sample.id"].isin(samples)
                                           & df["variant.label"].isin(mut_value)
                                           ]["sample.id"]))
    return new_samples


def create_mutation_dfs_for_comparison(aa_nt_radio,
                                       gene_value,
                                       seqtech_value,
                                       country_value,
                                       start_date,
                                       end_date,
                                       variantView_dfs,
                                       propertyView_dfs):
    if aa_nt_radio == 'cds':
        variantView_dfs = [df[df["element.symbol"].isin(gene_value)] for df in variantView_dfs]

    propertyView_dfs = [filter_propertyView(df, seqtech_value, country_value, start_date, end_date) for df in
                        propertyView_dfs]

    merged_dfs = []
    for i, variantView in enumerate(variantView_dfs):
        merged_dfs.append(merge_df(variantView,
                                   propertyView_dfs[i]))

    df_mutations = pd.concat(merged_dfs, ignore_index=True, axis=0)
    return df_mutations


def combine_labels_by_sample(df, aa_nt_radio):
    if not df.empty:
        if aa_nt_radio == "cds":
            df = (
                df.groupby(
                    list(df.columns)[:-1],
                    dropna=False,
                )["gene::variant"]
                    .apply(lambda x: ",".join([str(y) for y in set(x)]))
                    .reset_index()
                    .rename(columns={"gene::variant": "AA_PROFILE"})
            )
        elif aa_nt_radio == "source":
            df = (
                df.groupby(
                    list(df.columns)[:-1],
                    dropna=False,
                )["variant.label"]
                    .apply(lambda x: ",".join([str(y) for y in set(x)]))
                    .reset_index()
                    .rename(columns={"variant.label": "NUC_PROFILE"})
            )
    return df


def create_comparison_tables(df_dict,
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
                             ):
    variantView_dfs_left = select_variantView_dfs(df_dict, complete_partial_radio, reference_value_1, aa_nt_radio)
    variantView_dfs_right = select_variantView_dfs(df_dict, complete_partial_radio, reference_value_2, aa_nt_radio)
    propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)

    propertyView_dfs_left = [filter_propertyView(df,
                                                 seqtech_value_1,
                                                 country_value_1,
                                                 start_date_1,
                                                 end_date_1
                                                 )
                             for df in propertyView_dfs]
    propertyView_dfs_right = [filter_propertyView(df,
                                                  seqtech_value_2,
                                                  country_value_2,
                                                  start_date_2,
                                                  end_date_2)
                              for df in propertyView_dfs]

    if aa_nt_radio == 'source':
        gene_dropdown_1 = None
        gene_dropdown_2 = None

    # all samples of selection (filter by mutation directly prevents complete MUT PROFILE)
    samples_left_both = get_filtered_samples(
        propertyView_dfs_left,
        variantView_dfs_left,
        mut_value_3,
        gene_dropdown_1
    )
    samples_right_both = get_filtered_samples(
        propertyView_dfs_right,
        variantView_dfs_right,
        mut_value_3,
        gene_dropdown_2
    )
    samples_left = get_filtered_samples(
        propertyView_dfs_left,
        variantView_dfs_left,
        mut_value_1,
        gene_dropdown_1
    )
    samples_right = get_filtered_samples(
        propertyView_dfs_right,
        variantView_dfs_right,
        mut_value_2,
        gene_dropdown_2
    )
    variantView_dfs_left_both = [df[df['sample.id'].isin(samples_left_both)] for df in variantView_dfs_left]
    variantView_dfs_right_both = [df[df['sample.id'].isin(samples_right_both)] for df in variantView_dfs_right]
    variantView_dfs_left = [df[df['sample.id'].isin(samples_left)] for df in variantView_dfs_left]
    variantView_dfs_right = [df[df['sample.id'].isin(samples_right)] for df in variantView_dfs_right]

    table_columns = [
        "sample.name",
        "COLLECTION_DATE",
        "ISOLATE",
        "SEQ_TECH",
        "COUNTRY",
        "GEO_LOCATION",
        "HOST",
        "LENGTH",
        "reference.accession",
        "variant.label",
    ]
    if aa_nt_radio == 'cds':
        table_columns.pop()
        table_columns.append("gene::variant")
    table_df_1 = pd.concat(
        [
            merge_tables(variantView_dfs_left[i], propertyView_dfs_left[i])
            for i in range(len(variantView_dfs_left))
        ],
        ignore_index=True, axis=0)[table_columns]
    table_df_2 = pd.concat(
        [
            merge_tables(variantView_dfs_right[i], propertyView_dfs_right[i])
            for i in range(len(variantView_dfs_right))
        ],
        ignore_index=True, axis=0)[table_columns]
    table_df_3 = pd.concat(
        [
            merge_tables(variantView_dfs_left_both[i], propertyView_dfs_left[i])
            for i in range(len(variantView_dfs_left_both))
        ] +
        [
            merge_tables(variantView_dfs_right_both[i], propertyView_dfs_right[i])
            for i in range(len(variantView_dfs_right_both))
        ],
        ignore_index=True, axis=0)[table_columns]

    table_df_1 = combine_labels_by_sample(table_df_1, aa_nt_radio)
    table_df_2 = combine_labels_by_sample(table_df_2, aa_nt_radio)
    table_df_3 = combine_labels_by_sample(table_df_3, aa_nt_radio)

    return table_df_1, table_df_2, table_df_3
