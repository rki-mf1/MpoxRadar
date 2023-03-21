import unittest
from datetime import date
import os

import pandas as pd
from dash.html import Span
from pandas._testing import assert_frame_equal

from data import load_all_sql_files
from pages.utils import get_color_dict
from pages.utils_compare import create_comparison_tables, find_unique_and_shared_variants
from pages.utils_worldMap_explorer import TableFilter
from pages.utils_worldMap_explorer import DateSlider
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDbPreprocessing(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_04"
        self.processed_df_dict = load_all_sql_files(self.db_name, caching=False)
        self.countries = DbProperties.country_entries_cds_per_country.keys()
        self.table_explorer = TableFilter()
        self.date_slider = DateSlider(self.processed_df_dict)
        self.final_cols = self.table_explorer.table_columns.copy()
        self.final_cols[-1] = 'REFERENCE_ACCESSION'
        self.color_dict = get_color_dict(self.processed_df_dict)

    def test_find_unique_and_shared_variants(self):
        mut_options_left, mut_options_right, mut_options_both, \
        mut_value_left, mut_value_right, mut_value_both, \
        max_freq_nb_left, max_freq_nb_right, max_freq_nb_both = find_unique_and_shared_variants(
            self.processed_df_dict,
            self.color_dict,
            'partial',
            2,
            'cds',
            ['OPG193', 'OPG151'],
            ['Illumina'],
            self.countries,
            "2022-6-28",
            "2022-10-28",
            ['OPG106', 'OPG193', 'OPG113'],
            ['Nanopore'],
            self.countries,
            "2022-6-28",
            "2022-10-28",
        )
        correct_mut_opt_left = [{'label': Span(children='OPG151:L263F', style={'color': '#222A2A'}),
                                 'value': 'OPG151:L263F', 'freq': 1}]
        correct_mut_opt_right = [{'label': Span(children='OPG193:A233G', style={'color': '#750D86'}),
                                  'value': 'OPG193:A233G', 'freq': 3},
                                 {'label': Span(children='OPG113:D723G', style={'color': '#DA16FF'}),
                                  'value': 'OPG113:D723G', 'freq': 2}]
        correct_mut_opt_both = [{'label': Span(children='OPG193:L263F', style={'color': '#750D86'}),
                                 'value': 'OPG193:L263F', 'freq': 229}]
        correct_mut_left = ['OPG151:L263F']
        correct_mut_right = ['OPG193:A233G', 'OPG113:D723G']
        correct_mut_both = ['OPG193:L263F']
        for i in range(0, len(correct_mut_opt_left)):
            assert mut_options_left[i]['value'] == correct_mut_opt_left[i]['value']
            assert mut_options_left[i]['freq'] == correct_mut_opt_left[i]['freq']
        for i in range(0, len(correct_mut_opt_right)):
            assert mut_options_right[i]['value'] == correct_mut_opt_right[i]['value']
            assert mut_options_right[i]['freq'] == correct_mut_opt_right[i]['freq']
        for i in range(0, len(correct_mut_opt_both)):
            assert mut_options_both[i]['value'] == correct_mut_opt_both[i]['value']
            assert mut_options_both[i]['freq'] == correct_mut_opt_both[i]['freq']
        self.assertListEqual(mut_value_left, correct_mut_left)
        self.assertListEqual(mut_value_right, correct_mut_right)
        self.assertListEqual(mut_value_both, correct_mut_both)
        assert max_freq_nb_left == 1
        assert max_freq_nb_right == 3

    def test_create_comparison_tables_cds(self):
        table_df_1, table_df_2, table_df_3, variantView_df_both = create_comparison_tables(
            self.processed_df_dict,
            'partial',
            'cds',
            ['OPG151:L263F'],
            2,
            ['Illumina'],
            self.countries,
            "2022-6-28",
            "2022-10-28",
            ['OPG193:A233G', 'OPG113:D723G'],
            ['Nanopore'],
            self.countries,
            "2022-6-28",
            "2022-10-28",
            ['OPG193:L263F']
        )
        pd.set_option('display.max_columns', None)
        for mut in table_df_1['AA_PROFILE'].to_list():
            assert len(set(mut.split(',')).intersection({'OPG151:L263F'})) == 1
        for mut in table_df_2['AA_PROFILE'].to_list():
            assert len(set(mut.split(',')).intersection({'OPG193:A233G', 'OPG113:D723G'})) > 0
        for mut in table_df_1['AA_PROFILE'].to_list():
            assert len(set(mut.split(',')).intersection({'OPG193:L263F'})) == 1
        self.assertListEqual(list(table_df_1['SEQ_TECH'].unique()), ['Illumina'])
        self.assertListEqual(list(table_df_2['SEQ_TECH'].unique()), ['Nanopore'])
        self.assertListEqual(list(table_df_3['SEQ_TECH'].unique()), ['Illumina', 'Nanopore'])
        assert len(table_df_1) == 1
        assert len(table_df_2) == 5
        assert len(table_df_3) == 229
        correct_variantView_df_both = pd.DataFrame([["OPG193:L263F", 204, 25]],
                                                   columns=["gene:variant", "freq l", "freq r"])
        assert_frame_equal(variantView_df_both, correct_variantView_df_both, check_datetimelike_compat=True,
                           check_dtype=False)

    def test_empty_filtering(self):
        table_df_1, table_df_2, table_df_3, variantView_df_both = create_comparison_tables(
            self.processed_df_dict,
            'partial',
            'cds',
            [],
            2,
            [],
            [],
            "2022-6-28",
            "2022-10-28",
            [],
            [],
            [],
            "2022-6-28",
            "2022-10-28",
            []
        )
        assert table_df_1.empty
        assert table_df_2.empty
        assert table_df_3.empty
    # self.assertListEqual(list(table_df_1.columns), self.final_cols)
