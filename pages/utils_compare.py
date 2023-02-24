import pandas as pd
import datetime

from pages.utils_worldMap_explorer import DateSlider, TableFilter


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


def select_variantView_dfs(df_dict, complete_partial_radio, reference_value, aa_nt_radio):
    variantView_dfs = [df_dict["variantView"]['complete'][reference_value][aa_nt_radio]]
    if complete_partial_radio == 'partial':
        variantView_dfs.append(df_dict["variantView"]['partial'][reference_value][aa_nt_radio])
    return variantView_dfs


def select_propertyView_dfs(df_dict, complete_partial_radio):
    propertyView_dfs = [df_dict["propertyView"]["complete"]]
    if complete_partial_radio == 'partial':
        propertyView_dfs.append(df_dict["propertyView"]["partial"])
    return propertyView_dfs


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


def combine_labels_by_sample(df, aa_nt_radio, col):
    if not df.empty:
        if aa_nt_radio == "cds":
            df['variant.label'] = df['element.symbol'].astype(str) + "::" + df['variant.label']
        df = df.drop(columns=["element.symbol"])
        df = (
            df.groupby(
                col[:-2],
                dropna=False,
            )["variant.label"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index()
        )
        if aa_nt_radio == "cds":
            df = df.rename(columns={"variant.label": "AA_PROFILE"})
        elif aa_nt_radio == "source":
            df = df.rename(columns={"variant.label": "NUC_PROFILE"})
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

    propertyView_both = pd.concat(
        propertyView_dfs_left + propertyView_dfs_right,
        ignore_index=True, axis=0
    ).drop_duplicates()

    if aa_nt_radio == 'cds':
        variantView_dfs_both = [df[df['variant.label'].isin(mut_value_3)
                                   & df['element.symbol'].isin(gene_dropdown_1 + gene_dropdown_2)] for df in variantView_dfs_left] + \
                               [df[df['variant.label'].isin(mut_value_3)
                                   & df['element.symbol'].isin(gene_dropdown_1 + gene_dropdown_2)] for df in variantView_dfs_right]
        variantView_dfs_left = [df[df['variant.label'].isin(mut_value_1)
                                & df['element.symbol'].isin(gene_dropdown_1)] for df in variantView_dfs_left]
        variantView_dfs_right = [df[df['variant.label'].isin(mut_value_2)
                                    & df['element.symbol'].isin(gene_dropdown_2)] for df in variantView_dfs_right]
    else:
        variantView_dfs_both = [df[df['variant.label'].isin(mut_value_3)] for df in variantView_dfs_left] + \
                               [df[df['variant.label'].isin(mut_value_3)] for df in variantView_dfs_right]
        variantView_dfs_left = [df[df['variant.label'].isin(mut_value_1)] for df in variantView_dfs_left]
        variantView_dfs_right = [df[df['variant.label'].isin(mut_value_2)] for df in variantView_dfs_right]

    variantView_both = pd.concat(variantView_dfs_both, ignore_index=True, axis=0).drop_duplicates()

    table_columns = [
        "sample.name",
        "COLLECTION_DATE",
        "ISOLATE",
        "SEQ_TECH",
        "COUNTRY",
        "GEO_LOCATION",
        "HOST",
        "reference.accession",
        "element.symbol",
        "variant.label",
    ]

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

    table_df_3 = merge_tables(variantView_both, propertyView_both)[table_columns]

    table_df_1 = combine_labels_by_sample(table_df_1, aa_nt_radio, table_columns)
    table_df_2 = combine_labels_by_sample(table_df_2, aa_nt_radio, table_columns)
    table_df_3 = combine_labels_by_sample(table_df_3, aa_nt_radio, table_columns)

    return table_df_1, table_df_2, table_df_3
