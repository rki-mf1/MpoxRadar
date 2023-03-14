import unittest
from pages.utils_worldMap_explorer import VariantMapAndPlots
import pandas as pd
from pandas._testing import assert_frame_equal
from datetime import date, timedelta
import os
from data import load_all_sql_files

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDbPreprocessing(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_03"
        self.processed_df_dict = load_all_sql_files(self.db_name)

        # test results
        self.country_entries_cds = {'Germany': [30, 22, 25, 17], "USA": [21, 7, 62, 38], "Egypt": [2, 0, 0, 0]}
        self.variants_cds = {
            'Germany': [
                {'Q188F', 'S288F', 'T22K', 'R84K', 'D25G', 'T58K', 'D1604K', 'R194P', 'L263F', 'V305G', 'N95K', 'C133F',
                 'L29P'},
                {'Q188F', 'S288F', 'T22K', 'R84K', 'D25G', 'T58K', 'D1604K', 'R194P', 'L263F', 'V305G', 'N95K',
                 'C133F'},
                {'Q188F', 'S288F', 'R84K', 'L142P', 'D1604K', 'Q436P', 'R194P', 'L263F', 'V305G', 'E121K', 'L29P'},
                {'Q188F', 'S288F', 'R84K', 'L142P', 'D1604K', 'Q436P', 'R194P', 'V305G', 'E121K'}
            ],
            "USA": [
                {'A433G', 'T22K', 'R84K', 'L263F', 'I119K', 'L29P', 'A233G'},
                {'A433G', 'T22K', 'R84K', 'I119K', 'A233G'},
                {'D723G', 'A433G', 'T22K', 'S288F', 'D1604K', 'Q436P', 'E121K', 'I119K', 'L263F', 'A233G', 'L29P'},
                {'D723G', 'A433G', 'T22K', 'S288F', 'D1604K', 'Q436P', 'E121K', 'I119K', 'A233G'}
            ],
            "Egypt": [
                {'L263F', 'L29P'},
                set(),
                set(),
                set(),
            ]
        }
        self.seq_techs_cds = {
            'Germany': [
                {'Illumina'},
                {'Illumina'},
                {'Illumina'},
                {'Illumina'},
            ],
            "USA": [
                {'Nanopore', 'Illumina'},
                {'Nanopore', 'Illumina'},
                {'Nanopore'},
                {'Nanopore'},
            ],
            "Egypt": [
                {'Illumina'},
                set(),
                set(),
                set(),
            ]
        }
        self.seq_techs_propertyView = {
            'Germany': [
                {'Illumina'},
                {'Illumina'},
            ],
            "USA": [
                {'Nanopore', 'Illumina'},
                {'Nanopore'},
            ],
            "Egypt": [
                {'Illumina'},
                set(),
            ]
        }
        self.genes = {
            'Germany': [
                {'OPG044', 'OPG185', 'OPG193', 'OPG089', 'OPG094', 'OPG159', 'OPG151', 'OPG189', 'OPG015', 'OPG113',
                 'OPG016', 'OPG197', 'OPG210'},
                {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-072', 'MPXV-USA_2022_MA001-171',
                 'MPXV-USA_2022_MA001-165', 'MPXV-USA_2022_MA001-187', 'MPXV-USA_2022_MA001-162',
                 'MPXV-USA_2022_MA001-143', 'MPXV-USA_2022_MA001-096', 'MPXV-USA_2022_MA001-077',
                 'MPXV-USA_2022_MA001-186', 'MPXV-USA_2022_MA001-134'},
                {'OPG044', 'OPG185', 'OPG193', 'OPG089', 'OPG094', 'OPG151', 'OPG015', 'OPG016', 'OPG210'},
                {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-072', 'MPXV-USA_2022_MA001-187',
                 'MPXV-USA_2022_MA001-162', 'MPXV-USA_2022_MA001-077', 'MPXV-USA_2022_MA001-186',
                 'MPXV-USA_2022_MA001-134', 'MPXV-USA_2022_MA001-028'}
            ],
            "USA": [
                {'OPG044', 'OPG193', 'OPG117', 'OPG164', 'OPG005', 'OPG016'},
                {'MPXV-USA_2022_MA001-184', 'MPXV-USA_2022_MA001-148', 'MPXV-USA_2022_MA001-169',
                 'MPXV-USA_2022_MA001-186', 'MPXV-USA_2022_MA001-100'},
                {'OPG044', 'OPG185', 'OPG193', 'OPG117', 'OPG164', 'OPG005', 'OPG151', 'OPG113', 'OPG210'},
                {'MPXV-USA_2022_MA001-182', 'MPXV-USA_2022_MA001-096', 'MPXV-USA_2022_MA001-184',
                 'MPXV-USA_2022_MA001-162', 'MPXV-USA_2022_MA001-148', 'MPXV-USA_2022_MA001-169',
                 'MPXV-USA_2022_MA001-134', 'MPXV-USA_2022_MA001-100'},
            ],
            "Egypt": [
                {'OPG044', 'OPG193'},
                set(),
                set(),
                set(),
            ]
        }
        self.samples_dict_cds = {
            'Germany': [222, 107, 71, 34],
            "USA": [12, 8, 37, 30],
            "Egypt": [1, 0, 0, 0]
        }
        self.samples_dict_propertyView = {'Germany': [222, 71], "USA": [12, 37], "Egypt": [1, 0]}

    def test_df_dict_structure(self):
        assert list(self.processed_df_dict['propertyView'].keys()) == ["complete", "partial"]
        assert list(self.processed_df_dict['variantView'].keys()) == ["complete", "partial"]

        assert list(self.processed_df_dict["variantView"]["complete"].keys()) == [2, 4]
        assert list(self.processed_df_dict["variantView"]["complete"][2].keys()) == ['source', 'cds']
        assert list(self.processed_df_dict["variantView"]["partial"].keys()) == [2, 4]
        assert list(self.processed_df_dict["variantView"]["partial"][2].keys()) == ['source', 'cds']

        assert list(self.processed_df_dict["world_map"]["complete"].keys()) == [2, 4]
        assert list(self.processed_df_dict["world_map"]["partial"].keys()) == [2, 4]

    def test_world_df(self):
        world_df_2_c = self.processed_df_dict["world_map"]["complete"][2]
        world_df_4_c = self.processed_df_dict["world_map"]["complete"][4]
        world_df_2_p = self.processed_df_dict["world_map"]["partial"][2]
        world_df_4_p = self.processed_df_dict["world_map"]["partial"][4]
        world_dfs = [world_df_2_c, world_df_4_c, world_df_2_p, world_df_4_p]
        world_df_columns = ['COUNTRY', 'COLLECTION_DATE', 'SEQ_TECH', 'sample_id_list',
                            'variant.label', 'number_sequences', 'element.symbol', 'gene:variant']

        for world_df in world_dfs:
            assert list(world_df.columns) == world_df_columns
        # test nb entries per countrie
        for country in self.country_entries_cds.keys():
            for i, world_df in enumerate(world_dfs):
                assert len(world_df[world_df['COUNTRY'] == country]) == self.country_entries_cds[country][i]

        for country in self.country_entries_cds.keys():
            for i, world_df in enumerate(world_dfs):
                assert set(world_df[world_df['COUNTRY'] == country]['variant.label']) == self.variants_cds[country][i]
        # test different seq_techs per country
        for country in self.country_entries_cds.keys():
            for i, world_df in enumerate(world_dfs):
                assert set(world_df[world_df['COUNTRY'] == country]['SEQ_TECH']) == self.seq_techs_cds[country][i]

        for country in self.country_entries_cds.keys():
            for i, world_df in enumerate(world_dfs):
                assert set(world_df[world_df['COUNTRY'] == country]['element.symbol']) == self.genes[country][i]

        for country in self.country_entries_cds.keys():
            for i, world_df in enumerate(world_dfs):
                samples = set([item for sublist in
                               [x.split(',') for x in world_df[world_df['COUNTRY'] == country]["sample_id_list"]] for
                               item in sublist])
                assert len(samples) == self.samples_dict_cds[country][i]

    def test_variantView_df(self):
        variantView_2_c_s = self.processed_df_dict["variantView"]["complete"][2]['source']
        variantView_2_c_c = self.processed_df_dict["variantView"]["complete"][2]['cds']
        variantView_4_c_s = self.processed_df_dict["variantView"]["complete"][4]['source']
        variantView_4_c_c = self.processed_df_dict["variantView"]["complete"][4]['cds']
        variantView_2_p_s = self.processed_df_dict["variantView"]["partial"][2]['source']
        variantView_2_p_c = self.processed_df_dict["variantView"]["partial"][2]['cds']
        variantView_4_p_s = self.processed_df_dict["variantView"]["partial"][4]['source']
        variantView_4_p_c = self.processed_df_dict["variantView"]["partial"][4]['cds']
        variantView_dfs_cds = [variantView_2_c_c, variantView_4_c_c, variantView_2_p_c, variantView_4_p_c]
        variantView_dfs_source = [variantView_2_c_s, variantView_4_c_s, variantView_2_p_s, variantView_4_p_s]

        variantView_df_source_columns = ['sample.id', 'sample.name', 'reference.id', 'reference.accession',
                                         'element.symbol',
                                         'element.type', 'variant.id', 'variant.label']
        variantView_df_cds_columns = ['sample.id', 'sample.name', 'reference.id', 'reference.accession',
                                      'element.symbol',
                                      'element.type', 'variant.id', 'variant.label', 'gene:variant']
        source_variants = [
            ['C11343A', 'C70780T', 'G74360A', 'G8020A', 'del:150586-150602', 'del:197161-197209'],
            ['C159772T', 'G165079A', 'G50051A', 'del:133123'],
            ['C70780T', 'G173318A', 'G74360A', 'G97290A', 'del:150586-150602', 'del:197161-197209'],
            ['C159772T', 'C43029T', 'G165079A', 'G55179A', 'del:133123'],
        ]
        cds_variants = [
            ['A233G', 'A433G', 'C133F', 'D1604K', 'D25G', 'I119K', 'L263F', 'L29P', 'N95K', 'Q188F', 'R194P', 'R84K',
             'S288F', 'T22K', 'T58K', 'V305G'],
            ['A233G', 'A433G', 'C133F', 'D1604K', 'D25G', 'I119K', 'L263F', 'N95K', 'Q188F', 'R194P', 'R84K', 'S288F',
             'T22K', 'T58K', 'V305G'],
            ['A233G', 'A433G', 'D1604K', 'D723G', 'E121K', 'I119K', 'L142P', 'L263F', 'L29P', 'Q188F', 'Q436P', 'R194P',
             'R84K', 'S288F', 'T22K', 'V305G'],
            ['A233G', 'A433G', 'D1604K', 'D723G', 'E121K', 'I119K', 'L142P', 'Q188F', 'Q436P', 'R194P', 'R84K', 'S288F',
             'T22K', 'V305G']
        ]
        genes = [{'OPG113:T58K', 'OPG094:R194P', 'OPG164:I119K', 'OPG197:T22K', 'OPG193:A233G', 'OPG210:D1604K',
                  'OPG117:A433G', 'OPG197:D25G', 'OPG089:V305G', 'OPG189:N95K', 'OPG005:T22K', 'OPG016:R84K',
                  'OPG159:C133F', 'OPG015:Q188F', 'OPG151:L263F', 'OPG185:S288F', 'OPG044:L29P', 'OPG193:L263F'},
                 {'MPXV-USA_2022_MA001-186:R84K', 'MPXV-USA_2022_MA001-072:V305G', 'MPXV-USA_2022_MA001-100:A433G',
                  'MPXV-USA_2022_MA001-162:S288F', 'MPXV-USA_2022_MA001-148:I119K', 'MPXV-USA_2022_MA001-171:T22K',
                  'MPXV-USA_2022_MA001-171:D25G', 'MPXV-USA_2022_MA001-143:C133F', 'MPXV-USA_2022_MA001-184:T22K',
                  'MPXV-USA_2022_MA001-169:A233G', 'MPXV-USA_2022_MA001-134:L263F', 'MPXV-USA_2022_MA001-187:Q188F',
                  'MPXV-USA_2022_MA001-077:R194P', 'MPXV-USA_2022_MA001-182:D1604K', 'MPXV-USA_2022_MA001-165:N95K',
                  'MPXV-USA_2022_MA001-096:T58K'},
                 {'OPG094:R194P', 'OPG164:I119K', 'OPG185:E121K', 'OPG193:A233G', 'OPG210:D1604K', 'OPG117:A433G',
                  'OPG089:V305G', 'OPG005:T22K', 'OPG016:R84K', 'OPG113:D723G', 'OPG015:Q188F', 'OPG185:S288F',
                  'OPG151:Q436P', 'OPG044:L29P', 'OPG193:L263F', 'OPG044:L142P'},
                 {'MPXV-USA_2022_MA001-162:E121K', 'MPXV-USA_2022_MA001-186:R84K', 'MPXV-USA_2022_MA001-072:V305G',
                  'MPXV-USA_2022_MA001-100:A433G', 'MPXV-USA_2022_MA001-162:S288F', 'MPXV-USA_2022_MA001-148:I119K',
                  'MPXV-USA_2022_MA001-184:T22K', 'MPXV-USA_2022_MA001-169:A233G', 'MPXV-USA_2022_MA001-187:Q188F',
                  'MPXV-USA_2022_MA001-077:R194P', 'MPXV-USA_2022_MA001-096:D723G', 'MPXV-USA_2022_MA001-182:D1604K',
                  'MPXV-USA_2022_MA001-028:L142P', 'MPXV-USA_2022_MA001-134:Q436P'}
                 ]
        source_samples = [67,10, 53, 14]
        cds_samples = [235, 115, 108, 64]
        for variantView in variantView_dfs_source:
            assert list(variantView.columns) == variantView_df_source_columns
        for variantView in variantView_dfs_cds:
            assert list(variantView.columns) == variantView_df_cds_columns

        for i, variantView_df in enumerate(variantView_dfs_source):
            assert sorted(list(set(variantView_df['variant.label']))) == source_variants[i]
        for i, variantView_df in enumerate(variantView_dfs_cds):
            assert sorted(list(set(variantView_df['variant.label']))) == cds_variants[i]

        for i, variantView_df in enumerate(variantView_dfs_source):
            assert (len(set(variantView_df['sample.name']))) == source_samples[i]
        for i, variantView_df in enumerate(variantView_dfs_cds):
            assert (len(set(variantView_df['sample.name']))) == cds_samples[i]

        for i, variantView_df in enumerate(variantView_dfs_source):
            assert set(variantView_df['element.type']) == {'source'}
        for i, variantView_df in enumerate(variantView_dfs_cds):
            assert set(variantView_df['element.type']) == {'cds'}

        for i, variantView_df in enumerate(variantView_dfs_cds):
            assert set(variantView_df['gene:variant'])== genes[i]

    def test_propertyView_df(self):
        propertyView_c = self.processed_df_dict["propertyView"]["complete"]
        propertyView_p = self.processed_df_dict["propertyView"]["partial"]
        propertyView_columns = ['sample.id', 'sample.name', 'COLLECTION_DATE', 'COUNTRY', 'GENOME_COMPLETENESS',
                                'GEO_LOCATION', 'HOST', 'IMPORTED', 'ISOLATE', 'LENGTH', 'RELEASE_DATE', 'SEQ_TECH']

        countries = self.country_entries_cds.keys()

        for propertyView in [propertyView_c, propertyView_p]:
            assert list(propertyView.columns) == propertyView_columns

        for country in countries:
            for i, propertyView in enumerate([propertyView_c, propertyView_p]):
                assert len(list(propertyView[propertyView["COUNTRY"] == country]["sample.id"])) == self.samples_dict_propertyView[country][i]

        for propertyView in [propertyView_c, propertyView_p]:
            assert not propertyView['COLLECTION_DATE'].isnull().values.any()
            assert not propertyView['RELEASE_DATE'].isnull().values.any()
            assert not propertyView['IMPORTED'].isnull().values.any()

        assert set(propertyView_c["GENOME_COMPLETENESS"]) == {"complete"}

        assert set(propertyView_p["GENOME_COMPLETENESS"]) == {"partial"}
