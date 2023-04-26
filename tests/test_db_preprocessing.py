import os
import unittest
from datetime import date

from data import load_all_sql_files
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")


def to_date(d):
    return date.fromisoformat(d)


class TestDbPreprocessing(unittest.TestCase):
    """
    test database preprocessing, preprocessing functions in file data.py
    test dict structure, variantViews, propertyViews and world_dfs
    """

    @classmethod
    def setUpClass(cls):
        cls.db_name = "mpx_test_04"
        cls.processed_df_dict = load_all_sql_files(cls.db_name, test_db=True)
        cls.countries = DbProperties.country_entries_cds_per_country.keys()

    def test_df_dict_structure(self):
        assert list(self.processed_df_dict['propertyView'].keys()) == [
            "complete", "partial"]
        assert list(self.processed_df_dict['variantView'].keys()) == [
            "complete", "partial"]

        assert list(self.processed_df_dict["variantView"]["complete"].keys()) == [2, 4]
        assert list(self.processed_df_dict["variantView"]
                    ["complete"][2].keys()) == ['source', 'cds']
        assert list(self.processed_df_dict["variantView"]["partial"].keys()) == [2, 4]
        assert list(self.processed_df_dict["variantView"]
                    ["partial"][2].keys()) == ['source', 'cds']

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
                assert list(world_dfs[completeness]
                            [reference].columns) == DbProperties.world_df_columns
        # test entries per country
                for country in self.countries:
                    world_df = world_dfs[completeness][reference]
                    world_df_country = world_df[world_df['COUNTRY'] == country]

                    assert len(world_df_country) == \
                        DbProperties.country_entries_cds_per_country[country][completeness][reference]

                    assert set(world_df_country['variant.label']) == \
                        DbProperties.variants_cds_per_country[country][completeness][reference]

                    assert set(world_df_country['gene:variant']) == \
                        DbProperties.gene_variants_cds_per_country[country][completeness][reference]

                    assert set(world_df_country['SEQ_TECH']) == \
                        DbProperties.seq_techs_cds_per_country[country][completeness][reference]
                    assert set(world_df_country['element.symbol']) == \
                        DbProperties.genes_per_country[country][completeness][reference]

                    samples = set(
                        [
                            item for sublist in [
                                x.split(',')for x in world_df_country["sample_id_list"]
                            ]
                            for item in sublist
                        ]
                    )
                    assert len(samples) == \
                        DbProperties.samples_dict_cds_per_country[country][completeness][reference]

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

        source_samples = {'complete': {2: 51, 4: 7}, 'partial': {2: 29, 4: 8}}
        cds_samples = {'complete': {2: 162, 4: 57}, 'partial': {2: 69, 4: 27}}
        for reference in [2, 4]:
            for completeness in ['complete', 'partial']:
                variantView_source = variantView_dfs_source[completeness][reference]
                variantView_cds = variantView_dfs_cds[completeness][reference]
                assert list(variantView_source.columns) == \
                    DbProperties.variantView_df_source_columns
                assert list(variantView_cds.columns) == \
                    DbProperties.variantView_df_cds_columns

                assert sorted(list(set(variantView_source['variant.label']))) == \
                    DbProperties.source_variants[completeness][reference]
                assert sorted(list(set(variantView_cds['variant.label']))) == \
                    DbProperties.cds_variants[completeness][reference]

                assert (len(set(variantView_source['sample.name']))) == \
                    source_samples[completeness][reference]
                assert (len(set(variantView_cds['sample.name']))) == \
                    cds_samples[completeness][reference]

                assert set(variantView_source['element.type']) == {'source'}
                assert set(variantView_cds['element.type']) == {'cds'}

                assert set(variantView_cds['gene:variant']) == \
                    DbProperties.cds_gene_variants[completeness][reference]

    def test_propertyView_df(self):
        propertyView_dfs = {'complete': self.processed_df_dict["propertyView"]["complete"],
                            'partial': self.processed_df_dict["propertyView"]["partial"]}

        assert set(propertyView_dfs['complete']["GENOME_COMPLETENESS"]) == {"complete"}
        assert set(propertyView_dfs['partial']["GENOME_COMPLETENESS"]) == {"partial"}

        for completeness in ['complete', 'partial']:
            propertyView = propertyView_dfs[completeness]
            assert list(propertyView.columns) == DbProperties.propertyView_columns
            assert not propertyView['COLLECTION_DATE'].isnull().values.any()
            assert not propertyView['RELEASE_DATE'].isnull().values.any()
            assert not propertyView['IMPORTED'].isnull().values.any()

            for country in self.countries:
                propertyView_country = propertyView[propertyView["COUNTRY"] == country]
                assert len(list(propertyView_country["sample.id"])) == \
                    DbProperties.samples_dict_propertyView_per_country[country][completeness]
