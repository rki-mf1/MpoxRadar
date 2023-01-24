import copy
import datetime
from datetime import date
from datetime import timedelta
import math
import time

import pandas as pd
import plotly.express as px
from scipy.stats import linregress


# table results for filter
class TableFilter(object):
    """
    returns df for table output: sample.name, COLLECTION_DATE, RELEASE_DATE, ISOLATE, LENGTH, SEQ_TECH, COUNTRY,
    GEO_LOCATION, HOST, REFERENCE_ACCESSION, NUC_PROFILE, AA_PROFILE
    """

    def __init__(self, propertyView_df, variantView_df):
        """
        df_location: location_ID | location (str name) | lat | lon
        df_all_dates_all_voc: df containing information to all voc of all dates
                                location_ID | date | sample_id_list | mutations | number_sequences

        column sample_id_list = comma separated str with all strain_ids containing same voc on same date and same location
        """
        # TODO length column unfilled
        super(TableFilter, self).__init__()
        self.table_df = pd.merge(
            variantView_df[
                [
                    "variant.label",
                    "sample.id",
                    "element.type",
                    "reference.accession",
                    "reference.id",
                ]
            ],
            propertyView_df[
                [
                    "sample.name",
                    "sample.id",
                    "COLLECTION_DATE",
                    "RELEASE_DATE",
                    "ISOLATE",
                    "LENGTH",
                    "SEQ_TECH",
                    "COUNTRY",
                    "GEO_LOCATION",
                    "HOST",
                ]
            ],
            how="left",
            on="sample.id",
        )[
            [
                "sample.id",
                "sample.name",
                "COLLECTION_DATE",
                "RELEASE_DATE",
                "ISOLATE",
                "LENGTH",
                "SEQ_TECH",
                "COUNTRY",
                "GEO_LOCATION",
                "HOST",
                "reference.accession",
                "reference.id",
                "element.type",
                "variant.label",
            ]
        ]
        #        print(tabulate(self.table_df[0:10], headers='keys', tablefmt='psql'))

    def _get_filtered_samples(self, mutation_list, seq_tech_list, reference_id, dates):
        samples = self.table_df[
            self.table_df["COLLECTION_DATE"].isin(dates)
            & self.table_df["variant.label"].isin(mutation_list)
            & (self.table_df["reference.id"] == reference_id)
            & self.table_df["SEQ_TECH"].isin(seq_tech_list)
        ]["sample.id"]
        return samples.tolist()

    def get_filtered_table(
        self, mutation_list=None, seq_tech_list=None, reference_id=2, dates=None
    ):
        if mutation_list is None:
            mutation_list = []
        if seq_tech_list is None:
            seq_tech_list = []
        if dates is None:
            dates = []
        samples = self._get_filtered_samples(
            mutation_list, seq_tech_list, reference_id, dates
        )
        df = self.table_df[self.table_df["sample.id"].isin(samples)]
        # combine NT mutation to cs list (NUC_PROFILE) and AA mutations o cs list (element.type == cds or
        df.groupby(
            [
                "sample.id",
                "sample.name",
                "COLLECTION_DATE",
                "RELEASE_DATE",
                "ISOLATE",
                "LENGTH",
                "SEQ_TECH",
                "COUNTRY",
                "GEO_LOCATION",
                "HOST",
                "reference.accession",
                "element.type",
            ]
        )["variant.label"].apply(lambda x: x.str.cat(sep=",")).reset_index()
        # separate varaint.label into columns 'NUC_PROFILE' and 'AA_PROFILE' based on element.type value
        # TODO there must be a better way
        NUC_PROFILE_df = df.loc[df["element.type"] == "source"][
            ["sample.id", "variant.label"]
        ]
        nuc_dict = dict(
            zip(NUC_PROFILE_df["sample.id"], NUC_PROFILE_df["variant.label"])
        )
        AA_PROFILE_df = df.loc[df["element.type"] == "cds"][
            ["sample.id", "variant.label"]
        ]
        aa_dict = dict(zip(AA_PROFILE_df["sample.id"], AA_PROFILE_df["variant.label"]))
        df = df[
            [
                "sample.id",
                "sample.name",
                "COLLECTION_DATE",
                "RELEASE_DATE",
                "ISOLATE",
                "LENGTH",
                "SEQ_TECH",
                "COUNTRY",
                "GEO_LOCATION",
                "HOST",
                "reference.accession",
            ]
        ].drop_duplicates()
        df["NUC_PROFILE"] = "-"
        df["AA_PROFILE"] = "-"
        df["NUC_PROFILE"] = df["sample.id"].apply(lambda x: nuc_dict[x])
        df["AA_PROFILE"] = df["sample.id"].apply(lambda x: aa_dict[x])
        df = df.drop(columns=["sample.id"])
        df.columns = [
            "sample.name",
            "COLLECTION_DATE",
            "RELEASE_DATE",
            "ISOLATE",
            "LENGTH",
            "SEQ_TECH",
            "COUNTRY",
            "GEO_LOCATION",
            "HOST",
            "REFERENCE_ACCESSION",
            "NUC_PROFILE",
            "AA_PROFILE",
        ]
        return df


