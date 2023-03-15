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
        df, column_of_interest = variant_map_and_plot_instance.get_world_map_df('Increase')
        df = df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        df = df.round({"slope": 4})
        columns = ['COUNTRY', column_of_interest, 'ISO_Code']
        correct_df = pd.DataFrame(DbProperties.correct_rows_map_df_incr[reference][interval][completeness],
                                  columns=columns)
        correct_df = correct_df.sort_values(by=['ISO_Code']).reset_index(drop=True)
        assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    def test_map_empty_filter_options(self):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            2,
            'partial',
            [],
            [],
            [],
            self.dates21,
            self.interval["interval1"],
            self.color_dict,
            'map',
            location_coordinates, )
        df, column_of_interest = variant_map_and_plot_instance.get_world_map_df('Increase')
        correct_df = pd.DataFrame(columns=['COUNTRY', column_of_interest, 'ISO_Code'])
        assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

        df, column_of_interest = variant_map_and_plot_instance.get_world_map_df('Frequency')
        correct_df = pd.DataFrame(columns=['COUNTRY', column_of_interest, 'ISO_Code'])
        assert_frame_equal(df, correct_df, check_datetimelike_compat=True, check_dtype=False)

    def test_plots_empty_filter_options(self):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            2,
            'partial',
            [],
            [],
            [],
            self.dates21,
            self.interval["interval1"],
            self.color_dict,
            'detail',
            location_coordinates,
            self.genes,  # only detail plots
            "Germany"
        )
        df_scatter = variant_map_and_plot_instance.get_scatter_df()
        correct_df_scatter = pd.DataFrame(
            data=[['Germany', datetime.date(2022, 10, 2), 'no_mutations', 'no_gene', 0, 96]],
            columns=['COUNTRY', 'COLLECTION_DATE', 'variant.label', 'element.symbol', 'number_sequences',
                     'date_numbers'])
        assert_frame_equal(df_scatter, correct_df_scatter, check_datetimelike_compat=True, check_dtype=False)

        df_increase = variant_map_and_plot_instance.get_increase_df()
        df_increase.index = list(df_increase.index)
        correct_df_increase = pd.DataFrame(columns=['COUNTRY', 'variant.label', 'element.symbol', 'number_sequences',
                                                    'COLLECTION_DATE', 'slope'])
        assert_frame_equal(df_increase, correct_df_increase, check_datetimelike_compat=True, check_dtype=False)

        df_freq = variant_map_and_plot_instance.get_df_for_frequency_bar()
        df_freq.index = list(df_freq.index)
        correct_df_freq = pd.DataFrame(columns=["COUNTRY", "variant.label", "element.symbol", "number_sequences"])
        assert_frame_equal(df_freq, correct_df_freq, check_datetimelike_compat=True, check_dtype=False)

    def test_frequency_bar_chart(self):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            2,
            "partial",
            self.countries,
            self.seqtechs,
            self.variants1[2],
            self.dates21,
            self.interval["interval1"],
            self.color_dict,
            'detail',
            location_coordinates,
            self.genes,  # only detail plots
            "Germany")
        fig = variant_map_and_plot_instance.get_frequency_bar_chart()
        assert (fig['data'][0]['x'] == (['OPG159'], ['C133F']))
        assert (round(list(fig['data'][0]['y'])[0]) == 1)
        assert (fig['data'][1]['x'] == (['OPG210'], ['D1604K']))
        assert (round(list(fig['data'][1]['y'])[0]) == 31)

    def test_scatter_plot(self):
        variant_map_and_plot_instance = VariantMapAndPlots(
            self.processed_df_dict,
            self.date_slider,
            2,
            "partial",
            self.countries,
            self.seqtechs,
            self.variants1[2],
            self.dates21,
            self.interval["interval1"],
            self.color_dict,
            'detail',
            location_coordinates,
            self.genes,  # only detail plots
            "Germany")
        fig = variant_map_and_plot_instance.get_frequency_development_scatter_plot()

        for fig_value, test_value in zip(fig['data'][0]['customdata'],
                                         [[datetime.date(2022, 7, 1), 'D1604K', 'Germany', 'OPG210'],
                                          [datetime.date(2022, 8, 1), 'D1604K', 'Germany', 'OPG210'],
                                          [datetime.date(2022, 9, 1), 'D1604K', 'Germany', 'OPG210']]):
            self.assertListEqual(list(fig_value), test_value)
        self.assertListEqual(list(fig['data'][0]['x']), [3, 34, 65])
        self.assertListEqual(list(fig['data'][0]['y']), [17, 8, 6])
        self.assertListEqual(list(fig['data'][1]['x']), [3, 34, 65])
        self.assertListEqual([round(x, 2) for x in list(fig['data'][1]['y'])], [15.83, 10.33, 4.83])
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
