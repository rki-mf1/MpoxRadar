import unittest
import pandas as pd
from pandas._testing import assert_frame_equal
from datetime import date, timedelta
import os
from data import load_all_sql_files
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDbPreprocessing(unittest.TestCase):
    def setUp(self):
        self.db_name = "mpx_test_03"
        self.processed_df_dict = load_all_sql_files(self.db_name)
        self.countries = DbProperties.country_entries_cds_per_country.keys()

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
        world_dfs = {
            'complete':
                {
                    2: self.processed_df_dict["world_map"]["complete"][2],
                    4: self.processed_df_dict["world_map"]["complete"][4],
                },
            'partial':
                {
                    2: self.processed_df_dict["world_map"]["partial"][2],
                    4: self.processed_df_dict["world_map"]["partial"][4],
                }
        }
        for reference in [2, 4]:
            for completeness in ['complete', 'partial']:
                assert list(world_dfs[completeness][reference].columns) == DbProperties.world_df_columns
        # test nb entries per country
                for country in self.countries:
                    assert len(world_dfs[completeness][reference][world_dfs[completeness][reference]['COUNTRY'] == country]) \
                           == DbProperties.country_entries_cds_per_country[country][completeness][reference]
                    assert set(world_dfs[completeness][reference][world_dfs[completeness][reference]['COUNTRY'] == country]['variant.label']) \
                           == DbProperties.variants_cds_per_country[country][completeness][reference]
                    assert set(world_dfs[completeness][reference][world_dfs[completeness][reference]['COUNTRY'] == country]['gene:variant']) \
                           == DbProperties.gene_variants_cds_per_country[country][completeness][reference]

        # test different seq_techs per country
                    assert set(world_dfs[completeness][reference][world_dfs[completeness][reference]['COUNTRY'] == country]['SEQ_TECH'])\
                           == DbProperties.seq_techs_cds_per_country[country][completeness][reference]

                    assert set(world_dfs[completeness][reference][world_dfs[completeness][reference]['COUNTRY'] == country]['element.symbol']) \
                           == DbProperties.genes_per_country[country][completeness][reference]
                    samples = set([item for sublist in [
                        x.split(',')
                        for x in world_dfs[completeness][reference]
                        [world_dfs[completeness][reference]['COUNTRY'] == country]["sample_id_list"]]
                                   for item in sublist])
                    assert len(samples) == DbProperties.samples_dict_cds_per_country[country][completeness][reference]

    def test_variantView_df(self):
        variantView_dfs_cds = {
            'complete':
                {
                    2: self.processed_df_dict["variantView"]["complete"][2]['cds'],
                    4: self.processed_df_dict["variantView"]["complete"][4]['cds'],
                },
            'partial':
                {
                    2: self.processed_df_dict["variantView"]["partial"][2]['cds'],
                    4: self.processed_df_dict["variantView"]["partial"][4]['cds']
                }
        }
        variantView_dfs_source = {
            'complete':
                {
                    2: self.processed_df_dict["variantView"]["complete"][2]['source'],
                    4: self.processed_df_dict["variantView"]["complete"][4]['source'],
                },
            'partial':
                {
                    2: self.processed_df_dict["variantView"]["partial"][2]['source'],
                    4: self.processed_df_dict["variantView"]["partial"][4]['source']
                }
        }

        source_samples = {'complete': {2: 67, 4: 10}, 'partial': {2: 53, 4: 14}}
        cds_samples = {'complete': {2: 235, 4: 115}, 'partial': {2: 108, 4: 64}}
        for reference in [2, 4]:
            for completeness in ['complete', 'partial']:
                assert list(variantView_dfs_source[completeness][reference].columns) == DbProperties.variantView_df_source_columns
                assert list(variantView_dfs_cds[completeness][reference].columns) == DbProperties.variantView_df_cds_columns

                assert sorted(list(set(variantView_dfs_source[completeness][reference]['variant.label']))) == DbProperties.source_variants[completeness][reference]
                assert sorted(list(set(variantView_dfs_cds[completeness][reference]['variant.label']))) == DbProperties.cds_variants[completeness][reference]

                assert (len(set(variantView_dfs_source[completeness][reference]['sample.name']))) == source_samples[completeness][reference]
                assert (len(set(variantView_dfs_cds[completeness][reference]['sample.name']))) == cds_samples[completeness][reference]

                assert set(variantView_dfs_source[completeness][reference]['element.type']) == {'source'}
                assert set(variantView_dfs_cds[completeness][reference]['element.type']) == {'cds'}
                assert set(variantView_dfs_cds[completeness][reference]['gene:variant']) == DbProperties.cds_gene_variants[completeness][reference]

    def test_propertyView_df(self):
        propertyView_dfs = {'complete': self.processed_df_dict["propertyView"]["complete"],
                            'partial': self.processed_df_dict["propertyView"]["partial"]}

        assert set(propertyView_dfs['complete']["GENOME_COMPLETENESS"]) == {"complete"}
        assert set(propertyView_dfs['partial']["GENOME_COMPLETENESS"]) == {"partial"}

        for completeness in ['complete', 'partial']:
            assert list(propertyView_dfs[completeness].columns) == DbProperties.propertyView_columns
            assert not propertyView_dfs[completeness]['COLLECTION_DATE'].isnull().values.any()
            assert not propertyView_dfs[completeness]['RELEASE_DATE'].isnull().values.any()
            assert not propertyView_dfs[completeness]['IMPORTED'].isnull().values.any()

            for country in self.countries:
                assert len(list(propertyView_dfs[completeness][propertyView_dfs[completeness]["COUNTRY"] == country]["sample.id"])) == \
                           DbProperties.samples_dict_propertyView_per_country[country][completeness]
