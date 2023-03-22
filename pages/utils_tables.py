from datetime import datetime
import pandas as pd

from pages.utils_filters import select_propertyView_dfs
from pages.utils_filters import select_variantView_dfs
from pages.utils_worldMap_explorer import DateSlider


# table results for filter
class TableFilter(object):
    """
    returns df for table output: sample.name, COLLECTION_DATE, RELEASE_DATE, ISOLATE, LENGTH, SEQ_TECH, COUNTRY,
    GEO_LOCATION, HOST, REFERENCE_ACCESSION, NUC_PROFILE, AA_PROFILE
    for samples matching filter options, all nucleotide and aminoacid variants are returned
    """

    def __init__(self, table_type, mut_value, aa_nt_radio=None, seqtech=None, countries=None, start_date=None,
                 end_date=None):
        """
        """
        super(TableFilter, self).__init__()
        self.table_type = table_type
        self.mut_value = mut_value
        if table_type == "explorer":
            self.table_columns = [
                "sample.name",
                "NUC_PROFILE",
                "AA_PROFILE",
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
                "REFERENCE_ACCESSION",
            ]
        elif table_type == "compare":
            self.table_columns = [
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

            self.aa_nt_radio = aa_nt_radio
            self.seqtech = seqtech
            self.countries = countries
            self.start_date = start_date
            self.end_date = end_date
            if aa_nt_radio == 'cds':
                self.variant_col = "gene:variant"
                self.table_columns[1] = "gene:variant"
            elif aa_nt_radio == 'source':
                self.variant_col = "variant.label"

    def _get_samples_by_filters(
            self,
            propertyView_dfs,
            variantView_dfs,
            seq_tech_list,
            dates,
            countries,
    ):
        sample_set = set()
        for i, df in enumerate(variantView_dfs):
            samples = set(propertyView_dfs[i][
                              propertyView_dfs[i]["COLLECTION_DATE"].isin(dates)
                              & propertyView_dfs[i]["SEQ_TECH"].isin(seq_tech_list)
                              & propertyView_dfs[i]["COUNTRY"].isin(countries)
                              ]["sample.id"])
            sample_set = sample_set.union(
                set(
                    df[
                        df["sample.id"].isin(samples)
                        & df["gene:variant"].isin(self.mut_value)
                        ]["sample.id"]
                )
            )
        return sample_set

    def get_samples_by_mutation(self, propertyView_dfs, variantView_dfs):
        new_samples = set()
        for i, df in enumerate(variantView_dfs):
            samples = set(propertyView_dfs[i]["sample.id"])
            new_samples = new_samples.union(set(df[df["sample.id"].isin(samples)
                                                   & df[self.variant_col].isin(self.mut_value)
                                                   ]["sample.id"]))
        return new_samples

    def _merge_variantView_with_propertyView(self, variantView, propertyView):
        return pd.merge(
            variantView,
            propertyView,
            how="inner",
            on=["sample.id", "sample.name"]
        )

    def concat_and_merge_tables(self, variantView_dfs, propertyView_dfs):
        return pd.concat(
            [
                self._merge_variantView_with_propertyView(variantView_dfs[i], propertyView_dfs[i])
                for i in range(len(variantView_dfs))
            ],
            ignore_index=True,
            axis=0,
        )[self.table_columns]

    def combine_labels_by_sample(self, df, aa_nt):
        if self.table_type == 'explorer':
            cols = [
                "sample.name",
                "sample.id",
                "reference.id",
                "reference.accession",
            ]
            if aa_nt == "cds":
                cols.append("gene:variant")
            elif aa_nt == "source":
                cols.append("variant.label")
            df = df[cols]
        elif self.table_type == "compare":
            cols = list(df.columns)
        if aa_nt == "cds":
            cols.remove("gene:variant")
            df = (
                df.groupby(
                    cols,
                    dropna=False,
                    group_keys=True
                )["gene:variant"]
                    .apply(lambda x: ",".join([str(y) for y in set(x)]))
                    .reset_index()
                    .rename(columns={"gene:variant": "AA_PROFILE"})
            )[["sample.name", "AA_PROFILE"] + cols[1:]]
        elif aa_nt == "source":
            cols.remove("variant.label")
            df = (
                df.groupby(
                    cols,
                    dropna=False,
                    group_keys=True
                )["variant.label"]
                    .apply(lambda x: ",".join([str(y) for y in set(x)]))
                    .reset_index()
                    .rename(columns={"variant.label": "NUC_PROFILE"})
            )[['sample.name', "NUC_PROFILE"] + cols[1:]]
        df = df.rename(columns={'reference.accession': "REFERENCE_ACCESSION"})
        return df

    def filter_propertyView(self, df):
        date_list = DateSlider.get_all_dates(
            datetime.strptime(self.start_date, "%Y-%m-%d").date(),
            datetime.strptime(self.end_date, "%Y-%m-%d").date(),
        )
        return df[
            (df["SEQ_TECH"].isin(self.seqtech))
            & (df["COUNTRY"].isin(self.countries))
            & (df["COLLECTION_DATE"].isin(date_list))
            ]

    def create_explore_table(
            self,
            df_dict,
            complete_partial_radio,
            seq_tech_list,
            reference_id,
            dates,
            countries,
    ):
        """
        param df_dict: all pre-processed pandas df
        param complete_partial_radio: complete OR partial (= using complete AND partial dfs)
        param mutation_list: mutations of style "gene:variant" (user selected)
        param seq_tech_list: seq tech list of filter, type list of str
        param reference_id: int
        param dates: list of dates (date slider chosen date + interval)
        param countries: country list of filter, type list of str
        """
        variantView_dfs_cds = select_variantView_dfs(
            df_dict, complete_partial_radio, reference_id, 'cds'
        )
        variantView_dfs_source = select_variantView_dfs(
            df_dict, complete_partial_radio, reference_id, 'source'
        )
        propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)
        samples = self._get_samples_by_filters(
            propertyView_dfs,
            variantView_dfs_cds,
            seq_tech_list,
            dates,
            countries
        )
        variantView_dfs_cds = [variantView[variantView["sample.id"].isin(samples)]
                               for variantView in variantView_dfs_cds]
        variantView_dfs_source = [variantView[variantView["sample.id"].isin(samples)]
                                  for variantView in variantView_dfs_source]
        table_dfs_cds = []
        for variantView in variantView_dfs_cds:
            result_df = self.combine_labels_by_sample(variantView, 'cds')
            table_dfs_cds.append(result_df)
        table_df_cds = pd.concat(table_dfs_cds, ignore_index=True, axis=0)
        table_dfs_source = []
        for variantView in variantView_dfs_source:
            result_df = self.combine_labels_by_sample(variantView, 'source')
            table_dfs_source.append(result_df)
        table_df_source = pd.concat(table_dfs_source, ignore_index=True, axis=0)
        df = pd.merge(table_df_cds, table_df_source,
                      how="outer",
                      on=['sample.id', 'sample.name', 'REFERENCE_ACCESSION', "reference.id"])
        propertyView_df = pd.concat(propertyView_dfs, ignore_index=True, axis=0)
        df = self._merge_variantView_with_propertyView(df, propertyView_df)
        df = df[self.table_columns]
        if df.empty:
            df = pd.DataFrame(
                columns=self.table_columns
            )
        return df

    def create_compare_table_left_and_right(self, variantView_dfs, propertyView_dfs):
        # all samples of selection (filter by mutation directly do not allow a complete mutation PROFILE)
        samples = self.get_samples_by_mutation(propertyView_dfs, variantView_dfs)
        variantView_dfs = [df[df['sample.id'].isin(samples)] for df in variantView_dfs]
        table_df = self.concat_and_merge_tables(variantView_dfs, propertyView_dfs)
        table_df = self.combine_labels_by_sample(table_df, self.aa_nt_radio)
        return table_df

    def create_compare_table_both(self, variantView_dfs, propertyView_dfs_left, propertyView_dfs_right):
        # all samples of selection (filter by mutation directly do not allow a complete mutation PROFILE)
        samples_left_both = self.get_samples_by_mutation(
            propertyView_dfs_left,
            variantView_dfs,
        )
        samples_right_both = self.get_samples_by_mutation(
            propertyView_dfs_right,
            variantView_dfs,
        )
        samples = samples_left_both.union(samples_right_both)

        variantView_dfs = [df[df['sample.id'].isin(samples)] for df in variantView_dfs]
        table_df_l = self.concat_and_merge_tables(variantView_dfs, propertyView_dfs_left)
        table_df_r = self.concat_and_merge_tables(variantView_dfs, propertyView_dfs_right)
        table_df = pd.concat([table_df_l, table_df_r], ignore_index=True, axis=0)
        table_df = self.combine_labels_by_sample(table_df, self.aa_nt_radio)
        return table_df, samples_left_both, samples_right_both