class DfsAndDetailPlot(object):
    def __init__(self, propertyView, variantView, location_coordinates):
        """
        df_location: location_ID | location (str name) | lat | lon
        df_all_dates_all_voc: df containing information to all voc of all dates
                                location_ID | date | sample_id_list | mutations | number_sequences

        column sample_id_list = comma separated str with all strain_ids containing same voc on same date and same location
        """
        super(DfsAndDetailPlot, self).__init__()
        variantView = variantView[variantView["element.type"] == "cds"].reset_index(
            drop=True
        )
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
        self.mutations_of_concern = self.get_mutations_of_concern(variantView)
        self.mutations = copy.deepcopy(self.mutations_of_concern)
        self.color_dict = self.get_color_dict()
        dates = propertyView["COLLECTION_DATE"]
        try:
            self.min_date = min(dates)
        except:  # noqa: E722
            print(propertyView)
        self.max_date = max(dates)
        self.df_location = location_coordinates[["name", "lat", "lon"]].rename(
            columns={"name": "COUNTRY"}
        )
        self.df_all_dates_all_voc = self._get_full_df(propertyView, variantView)
        # print(tabulate(self.df_all_dates_all_voc[0:10], headers='keys', tablefmt='psql'))

    def _get_full_df(self, propertyView, variantView):
        # 1. join metadata
        df = variantView[variantView["element.type"] == "cds"].reset_index(drop=True)
        # 79914
        df_all_dates_all_voc = pd.merge(
            df[["sample.id", "variant.label", "reference.id"]],
            propertyView[["sample.id", "COUNTRY", "COLLECTION_DATE", "SEQ_TECH"]],
            how="left",
            on="sample.id",
        )[
            [
                "sample.id",
                "COUNTRY",
                "COLLECTION_DATE",
                "variant.label",
                "reference.id",
                "SEQ_TECH",
            ]
        ]

        # 4. location_ID, date, amino_acid --> concat all strain_ids into one comma separated string list and count
        df_all_dates_all_voc = (
            df_all_dates_all_voc.groupby(
                [
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "variant.label",
                    "reference.id",
                    "SEQ_TECH",
                ]
            )["sample.id"]
            .apply(lambda x: ",".join([str(y) for y in set(x)]))
            .reset_index(name="sample_id_list")
        )
        # 5. add sequence count
        # df_all_dates_all_voc["number_sequences"] = df_all_dates_all_voc["sample_id_list"].apply(lambda x: len(x))
        df_all_dates_all_voc["number_sequences"] = df_all_dates_all_voc[
            "sample_id_list"
        ].apply(lambda x: len(x.split(",")))
        # df_all_dates_all_voc = df_all_dates_all_voc.rename(columns={"variant.label": "mutations"})
        # 6. fill with 0 no mutation
        full_df_without_nb_seq = df_all_dates_all_voc[
            ["COUNTRY", "COLLECTION_DATE", "reference.id", "SEQ_TECH"]
        ].drop_duplicates()
        full_df_without_nb_seq["number_sequences"] = 0
        full_df_without_nb_seq = full_df_without_nb_seq.merge(
            pd.DataFrame(self.mutations, columns=["variant.label"]), how="cross"
        )
        # combine real seq counts (per voc per date per location) with zero values
        df_all_dates_all_voc = (
            pd.concat([df_all_dates_all_voc, full_df_without_nb_seq])
            .drop_duplicates(
                subset=[
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "reference.id",
                    "SEQ_TECH",
                    "variant.label",
                ],
                keep="first",
            )
            .reset_index(drop=True)
        )
        df_all_dates_all_voc = df_all_dates_all_voc[
            [
                "COUNTRY",
                "COLLECTION_DATE",
                "reference.id",
                "SEQ_TECH",
                "sample_id_list",
                "variant.label",
                "number_sequences",
            ]
        ]
        df_all_dates_all_voc = df_all_dates_all_voc.astype({"sample_id_list": "str"})
        return df_all_dates_all_voc[
            [
                "COUNTRY",
                "COLLECTION_DATE",
                "reference.id",
                "SEQ_TECH",
                "sample_id_list",
                "variant.label",
                "number_sequences",
            ]
        ]

    def get_number_sequences_per_interval(self, dates, mutations, location_ID=None):
        """
        param df: df_all_dates_all_voc
        param dates: [date(2021, 12, 12), date(2021, 12, 13), ...]
        """
        df = self.df_all_dates_all_voc[
            self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
            & self.df_all_dates_all_voc["variant.label"].isin(mutations)
        ]
        if location_ID:
            df = df[df.location_ID == location_ID]
        seq_set = set(",".join(list(df["sample_id_list"])).split(","))
        if "0" in seq_set:
            return len(seq_set) - 1
        else:
            return len(seq_set)

    def get_color_dict(self):
        """
        defined color by mutation
        color scheme contains 24 different colors, if #mutations>24 use second color scheme with 24 colors
        more mutations --> color schema starts again (max 48 different colors)
        wildtype= green, no_mutation (no sequence meets the user selected mutations, dates, location) = grey
        """
        color_dict = {}
        color_schemes = [px.colors.qualitative.Light24, px.colors.qualitative.Dark24]
        mutations = [
            var[1:-1] if "`" in var else var for var in self.mutations_of_concern
        ]
        for i, mutation in enumerate(mutations):
            j = i % 48
            if j < 24:
                color_dict[mutation] = color_schemes[0][j]
            elif j > 23 and j < 48:
                color_dict[mutation] = color_schemes[1][j - 24]
        color_dict["no_mutation"] = "grey"
        return color_dict

    def get_mutations_of_concern(self, variantView):
        """
        returns: list of voc, ["Y144-144del", "N501Y", "L18F", "N501Y", "R190S", "E484K,R683G", ... ]
        """
        df_grouped_by_mutation = (
            variantView[["variant.label"]]
            .groupby(["variant.label"])["variant.label"]
            .count()
            .reset_index(name="count")
            .sort_values(["count"], ascending=False)
        )
        sorted_mutations = df_grouped_by_mutation["variant.label"].tolist()
        return sorted_mutations

    # pandas df methods instead of sql queries
    def get_nb_of_seq(self, x):
        x_s = set(x.split(","))
        if "0" in x_s:
            return len(x_s) - 1
        else:
            return len(x_s)

    def get_number_sequences_all_dates_all_var(self, da_loc_id_list_df):
        """
        return date  location_ID  number_sequences
        """

        da_loc_nb_df = (
            da_loc_id_list_df.groupby(["COLLECTION_DATE", "COUNTRY"])["sample_id_list"]
            .agg(lambda x: ",".join(x))
            .reset_index()
        )
        da_loc_nb_df["number_sequences"] = (
            da_loc_nb_df["sample_id_list"]
            .apply(lambda x: self.get_nb_of_seq(x))
            .drop(columns=["sample_id_list"])
        )
        return da_loc_nb_df

    def get_number_mut_sequences_per_location(self, full_df, dates, mutations):
        df_loc_seq_nb_for_selected_voc = full_df[
            full_df["COLLECTION_DATE"].isin(dates)
        ].drop(columns=["COLLECTION_DATE"])
        df_loc_seq_nb_for_selected_voc = (
            df_loc_seq_nb_for_selected_voc[
                df_loc_seq_nb_for_selected_voc.mutations.isin(mutations)
            ]
            .drop(columns=["variant.label", "number_sequences"])
            .drop_duplicates()
        )
        df_loc_seq_nb_for_selected_voc2 = (
            df_loc_seq_nb_for_selected_voc.groupby(["COUNTRY"])["sample_id_list"]
            .agg(lambda x: ",".join(x))
            .reset_index()
        )
        df_loc_seq_nb_for_selected_voc2[
            "number_sequences"
        ] = df_loc_seq_nb_for_selected_voc2["sample_id_list"].apply(
            lambda x: self.get_nb_of_seq(x)
        )
        return df_loc_seq_nb_for_selected_voc2.drop(columns=["sample_id_list"])

    def get_df_for_increase_map_or_plot(
        self, mutations, dates, reference_id, seq_tech_list, location_name=None
    ):
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        if not location_name:
            df = (
                self.df_all_dates_all_voc[
                    self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                    & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                    & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                    & (self.df_all_dates_all_voc["reference.id"] == reference_id)
                ]
                .groupby(["COUNTRY", "variant.label", "COLLECTION_DATE"])
                .sum()
                .reset_index()
            )
        else:
            df = (
                self.df_all_dates_all_voc[
                    self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                    & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                    & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                    & (self.df_all_dates_all_voc["reference.id"] == reference_id)
                    & (self.df_all_dates_all_voc["COUNTRY"] == location_name)
                ]
                .groupby(["COUNTRY", "variant.label", "COLLECTION_DATE"])
                .sum()
                .reset_index()
            )
        return df

    def get_df_for_frequency_bar(
        self, mutations, dates, reference_id, seqtech_list, location_name
    ):
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        df = (
            self.df_all_dates_all_voc[
                [
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "variant.label",
                    "SEQ_TECH",
                    "reference.id",
                    "number_sequences",
                ]
            ][
                self.df_all_dates_all_voc["COUNTRY"].isin([location_name])
                & self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seqtech_list)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
            ]
            .groupby(["COUNTRY", "variant.label"])
            .sum()
            .reset_index()
        )
        return df

    def get_increase_df(
        self, dates, mutations, reference_id, seq_tech_list, location_name=None
    ):
        """
        shows change in frequency of the different virus mutations, calculate lin regression with scipy.stats module and
        returns the slope of the regression line (x:range (interval)), y:number of sequences per day in selected interval
        :param dates: list of date objects in selected interval e.g. [2021-01-01, 2021-01-10]
        :param mutations: list of str, selected mutations (from dropdown left menu)
        :param location_ID: int
        """
        # df:     location_ID | date | mutations | number_sequences
        df = self.get_df_for_increase_map_or_plot(
            mutations, dates, reference_id, seq_tech_list, location_name=location_name
        )
        df = df.groupby(["COUNTRY", "variant.label"]).agg(
            {
                "number_sequences": lambda x: list(x),
                "COLLECTION_DATE": lambda x: list(x),
            }
        )
        if df.empty:
            df = pd.DataFrame(
                [], columns=["number_sequences", "COLLECTION_DATE", "slope"]
            )
        else:
            df.reset_index(inplace=True)
            slopes = []
            for i in range(len(df["number_sequences"])):
                dates = [
                    (date - self.min_date).days for date in df["COLLECTION_DATE"][i]
                ]
                nu = df["number_sequences"][i]
                if len(set(nu)) == 1:
                    slopes.append(0)
                else:
                    slopes.append(linregress(dates, nu).slope)
            df["slope"] = slopes
            df = df.astype({"slope": float})
        return df

    def get_nth_mutation_per_region(self, df_all, column_of_interest, ordinal_number=1):
        """
        group by location_ID and take every nth row from group,
        if ordinal number > number of rows per group -> take last row
        :param df_all: df with location, mutations and number_sequences
        :param column_of_interest: 'number_sequences' or 'slope'
        :param ordinal_number: int the n of nth
        :return df: with every nth most frequent mutation per postal code
        """
        ordinal_number -= 1
        df_all.sort_values(
            by=["COUNTRY", column_of_interest], inplace=True, ascending=False
        )
        grouped_df = df_all.groupby(["COUNTRY"], as_index=False)
        df = grouped_df.nth(ordinal_number)

        # no entry for nth mutation, not needed anymore, now all with seq (number_seq = 0)
        if len(grouped_df) != len(df):
            l = []
            for location_ID in set(df_all["COUNTRY"]):
                try:
                    l.append(grouped_df.get_group(location_ID).iloc[ordinal_number])
                except IndexError:
                    pass
            df = pd.DataFrame(
                l, columns=["COUNTRY", "variant.label", "number_sequences"]
            )
        return df

    def get_df_for_scatter_plot(
        self, mutations, dates, reference_id, seqtech_list, location_name
    ):
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        df = self.df_all_dates_all_voc[
            self.df_all_dates_all_voc["COUNTRY"].isin([location_name])
            & self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
            & self.df_all_dates_all_voc["variant.label"].isin(mutations)
            & self.df_all_dates_all_voc["SEQ_TECH"].isin(seqtech_list)
            & (self.df_all_dates_all_voc["reference.id"] == reference_id)
        ].reset_index(drop=True)
        return df[["COUNTRY", "COLLECTION_DATE", "variant.label", "number_sequences"]]

    # TODO change from df_count to use df_all_dates
    def get_mutation_proportion_df(self, dates, mutations):
        """
                df_count: number all seq per day per location
                    date | location_ID | sample_id_list | number_sequences |
        :param dates: list of dates [type:date] of selected date and interval
        :param mutations: list of str, selected mutations (from dropdown left menu)
        :return df  location_ID |  mutation_proportion
        returns proportion of ([all variants not in voc](if wildtype in param mutations) + vocs in param mutations)
        but this case can only occur if wildtype included in drop down selected mutations
        """
        # df_loc_seq_nb_for_selected_voc:  location_ID | number_sequences
        df_loc_seq_nb_for_selected_voc = self.get_number_mut_sequences_per_location(
            self.df_all_dates_all_voc, dates, mutations
        )
        if not df_loc_seq_nb_for_selected_voc.empty:
            df_count = (
                self.df_all_dates_all_voc[
                    self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                ]
                .groupby("COUNTRY", as_index=False)["number_sequences"]
                .sum()
            )
            var_to_nb_seq_dict = dict(zip(df_count.COUNTRY, df_count.number_sequences))
            df_loc_seq_nb_for_selected_voc = df_loc_seq_nb_for_selected_voc.groupby(
                ["COUNTRY"], as_index=False
            ).sum()
            df_loc_seq_nb_for_selected_voc[
                "mutation_proportion"
            ] = df_loc_seq_nb_for_selected_voc.apply(
                lambda row: row.number_sequences
                / var_to_nb_seq_dict[int(row.location_ID)]
                * 100,
                axis=1,
            )
            df_loc_seq_nb_for_selected_voc[
                "number_sequences"
            ] = df_loc_seq_nb_for_selected_voc.apply(
                lambda row: var_to_nb_seq_dict[row.location_ID], axis=1
            )
        else:
            df_loc_seq_nb_for_selected_voc["mutation_proportion"] = 0.0
        return df_loc_seq_nb_for_selected_voc

    def drop_rows_by_value(self, df, value, column):
        index_rows = df[df[column] == value].index
        df.drop(index_rows, inplace=True)
        return df

    def calculate_ticks_from_dates(self, dates, date_numbers):
        """
        set tickvals and ticktext for displaying dates in plot
        show only 6 dates for readability: /6
        """
        unique_dates = list(set(list(dates)))
        unique_dates.sort()
        unique_date_numbers = list(set(date_numbers))
        unique_date_numbers.sort()
        tickvals_date = unique_date_numbers[
            0 :: math.ceil(len(unique_date_numbers) / 6)
        ]
        ticktext_date = unique_dates[0 :: math.ceil(len(unique_dates) / 6)]
        return tickvals_date, ticktext_date

    def create_frequency_plot(self, df):
        fig = px.bar(
            df,
            y="number_sequences",
            x="variant.label",
            color="variant.label",
            orientation="v",
            hover_name="variant.label",
            hover_data={"variant.label": True, "number_sequences": True},
            color_discrete_map=self.color_dict,
            labels={"number_sequences": "# sequences", "variant.label": ""},
            height=300,
        )
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            margin={"l": 20, "b": 30, "r": 10, "t": 10},
            xaxis_title="selected variants",
            title_x=0.5,
        )
        return fig

    # plot methods
    def get_frequency_bar_chart(
        self, mutations, reference_id, seqtech_list, dates, location_name
    ):
        """
        :param mutations: list of str, selected mutations (from dropdown left menu)
        :param dates: list of dates [type:date] of selected date and interval
        :param location_ID: ID of hovered location
        :return fig bar chart showing mutation information of last hovered plz
        """
        df = self.get_df_for_frequency_bar(
            mutations, dates, reference_id, seqtech_list, location_name=location_name
        )
        df = self.drop_rows_by_value(df, 0, "number_sequences")
        #  df['variant.label'] = df['variant.label'].map(voc_label_dict).fillna(df['variant.label'])
        if df.empty:
            df = pd.DataFrame(
                data=[["no_mutation", 0]], columns=["variant.label", "number_sequences"]
            )
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type, unclear why this is working
        try:
            fig = self.create_frequency_plot(df)
        except ValueError:
            fig = self.create_frequency_plot(df)
        return fig

    def create_slope_plot(self, df):
        fig = px.bar(
            df,
            y="slope",
            x="variant.label",
            color="variant.label",
            orientation="v",
            hover_name="variant.label",
            hover_data={"variant.label": False, "slope": True},
            color_discrete_map=self.color_dict,
            height=300,
        )
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            margin={"l": 20, "b": 30, "r": 10, "t": 10},
            title_x=0.5,
        )
        return fig

    def get_slope_bar_plot(
        self, dates, mutations, reference_id, seqtech_list, location_name
    ):
        df = self.get_increase_df(
            dates, mutations, reference_id, seqtech_list, location_name
        )
        df = self.drop_rows_by_value(df, 0, "slope")
        if df.empty:
            columns = ["number_sequences", "COLLECTION_DATE", "slope", "variant.label"]
            row = [[0, "", 0, "no_mutation"]]
            df = pd.concat([df, pd.DataFrame(row, columns=columns)])
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type, unclear why this is working
        try:
            fig = self.create_slope_plot(df)
        except ValueError:
            fig = self.create_slope_plot(df)
        return fig

    def create_scatter_plot(self, df, tickvals_date, ticktext_date, axis_type):
        fig = px.scatter(
            df,
            x="date_numbers",
            y="number_sequences",
            color="variant.label",
            trendline="ols",
            color_discrete_map=self.color_dict,
            labels={
                "date_numbers": "COLLECTION_DATE",
                "number_sequences": "# sequences",
            },
            height=300,
        )
        fig.update_yaxes(
            type="linear" if axis_type == "linear" else "log",
        )
        fig.update_xaxes(
            showgrid=False,
            # show only 7 values
            tickmode="array",
            tickvals=tickvals_date,
            ticktext=ticktext_date,
            tickangle=-45,
        ),
        fig.update_layout(
            legend_title_text="",
            showlegend=True,
            margin={"l": 20, "b": 30, "r": 10, "t": 10},
            title_x=0.5,
        )
        fig.update_traces(marker={"size": 5})
        return fig

    def get_frequency_development_scatter_plot(
        self,
        mutations,
        reference_id,
        seqtech_list,
        dates,
        location_name,
        axis_type="lin",
    ):

        """
        :param mutations: list of str, selected mutations (from dropdown left menu)
        :param axis_type: lin or log
        :param dates: list of dates [type:datetime.date] of selected date and interval
        :return fig: scatter plot showing number of sequences per day of last hovered location
        """
        # TODO: same lines on top of each other have color of latest MOC -> change to mixed color
        if len(dates) == 0:
            dates = [
                dat
                for dat in [
                    self.max_date - timedelta(days=x) for x in reversed(range(28))
                ]
            ]

        df = self.get_df_for_scatter_plot(
            mutations, dates, reference_id, seqtech_list, location_name
        )
        # remove rows if VOC no seq in time-interval
        for var in mutations:
            if df[df["variant.label"] == var]["number_sequences"].sum() == 0:
                df = df[df["variant.label"] != var]
        # df['variant.label'] = df['variant.label'].map(voc_label_dict).fillna(df['variant.label'])
        # dummy dataframe for showing empty results
        if df.empty:
            df = pd.DataFrame(
                data=[[location_name, dates[-1], "no_mutations", 0]],
                columns=[
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "variant.label",
                    "number_sequences",
                ],
            )
        # date_numbers: assign date to number, numbers needed for calculation of trendline
        date_numbers = [(d - self.min_date).days for d in df["COLLECTION_DATE"]]
        df["date_numbers"] = date_numbers
        dates = df["COLLECTION_DATE"].apply(lambda x: x.strftime("%Y-%m-%d"))
        tickvals_date, ticktext_date = self.calculate_ticks_from_dates(
            dates, date_numbers
        )
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type, unclear why this is working
        try:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        except ValueError:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        return fig


