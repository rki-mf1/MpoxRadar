import datetime
import unittest

import pytest
from parameterized import parameterized
from pages.config import location_coordinates
from pages.utils import get_color_dict
from pages.utils_worldMap_explorer import VariantMapAndPlots, DateSlider
import pandas as pd
from pandas._testing import assert_frame_equal
from datetime import date, timedelta
import os
from data import load_all_sql_files
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDateSlider(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_03"
        self.processed_df_dict = load_all_sql_files(self.db_name)
        dates_in_propertyViews = sorted(
            list(
                {i for s in [set(df["COLLECTION_DATE"]) for df in [
                    self.processed_df_dict["propertyView"]['complete'],
                    self.processed_df_dict["propertyView"]['partial']
                ]] for i in s}
            )
        )
        self.date_slider = DateSlider(dates_in_propertyViews)

    def test_dates(self):
        assert (self.date_slider.min_date == date(2022, 6, 28))
        assert (self.date_slider.max_date == date(2022, 10, 1))
        assert len(self.date_slider.date_list) == 96


test_params = [
    [2, "interval1", "complete"],
    [2, "interval1", "partial"],
    [2, "interval2", "complete"],
    [2, "interval2", "partial"],
]


class TestWorldMap(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_03"
        self.processed_df_dict = load_all_sql_files(self.db_name)
        dates_in_propertyViews = sorted(
            list(
                {i for s in [set(df["COLLECTION_DATE"]) for df in [
                    self.processed_df_dict["propertyView"]['complete'],
                    self.processed_df_dict["propertyView"]['partial']
                ]] for i in s}
            )
        )
        self.date_slider = DateSlider(dates_in_propertyViews)
        self.countries = list(DbProperties.country_entries_cds_per_country.keys())
        self.seqtechs = ["Illumina", "Nanopore"]
        self.reference_genomes = [2, 4]
        self.complete_partial = ["complete", "partial"]
        self.genes = {2: ["OPG001", "OPG098"], 4: []}
        self.variants1 = {2: DbProperties.cds_gene_variants["complete"][2],
                          4: DbProperties.cds_gene_variants["complete"][4]}
        # T58K A233G appears only once
        self.variants2 = {2: ['OPG197:T22K', 'OPG151:L263F', 'OPG193:L263F', 'OPG016:R84K', 'OPG113:T58K',
                              'OPG193:A233G'],
                          4: DbProperties.cds_gene_variants["complete"][4]}
        self.date1 = date.fromisoformat('2022-06-28')
        self.date2 = date.fromisoformat('2022-10-02')
        self.interval = {'interval1': 100, 'interval2': 30}
        self.interval2 = 30
        self.dates21 = (DateSlider.unix_time_millis(datetime.date(2022, 6, 28)),
                        DateSlider.unix_time_millis(datetime.date(2022, 10, 2)))
        self.color_dict = get_color_dict(self.processed_df_dict)

    @parameterized.expand(test_params)
    def test_get_df_for_frequency_bar(self, reference, interval, completeness):
        for country in self.countries:
            variant_map_and_plot_instance = VariantMapAndPlots(
                self.processed_df_dict,
                self.date_slider,
                reference,
                completeness,
                self.countries,
                self.seqtechs,
                self.variants2[2],
                self.dates21,
                self.interval[interval],
                self.color_dict,
                'detail',
                location_coordinates,
                self.genes,  # only detail plots
                country)
            columns = ["COUNTRY", "variant.label", "element.symbol", "number_sequences"]
            correct_df = pd.DataFrame(
                DbProperties.correct_rows_frequency_bar[reference][country][interval][completeness], columns=columns)
            correct_df = correct_df.sort_values(by=["variant.label"]).reset_index(drop=True)
            df = variant_map_and_plot_instance.get_df_for_frequency_bar()
            df = df.sort_values(by=["variant.label"]).reset_index(drop=True)
            assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    @parameterized.expand(test_params)
    def test_increase_df(self, reference, interval, completeness):
        columns = ['COUNTRY', 'variant.label', 'element.symbol', 'number_sequences', 'COLLECTION_DATE', 'slope']
        for country in self.countries:
            variant_map_and_plot_instance = VariantMapAndPlots(
                self.processed_df_dict,
                self.date_slider,
                reference,
                completeness,
                self.countries,
                self.seqtechs,
                self.variants2[2],
                self.dates21,
                self.interval[interval],
                self.color_dict,
                'detail',
                location_coordinates,
                self.genes,  # only detail plots
                country)

            correct_df = pd.DataFrame(DbProperties.correct_rows_increase_df[reference][country][interval][completeness],
                                      columns=columns)
            correct_df = correct_df.sort_values(by=["COUNTRY", "variant.label"]).reset_index(drop=True)
            df = variant_map_and_plot_instance.get_increase_df()
            df = df.sort_values(by=["COUNTRY", "variant.label"]).reset_index(drop=True)
            df = df.round({"slope": 4})
            assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    @parameterized.expand(test_params)
    def test_get_scatter_df(self, reference, interval, completeness):
        columns = ['COUNTRY', 'COLLECTION_DATE', 'variant.label', 'element.symbol', 'number_sequences', 'date_numbers']
        for country in self.countries:
            variant_map_and_plot_instance = VariantMapAndPlots(
                self.processed_df_dict,
                self.date_slider,
                reference,
                completeness,
                self.countries,
                self.seqtechs,
                self.variants2[2],
                self.dates21,
                self.interval[interval],
                self.color_dict,
                'detail',
                location_coordinates,
                self.genes,  # only detail plots
                country)

            correct_df = pd.DataFrame(DbProperties.correct_rows_scatter_df[reference][country][interval][completeness],
                                      columns=columns)
            correct_df = correct_df.sort_values(by=["COLLECTION_DATE", "variant.label"]).reset_index(
                drop=True)
            df = variant_map_and_plot_instance.get_scatter_df()
            df = df.sort_values(by=["COLLECTION_DATE", "variant.label"]).reset_index(drop=True)
            assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    @parameterized.expand(test_params)
    def test_get_world_frequency_df(self, reference, interval, completeness):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            reference,
            completeness,
            self.countries,
            self.seqtechs,
            self.variants1[2],
            self.dates21,
            self.interval[interval],
            self.color_dict,
            'map',
            location_coordinates, )
        columns = ['COUNTRY', 'number_sequences', 'ISO_Code']
        correct_df = pd.DataFrame(DbProperties.correct_rows_map_df_freq[reference][interval][completeness],
                                  columns=columns)
        correct_df = correct_df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        df, column_of_interest = variant_map_and_plot_instance.get_world_map_df('Frequency')
        df = df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    @parameterized.expand(test_params)
    def test_get_world_increase_df(self, reference, interval, completeness):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            reference,
            completeness,
            self.countries,
            self.seqtechs,
            self.variants1[2],
            self.dates21,
            self.interval[interval],
            self.color_dict,
            'map',
            location_coordinates, )
        columns = ['COUNTRY', 'slope', 'ISO_Code']
        correct_df = pd.DataFrame(DbProperties.correct_rows_map_df_incr[reference][interval][completeness],
                                  columns=columns)
        correct_df = correct_df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        df, column_of_interest = variant_map_and_plot_instance.get_world_map_df('Increase')
        df = df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        df = df.round({"slope": 4})
        assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_get_world_map_mutation_proportion(self):
    #     # method Mutation Proportion all variants, all dates
    #     columns = ["location_ID", "number_sequences", "mutation_proportion", "location", "lat", "lon"]
    #     rows = [[1, 4, 75.0, "France", 46.2276, 2.2137],
    #             [2, 2, 50.0, "Austria", 47.5162, 14.5501],
    #             [10115, 6, 50.0, "Berlin", 32.5337, 13.3872],
    #             [30161, 4, 50.0, "Hannover", 52.3842, 9.7446],
    #             [80331, 5, 100.0, "München", 48.1379, 11.5722]]
    #     correct_df2 = pd.DataFrame(rows, columns=columns)
    #     correct_df2 = correct_df2.sort_values(by=['location_ID']).reset_index(drop=True)
    #     df2, _ = self.world_map.get_world_map_df('Mutation Proportion', self.variants1, self.dates21)
    #     df2 = df2.round({"lat": 4, 'lon': 4, "mutation_proportion": 4})
    #     df2 = df2.sort_values(by=['location_ID']).reset_index(drop=True)
    #     assert_frame_equal(df2, correct_df2, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_get_world_map_mutation_proportion_2(self):
    #     # voc: ['L18F', 'E484K']
    #     # dates: 29.12.2021 - 12.01.2022
    #     columns = ["location_ID", "number_sequences", "mutation_proportion", "location", "lat", "lon", ]
    #     rows = [[1, 4, 75.0, "France", 46.2276, 2.2137],
    #             [2, 2, 50.0, "Austria", 47.5162, 14.5501],
    #             [10115, 6, 50.0, "Berlin", 32.5337, 13.3872],
    #             [30161, 4, 50.0, "Hannover", 52.3842, 9.7446],
    #             [80331, 5, 40.0, "München", 48.1379, 11.5722]]
    #     correct_df2b = pd.DataFrame(rows, columns=columns).sort_values(by=['location_ID']).reset_index(drop=True)
    #     df2b, _ = self.world_map.get_world_map_df('Mutation Proportion', self.variants2, self.dates21)
    #     df2b = df2b.round({"lat": 4, 'lon': 4, "mutation_proportion": 4}).sort_values(by=['location_ID']).reset_index(
    #         drop=True)
    #     assert_frame_equal(df2b, correct_df2b, check_datetimelike_compat=True, check_dtype=False)
    #
    #     # method increase
    #     columns = ["location_ID", "mutations", "number_sequences", "date", "slope", "location", "lat", "lon"]
    #     rows = [[1, "A475V", [2], [to_date("2022-01-07")], 0.00000, "France", 46.2276, 2.2137],
    #             [1, "T20N", [1], [to_date("2022-01-07")], 0.0000, "France", 46.2276, 2.2137],
    #             [2, "A475V", [1], [to_date("2022-01-07")], 0.0000, "Austria", 47.5162, 14.5501],
    #             [2, "T20N", [1], [to_date("2022-01-07")], 0.0000, "Austria", 47.5162, 14.5501],
    #             [10115, "A475V", [2, 0], [to_date("2022-01-01"), to_date("2022-01-10")], 0.0000, "Berlin", 32.5337,
    #              13.3872],
    #             [10115, "T20N", [2, 0], [to_date("2022-01-01"), to_date("2022-01-10")], 0.0000, "Berlin", 32.5337,
    #              13.3872],
    #             [30161, "A475V", [0], [to_date("2022-01-10")], 0.0000, "Hannover", 52.3842, 9.7446],
    #             [30161, "T20N", [2], [to_date("2022-01-10")], 0.0000, "Hannover", 52.3842, 9.7446],
    #             [80331, "A475V", [1, 2], [to_date("2022-01-01"), to_date("2022-01-10")], 0.1111, "München", 48.1379,
    #              11.5722],
    #             [80331, "T20N", [1, 2], [to_date("2022-01-01"), to_date("2022-01-10")], 0.1111, "München", 48.1379,
    #              11.5722],
    #             ]
    #
    #     correct_df3 = pd.DataFrame(rows, columns=columns)
    #     df3, _ = self.world_map.get_world_map_df('Increase', ["A475V", "T20N"], self.dates21)
    #     df3 = df3.round({"lat": 4, 'lon': 4, "slope": 4})
    #     assert_frame_equal(df3, correct_df3, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_df_with_wildtype_selected_frequency(self):
    #     mutations = ["wildtype"]
    #     columns = ["location_ID", "mutations", "number_sequences", "location", "lat", "lon"]
    #     rows = [[1, "wildtype", 1, "France", 46.2276, 2.2137],
    #             [2, "wildtype", 1, "Austria", 47.5162, 14.5501],
    #             [10115, "wildtype", 3, "Berlin", 32.5337, 13.3872],
    #             [30161, "wildtype", 2, "Hannover", 52.3842, 9.7446],
    #             [80331, "wildtype", 0, "München", 48.1379, 11.5722]]
    #     correct_df1 = pd.DataFrame(rows, columns=columns)
    #     df1, _ = self.world_map.get_world_map_df('Frequency', mutations, self.dates21)
    #     df1 = df1.round({"lat": 4, 'lon': 4})
    #     assert_frame_equal(df1, correct_df1, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_df_with_no_vars_selected_mutation_proportion(self):
    #     mutations = ["wildtype"]
    #     columns = ["location_ID", "number_sequences", "mutation_proportion", "location", "lat", "lon", ]
    #     rows = [[1, 4, 25.0, "France", 46.2276, 2.2137],
    #             [2, 2, 50.0, "Austria", 47.5162, 14.5501],
    #             [10115, 6, 50.0, "Berlin", 32.5337, 13.3872],
    #             [30161, 4, 50.0, "Hannover", 52.3842, 9.7446],
    #             [80331, 5, 0.0, "München", 48.1379, 11.5722]]
    #     correct_df2 = pd.DataFrame(rows, columns=columns)
    #     df2, _ = self.world_map.get_world_map_df('Mutation Proportion', mutations, self.dates21)
    #     df2 = df2.round({"lat": 4, 'lon': 4})
    #     assert_frame_equal(df2, correct_df2, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_df_with_no_vars_selected_lab_increase(self):
    #     columns = ["number_sequences", "date", "slope"]
    #     rows = []
    #     mutations = []
    #     correct_df3 = pd.DataFrame(rows, columns=columns)
    #     df3, _ = self.world_map.get_world_map_df('Increase', mutations, self.dates21)
    #     assert_frame_equal(df3, correct_df3, check_datetimelike_compat=True, check_dtype=False)
    #
    #     columns = ["number_sequences", "date", "slope"]
    #     rows = []
    #     correct_df5 = pd.DataFrame(rows, columns=columns)
    #     df5 = self.world_map.get_increase_df(self.dates21, mutations, location_ID=30161)
    #     assert_frame_equal(df5, correct_df5, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_get_frequency_bar_chart(self):
    #     fig = self.world_map.get_frequency_bar_chart(self.variants1, self.dates21, location_ID=10115)
    #     assert (fig['data'][0]['name'] == 'A475V')
    #     assert (round(list(fig['data'][0]['y'])[0]) == 2)
    #     assert (fig['data'][1]['name'] == 'D138Y')
    #     assert (round(list(fig['data'][1]['y'])[0]) == 2)
    #     assert (fig['data'][2]['name'] == 'E484K')
    #     assert (round(list(fig['data'][2]['y'])[0]) == 2)
    #     assert (fig['data'][3]['name'] == 'L18F')
    #     assert (round(list(fig['data'][3]['y'])[0]) == 3)
    #     assert (fig['data'][4]['name'] == 'T20N')
    #     assert (round(list(fig['data'][4]['y'])[0]) == 2)
    #
    # def test_get_number_sequences_per_interval(self):
    #     nb_mut = self.world_map.get_number_sequences_per_interval(self.dates21, self.variants1)
    #     assert (14 == nb_mut)
    #     nb_wt = self.world_map.get_number_sequences_per_interval(self.dates21, ["wildtype"])
    #     assert (7 == nb_wt)
    #
    # def test_get_frequency_development_scatter_plot(self):
    #     fig = self.world_map.get_frequency_development_scatter_plot(self.variants1, 'linear', self.dates21, 80331)
    #     assert (fig['layout']['xaxis']['ticktext'] == ("2022-01-01", "2022-01-10"))
    #     assert (fig['data'][0]['legendgroup'] == 'A475V')
    #     assert (list(fig['data'][0]['x']) == [0, 9])
    #     assert ([round(x) for x in list(fig['data'][0]['y'])] == [1, 2])
    #
    # def test_empty_df(self):
    #     pass
    #
    # def test_get_full_df(self):
    #     columns = ["location_ID", "date", "id_list", "mutations", "number_sequences"]
    #     rows = [[1, to_date("2022-01-07"), "18", "T20N", 1],
    #             [1, to_date("2022-01-07"), "17,18,19", "L18F", 3],
    #             [1, to_date("2022-01-07"), "17,19", "E484K", 2],
    #             [1, to_date("2022-01-07"), "0", "D138Y", 0],
    #             [1, to_date("2022-01-07"), "17,19", "A475V", 2],
    #             [1, to_date("2022-01-07"), "16", "wildtype", 1],
    #             [2, to_date("2022-01-07"), "21", "L18F", 1],
    #             [2, to_date("2022-01-07"), "21", "A475V", 1],
    #             [2, to_date("2022-01-07"), "20", "wildtype", 1],
    #             [2, to_date("2022-01-07"), "21", "E484K", 1],
    #             [2, to_date("2022-01-07"), "21", "T20N", 1],
    #             [2, to_date("2022-01-07"), "21", "D138Y", 1],
    #             [10115, to_date("2022-01-10"), "0", "T20N", 0],
    #             [10115, to_date("2022-01-10"), "0", "L18F", 0],
    #             [10115, to_date("2022-01-10"), "0", "A475V", 0],
    #             [10115, to_date("2022-01-10"), "0", "D138Y", 0],
    #             [10115, to_date("2022-01-10"), "0", "E484K", 0],
    #             [10115, to_date("2022-01-01"), "2,3", "wildtype", 2],
    #             [10115, to_date("2022-01-10"), "8", "wildtype", 1],
    #             [10115, to_date("2022-01-01"), "4,5", "A475V", 2],
    #             [10115, to_date("2022-01-01"), "4,5", "D138Y", 2],
    #             [10115, to_date("2022-01-01"), "4,5", "E484K", 2],
    #             [10115, to_date("2022-01-01"), "1,4,5", "L18F", 3],
    #             [10115, to_date("2022-01-01"), "4,5", "T20N", 2],
    #             [30161, to_date("2022-01-10"), "0", "E484K", 0],
    #             [30161, to_date("2022-01-10"), "10,9", "wildtype", 2],
    #             [30161, to_date("2022-01-10"), "11,12", "L18F", 2],
    #             [30161, to_date("2022-01-10"), "11,12", "T20N", 2],
    #             [30161, to_date("2022-01-10"), "0", "D138Y", 0],
    #             [30161, to_date("2022-01-10"), "0", "A475V", 0],
    #             [80331, to_date("2022-01-01"), "6", "E484K", 1],
    #             [80331, to_date("2022-01-01"), "0", "wildtype", 0],
    #             [80331, to_date("2022-01-01"), "7", "T20N", 1],
    #             [80331, to_date("2022-01-01"), "0", "D138Y", 0],
    #             [80331, to_date("2022-01-01"), "0", "L18F", 0],
    #             [80331, to_date("2022-01-10"), "13,14", "T20N", 2],
    #             [80331, to_date("2022-01-10"), "15", "L18F", 1],
    #             [80331, to_date("2022-01-10"), "13,14,15", "D138Y", 3],
    #             [80331, to_date("2022-01-10"), "13,14", "A475V", 2],
    #             [80331, to_date("2022-01-10"), "0", "E484K", 0],
    #             [80331, to_date("2022-01-01"), "6", "A475V", 1],
    #             [80331, to_date("2022-01-10"), "0", "wildtype", 0], ]
    #
    #     correct_df = pd.DataFrame(rows, columns=columns).sort_values(
    #         by=['location_ID', 'date', 'mutations']).reset_index(drop=True)
    #     df_all_dates_all_voc = self.world_map.df_all_dates_all_voc.sort_values(
    #         by=['location_ID', 'date', 'mutations']).reset_index(drop=True)
    #     correct_df['id_list'] = correct_df['id_list'].apply(lambda x: sorted(x.split(',')))
    #     df_all_dates_all_voc['id_list'] = df_all_dates_all_voc['id_list'].apply(lambda x: sorted(x.split(',')))
    #     assert_frame_equal(df_all_dates_all_voc, correct_df, check_datetimelike_compat=True, check_dtype=False)
    #
    # def test_get_most_frequent_map_df(self):
    #     columns = ["location_ID", "mutations", "number_sequences", "location", "lat", "lon", "scaled_column"]
    #     rows = [[80331, "A475V", 3, "München", 48.137900, 11.572200, 30],
    #             [30161, "L18F", 2, "Hannover", 52.384200, 9.744600, 20],
    #             [10115, "L18F", 3, "Berlin", 32.533700, 13.387200, 30],
    #             [2, "A475V", 1, "Austria", 47.516231, 14.550072, 10],
    #             [1, "L18F", 3, "France", 46.227638, 2.213749, 30]]
    #     correct_df = pd.DataFrame(rows, columns=columns).sort_values(by=['location_ID', 'mutations']).reset_index(
    #         drop=True)
    #
    #     nth = 1
    #     world_map_df, column_of_interest = self.world_map.get_world_map_df("Frequency", self.variants1, self.dates21)
    #     df = self.world_map.get_most_frequent_map_df(world_map_df, column_of_interest, nth).sort_values(
    #         by=['location_ID', 'mutations']).reset_index(drop=True)
    #     assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)
