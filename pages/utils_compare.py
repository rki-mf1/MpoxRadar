import datetime

import pandas as pd

from pages.utils_filters import select_propertyView_dfs
from pages.utils_filters import select_variantView_dfs
from pages.utils_worldMap_explorer import DateSlider


overview_columns = [
    'unique left', "# left",
    'shared', "# l", "# r",
    'unique right', "# right",
]
overview_column_names = [
    'unique variants for left selection', "# seq left",
    'shared variants of both selections', "# seq left", "# seq right",
    'unique variants for right selection', "# seq right",
]


def merge_df(variantView, propertyView, aa_nt_radio):
    if aa_nt_radio == "cds":
        return pd.merge(
            variantView, propertyView, how="inner", on="sample.id"
        )[["sample.id", "variant.label", "element.symbol", "gene:variant"]]
    else:
        return pd.merge(
            variantView, propertyView, how="inner", on="sample.id"
        )[["sample.id", "variant.label"]]


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


def get_filtered_samples(propertyView_dfs, variantView_dfs, mut_value, variant_col):
    new_samples = set()
    for i, df in enumerate(variantView_dfs):
        samples = set(propertyView_dfs[i]["sample.id"])
        new_samples = new_samples.union(set(df[df["sample.id"].isin(samples)
                                               & df[variant_col].isin(mut_value)
                                               ]["sample.id"]))
    return new_samples


def select_min_x_frequent_mut(mut_options, min_nb_freq):
    df = pd.DataFrame.from_records(mut_options)
    df = df[df['freq'] >= min_nb_freq]
    return df['value']


def create_mutation_dfs_for_comparison(aa_nt_radio,
                                       gene_value,
                                       seqtech_value,
                                       country_value,
                                       start_date,
                                       end_date,
                                       variantView_dfs,
                                       propertyView_dfs,
                                       ):
    if aa_nt_radio == 'cds':
        variantView_dfs = [df[df["element.symbol"].isin(gene_value)] for df in variantView_dfs]

    propertyView_dfs = [filter_propertyView(df, seqtech_value, country_value, start_date, end_date) for df in
                        propertyView_dfs]

    merged_dfs = []
    for i, variantView in enumerate(variantView_dfs):
        merged_dfs.append(merge_df(variantView, propertyView_dfs[i], aa_nt_radio))
    df_mutations = pd.concat(merged_dfs, ignore_index=True, axis=0).reset_index(drop=True)
    return df_mutations