class WorldMap(DfsAndDetailPlot):
    def __init__(self, propertyView, variantView, location_coordinates):
        """ """
        super(WorldMap, self).__init__(propertyView, variantView, location_coordinates)

    def get_world_map_df(self, method, mutations, reference_id, seq_tech_list, dates):
        """
        :param method: 'Frequency' or 'Mutation Proportion' or 'Increase'
        :param mutations: list of selected voc mutations
        :param dates: list of dates of selcted date and interval, date = class 'datetime.date'
        """

        if method == "Frequency":
            #  df:     location_ID   mutations  number_sequences
            # TODO exist ' in mpx too?
            mutations = [var[1:-1] if "`" in var else var for var in mutations]
            df = self.df_all_dates_all_voc[
                self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
            ]
            df = df.groupby(["COUNTRY", "variant.label"]).sum().reset_index()
            column_of_interest = "number_sequences"
        elif method == "Increase":
            #  df: date | mutations | number_sequences
            df = self.get_increase_df(dates, mutations, reference_id, seq_tech_list)
            # replace negative slope by 0 (cannot be shown)
            df["slope"] = df["slope"].fillna(0)
            num = df._get_numeric_data()
            num[num < 0] = 0
            column_of_interest = "slope"

        df = self.drop_rows_by_value(df, 0, column_of_interest)
        # df = _add_zero_fo_all_countries(df, countries, column_of_interest)
        if df.empty:
            df = pd.DataFrame(
                data=[["Germany", "no_mutation", 0, 0]],
                columns=[
                    "COUNTRY",
                    "variant.label",
                    "reference.id",
                    column_of_interest,
                ],
            )
        df = pd.merge(df, self.df_location, on="COUNTRY")[
            ["COUNTRY", "variant.label", column_of_interest, "lat", "lon"]
        ]
        print(len(df))

        return df, column_of_interest

    def get_most_frequent_map_df(self, world_map_df, column_of_interest, nth):
        def _circle_size(v, max_val, no_cats=29, basis_size=1):
            if v == 0:
                return 0
            delta = max_val / no_cats
            result = int(v / delta) + basis_size
            return result

        # df: location | mutations | number_sequences
        if world_map_df.empty:
            world_map_df = pd.DataFrame(
                data=[["51", "10", "", 10115, "no_mutation", 0, 0]],
                columns=[
                    "lat",
                    "lon",
                    "COUNTRY",
                    "variant.label",
                    column_of_interest,
                    "scaled_column",
                ],
            )
        for i in range(1, nth + 1):
            df_nth = self.get_nth_mutation_per_region(
                world_map_df, column_of_interest, i
            )
            if i == 1:
                df_nth_combined = df_nth
            else:
                df_nth_combined = pd.concat([df_nth_combined, df_nth])
        df = (
            pd.DataFrame(
                data=[["", 0]], columns=["COUNTRY", "lat", "lon", column_of_interest]
            )
            if df_nth_combined.empty
            else df_nth_combined
        )
        max_val = df["number_sequences"].max()
        df["scaled_column"] = df[column_of_interest].apply(
            lambda x: _circle_size(x, max_val)
        )
        # df['mutations'] = df['mutations'].map(voc_label_dict).fillna(df['mutations'])
        return df

    def create_map_fig(
        self, df, shown_hover_data, color_column, size_column, z=2, cen=None
    ):
        """
        param df:  COUNTRY  | variant.label   |   reference.id |   number_sequences | lat |  lon |   scaled_column
        param shown_hover_data: {'variant.label': True, 'number_sequences': True, 'COUNTRY': False, 'lat': False, 'lon': False, 'scaled_column': False}
        param color_column: variant.label
        param size_column: scaled_column

        OR
        param df:COUNTRY  | variant.label   |   number_sequences (list of nb seq per date) |    COLLECTION_DATE (list of dates)| slope (float)  |  lat |   lon
        param shown_hover_data: {'variant.label': True, 'slope': True, 'COUNTRY': False, 'lat': False, 'lon': False}
        param color_column: variant.label
        param size_column: slope

        """
        if cen is None:
            cen = dict(lat=51.5, lon=10.5)
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            color=color_column,
            size=size_column,
            color_discrete_map=self.color_dict,
            hover_name="COUNTRY",
            hover_data=shown_hover_data,
            center=cen,
            zoom=z,
            size_max=30,
            opacity=0.5,
            labels={el: el.replace(".", " ").title() for el in df.columns},
        )
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            mapbox_style="open-street-map",  # carto-positron
        )
        return fig

    def get_world_map(
        self,
        mutations,
        reference_id,
        seq_tech_list,
        method,
        dates,
        zoom,
        center,
        mode="absolute frequencies",
        nth=0,
    ):
        """
        :param mutations: list of str mutations (from dropdown left menu)
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :param interval: int size time interval (input field left menu)
        :param date: selected date (date slider)
        :return fig: map with mutations per location
        """

        def _circle_size(v, max_val, no_cats=29, basis_size=1):
            if v == 0:
                return 0
            delta = max_val / no_cats
            result = int(v / delta) + basis_size
            return result

        def _add_zero_fo_all_countries(df, countries, column_of_interest):
            """
            param countries: pandas df (country, lat, lon) of all countries in PropertyView
            """
            # add zero values for all countries and selectd mutations, but still no change in point size
            countries["variant.label"] = [mutations] * len(countries)
            countries = countries.explode("variant.label")
            countries[column_of_interest] = 0
            df_all_countries = pd.concat([df, countries]).drop_duplicates(
                subset=["COUNTRY", "variant.label"], keep="first"
            )
            return df_all_countries

        if mode == "absolute frequencies":
            df, column_of_interest = self.get_world_map_df(
                method, mutations, reference_id, seq_tech_list, dates
            )

            # print(tabulate(df, headers='keys', tablefmt='psql'))
            if method == "Frequency":
                max_val = df["number_sequences"].max()
                df["scaled_column"] = df[column_of_interest].apply(
                    lambda x: _circle_size(x, max_val) if x != 0 else 0
                )
                # df['mutations'] = df['mutations'].map(voc_label_dict).fillna(df['mutations'])
                shown_hover_data = {
                    "variant.label": True,
                    column_of_interest: True,
                    "COUNTRY": False,
                    "lat": False,
                    "lon": False,
                    "scaled_column": False,
                }
                fig = self.create_map_fig(
                    df, shown_hover_data, "variant.label", "scaled_column", zoom, center
                )

            elif method == "Increase":
                shown_hover_data = {
                    "variant.label": True,
                    column_of_interest: True,
                    "COUNTRY": False,
                    "lat": False,
                    "lon": False,
                }
                fig = self.create_map_fig(
                    df,
                    shown_hover_data,
                    "variant.label",
                    column_of_interest,
                    zoom,
                    center,
                )

        elif mode == "n-th most frequent mutation":
            # df: location | mutations | number_sequences
            world_map_df, column_of_interest = self.get_world_map_df(
                "Frequency", mutations, reference_id, seq_tech_list, dates
            )
            df = self.get_most_frequent_map_df(world_map_df, column_of_interest, nth)
            shown_hover_data = {
                "variant.label": True,
                column_of_interest: True,
                "COUNTRY": False,
                "lat": False,
                "lon": False,
                "scaled_column": False,
            }
            fig = self.create_map_fig(
                df, shown_hover_data, "variant.label", "scaled_column", zoom, center
            )
        return fig

    def get_params_table(
        self, mutations, method, dates, interval, mode, nth, date_slider, text_dict
    ):
        # date and interval
        if interval is None:
            interval = 0
        # TODO None type in dates
        second_date = DateSlider.unix_to_date(dates[1])
        if (
            DateSlider.get_date_x_days_before(second_date, interval)
            < date_slider.min_date
        ):
            interval = (second_date - date_slider.min_date).days + 1
        # text in info box:
        all_dates = [
            d
            for d in [
                second_date - timedelta(days=x) for x in reversed(range(interval))
            ]
        ]
        sum_selected_var_seq = self.get_number_sequences_per_interval(
            all_dates, mutations
        )
        sum_wildtype_seq = self.get_number_sequences_per_interval(
            all_dates, ["wildtype"]
        )
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        #  mutations = [voc_label_dict[var] if var in voc_label_dict else var for var in mutations]
        # TODO I excluded "common_X" for now in the map, because this leads to underrepresentation/misinterpretation.
        # (Only cases with ALL these mutations are shown)
        mutations = [el for el in mutations if "common" not in str(el)]
        variant_str = ", ".join(mutations)
        table_md = text_dict["param_table"] % (
            variant_str,
            method,
            mode,
            str(second_date),
            str(interval),
        )
        if mode == "n-th most frequent mutation":
            table_md = table_md + text_dict["param_table2"] % (nth)
        table_md = (
            table_md
            + "\n"
            + text_dict["param_table_seq"]
            % (str(sum_selected_var_seq), str(sum_wildtype_seq))
        )
        # text = text_dict["info_text"] % (variant_str, method, str(sum_wildtype_seq), str(sum_selected_var_seq), str(second_date.date()), str(interval))
        return table_md


