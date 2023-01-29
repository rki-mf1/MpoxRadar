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
    for samples matching filter opitons, all nucleotide and aminoacid variants are returned
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

    def _get_filtered_samples(
        self, mutation_list, seq_tech_list, reference_id, dates, gene_list, countries
    ):
        samples = self.table_df[
            self.table_df["COLLECTION_DATE"].isin(dates)
            & self.table_df["variant.label"].isin(mutation_list)
            & (self.table_df["reference.id"] == reference_id)
            & self.table_df["SEQ_TECH"].isin(seq_tech_list)
            & self.table_df["COUNTRY"].isin(countries)
        ]["sample.id"]
        return samples.tolist()

    # TODO no filtering for mutations/genes possible
    def get_filtered_table(
        self,
        mutation_list=None,
        seq_tech_list=None,
        reference_id=2,
        dates=None,
        gene_list=None,
        countries=None,
    ):

        if mutation_list is None:
            mutation_list = []
        if seq_tech_list is None:
            seq_tech_list = []
        if dates is None:
            dates = []
        if gene_list is None:
            gene_list = []
        if countries is None:
            countries = []

        samples = self._get_filtered_samples(
            mutation_list, seq_tech_list, reference_id, dates, gene_list, countries
        )
        df = self.table_df[self.table_df["sample.id"].isin(samples)]
        if not df.empty:
            df = (
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
                        "reference.id",
                        "element.type",
                    ],
                    dropna=False,
                )["variant.label"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index(name="labels")
            )
            c = [
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
            ]
            df = df.set_index(["element.type"] + c).unstack("element.type")
            df = df.labels.rename_axis([None], axis=1).reset_index()
            df = df.rename(columns={"cds": "AA_PROFILE", "source": "NUC_PROFILE"})
            df = df[
                [
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
                    "NUC_PROFILE",
                    "AA_PROFILE",
                ]
            ]
        else:
            df = pd.DataFrame(
                [],
                columns=[
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
                    "NUC_PROFILE",
                    "AA_PROFILE",
                ],
            )
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

        dates = propertyView["COLLECTION_DATE"]
        self.min_date = min(dates)
        self.max_date = max(dates)
        self.df_location = location_coordinates[
            ["name", "ISO_Code", "lat", "lon"]
        ].rename(columns={"name": "COUNTRY"})
        self.df_all_dates_all_voc = self._get_full_df(propertyView, variantView)
        self.color_dict = self.get_color_dict(variantView)
        # print(tabulate(self.df_all_dates_all_voc[0:10], headers='keys', tablefmt='psql'))

    def _get_full_df(self, propertyView, variantView):
        """
        return df_all_dates_all_voc: COUNTRY | COLLECTION_DATE | reference.id | SEQ_TECH | sample_id_list |
         variant.label | number_sequences
        """
        # 1. join metadata
        df = variantView[variantView["element.type"] == "cds"].reset_index(drop=True)
        df_all_dates_all_voc = pd.merge(
            df[["sample.id", "variant.label", "reference.id", "element.symbol"]],
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
                "element.symbol",
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
                    "element.symbol",
                ],
                dropna=False,
            )["sample.id"]
            .apply(lambda x: ",".join([str(y) for y in set(x)]))
            .reset_index(name="sample_id_list")
        )
        # 5. add sequence count
        df_all_dates_all_voc["number_sequences"] = df_all_dates_all_voc[
            "sample_id_list"
        ].apply(lambda x: len(x.split(",")))

        # TODO do I need this? Working without so far but in detail plots lines e.g. sart at a later date
        # 6. fill with 0 no mutation
        # full_df_without_nb_seq = df_all_dates_all_voc[["COUNTRY", "COLLECTION_DATE", 'reference.id', "SEQ_TECH"]].drop_duplicates()
        # full_df_without_nb_seq["number_sequences"] = 0
        # full_df_without_nb_seq = full_df_without_nb_seq.merge(pd.DataFrame(self.mutations, columns=["variant.label"]), how='cross')
        # combine real seq counts (per voc per date per location) with zero values
        # df_all_dates_all_voc = pd.concat([df_all_dates_all_voc, full_df_without_nb_seq]) \
        #     .drop_duplicates(subset=["COUNTRY", "COLLECTION_DATE", 'reference.id', "SEQ_TECH", "variant.label"], keep="first") \
        #     .reset_index(drop=True)
        # df_all_dates_all_voc = df_all_dates_all_voc[["COUNTRY", "COLLECTION_DATE", 'reference.id', "SEQ_TECH", 'sample_id_list',
        #                                              "variant.label", 'number_sequences']]
        # df_all_dates_all_voc = df_all_dates_all_voc.astype({'sample_id_list': 'str'})

        # remove once appearing variants
        df_all_dates_all_voc = self._remove_x_appearing_variants(
            df_all_dates_all_voc, nb=1
        )

        return df_all_dates_all_voc[
            [
                "COUNTRY",
                "COLLECTION_DATE",
                "reference.id",
                "SEQ_TECH",
                "sample_id_list",
                "variant.label",
                "number_sequences",
                "element.symbol",
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

    def get_color_dict(self, variantView):
        """
        defined color by mutation
        color scheme contains 24 different colors, if #mutations>24 use second color scheme with 24 colors
        more mutations --> color schema starts again (max 48 different colors)
        wildtype= green, no_mutation (no sequence meets the user selected mutations, dates, location) = grey
        """
        color_dict = {}
        color_schemes = [
            px.colors.qualitative.Light24[1:],
            px.colors.qualitative.Dark24[1:],
        ]
        for ref, group_df in variantView.groupby("reference.id"):
            for i, (gene, gene_df) in enumerate(group_df.groupby("element.symbol")):
                j = i % 46
                if j < 23:
                    color_dict[gene] = color_schemes[0][j]
                elif 22 < j < 46:
                    color_dict[gene] = color_schemes[1][j - 23]
        color_dict["no_gene"] = "grey"
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

    def _remove_x_appearing_variants(self, df, nb=1):
        df2 = df.groupby(["variant.label", "reference.id"]).sum().reset_index()
        variants_to_remove = df2[df2["number_sequences"] <= nb][
            "variant.label"
        ].tolist()
        if variants_to_remove:
            df = df[~df["variant.label"].isin(variants_to_remove)]
        return df

    def get_df_for_frequency_bar(
        self, mutations, dates, reference_id, seqtech_list, genes, location_name
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
                    "element.symbol",
                ]
            ][
                self.df_all_dates_all_voc["COUNTRY"].isin([location_name])
                & self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seqtech_list)
                & self.df_all_dates_all_voc["element.symbol"].isin(genes)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
            ]
            .groupby(["COUNTRY", "variant.label", "element.symbol"])
            .sum()
            .reset_index()
        )
        return df

    def add_slope_column(self, df):
        df.reset_index(inplace=True)
        slopes = []
        for i in range(len(df["number_sequences"])):
            dates = [(date - self.min_date).days for date in df["COLLECTION_DATE"][i]]
            nu = df["number_sequences"][i]
            if len(set(nu)) == 1:
                slopes.append(0)
            else:
                slopes.append(linregress(dates, nu).slope)
        df["slope"] = slopes
        df = df.astype({"slope": float})
        return df

    def get_increase_df_for_map(
        self, dates, mutations, reference_id, seq_tech_list, countries, genes
    ):
        """
        shows change in frequency of the different virus mutations, calculate lin regression with scipy.stats module and
        returns the slope of the regression line (x:range (interval)), y:number of sequences per day in selected interval
        """
        # df:     location_ID | date | mutations | number_sequences
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        df = (
            self.df_all_dates_all_voc[
                self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                & self.df_all_dates_all_voc["COUNTRY"].isin(countries)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
                & self.df_all_dates_all_voc["element.symbol"].isin(genes)
            ]
            .groupby(["COUNTRY", "COLLECTION_DATE"])
            .sum()
            .reset_index()
        )
        df = df.groupby(["COUNTRY"]).agg(
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
            df = self.add_slope_column(df)
        return df

    def get_increase_df_for_plot(
        self, dates, mutations, reference_id, seq_tech_list, genes, location_name
    ):
        """
        shows change in frequency of the different virus mutations, calculate lin regression with scipy.stats module and
        returns the slope of the regression line (x:range (interval)), y:number of sequences per day in selected interval
        :param location_name: str country name
        """
        # df:     location_ID | date | mutations | number_sequences
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        df = (
            self.df_all_dates_all_voc[
                self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                & self.df_all_dates_all_voc["element.symbol"].isin(genes)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
                & (self.df_all_dates_all_voc["COUNTRY"] == location_name)
            ]
            .groupby(["COUNTRY", "variant.label", "element.symbol", "COLLECTION_DATE"])
            .sum()
            .reset_index()
        )
        df = df.groupby(["COUNTRY", "variant.label", "element.symbol"]).agg(
            {
                "number_sequences": lambda x: list(x),
                "COLLECTION_DATE": lambda x: list(x),
            }
        )
        if df.empty:
            df = pd.DataFrame(
                [],
                columns=[
                    "number_sequences",
                    "variant.label",
                    "element.symbol",
                    "COLLECTION_DATE",
                    "slope",
                ],
            )
        else:
            df = self.add_slope_column(df)
        return df

    def get_df_for_scatter_plot(
        self, mutations, dates, reference_id, seqtech_list, location_name, genes
    ):
        mutations = [var[1:-1] if "`" in var else var for var in mutations]
        df = self.df_all_dates_all_voc[
            (self.df_all_dates_all_voc["COUNTRY"] == location_name)
            & self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
            & self.df_all_dates_all_voc["variant.label"].isin(mutations)
            & self.df_all_dates_all_voc["SEQ_TECH"].isin(seqtech_list)
            & self.df_all_dates_all_voc["element.symbol"].isin(genes)
            & (self.df_all_dates_all_voc["reference.id"] == reference_id)
        ].reset_index(drop=True)
        return df[
            [
                "COUNTRY",
                "COLLECTION_DATE",
                "variant.label",
                "number_sequences",
                "element.symbol",
            ]
        ]

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
            color="element.symbol",
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
        self, mutations, reference_id, seqtech_list, dates, location_name, genes
    ):
        """
        :return fig bar chart showing mutation information of last hovered plz
        """
        df = self.get_df_for_frequency_bar(
            mutations,
            dates,
            reference_id,
            seqtech_list,
            genes,
            location_name=location_name,
        )
        df = self.drop_rows_by_value(df, 0, "number_sequences")
        if df.empty:
            df = pd.DataFrame(
                data=[["no_mutation", "no_gene", 0]],
                columns=["variant.label", "element.symbol", "number_sequences"],
            )
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type,
        # unclear why this is working
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
            color="element.symbol",
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
        self, dates, mutations, reference_id, seqtech_list, location_name, genes
    ):
        df = self.get_increase_df_for_plot(
            dates, mutations, reference_id, seqtech_list, genes, location_name
        )
        df = self.drop_rows_by_value(df, 0, "slope")
        if df.empty:
            columns = [
                "number_sequences",
                "COLLECTION_DATE",
                "slope",
                "variant.label",
                "element.symbol",
            ]
            row = [[0, "", 0, "no_mutation", "no_gene"]]
            df = pd.concat([df, pd.DataFrame(row, columns=columns)])
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type,
        # unclear why this is working
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
            color="element.symbol",
            trendline="ols",
            symbol="variant.label",
            color_discrete_map=self.color_dict,
            labels={
                "date_numbers": "COLLECTION_DATE",
                "number_sequences": "# sequences",
            },
            height=300,
            hover_data={
                "COLLECTION_DATE": True,
                "number_sequences": True,
                "variant.label": True,
                "COUNTRY": False,
                "element.symbol": True,
                "date_numbers": False,
            },
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
            legend_title_text="Gene, Mutation",
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
        genes,
        axis_type="lin",
    ):
        # TODO: same lines on top of each other have color of latest MOC -> change to mixed color
        if len(dates) == 0:
            dates = [
                dat
                for dat in [
                    self.max_date - timedelta(days=x) for x in reversed(range(28))
                ]
            ]

        df = self.get_df_for_scatter_plot(
            mutations, dates, reference_id, seqtech_list, location_name, genes
        )
        # remove rows if VOC no seq in time-interval
        for var in mutations:
            if df[df["variant.label"] == var]["number_sequences"].sum() == 0:
                df = df[df["variant.label"] != var]
        # df['variant.label'] = df['variant.label'].map(voc_label_dict).fillna(df['variant.label'])
        # dummy dataframe for showing empty results
        if df.empty:
            df = pd.DataFrame(
                data=[[location_name, dates[-1], "no_mutations", 0, "no_gene"]],
                columns=[
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "variant.label",
                    "number_sequences",
                    "element.symbol",
                ],
            )
        # date_numbers: assign date to number, numbers needed for calculation of trendline
        date_numbers = [(d - self.min_date).days for d in df["COLLECTION_DATE"]]
        df["date_numbers"] = date_numbers

        tickvals_date, ticktext_date = self.calculate_ticks_from_dates(
            dates, date_numbers
        )
        print(tickvals_date, ticktext_date)
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type,
        # unclear why this is working
        try:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        except ValueError:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        return fig