def combine_labels_by_sample(df, aa_nt_radio):
    cols = list(df.columns)
    if not df.empty:
        if aa_nt_radio == "cds":
            cols.remove("gene:variant")
            df = (
                df.groupby(
                    cols,
                    dropna=False,
                )["gene:variant"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index()
                .rename(columns={"gene:variant": "AA_PROFILE"})
            )[["sample.name", "AA_PROFILE"] + cols[1:]]
        elif aa_nt_radio == "source":
            cols.remove("variant.label")
            df = (
                df.groupby(
                    cols,
                    dropna=False,
                )["variant.label"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index()
                .rename(columns={"variant.label": "NUC_PROFILE"})
            )[['sample.name', "NUC_PROFILE"] + cols[1:]]
    df = df.rename(columns={'reference.accession': "REFERENCE_ACCESSION"})
    return df


def create_comparison_tables(
        df_dict,
        complete_partial_radio,
        aa_nt_radio,
        mut_value_1,
        reference_value,
        seqtech_value_1,
        country_value_1,
        start_date_1,
        end_date_1,
        mut_value_2,
        seqtech_value_2,
        country_value_2,
        start_date_2,
        end_date_2,
        mut_value_3
):
    if aa_nt_radio == 'cds':
        variant_col = "gene:variant"
    else:
        variant_col = "variant.label"

    variantView_dfs = select_variantView_dfs(df_dict, complete_partial_radio, reference_value, aa_nt_radio)
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

    # all samples of selection (filter by mutation directly prevents complete MUT PROFILE)
    samples_left_both = get_filtered_samples(
        propertyView_dfs_left,
        variantView_dfs,
        mut_value_3,
        variant_col
    )

    samples_right_both = get_filtered_samples(
        propertyView_dfs_right,
        variantView_dfs,
        mut_value_3,
        variant_col
    )

    samples_both = samples_left_both.union(samples_right_both)

    samples_left = get_filtered_samples(
        propertyView_dfs_left,
        variantView_dfs,
        mut_value_1,
        variant_col
    )
    samples_right = get_filtered_samples(
        propertyView_dfs_right,
        variantView_dfs,
        mut_value_2,
        variant_col
    )

    # count nb seq in both for left and right selection --> used in actualize_overview_table
    variantView_df_both_left = pd.concat([df[df['sample.id'].isin(samples_left_both)
                                             & df[variant_col].isin(mut_value_3)][[variant_col, "sample.id"]] for df in
                                          variantView_dfs],
                                         ignore_index=True, axis=0)
    variantView_df_both_left = variantView_df_both_left.groupby([variant_col]) \
        .size().reset_index().rename(columns={0: "freq l"})
    variantView_df_both_right = pd.concat([df[df['sample.id'].isin(samples_right_both)
                                              & df[variant_col].isin(mut_value_3)] for df in variantView_dfs],
                                          ignore_index=True, axis=0)
    variantView_df_both_right = variantView_df_both_right.groupby([variant_col]) \
        .size().reset_index().rename(columns={0: "freq r"})
    variantView_df_both = pd.merge(variantView_df_both_left, variantView_df_both_right,
                                   how='inner', on=[variant_col]).reset_index(drop=True)
    # sort by sum of both freq
    sorted_indices = (variantView_df_both["freq l"] + variantView_df_both["freq r"]).sort_values(ascending=False).index
    variantView_df_both = variantView_df_both.loc[sorted_indices, :].reset_index(drop=True)

    variantView_dfs_both = [df[df['sample.id'].isin(samples_both)] for df in variantView_dfs]
    variantView_dfs_left = [df[df['sample.id'].isin(samples_left)] for df in variantView_dfs]
    variantView_dfs_right = [df[df['sample.id'].isin(samples_right)] for df in variantView_dfs]
    table_columns = [
        "sample.name",
        "variant.label",
        "IMPORTED",
        "COLLECTION_DATE",
        "RELEASE_DATE",
        "ISOLATE",
        "LENGTH",
        "SEQ_TECH",
        "COUNTRY",
        "GEO_LOCATION",
        "HOST",
        "GENOME_COMPLETENESS",
        "reference.accession",
    ]
    if aa_nt_radio == 'cds':
        table_columns[1] = "gene:variant"
    table_df_1 = pd.concat(
        [
            merge_tables(variantView_dfs_left[i], propertyView_dfs_left[i])
            for i in range(len(variantView_dfs_left))
        ],
        ignore_index=True,
        axis=0,
    )[table_columns]
    table_df_2 = pd.concat(
        [
            merge_tables(variantView_dfs_right[i], propertyView_dfs_right[i])
            for i in range(len(variantView_dfs_right))
        ],
        ignore_index=True,
        axis=0
    )[table_columns]
    table_df_3 = pd.concat(
        [
            merge_tables(variantView_dfs_both[i], propertyView_dfs_left[i])
            for i in range(len(variantView_dfs_both))
        ]
        + [
            merge_tables(variantView_dfs_both[i], propertyView_dfs_right[i])
            for i in range(len(variantView_dfs_both))
        ],
        ignore_index=True,
        axis=0,
    )[table_columns]

    table_df_1 = combine_labels_by_sample(table_df_1, aa_nt_radio)
    table_df_2 = combine_labels_by_sample(table_df_2, aa_nt_radio)
    table_df_3 = combine_labels_by_sample(table_df_3, aa_nt_radio)

    return table_df_1, table_df_2, table_df_3, variantView_df_both
