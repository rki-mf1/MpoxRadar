import os
import unittest
from datetime import date

from parameterized import parameterized

from data import load_all_sql_files
from pages.utils_tables import TableFilter
from pages.utils_worldMap_explorer import DateSlider
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")

test_params = [
    ["Germany", "Illumina"],
    ["Germany", "Nanopore"],
    ["USA", "Illumina"],
    ["USA", "Nanopore"],
]


class TestExplorerTable(unittest.TestCase):
    """
    test of table properties of explorer tool table
    """
    @classmethod
    def setUpClass(cls):
        cls.db_name = "mpx_test_04"
        cls.processed_df_dict = load_all_sql_files(cls.db_name, test_db=True)
        cls.countries = DbProperties.country_entries_cds_per_country.keys()
        cls.date_slider = DateSlider(cls.processed_df_dict)
        cls.countries = ['Germany', 'USA']
        cls.mutations = [
            'OPG197:T22K', 'OPG151:L263F', 'OPG193:L263F', 'OPG016:R84K', 'OPG113:T58K',
            'OPG193:A233G'
        ]
        cls.seq_techs = ["Illumina", "Nanopore"]
        cls.table_explorer = TableFilter('explorer', cls.mutations)
        cls.final_cols = cls.table_explorer.table_columns.copy()
        cls.final_cols[-1] = 'REFERENCE_ACCESSION'
        all_dates = [
            DateSlider.unix_time_millis(date(2022, 6, 28)),
            DateSlider.unix_time_millis(date(2022, 10, 1))
        ]
        interval = 100
        cls.date_list = cls.date_slider.get_all_dates_in_interval(all_dates, interval)

    def test_table_columns(self):
        correct_columns = [
            'sample.name', 'NUC_PROFILE', 'AA_PROFILE', 'IMPORTED', 'COLLECTION_DATE',
            'RELEASE_DATE', 'ISOLATE', 'LENGTH', 'SEQ_TECH', 'COUNTRY', 'GEO_LOCATION', 'HOST',
            'GENOME_COMPLETENESS', 'REFERENCE_ACCESSION'
        ]
        self.assertListEqual(self.table_explorer.table_columns, correct_columns)

    @parameterized.expand(test_params)
    def test_filtering(self, country, seq_tech):
        table_df = self.table_explorer.create_explore_table(
            self.processed_df_dict,
            'partial',
            [seq_tech],
            2,
            self.date_list,
            [country],
        )
        if not table_df.empty:
            assert len(set(table_df['GENOME_COMPLETENESS']).intersection(
                {'complete', 'partial'})) > 0
            assert table_df['COUNTRY'].unique()[0] == country
            assert table_df['SEQ_TECH'].unique()[0] == seq_tech

    def test_filtering_full(self):
        full_table_df = self.table_explorer.create_explore_table(
            self.processed_df_dict,
            'partial',
            self.seq_techs,
            2,
            self.date_list,
            self.countries,
        )
        assert len(full_table_df) == 230
        assert len(full_table_df['sample.name'].unique()) == 230
        self.assertListEqual(
            list(full_table_df.columns),
            self.final_cols
        )
        self.assertListEqual(
            list(full_table_df['COUNTRY'].unique()),
            self.countries
        )
        self.assertListEqual(
            list(full_table_df['SEQ_TECH'].unique()),
            self.seq_techs
        )

    def test_empty_filtering(self):
        table_df = self.table_explorer.create_explore_table(
            self.processed_df_dict,
            'complete',
            [],
            2,
            [],
            [],
        )
        assert table_df.empty
        self.assertListEqual(
            list(table_df.columns),
            self.final_cols
        )
