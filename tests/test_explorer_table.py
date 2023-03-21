import unittest
from datetime import date
import os

from data import load_all_sql_files
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

    def test_table_columns(self):
        print(self.table_explorer.table_columns)
        correct_columns = [
            'sample.name', 'NUC_PROFILE', 'AA_PROFILE', 'IMPORTED', 'COLLECTION_DATE', 'RELEASE_DATE', 'ISOLATE',
            'LENGTH', 'SEQ_TECH', 'COUNTRY', 'GEO_LOCATION', 'HOST', 'GENOME_COMPLETENESS', 'reference.accession'
        ]
        self.assertListEqual(self.table_explorer.table_columns, correct_columns)

    def test_filtering(self):
        all_dates = [DateSlider.unix_time_millis(date(2022, 6, 28)), DateSlider.unix_time_millis(date(2022, 10, 1))]
        interval = 100
        date_list = self.date_slider.get_all_dates_in_interval(all_dates, interval)
        countries = ['Germany', 'USA']
        mutations = ['OPG197:T22K', 'OPG151:L263F', 'OPG193:L263F', 'OPG016:R84K', 'OPG113:T58K',
         'OPG193:A233G']
        seq_techs = ["Illumina", "Nanopore"]
        for country in countries:
            for seq_tech in seq_techs:
                    table_df = self.table_explorer.get_filtered_table(
                        self.processed_df_dict,
                        'partial',
                        mutations,
                        [seq_tech],
                        2,
                        date_list,
                        [country],
                    )
                    if not table_df.empty:
                        assert len(set(table_df['GENOME_COMPLETENESS']).intersection({'complete', 'partial'})) > 0
                        assert table_df['COUNTRY'].unique()[0] == country
                        assert table_df['SEQ_TECH'].unique()[0] == seq_tech

        full_table_df = self.table_explorer.get_filtered_table(
            self.processed_df_dict,
            'partial',
            mutations,
            seq_techs,
            2,
            date_list,
            countries,
        )
        assert len(full_table_df) == 230
        assert len(full_table_df['sample.name'].unique()) == 230
        self.assertListEqual(list(full_table_df.columns), self.final_cols)
        self.assertListEqual(list(full_table_df['COUNTRY'].unique()), countries)
        self.assertListEqual(list(full_table_df['SEQ_TECH'].unique()), seq_techs)

    def test_empty_filtering(self):
        table_df = self.table_explorer.get_filtered_table(
            self.processed_df_dict,
            'complete',
            [],
            [],
            2,
            [],
            [],
        )
        assert table_df.empty
        self.assertListEqual(list(table_df.columns), self.final_cols)
