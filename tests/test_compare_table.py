import unittest
import os
import pandas as pd
from dash.html import Span
from pandas._testing import assert_frame_equal
from parameterized import parameterized

from data import load_all_sql_files
from pages.utils import get_color_dict
from pages.utils_compare import create_comparison_tables
from pages.utils_compare import find_unique_and_shared_variants
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")

correct_result_dict = {'cds': {
    "correct_cols": ["sample.name", "AA_PROFILE", "IMPORTED", "COLLECTION_DATE", "RELEASE_DATE", "ISOLATE",
                     "LENGTH", "SEQ_TECH", "COUNTRY", "GEO_LOCATION", "HOST", "GENOME_COMPLETENESS",
                     "REFERENCE_ACCESSION"],
    "correct_cols_overview_variant": ["gene:variant", "freq l", "freq r"],
    "mut_opt_left": [{'label': Span(children='OPG151:L263F', style={'color': '#222A2A'}),
                      'value': 'OPG151:L263F', 'freq': 1}],
    "mut_opt_right": [{'label': Span(children='OPG193:A233G', style={'color': '#750D86'}),
                       'value': 'OPG193:A233G', 'freq': 3},
                      {'label': Span(children='OPG113:D723G', style={'color': '#DA16FF'}),
                       'value': 'OPG113:D723G', 'freq': 2}],
    "mut_opt_both": [{'label': Span(children='OPG193:L263F', style={'color': '#750D86'}),
                      'value': 'OPG193:L263F', 'freq': 229}],
    "seq_tech_left":  ['Illumina'],
    "seq_tech_right":  ['Nanopore'],
    "seq_tech_both":  ['Illumina', 'Nanopore'],
    "max_freq_nb_left": 1,
    "max_freq_nb_right": 3,
    "max_freq_nb_both": 0,
    "mut_value_left": ['OPG151:L263F'],
    "mut_value_both": ['OPG193:L263F'],
    "mut_value_right": ['OPG193:A233G', 'OPG113:D723G'],
    "len_table_left": 1,
    "len_table_right": 5,
    "len_table_both": 229,
    "variantView_df_both": pd.DataFrame([["OPG193:L263F", 204, 25]],
                                        columns=["gene:variant", "freq l", "freq r"]),
},
    'source': {
        "correct_cols": ["sample.name", "NUC_PROFILE", "IMPORTED", "COLLECTION_DATE", "RELEASE_DATE", "ISOLATE",
                         "LENGTH", "SEQ_TECH", "COUNTRY", "GEO_LOCATION", "HOST", "GENOME_COMPLETENESS",
                         "REFERENCE_ACCESSION"],
        "correct_cols_overview_variant": ["variant.label", "freq l", "freq r"],
        "mut_opt_left": [{'label': 'G74360A', 'value': 'G74360A', 'freq': 37},
                         {'label': 'C70780T', 'value': 'C70780T', 'freq': 12},
                         {'label': 'G8020A', 'value': 'G8020A', 'freq': 2},
                         {'label': 'C11343A', 'value': 'C11343A', 'freq': 1},
                         {'label': 'G173318A', 'value': 'G173318A', 'freq': 1}],
        "mut_opt_right": [{'label': 'del:150586-150602', 'value': 'del:150586-150602', 'freq': 25}],
        "mut_opt_both": [],
        "seq_tech_left":  ['Illumina'],
        "seq_tech_right":  ['Nanopore'],
        "seq_tech_both":  [],
        "max_freq_nb_left": 37,
        "max_freq_nb_right": 25,
        "max_freq_nb_both": 0,
        "mut_value_left": ['G74360A', 'C70780T', 'G8020A', 'C11343A', 'G173318A'],
        "mut_value_both": [],
        "mut_value_right": ['del:150586-150602'],
        "len_table_left": 53,
        "len_table_right": 25,
        "len_table_both": 0,
        "variantView_df_both": pd.DataFrame(columns=["variant.label", "freq l", "freq r"], index=pd.RangeIndex(0, 0, 1))
    }
}

test_params = [
    ["cds"],
    ["source"],
]