class DateSlider:
    def __init__(self, dates):
        """
        param dates: propertyView["COLLECTION_DATE"], type 'datetime.date' (YYYY, M, D)
        """
        # TODO min date = 1978, max 2202-07-01
        self.min_date = datetime.datetime.strptime(
            "2022-01-01", "%Y-%m-%d"
        ).date()  # min(dates)
        self.max_date = max(dates)
        self.date_list = [
            self.max_date - timedelta(days=x)
            for x in reversed(range((self.max_date - self.min_date).days + 1))
        ]

    @staticmethod
    def unix_time_millis(dt):
        """Convert datetime to unix timestamp
        :param dt: datetime.date e.g. datetime.date(2021, 3, 7)
        :return: int, e.g. 1615071600"""
        return int(time.mktime(dt.timetuple()))

    @staticmethod
    def unix_to_date(unix):
        """Convert unix timestamp to date
        :param unix: int e.g. 1615071600
        :return: datetime.date, e.g.(2021, 3, 7)"""
        return date.fromtimestamp(unix)

    @staticmethod
    def get_date_x_days_before(date, interval=100):
        return date - timedelta(days=interval)

    @staticmethod
    def get_days_between_date(first_date, second_date):
        return (second_date - first_date).days

    def get_all_dates_in_interval(self, dates, interval):
        second_date = DateSlider.unix_to_date(dates[1])
        if interval is None:
            interval = 0
        if DateSlider.get_date_x_days_before(second_date, interval) < self.min_date:
            interval = (second_date - self.min_date).days + 1
        date_list = [
            d
            for d in [
                second_date - timedelta(days=x) for x in reversed(range(interval))
            ]
        ]
        return date_list

    def get_date_list_by_range(self):
        """
        :return date_list: list of dates,
        """
        date_range = range((self.max_date - self.min_date).days)
        date_list = [self.max_date - timedelta(days=x) for x in date_range]
        return date_list

    def get_marks_date_range(self, n=4):
        """
        :returns n marks for labeling
        """
        marks = {}
        nth = int(len(self.date_list) / n) + 1
        for i, _date in enumerate(self.date_list):
            if i % nth == 0:
                marks[self.unix_time_millis(_date)] = _date.strftime("%Y-%m-%d")
        marks[self.unix_time_millis(self.date_list[-1])] = self.date_list[-1].strftime(
            "%Y-%m-%d"
        )
        return marks
