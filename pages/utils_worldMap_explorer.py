from datetime import date
from datetime import datetime
from datetime import timedelta
import math
import time

import pandas as pd
from plotly import graph_objects as go
import plotly.express as px
from scipy.stats import linregress

from pages.utils_filters import select_propertyView_dfs
from pages.utils_filters import select_variantView_dfs


# table results for filter
class TableFilter(object):
    """
    returns df for table output: sample.name, COLLECTION_DATE, RELEASE_DATE, ISOLATE, LENGTH, SEQ_TECH, COUNTRY,
    GEO_LOCATION, HOST, REFERENCE_ACCESSION, NUC_PROFILE, AA_PROFILE
    for samples matching filter options, all nucleotide and aminoacid variants are returned
    """

    def __init__(self):
        """
        """
        # TODO length column unfilled
        super(TableFilter, self).__init__()
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
            "reference.accession",
        ]

    def _get_filtered_samples(
            self,
            propertyView_dfs,
            variantView_dfs,
            seq_tech_list,
            dates,
            countries,
            mut_value,
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
                        & df["gene:variant"].isin(mut_value)
                        ]["sample.id"]
                )
            )
        return sample_set

    def _merge_variantView_with_propertyView(self, variantView, propertyView):
        return pd.merge(
            variantView, propertyView,
            how="left",
            on=["sample.id", "sample.name"]
        )

    def combine_labels_by_sample(self, df, aa_nt):
        if aa_nt == "cds":
            cols = [
                "reference.id",
                "reference.accession",
                "sample.name",
                "sample.id",
                "gene:variant",
            ]
            df = df[cols]
            df = (
                df.groupby(
                    cols[0:-1],
                    dropna=False,
                    group_keys=True
                )["gene:variant"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index()
                .rename(columns={"gene:variant": "AA_PROFILE"})
            )

        elif aa_nt == "source":
            cols = [
                "reference.id",
                "reference.accession",
                "sample.name",
                "sample.id",
                "variant.label",
            ]
            df = df[cols]
            df = (
                df.groupby(
                    cols[0:-1],
                    dropna=False,
                    group_keys=True
                )["variant.label"]
                .apply(lambda x: ",".join([str(y) for y in set(x)]))
                .reset_index()
                .rename(columns={"variant.label": "NUC_PROFILE"})
            )
        return df

    def get_filtered_table(
            self,
            df_dict,
            complete_partial_radio,
            mutation_list,
            seq_tech_list,
            reference_id,
            dates,
            countries,
    ):
        variantView_dfs_cds = select_variantView_dfs(
            df_dict, complete_partial_radio, reference_id, 'cds'
        )
        variantView_dfs_source = select_variantView_dfs(
            df_dict, complete_partial_radio, reference_id, 'source'
        )
        propertyView_dfs = select_propertyView_dfs(df_dict, complete_partial_radio)
        samples = self._get_filtered_samples(
            propertyView_dfs,
            variantView_dfs_cds,
            seq_tech_list,
            dates,
            countries,
            mutation_list,
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
                      how="inner",
                      on=['sample.id', 'sample.name', 'reference.accession', "reference.id"])

        propertyView_df = pd.concat(propertyView_dfs, ignore_index=True, axis=0)
        df = self._merge_variantView_with_propertyView(df, propertyView_df)
        df = df[self.table_columns]
        if df.empty:
            df = pd.DataFrame(
                [],
                columns=[self.table_columns]
            )
        df = df.rename(columns={'reference.accession': "REFERENCE_ACCESSION"})
        return df


class DfsAndDetailPlot(object):
    def __init__(self, world_dfs, color_dict, location_coordinates):
        super(DfsAndDetailPlot, self).__init__()
        dates = sorted(
            list(
                {i for s in [set(df["COLLECTION_DATE"]) for df in world_dfs] for i in s}
            )
        )
        # self.min_date = dates[0]
        self.min_date = datetime.strptime("2022-01-01", "%Y-%m-%d").date()
        self.max_date = dates[-1]
        self.world_dfs = world_dfs
        self.color_dict = color_dict
        self.df_location = location_coordinates[
            ["name", "ISO_Code", "lat", "lon"]
        ].rename(columns={"name": "COUNTRY"})

    def get_number_sequences_per_interval(self, df, dates, mutations, location_ID=None):
        """
        param df: df_all_dates_all_voc
        param dates: [date(2021, 12, 12), date(2021, 12, 13), ...]
        """
        df = df[
            df["COLLECTION_DATE"].isin(dates)
            & df["variant.label"].isin(mutations)
            ]
        if location_ID:
            df = df[df.location_ID == location_ID]
        seq_set = set(",".join(list(df["sample_id_list"])).split(","))
        if "0" in seq_set:
            return len(seq_set) - 1
        else:
            return len(seq_set)

    def get_nb_filtered_seq(self, seq_tech_list, dates, countries, genes, mutations):
        samples_1 = set()
        samples_2 = set()
        for world_df in self.world_dfs:
            df = world_df[
                    world_df["COLLECTION_DATE"].isin(dates)
                    & world_df["SEQ_TECH"].isin(seq_tech_list)
                    & world_df["COUNTRY"].isin(countries)
                    & world_df["element.symbol"].isin(genes)
                    ].copy()
            df.sample_id_list = df.sample_id_list.map(lambda x: x.split(','))
            df2 = df[df['gene:variant'].isin(mutations)]

            for sample_list in df['sample_id_list'].tolist():
                samples_1.update(sample_list)
            for sample_list in df2['sample_id_list'].tolist():
                samples_2.update(sample_list)
        return len(samples_1), len(samples_2)

    def filter_df(self, df, mutations, seq_tech_list, dates, countries):
        df = df[
            df["COLLECTION_DATE"].isin(dates)
            & df["SEQ_TECH"].isin(seq_tech_list)
            & df["gene:variant"].isin(mutations)
            & df["COUNTRY"].isin(countries)
            ]
        return df

    def get_df_for_frequency_bar(self, filtered_dfs):
        dfs = [
            (
                filtered_df[
                    [
                        "COUNTRY",
                        "COLLECTION_DATE",
                        "variant.label",
                        "SEQ_TECH",
                        "number_sequences",
                        "element.symbol",
                    ]
                ]
                .groupby(["COUNTRY", "variant.label", "element.symbol"])
                .sum(numeric_only=True)
                .reset_index()
            )
            for filtered_df in filtered_dfs
        ]
        df = pd.concat(dfs, ignore_index=True, axis=0)
        return df

    def add_slope_column(self, df):
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

    def get_increase_df(self, filtered_dfs):
        """
        shows change in frequency of the different virus mutations, calculate lin regression with scipy.stats module and
        returns the slope of the regression line (x:range (interval)), y:number of sequences per day in selected interval
        for choropleth map select slope with greatest increase
        """
        df = pd.concat(filtered_dfs, ignore_index=True, axis=0)
        df = (
            df.groupby(
                ["COUNTRY", "variant.label", "element.symbol", "COLLECTION_DATE"]
            )
            .sum(numeric_only=True)
            .reset_index()
        )
        df = (
            df.groupby(["COUNTRY", "variant.label", "element.symbol"])
            .agg(
                {
                    "number_sequences": lambda x: list(x),
                    "COLLECTION_DATE": lambda x: list(x),
                }
            )
            .reset_index()
        )
        df = self.add_slope_column(df)
        return df

    def get_df_for_scatter_plot(self, filtered_dfs):
        df = pd.concat(filtered_dfs, ignore_index=True, axis=0)
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
                        0:: math.ceil(len(unique_date_numbers) / 6)
                        ]
        ticktext_date = unique_dates[0:: math.ceil(len(unique_dates) / 6)]
        return tickvals_date, ticktext_date

    def create_frequency_plot(self, df):
        """
        param df: COUNTRY variant.label element.symbol  number_sequences
        """
        fig = go.Figure()
        for gene in df["element.symbol"].unique():
            df_g = df[df["element.symbol"] == gene]
            fig.add_trace(
                go.Bar(
                    x=[df_g["element.symbol"], df_g["variant.label"]],
                    y=df_g["number_sequences"],
                    marker_color=self.color_dict[gene],
                ),
            )
        #              hover_name="variant.label",
        #              hover_data={'variant.label': True, "number_sequences": True},
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            margin={"l": 20, "b": 30, "r": 10, "t": 10},
            xaxis_title="selected variants",
            title_x=0.5,
            height=300,
        )
        return fig

    # plot methods
    def get_frequency_bar_chart(
            self, mutations, seqtech_list, dates, location_name
    ):
        """
        :return fig bar chart showing mutation information of last hovered plz
        """
        if location_name:
            filtered_dfs = [
                self.filter_df(
                    world_df, mutations, seqtech_list, dates, [location_name]
                )
                for world_df in self.world_dfs
            ]
            df = self.get_df_for_frequency_bar(filtered_dfs)
            df = self.drop_rows_by_value(df, 0, "number_sequences")
        else:
            df = pd.DataFrame()
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
        fig = go.Figure()
        for gene in df["element.symbol"].unique():
            df_g = df[df["element.symbol"] == gene]
            fig.add_trace(
                go.Bar(
                    x=[df_g["element.symbol"], df_g["variant.label"]],
                    y=df_g["slope"],
                    marker_color=self.color_dict[gene],
                ),
            )
        fig.update_layout(
            showlegend=False,
            xaxis_tickangle=-45,
            margin={"l": 20, "b": 30, "r": 10, "t": 10},
            xaxis_title="selected variants",
            title_x=0.5,
            height=300,
        )
        return fig

    def get_slope_bar_plot(self, dates, mutations, seqtech_list, location_name):
        if location_name:
            filtered_dfs = [
                self.filter_df(
                    world_df, mutations, seqtech_list, dates, [location_name]
                )
                for world_df in self.world_dfs
            ]
            df = self.get_increase_df(filtered_dfs)
        else:
            df = pd.DataFrame()
        if df.empty:
            df = pd.DataFrame(
                [[0, "", 0, "no_mutation", "no_gene"]],
                columns=[
                    "number_sequences",
                    "COLLECTION_DATE",
                    "slope",
                    "variant.label",
                    "element.symbol",
                ],
            )
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
            seqtech_list,
            dates,
            location_name,
            axis_type="lin",
    ):
        # TODO: same lines on top of each other have color of latest MOC -> change to mixed color
        if location_name:
            filtered_dfs = [
                self.filter_df(
                    world_df, mutations, seqtech_list, dates, [location_name]
                )
                for world_df in self.world_dfs
            ]
            if len(dates) == 0:
                dates = [
                    dat
                    for dat in [
                        self.max_date - timedelta(days=x) for x in reversed(range(28))
                    ]
                ]
            df = self.get_df_for_scatter_plot(filtered_dfs)
            # remove rows if VOC no seq in time-interval
            for var in mutations:
                if df[df["variant.label"] == var]["number_sequences"].sum() == 0:
                    df = df[df["variant.label"] != var]
        # dummy dataframe for showing empty results
        else:
            df = pd.DataFrame()
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
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type,
        # unclear why this is working
        try:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        except ValueError:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        return fig