class TestCompareTable(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_04"
        self.processed_df_dict = load_all_sql_files(self.db_name, caching=False)
        self.countries = DbProperties.country_entries_cds_per_country.keys()
        self.color_dict = get_color_dict(self.processed_df_dict)
        self.genes_left = ['OPG193', 'OPG151']
        self.seq_tech_left = ['Illumina']
        self.genes_right = ['OPG106', 'OPG193', 'OPG113']
        self.seq_tech_right = ['Nanopore']
        self.completeness = "partial"
        self.reference = 2
        self.start_date = "2022-6-28"
        self.end_date = "2022-10-28"

    @parameterized.expand(test_params)
    def test_find_unique_and_shared_variants(self, aa_nt):
        mut_options_left, mut_options_right, mut_options_both, \
        mut_value_left, mut_value_right, mut_value_both, \
        max_freq_nb_left, max_freq_nb_right, max_freq_nb_both = find_unique_and_shared_variants(
            self.processed_df_dict,
            self.color_dict,
            self.completeness,
            self.reference,
            aa_nt,
            self.genes_left,
            self.seq_tech_left,
            self.countries,
            self.start_date,
            self.end_date,
            self.genes_right,
            self.seq_tech_right,
            self.countries,
            self.start_date,
            self.end_date,
        )
        for i in range(0, len(correct_result_dict[aa_nt]["mut_opt_left"])):
            assert mut_options_left[i]['value'] == correct_result_dict[aa_nt]["mut_opt_left"][i]['value']
            assert mut_options_left[i]['freq'] == correct_result_dict[aa_nt]["mut_opt_left"][i]['freq']
        for i in range(0, len(correct_result_dict[aa_nt]["mut_opt_right"])):
            assert mut_options_right[i]['value'] == correct_result_dict[aa_nt]["mut_opt_right"][i]['value']
            assert mut_options_right[i]['freq'] == correct_result_dict[aa_nt]["mut_opt_right"][i]['freq']
        for i in range(0, len(correct_result_dict[aa_nt]["mut_opt_both"])):
            assert mut_options_both[i]['value'] == correct_result_dict[aa_nt]["mut_opt_both"][i]['value']
            assert mut_options_both[i]['freq'] == correct_result_dict[aa_nt]["mut_opt_both"][i]['freq']
        self.assertListEqual(mut_value_left, correct_result_dict[aa_nt]["mut_value_left"])
        self.assertListEqual(mut_value_right, correct_result_dict[aa_nt]["mut_value_right"])
        self.assertListEqual(mut_value_both, correct_result_dict[aa_nt]["mut_value_both"])
        assert max_freq_nb_left == correct_result_dict[aa_nt]["max_freq_nb_left"]
        assert max_freq_nb_right == correct_result_dict[aa_nt]["max_freq_nb_right"]

    @parameterized.expand(test_params)
    def test_create_comparison_tables_cds(self, aa_nt):
        table_df_1, table_df_2, table_df_3, variantView_df_overview_both = create_comparison_tables(
            self.processed_df_dict,
            self.completeness,
            aa_nt,
            correct_result_dict[aa_nt]["mut_value_left"],
            self.reference,
            self.seq_tech_left,
            self.countries,
            self.start_date,
            self.end_date,
            correct_result_dict[aa_nt]["mut_value_right"],
            self.seq_tech_right,
            self.countries,
            self.start_date,
            self.end_date,
            correct_result_dict[aa_nt]["mut_value_both"]
        )
        mut_col = "AA_PROFILE" if aa_nt == 'cds' else "NUC_PROFILE"
        for mut in table_df_1[mut_col].to_list():
            assert len(set(mut.split(',')).intersection(set(correct_result_dict[aa_nt]["mut_value_left"]))) > 0
        for mut in table_df_2[mut_col].to_list():
            assert len(set(mut.split(',')).intersection(set(correct_result_dict[aa_nt]["mut_value_right"]))) > 0
        for mut in table_df_3[mut_col].to_list():
            assert len(set(mut.split(',')).intersection(set(correct_result_dict[aa_nt]["mut_value_both"]))) > 0
        self.assertListEqual(list(table_df_1['SEQ_TECH'].unique()), correct_result_dict[aa_nt]["seq_tech_left"])
        self.assertListEqual(list(table_df_2['SEQ_TECH'].unique()), correct_result_dict[aa_nt]["seq_tech_right"])
        self.assertListEqual(list(table_df_3['SEQ_TECH'].unique()), correct_result_dict[aa_nt]["seq_tech_both"])
        assert len(table_df_1) == correct_result_dict[aa_nt]["len_table_left"]
        assert len(table_df_2) == correct_result_dict[aa_nt]["len_table_right"]
        assert len(table_df_3) == correct_result_dict[aa_nt]["len_table_both"]
        assert_frame_equal(variantView_df_overview_both, correct_result_dict[aa_nt]["variantView_df_both"],
                           check_datetimelike_compat=True,
                           check_dtype=False)

    @parameterized.expand(test_params)
    def test_empty_filtering(self, aa_nt):
        table_df_1, table_df_2, table_df_3, variantView_df_both = create_comparison_tables(
            self.processed_df_dict,
            self.completeness,
            aa_nt,
            [],
            self.reference,
            [],
            [],
            self.start_date,
            self.end_date,
            [],
            [],
            [],
            self.start_date,
            self.end_date,
            []
        )
        for df in table_df_1, table_df_2, table_df_3:
            assert df.empty
            self.assertListEqual(list(df.columns), correct_result_dict[aa_nt]["correct_cols"])
        assert variantView_df_both.empty
        self.assertListEqual(list(variantView_df_both.columns), correct_result_dict[aa_nt]["correct_cols_overview_variant"])


class TestOverviewTable(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_04"
        self.processed_df_dict = load_all_sql_files(self.db_name, caching=False)
        self.countries = DbProperties.country_entries_cds_per_country.keys()
        self.color_dict = get_color_dict(self.processed_df_dict)
        self.genes_left = ['OPG193', 'OPG151']
        self.seq_tech_left = ['Illumina']
        self.genes_right = ['OPG106', 'OPG193', 'OPG113']
        self.seq_tech_right = ['Nanopore']
        self.completeness = "partial"
        self.reference = 2
        self.start_date = "2022-6-28"
        self.end_date = "2022-10-28"