class WorldMap(DfsAndDetailPlot):
    def __init__(self, propertyView, variantView, location_coordinates):
        """
        creates df for maps and map figures

        """
        super(WorldMap, self).__init__(propertyView, variantView, location_coordinates)

    def get_world_map_df(
        self, method, mutations, reference_id, seq_tech_list, dates, countries, genes
    ):
        """
        :param method: 'Frequency' or 'Increase'
        :param mutations: list of selected voc mutations
        :param reference_id: int
        :param seq_tech_list: list of selected sequencing technologies
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :param dates: all selected dates in interval (date slider)
        :param countries: list of selected countries
        """
        if countries is None:
            countries = []
        if method == "Frequency":
            #  df:     location_ID   mutations  number_sequences
            # TODO exist ' in mpx too?
            mutations = [var[1:-1] if "`" in var else var for var in mutations]
            df = self.df_all_dates_all_voc[
                self.df_all_dates_all_voc["COLLECTION_DATE"].isin(dates)
                & self.df_all_dates_all_voc["SEQ_TECH"].isin(seq_tech_list)
                & self.df_all_dates_all_voc["variant.label"].isin(mutations)
                & (self.df_all_dates_all_voc["reference.id"] == reference_id)
                & self.df_all_dates_all_voc["COUNTRY"].isin(countries)
                & self.df_all_dates_all_voc["element.symbol"].isin(genes)
            ]
            df = df.groupby(["COUNTRY", "reference.id"]).sum().reset_index()
            column_of_interest = "number_sequences"
        elif method == "Increase":
            #  df: date | mutations | number_sequences
            df = self.get_increase_df_for_map(
                dates, mutations, reference_id, seq_tech_list, countries, genes
            )
            # replace negative slope by 0 (cannot be shown)
            df["slope"] = df["slope"].fillna(0)
            num = df._get_numeric_data()
            num[num < 0] = 0
            column_of_interest = "slope"

        df = self.drop_rows_by_value(df, 0, column_of_interest)
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
            ["COUNTRY", column_of_interest, "ISO_Code"]
        ]
        return df, column_of_interest

    def create_choropleth_map(self, df, shown_hover_data, color_column):
        fig = px.choropleth(
            df,
            locations="ISO_Code",
            color=color_column,
            color_continuous_scale=px.colors.sequential.Plasma,
            hover_name="COUNTRY",
            hover_data=shown_hover_data,
            labels={el: el.replace(".", " ").title() for el in df.columns},
        )
        fig.update_layout(
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            legend=dict(yanchor="top", y=0.99, xanchor="left", x=0.01),
            # mapbox_style="open-street-map", #carto-positron
        )
        return fig

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
            # mapbox_style="open-street-map", #carto-positron
        )
        return fig

    def get_world_map(
        self, mutations, reference_id, seq_tech_list, method, dates, countries, genes
    ):
        """
        :param mutations: list of str mutations (from dropdown left menu)
        :param reference_id: int
        :param seq_tech_list: list of selected sequencing technologies
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :param dates: all selected dates in interval (date slider)
        :param countries: list of selected countries
        :return fig: map with mutations per location
        """
        df, column_of_interest = self.get_world_map_df(
            method, mutations, reference_id, seq_tech_list, dates, countries, genes
        )
        # print(tabulate(df, headers='keys', tablefmt='psql'))
        if method == "Frequency":
            shown_hover_data = {
                column_of_interest: True,
                "COUNTRY": False,
                "ISO_Code": False,
            }
            fig = self.create_choropleth_map(df, shown_hover_data, column_of_interest)
        elif method == "Increase":
            shown_hover_data = {
                column_of_interest: True,
                "COUNTRY": False,
                "ISO_Code": False,
            }
            fig = self.create_choropleth_map(df, shown_hover_data, column_of_interest)
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