class WorldMap(DfsAndDetailPlot):
    def __init__(self, world_dfs, color_dict, location_coordinates):
        """
        creates df for maps and map figures
        param world_dfs: list of dfs, [partial_df] OR  [partial AND complete df]
                df.columns = COUNTRY,COLLECTION_DATE,SEQ_TECH,sample_id_list,variant.label,number_sequences,element.symbol,gene:variant
                column types: str, str, datetime.date, str, str, str, int, str, str
                sample_id_list: comma seperated sample ids e.g. "3,45,67" or "3"
        """
        super(WorldMap, self).__init__(world_dfs, color_dict, location_coordinates)

    def get_world_map_df(
            self, method, mutations, seq_tech_list, dates, countries
    ):
        """
        :param method: 'Frequency' or 'Increase'
        :param mutations: list of selected voc mutations gene:mut
        :param seq_tech_list: list of selected sequencing technologies
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :param dates: all selected dates in interval (date slider)
        :param countries: list of selected countries
        return frequency OR increase  df: frequency_df.columns = COUNTRY,number_sequences,ISO_Code
                                         increase_df.columns = COUNTRY,slope,ISO_Code

        """
        if countries is None:
            countries = []
        filtered_dfs = [
            self.filter_df(
                world_df, mutations, seq_tech_list, dates, countries
            )
            for world_df in self.world_dfs
        ]

        if method == "Frequency":
            df = pd.concat(filtered_dfs, ignore_index=True, axis=0)
            countries = []
            number_sequences = []
            for name, group in df.groupby("COUNTRY"):
                sample_set = {
                    item
                    for sublist in [
                        sample.split(',') for sample in group["sample_id_list"].unique()
                    ]
                    for item in sublist
                }
                countries.append(name)
                number_sequences.append(len(sample_set))
            df = pd.DataFrame(
                list(zip(countries, number_sequences)),
                columns=['COUNTRY', 'number_sequences']
            )
            column_of_interest = "number_sequences"
        elif method == "Increase":
            df = self.get_increase_df(filtered_dfs)
            # select max slope for each country, remove zero first to get negative slopes too
            df = df.sort_values("slope", ascending=False).drop_duplicates(["COUNTRY"])
            column_of_interest = "slope"

        # df = self.drop_rows_by_value(df, 0, column_of_interest)
        if df.empty:
            df = pd.DataFrame(
                data=[["", 0]],
                columns=[
                    "COUNTRY",
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
        )
        return fig

    def create_map_fig(
            self, df, shown_hover_data, color_column, size_column, z=2, cen=None
    ):
        """
        param df:  COUNTRY  | variant.label   |   number_sequences | lat |  lon |   scaled_column
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
            mapbox_style="carto-positron",
        )
        return fig

    def get_world_map(self, mutations, seq_tech_list, method, dates, countries):
        """
        :param mutations: list of str mutations (from dropdown left menu) gene:mut
        :param seq_tech_list: list of selected sequencing technologies
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :param dates: all selected dates in interval (date slider)
        :param countries: list of selected countries
        :return fig:
            frequency method: choropleth map with number of sequences with selected properties per country
            increase method: choropleth map showing decrease/increase of mutation with strongest increase in selected interval
                            (zero values = one time point are excluded)
        """
        df, column_of_interest = self.get_world_map_df(
            method, mutations, seq_tech_list, dates, countries
        )
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


class DateSlider:
    def __init__(self, dates):
        """
        param dates: propertyView["COLLECTION_DATE"], type 'datetime.date' (YYYY, M, D)
        """
        # TODO min date = 1978, max 2202-07-01
        self.min_date = datetime.strptime("2022-01-01", "%Y-%m-%d").date()  # min(dates)
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

    @staticmethod
    def get_all_dates(first_date, second_date):
        days = DateSlider.get_days_between_date(first_date, second_date)
        date_list = [
            d for d in [second_date - timedelta(days=x) for x in reversed(range(days))]
        ]
        return date_list

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
