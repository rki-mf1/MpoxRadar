import math
import time
import pandas as pd
from datetime import date
from datetime import datetime
from datetime import timedelta
from plotly import graph_objects as go
import plotly.express as px
from scipy.stats import linregress


class VariantMapAndPlots(object):
    """
        world_dfs df.columns:
         COUNTRY,COLLECTION_DATE,SEQ_TECH,sample_id_list,variant.label,number_sequences,element.symbol,gene:variant
        column types: str, str, datetime.date, str, str, str, int, str, str
        column sample_id_list: comma seperated sample ids e.g. "3,45,67" or "3"
        :param countries: list of selected countries
        :param mutations: list of selected mutations gene:mut
        :param seq_techs: list of selected sequencing technologies
        :param dates: [start_date, end_dat] by Dateslider
        :param interval:
        :param color_dict: {variant:color}
        :param plot_type: 'map', OR 'detail'
        :param location_coordinates: dict
        :param genes: list of selected genes, only relevant for calculate nb filtered sequences
        :param countries: list of selected countries
    """

    def __init__(self,
                 df_dict,
                 date_slider,
                 reference_id,
                 complete_partial_radio,
                 countries,
                 seq_techs,
                 mutations,
                 dates,
                 interval,
                 color_dict,
                 plot_type,
                 location_coordinates,
                 genes=None,  # only detail plots
                 clicked_country=None  # only detail plots
                 ):
        super(VariantMapAndPlots, self).__init__()

        self.world_dfs = [df_dict["world_map"]['complete'][reference_id]]
        if complete_partial_radio == 'partial':
            self.world_dfs.append(df_dict["world_map"]['partial'][reference_id])
        self.countries = countries
        self.mutations = mutations
        self.seq_techs = seq_techs
        self.min_date = date_slider.min_date
        self.dates = self.define_interval_dates(date_slider, dates, interval)
        self.color_dict = color_dict
        self.df_location = location_coordinates[
            ["name", "ISO_Code", "lat", "lon"]
        ].rename(columns={"name": "COUNTRY"})
        if plot_type == "map":
            countries_for_filter = self.countries
            if genes or clicked_country:
                raise ValueError("Instance is not correct initialized, map plotting does not require gene and click country information")
        elif plot_type == "detail":
            self.location_name, \
            self.number_selected_sequences, \
            self.seq_with_mut = self.select_country_for_detail_plots_and_nb_filtered_seq(clicked_country, genes)
            countries_for_filter = [self.location_name] if self.location_name else []

        self.filtered_dfs = [
            self.filter_df(
                world_df, countries_for_filter
            )
            for world_df in self.world_dfs
        ]

    def define_interval_dates(self, date_slider, dates, interval):
        dates = date_slider.get_all_dates_in_interval(dates, interval)
        if len(dates) == 0:
            dates_in_world_df = sorted(
                list(
                    {i for s in [set(df["COLLECTION_DATE"]) for df in self.world_dfs] for i in s}
                )
            )
            dates = [
                dat
                for dat in [
                    dates_in_world_df[-1] - timedelta(days=x) for x in reversed(range(28))
                ]
            ]
        return dates

    def select_country_for_detail_plots_and_nb_filtered_seq(
            self,
            clicked_country,
            genes,
    ):
        """
        param clicked_country: user clicked country OR ""
        define country to show detail plots
        order country selection: 1. user click data, 2. country with most seq in filter without date filtering
        3. if country of old click selection not in updated filters --> take first country of country dropdown values
        4. if no seq for country --> select one from country values (e.g. USA #1 in list, no clicks, but no seq in
        interval days)
        """
        location_name = clicked_country
        number_selected_sequences = 0
        seq_with_mut = 0
        if self.countries:
            if not clicked_country:
                location_name = self.countries[0]
            if clicked_country and clicked_country not in self.countries:
                location_name = self.countries[0]

            countries_to_check_for_seq = [location_name] + [country for country in self.countries if country != location_name]
        else:
            countries_to_check_for_seq = [location_name]

        for country in countries_to_check_for_seq:
            number_selected_sequences, seq_with_mut = self.get_nb_filtered_seq(
                [country],
                genes,
            )
            if number_selected_sequences > 0:
                location_name, country_name = country, country
                break

        return location_name, number_selected_sequences, seq_with_mut

    def get_nb_filtered_seq(self, countries, genes):
        samples_1 = set()
        samples_2 = set()
        for world_df in self.world_dfs:
            df = world_df[
                world_df["COLLECTION_DATE"].isin(self.dates)
                & world_df["SEQ_TECH"].isin(self.seq_techs)
                & world_df["COUNTRY"].isin(countries)
                & world_df["element.symbol"].isin(genes)
                ].copy()
            df.sample_id_list = df.sample_id_list.map(lambda x: x.split(','))
            df2 = df[df['gene:variant'].isin(self.mutations)]

            for sample_list in df['sample_id_list'].tolist():
                samples_1.update(sample_list)
            for sample_list in df2['sample_id_list'].tolist():
                samples_2.update(sample_list)
        return len(samples_1), len(samples_2)

    def filter_df(self, world_df, countries):
        if countries:
            df = world_df[
                world_df["COLLECTION_DATE"].isin(self.dates)
                & world_df["SEQ_TECH"].isin(self.seq_techs)
                & world_df["gene:variant"].isin(self.mutations)
                & world_df["COUNTRY"].isin(countries)
                ]
        else:
            df = pd.DataFrame(columns=world_df.columns)
        df = df.astype({'number_sequences': 'int32'})
        return df

    def get_df_for_frequency_bar(self):
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
            for filtered_df in self.filtered_dfs
        ]
        df = pd.concat(dfs, ignore_index=True, axis=0)
        df = df.groupby(["COUNTRY", "variant.label", "element.symbol"])\
            .sum(numeric_only=True)\
            .reset_index()
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

    def get_increase_df(self):
        """
        shows change in frequency of the different virus mutations, calculate lin regression with scipy.stats module and
        returns the slope of the regression line (x:range (interval)), y:number of sequences per day in selected interval
        for choropleth map select slope with greatest increase
        """
        df = pd.concat(self.filtered_dfs, ignore_index=True, axis=0).reset_index(drop=True)
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

    def concat_filtered_dfs(self):
        df = pd.concat(self.filtered_dfs, ignore_index=True, axis=0)
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
    def get_frequency_bar_chart(self):
        """
        :return fig bar chart showing mutation information of last hovered plz
        """
        if self.location_name:
            df = self.get_df_for_frequency_bar()
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

    def create_slope_bar_plot(self):
        if self.location_name:
            df = self.get_increase_df()
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

    def get_scatter_df(self):
        if self.location_name:
            df = self.concat_filtered_dfs()
            df = df.groupby(["COUNTRY", 'COLLECTION_DATE', "variant.label", "element.symbol"]) \
                .sum(numeric_only=True) \
                .reset_index()
            # remove rows if VOC no seq in time-interval
            for var in self.mutations:
                if df[df["variant.label"] == var]["number_sequences"].sum() == 0:
                    df = df[df["variant.label"] != var]
        # dummy dataframe for showing empty results
        else:
            df = pd.DataFrame()
        if df.empty:
            df = pd.DataFrame(
                data=[[self.location_name, self.dates[-1], "no_mutations", "no_gene", 0]],
                columns=[
                    "COUNTRY",
                    "COLLECTION_DATE",
                    "variant.label",
                    "element.symbol",
                    "number_sequences",
                ],
            )
        # date_numbers: assign date to number, numbers needed for calculation of trendline
        date_numbers = [(d - self.min_date).days for d in df["COLLECTION_DATE"]]
        df["date_numbers"] = date_numbers
        return df

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

    def get_frequency_development_scatter_plot(self, axis_type="lin"):
        # TODO: same lines on top of each other have color of latest MOC -> change to mixed color
        df = self.get_scatter_df()

        tickvals_date, ticktext_date = self.calculate_ticks_from_dates(
            self.dates, df["date_numbers"]
        )
        # this try/except block is a hack that catches randomly appearing errors of data with wrong type,
        # unclear why this is working
        try:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        except ValueError:
            fig = self.create_scatter_plot(df, tickvals_date, ticktext_date, axis_type)
        return fig

    def get_nb_seq_per_country_df(self):
        concatenated_filtered_df = pd.concat(self.filtered_dfs, ignore_index=True, axis=0)
        countries = []
        number_sequences = []
        for name, group in concatenated_filtered_df.groupby("COUNTRY"):
            sample_set = {
                item
                for sublist in [
                    sample.split(',') for sample in group["sample_id_list"].unique()
                ]
                for item in sublist
            }
            countries.append(name)
            number_sequences.append(len(sample_set))
        return pd.DataFrame(
            list(zip(countries, number_sequences)),
            columns=['COUNTRY', 'number_sequences']
        )

    def get_world_map_df(self, method):
        """
        :param method: 'Frequency' or 'Increase'
        return frequency OR increase  df: frequency_df.columns = COUNTRY,number_sequences,ISO_Code
                                         increase_df.columns = COUNTRY,slope,ISO_Code

        """
        if method == "Frequency" and self.filtered_dfs:
            map_df = self.get_nb_seq_per_country_df()
            column_of_interest = "number_sequences"
        elif method == "Increase":
            map_df = self.get_increase_df()
            # select max slope for each country, remove zero first to get negative slopes too
            map_df = map_df.sort_values("slope", ascending=False).drop_duplicates(["COUNTRY"])
            column_of_interest = "slope"

        # df = self.drop_rows_by_value(df, 0, column_of_interest)
        map_location_df = pd.merge(map_df, self.df_location, on="COUNTRY")[
            ["COUNTRY", column_of_interest, "ISO_Code"]
        ]
        return map_location_df, column_of_interest

    def create_choropleth_map(self, df, shown_hover_data, color_column):
        fig = px.choropleth(
            df,
            locations="ISO_Code",
            color=color_column,
            color_continuous_scale=px.colors.sequential.Plasma,
            hover_name="COUNTRY",
            hover_data=shown_hover_data,
            labels={
                el: (
                    el.replace(".", " ").title() if el != "number_sequences" else "number of sequences"
                )
                for el in df.columns
            },
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

    def get_world_map(self, method):
        """
        :param method: 'Frequency' or 'Increase' (from dropdown left menu)
        :return fig:
            frequency method: choropleth map with number of sequences with selected properties per country
            increase method: choropleth map showing decrease/increase of mutation with strongest increase in selected interval
                            (zero values = one time point are excluded)
        """
        df, column_of_interest = self.get_world_map_df(method)
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
    def __init__(self, df_dict):
        """
        param dates: propertyView["COLLECTION_DATE"], type 'datetime.date' (YYYY, M, D)
        """
        # TODO min date = 1978, max 2202-07-01
        dates_in_propertyViews = sorted(
            list(
                {i for s in [set(df["COLLECTION_DATE"]) for df in [
                    df_dict["propertyView"]['complete'],
                    df_dict["propertyView"]['partial']
                ]] for i in s}
            )
        )
        defined_min_date = datetime.strptime("2022-01-01", "%Y-%m-%d").date()  # min(dates)
        if min(dates_in_propertyViews) < defined_min_date:
            self.min_date = defined_min_date
        else:
            self.min_date = min(dates_in_propertyViews)
        self.max_date = max(dates_in_propertyViews)
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
        """
        uses second date and interval for preparing date list
        """
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