class OverviewTable:
    table_columns = [
        'unique left', "# left",
        'shared', "# l", "# r",
        'unique right', "# right",
    ]
    column_names = [
        'unique variants for left selection', "# seq left",
        'shared variants of both selections', "# seq left", "# seq right",
        'unique variants for right selection', "# seq right",
    ]

    def __init__(self, aa_nt_radio):
        """
        """
        super(OverviewTable, self).__init__()
        if aa_nt_radio == 'cds':
            self.variant_col = "gene:variant"
        elif aa_nt_radio == 'source':
            self.variant_col = "variant.label"
        self.single_table_cols = [self.variant_col, "freq"]

    def _filter_for_samples_and_group_by_variant(self, samples, mut, variantView_dfs, col_name):
        filtered_variantView_df = pd.concat([df[df['sample.id'].isin(samples)
                                                & df[self.variant_col].isin(mut)]
                                             [[self.variant_col, "sample.id"]] for df in variantView_dfs],
                                            ignore_index=True, axis=0)
        grouped_df = filtered_variantView_df.groupby([self.variant_col]) \
            .size().reset_index().rename(columns={0: col_name})
        return grouped_df

    def _sort_by_sum_of_both_frequencies(self, variantView_df_overview_both):
        sorted_indices = (variantView_df_overview_both["freq l"] + variantView_df_overview_both["freq r"]) \
            .sort_values(ascending=False).index
        variantView_df_overview_both = variantView_df_overview_both.loc[sorted_indices, :].reset_index(drop=True)
        return variantView_df_overview_both

    def count_shared_mutation_in_left_and_right_selection(
            self,
            mut_value_both,
            samples_left,
            samples_right,
            variantView_dfs
    ):
        """
        count nb seq in both for left and right selection --> used in actualize_overview_table
        """
        variantView_df_both_left = self._filter_for_samples_and_group_by_variant(samples_left,
                                                                                 mut_value_both,
                                                                                 variantView_dfs,
                                                                                 "freq l")

        variantView_df_both_right = self._filter_for_samples_and_group_by_variant(samples_right,
                                                                                  mut_value_both,
                                                                                  variantView_dfs,
                                                                                  "freq r")
        variantView_df_overview_both = pd.merge(variantView_df_both_left, variantView_df_both_right,
                                                how='inner', on=[self.variant_col]).reset_index(drop=True)
        variantView_df_overview_both = self._sort_by_sum_of_both_frequencies(variantView_df_overview_both)
        return variantView_df_overview_both[[self.variant_col, 'freq l', 'freq r']]

    def create_df_from_mutation_options(self, mut_options, mut_values):
        df = pd.DataFrame.from_records(mut_options, columns=['value', 'freq'])
        return df[df['value'].isin(mut_values)]

    def create_overview_table(self, df_left, df_both, df_right):
        table_df = pd.concat([df_left, df_both, df_right], axis=1, ignore_index=True)
        table_df.columns = self.table_columns
        table_df_records = table_df.to_dict("records")
        column_names = [{"name": self.column_names[i], "id": j} for i, j in enumerate(self.table_columns)]

        return table_df_records, column_names
