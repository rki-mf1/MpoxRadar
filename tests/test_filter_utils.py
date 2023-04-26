import os
import unittest
from datetime import datetime

import pandas as pd
from dash.html import Span
from pandas._testing import assert_frame_equal
from parameterized import parameterized

from data import load_all_sql_files
from pages.utils import get_color_dict
from pages.utils_filters import (filter_by_seqtech_country_gene_and_merge,
                                 filter_propertyView_by_seqtech_and_country,
                                 filter_propertyView_by_seqtech_and_gene,
                                 filter_variantView_by_genes,
                                 get_all_frequency_sorted_countries_by_filters,
                                 get_all_frequency_sorted_seqtech,
                                 get_all_gene_dict, get_all_references,
                                 get_frequency_sorted_cds_mutation_by_filters,
                                 get_frequency_sorted_mutation_by_df,
                                 get_frequency_sorted_seq_techs_by_filters,
                                 get_sample_and_seqtech_df,
                                 select_propertyView_dfs,
                                 select_variantView_dfs,
                                 sort_and_extract_by_col)
from tests.test_db_properties import DbProperties

DB_DUMP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "sql_dumps")

test_params = [
    ["cds", "complete"],
    ["cds", "partial"],
    ["source", "complete"],
    ["source", "partial"],
]
test_params_completeness = [
    ["complete"], ["partial"]
]


class TestFilterUtils(unittest.TestCase):
    """
    test functions or utils_filters
    """

    @classmethod
    def setUpClass(cls):
        cls.db_name = "mpx_test_04"
        cls.processed_df_dict = load_all_sql_files(cls.db_name, test_db=True)
        cls.countries = DbProperties.country_entries_cds_per_country.keys()
        cls.color_dict = get_color_dict(cls.processed_df_dict)
        cls.seqtech_value = ['Illumina']
        cls.gene_value_cds = ["OPG005", "OPG197", "OPG151"]
        cls.gene_value_source = ["no_gene_values"]
        cls.country_value = ["Germany"]

    @parameterized.expand(test_params)
    def test_select_variantView_dfs(self, aa_nt_radio, complete_partial_radio):
        """
        corresponding sql queries:
        select count(*) from variantView where `reference.id`=2 AND `element.type`='cds';
            result: 329 (partial + complete)
        select count(*) from variantView where `reference.id`=2 AND `element.type`='source';
            result: 80 (partial + complete)
        """
        result_dict = {
            'cds':
            {
                'complete': 220,
                'partial': 109,
                'cols':
                [
                    'sample.id', 'sample.name', 'reference.id', 'reference.accession',
                    'element.symbol', 'element.type', 'variant.id', 'variant.label', 'gene:variant'
                ]
            },
            'source': {
                'complete': 51,
                'partial': 29,
                'cols':
                [
                    'sample.id', 'sample.name', 'reference.id', 'reference.accession',
                    'element.symbol', 'element.type', 'variant.id', 'variant.label'
                ]
            }
        }

        variantView_dfs = select_variantView_dfs(
            self.processed_df_dict, complete_partial_radio, 2, aa_nt_radio)
        for i, df in enumerate(variantView_dfs):
            self.assertListEqual(list(df.columns), result_dict[aa_nt_radio]['cols'])
            if i == 0:
                assert len(df) == result_dict[aa_nt_radio]['complete']
            elif i == 1:
                assert len(df) == result_dict[aa_nt_radio]['partial']

    @parameterized.expand(test_params_completeness)
    def test_select_propertyView_dfs(self, complete_partial_radio):
        """
        corresponding sql queries:
        select count(*) from propertyView  where value_text="complete";
        result: 162
        select count(*) from propertyView  where value_text="complete";
        result: 69
        """
        result_dict = {'complete': 162,
                       'cols': [
                           'sample.id', 'sample.name', 'COLLECTION_DATE', 'COUNTRY',
                           'GENOME_COMPLETENESS', 'GEO_LOCATION', 'HOST', 'IMPORTED', 'ISOLATE',
                           'LENGTH', 'RELEASE_DATE', 'SEQ_TECH'
                       ],
                       'partial': 69}
        propertyView_dfs = select_propertyView_dfs(
            self.processed_df_dict, complete_partial_radio)
        for i, df in enumerate(propertyView_dfs):
            self.assertListEqual(list(df.columns), result_dict['cols'])
            if i == 0:
                assert len(df) == result_dict['complete']
            elif i == 1:
                assert len(df) == result_dict['partial']

    @parameterized.expand(test_params_completeness)
    def test_sort_and_extract_by_col(self, complete_partial_radio):
        """
        corresponding SQL queries:
        select distinct(value_text) from propertyView  where `property.name`="SEQ_TECH" AND
        `sample.id` in (SELECT `sample.id` from propertyView  where value_text='partial' AND
        `property.name`="GENOME_COMPLETENESS");
        select distinct(value_text) from propertyView  where `property.name`="COUNTRY" AND
        `sample.id` in (SELECT `sample.id` from propertyView  where value_text='partial' AND
        `property.name`="GENOME_COMPLETENESS");
        select distinct(value_text) from propertyView  where `property.name`="SEQ_TECH" AND
        `sample.id` in (SELECT `sample.id` from propertyView  where value_text='complete' AND
        `property.name`="GENOME_COMPLETENESS");
        select distinct(value_text) from propertyView  where `property.name`="COUNTRY" AND
        `sample.id` in (SELECT `sample.id` from propertyView  where value_text='complete' AND
        `property.name`="GENOME_COMPLETENESS");
        """
        result_dict = {
            "SEQ_TECH": {
                'complete': ['Illumina', 'Nanopore'], 'partial': ['Illumina', 'Nanopore']
            },
            "COUNTRY": {
                'complete': ['Germany', 'USA', 'Egypt'], 'partial': ['Germany', 'USA']
            }
        }
        propertyView = self.processed_df_dict['propertyView'][complete_partial_radio]
        for col in ["SEQ_TECH", "COUNTRY"]:
            sorted_list = sort_and_extract_by_col(propertyView, col)
            self.assertListEqual(sorted_list, result_dict[col][complete_partial_radio])

    def test_get_all_references(self):
        """
        corresponding SQL query:
        SELECT DISTINCT `reference.id`,`reference.accession` from variantView;
        """
        references_in_test_db = [
            {'label': 'NC_063383.1', 'value': 2, 'disabled': False},
            {'label': 'ON563414.3', 'value': 4, 'disabled': False}
        ]
        references = get_all_references(self.processed_df_dict)
        for i, ref in enumerate(references):
            self.assertDictEqual(ref, references_in_test_db[i])

    @parameterized.expand(test_params_completeness)
    def test_get_all_gene_dict(self, complete_partial_radio):
        """
        corresponding SQL queries:
        query for partial:
        SELECT DISTINCT `element.symbol` from variantView WHERE `reference.id`=2 AND
        `element.type`='cds';
        query for complete:
        SELECT DISTINCT `element.symbol` from variantView LEFT JOIN propertyView
        ON (variantView.`sample.id`=propertyView.`sample.id`) WHERE `reference.id`=2 AND
        `element.type`='cds' AND value_text='complete' and `property.name`="GENOME_COMPLETENESS";
        """
        complete_options = [
            {'label': Span(children='OPG005', style={'color': '#2E91E5'}),
             'value': 'OPG005'},
            {'label': Span(children='OPG015', style={
                'color': '#E15F99'}), 'value': 'OPG015'},
            {'label': Span(children='OPG016', style={
                'color': '#1CA71C'}), 'value': 'OPG016'},
            {'label': Span(children='OPG094', style={
                'color': '#FB0D0D'}), 'value': 'OPG094'},
            {'label': Span(children='OPG113', style={
                'color': '#DA16FF'}), 'value': 'OPG113'},
            {'label': Span(children='OPG151', style={
                'color': '#222A2A'}), 'value': 'OPG151'},
            {'label': Span(children='OPG159', style={
                'color': '#B68100'}), 'value': 'OPG159'},
            {'label': Span(children='OPG193', style={
                'color': '#750D86'}), 'value': 'OPG193'},
            {'label': Span(children='OPG197', style={'color': '#EB663B'}),
             'value': 'OPG197'}
        ]
        partial_options = complete_options.copy()
        partial_options.insert(
            7, {'label': Span(children='OPG185', style={
                              'color': '#750D86'}), 'value': 'OPG185'}
        )
        result_d = {'complete': complete_options,
                    "partial": partial_options, }
        gene_dict = get_all_gene_dict(
            self.processed_df_dict, 2, complete_partial_radio, self.color_dict)
        for i, elem in enumerate(result_d[complete_partial_radio]):
            assert gene_dict[i]['value'] == elem['value']

    def test_get_all_frequency_sorted_seqtech(self):
        """
        corresponding SQL query:
        SELECT value_text, COUNT(DISTINCT `sample.id`) AS COUNT from propertyView
        WHERE `property.name`="SEQ_TECH" GROUP BY value_text;
        """
        sorted_seqtech_dict_t = [
            {'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
            {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': False}
        ]
        sorted_seqtech_dict = get_all_frequency_sorted_seqtech(self.processed_df_dict)
        for i, elem in enumerate(sorted_seqtech_dict):
            assert sorted_seqtech_dict_t[i]['label'] == elem['label']

    @parameterized.expand(test_params_completeness)
    def test_get_all_frequency_sorted_countries_by_filters(self, complete_partial_radio):
        """
        corresponding SQL queries:
        query for partial:
        SELECT value_text, COUNT(DISTINCT propertyView.`sample.id`) AS COUNT from variantView
        LEFT JOIN propertyView ON (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `property.name`="COUNTRY" AND `element.type`="cds" AND `element.symbol`
        IN ("OPG005","OPG197","OPG151") GROUP BY value_text;
        query for complete:
        SELECT value_text, COUNT(DISTINCT propertyView.`sample.id`) AS COUNT from variantView
        LEFT JOIN propertyView ON (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `property.name`="COUNTRY" AND `element.type`="cds" AND `element.symbol`
        IN ("OPG005","OPG197","OPG151") AND propertyView.`sample.id`
        IN (SELECT `sample.id` from propertyView  where value_text='complete'
        AND `property.name`="GENOME_COMPLETENESS") GROUP BY value_text;
        """
        correct_country_options = {
            'complete': [
                {'label': 'Germany', 'value': 'Germany', 'disabled': False},
                {'label': 'USA', 'value': 'USA', 'disabled': False},
            ],
            'partial': [
                {'label': 'USA', 'value': 'USA', 'disabled': False},
                {'label': 'Germany', 'value': 'Germany', 'disabled': False}
            ]
        }
        country_options = get_all_frequency_sorted_countries_by_filters(
            self.processed_df_dict,
            ['Illumina', 'Nanopore'],
            complete_partial_radio,
            2,
            self.gene_value_cds,
            aa_nt='cds',
            min_date=None
        )
        for i, country_option in enumerate(country_options):
            self.assertDictEqual(
                country_option, correct_country_options[complete_partial_radio][i]
            )

    def test_filter_propertyView_by_seqtech_and_country(self):
        """
        corresponding SQL query:
        SELECT `sample.id` FROM propertyView WHERE `sample.id` IN
        (SELECT `sample.id` FROM propertyView WHERE  value_text in ("Illumina", "Nanopore")
        AND `property.name`="SEQ_TECH")  INTERSECT
        SELECT `sample.id` FROM propertyView WHERE `sample.id` IN (SELECT `sample.id` FROM
        propertyView WHERE  value_text="USA" AND `property.name`="COUNTRY");
        """
        propertyView = self.processed_df_dict['propertyView']['complete']
        df = filter_propertyView_by_seqtech_and_country(
            propertyView, ["Illumina"], ["USA"])
        assert len(df) == 3
        assert set(df["COUNTRY"]) == {"USA"}
        assert set(df["SEQ_TECH"]) == {'Illumina'}

    @ parameterized.expand(["source", "cds"])
    def test_filter_propertyView_by_seqtech_and_gene(self, aa_nt_radio):
        """
        corresponding SQL queries:
        SELECT propertyView.`sample.id` FROM variantView LEFT JOIN propertyView ON
        (variantView.`sample.id`=propertyView.`sample.id`) where `element.type`="cds" AND
        `element.symbol` in ("OPG005","OPG197","OPG151") AND value_text="Illumina" AND
        `property.name`="SEQ_TECH"
        ... INTERSECT SELECT `sample.id` FROM propertyView WHERE  value_date>="2022-08-01" AND
        `property.name`="COLLECTION_DATE";

        SELECT propertyView.`sample.id` FROM variantView LEFT JOIN propertyView ON
        (variantView.`sample.id`=propertyView.`sample.id`) where `element.type`="source"
        AND value_text="Illumina" AND `property.name`="SEQ_TECH" AND `reference.id`=2
        INTERSECT SELECT `sample.id` FROM propertyView WHERE value_text="complete" AND
        `property.name`="GENOME_COMPLETENESS";
        ...
        INTERSECT SELECT `sample.id` FROM propertyView WHERE  value_date>="2022-08-01"
        AND `property.name`="COLLECTION_DATE";

        SELECT DISTINCT value_date FROM propertyView WHERE `property.name`="COLLECTION_DATE" AND
        `sample.id` in (235, 406, 591, 682, 712);
        """
        result_d = {
            "cds":
            {
                "sample_ids_min": [712],
                "sample_ids": [235, 406, 591, 682, 712],
                "dates_min": [datetime.strptime("2022-09-01", "%Y-%m-%d").date()],
                "dates": [datetime.strptime("2022-07-01", "%Y-%m-%d").date(),
                          datetime.strptime("2022-09-01", "%Y-%m-%d").date()]
            },
            "source":
            {
                "sample_ids_min": [
                    53, 206, 276, 348, 380, 416, 556, 578, 584, 588, 676, 677, 705, 772, 778, 820,
                    836, 922, 932, 1083, 1095, 1169, 1181, 1184, 161472
                ],
                "sample_ids": [
                    53, 206, 235, 248, 261, 270, 276, 348, 380, 416, 434, 545, 551, 556, 578, 584,
                    588, 640, 676, 677, 693, 704, 705, 725, 765, 771, 772, 778, 820, 836, 843, 862,
                    922, 929, 932, 961, 967, 1044, 1056, 1083, 1087, 1095, 1169, 1181, 1184, 161472
                ],
                "dates_min": [datetime.strptime("2022-08-01", "%Y-%m-%d").date(),
                              datetime.strptime("2022-09-01", "%Y-%m-%d").date()],
                "dates": [datetime.strptime("2022-07-01", "%Y-%m-%d").date(),
                          datetime.strptime("2022-08-01", "%Y-%m-%d").date(),
                          datetime.strptime("2022-09-01", "%Y-%m-%d").date()],
            }
        }

        propertyView = self.processed_df_dict['propertyView']['complete']
        variantView = self.processed_df_dict['variantView']['complete'][2][aa_nt_radio]
        gene_value = self.gene_value_cds if aa_nt_radio == "cds" else self.gene_value_source
        min_date = "2022-08-01"
        filtered_propertyView = filter_propertyView_by_seqtech_and_gene(
            variantView,
            propertyView,
            self.seqtech_value,
            gene_value,
            aa_nt_radio,
            min_date
        )
        self.assertListEqual(
            list(filtered_propertyView['sample.id']),
            result_d[aa_nt_radio]["sample_ids_min"]
        )
        self.assertListEqual(
            sorted(list(set(filtered_propertyView['COLLECTION_DATE']))),
            result_d[aa_nt_radio]["dates_min"]
        )

        filtered_propertyView = filter_propertyView_by_seqtech_and_gene(
            variantView,
            propertyView,
            self.seqtech_value,
            gene_value,
            aa_nt_radio,
        )
        self.assertListEqual(
            list(filtered_propertyView['sample.id']),
            result_d[aa_nt_radio]["sample_ids"]
        )
        self.assertListEqual(
            sorted(list(set(filtered_propertyView['COLLECTION_DATE']))),
            result_d[aa_nt_radio]["dates"]
        )

    @ parameterized.expand(["complete", "partial"])
    def test_filter_variantView_by_genes(self, complete_partial_radio):
        """
        corresponding SQL query:
        SELECT DISTINCT propertyView.`sample.id`, propertyView.`sample.name`,`reference.id`,
        `reference.accession`, `element.symbol`, `element.type`, `variant.id`, `variant.label`
        FROM variantView  LEFT JOIN propertyView ON
        (variantView.`sample.id`=propertyView.`sample.id`) WHERE `element.type`="cds"
        AND `element.symbol` in ("OPG005","OPG197","OPG151") AND `reference.id`=2
        AND propertyView.`sample.id` in (SELECT `sample.id` from propertyView
         WHERE value_text='complete' and `property.name`="GENOME_COMPLETENESS");
        """
        cols = [
            'sample.id', 'sample.name', 'reference.id', 'reference.accession',
            'element.symbol', 'element.type', 'variant.id', 'variant.label', 'gene:variant'
        ]
        df_dict = {
            'complete':
            [
                [805, 'OP536740.2', 2, 'NC_063383.1', 'OPG005',
                    'cds', 19106, 'T22K', 'OPG005:T22K'],
                [406, 'OP626112.1', 2, 'NC_063383.1', 'OPG197',
                    'cds', 4967, 'D25G', 'OPG197:D25G'],
                [235, 'OP626118.1', 2, 'NC_063383.1', 'OPG197',
                    'cds', 4967, 'D25G', 'OPG197:D25G'],
                [712, 'OP484666.1', 2, 'NC_063383.1', 'OPG197',
                    'cds', 43166, 'T22K', 'OPG197:T22K'],
                [591, 'OP626116.1', 2, 'NC_063383.1', 'OPG151',
                    'cds', 90600, 'L263F', 'OPG151:L263F'],
                [785, 'OP536738.2', 2, 'NC_063383.1', 'OPG005',
                    'cds', 19106, 'T22K', 'OPG005:T22K'],
                [682, 'OP626114.1', 2, 'NC_063383.1', 'OPG197',
                    'cds', 4967, 'D25G', 'OPG197:D25G'],
                [595, 'OP536745.2', 2, 'NC_063383.1', 'OPG005',
                    'cds', 19106, 'T22K', 'OPG005:T22K']
            ],
            'partial':
            [
                [159233, 'OP536668.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [159233, 'OP536668.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [159562, 'OP536734.1', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [160376, 'OP536671.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [161887, 'OP536719.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [161887, 'OP536719.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [162340, 'OP536682.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [162438, 'OP536672.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [160574, 'OP536678.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [160574, 'OP536678.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [161445, 'OP536736.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [160314, 'OP536676.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [161574, 'OP536730.2', 2, 'NC_063383.1', 'OPG151',
                 'cds', 9958, 'Q436P', 'OPG151:Q436P'],
                [161574, 'OP536730.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [159281, 'OP536677.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [159157, 'OP536715.2', 2, 'NC_063383.1', 'OPG005',
                 'cds', 19106, 'T22K', 'OPG005:T22K'],
                [161639, 'OP536669.1', 2, 'NC_063383.1',
                 'OPG005', 'cds', 19106, 'T22K', 'OPG005:T22K']
            ]
        }
        variantView = self.processed_df_dict['variantView'][complete_partial_radio][2]['cds']
        df = filter_variantView_by_genes(variantView, self.gene_value_cds)
        correct_df = pd.DataFrame(df_dict[complete_partial_radio], columns=cols)
        assert_frame_equal(
            df,
            correct_df,
            check_dtype=False
        )

    @ parameterized.expand(test_params_completeness)
    def test_filter_by_seqtech_country_gene_and_merge(self, complete_partial_radio):
        """
        corresponding SQL query:
        SELECT DISTINCT propertyView.`sample.id`, `variant.label`, `element.symbol` FROM
        variantView LEFT JOIN propertyView ON (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `element.type`="cds" AND `element.symbol` IN ("OPG005","OPG197","OPG151") AND
        `reference.id`=2 AND propertyView.`sample.id` IN
        (SELECT `sample.id` from propertyView  WHERE value_text='complete'
        AND `property.name`="GENOME_COMPLETENESS"
            INTERSECT
        SELECT `sample.id` from propertyView  WHERE value_text='Illumina'
        AND `property.name`="SEQ_TECH"
            INTERSECT
        SELECT `sample.id` from propertyView  WHERE value_text='Germany'
        AND `property.name`="COUNTRY");
        """
        correct_df_dict = {
            'complete': pd.DataFrame(
                [
                    [235, 'D25G', 'OPG197:D25G', 'OPG197'],
                    [406, 'D25G', 'OPG197:D25G', 'OPG197'],
                    [591, 'L263F', 'OPG151:L263F', 'OPG151'],
                    [682, 'D25G', 'OPG197:D25G', 'OPG197'],
                    [712, 'T22K', 'OPG197:T22K', 'OPG197']
                ],
                columns=['sample.id', 'variant.label',
                         'gene:variant', 'element.symbol']
            ),
            'partial': pd.DataFrame(
                columns=['sample.id', 'variant.label', 'gene:variant', 'element.symbol']
            )
        }
        df = filter_by_seqtech_country_gene_and_merge(
            self.processed_df_dict["propertyView"][complete_partial_radio],
            self.processed_df_dict['variantView'][complete_partial_radio][2]['cds'],
            self.seqtech_value,
            self.country_value,
            self.gene_value_cds
        )
        assert_frame_equal(
            df, correct_df_dict[complete_partial_radio], check_dtype=False
        )

    @ parameterized.expand(test_params_completeness)
    def test_get_frequency_sorted_cds_mutation_by_filters(self, complete_partial_radio):
        """
        corresponding SQL queries:
        SELECT DISTINCT `variant.label`, `element.symbol`, COUNT(DISTINCT propertyView.`sample.id`) 
        AS Count FROM variantView LEFT JOIN propertyView ON 
        (variantView.`sample.id`=propertyView.`sample.id`) WHERE `element.type`="cds" AND 
        `element.symbol` in ("OPG005", "OPG151") AND `reference.id`=2 AND propertyView.`sample.id` 
        IN (SELECT `sample.id` from propertyView  WHERE value_text='complete' AND 
        `property.name`="GENOME_COMPLETENESS" INTERSECT
        SELECT `sample.id` from propertyView  WHERE value_text IN ('Illumina', 'Nanopore')  
        AND `property.name`="SEQ_TECH" INTERSECT
        SELECT `sample.id` from propertyView  WHERE value_text IN ('USA', 'Germany') AND 
        `property.name`="COUNTRY") GROUP BY `variant.label`,`element.symbol` ORDER BY Count DESC;

        SELECT DISTINCT `variant.label`, `element.symbol`, COUNT(DISTINCT propertyView.`sample.id`) 
        AS Count FROM variantView LEFT JOIN propertyView ON 
        (variantView.`sample.id`=propertyView.`sample.id`) WHERE `element.type`="cds" AND 
        `element.symbol` in ("OPG005","OPG151") AND `reference.id`=2 AND propertyView.`sample.id` IN
        (SELECT `sample.id` from propertyView  WHERE value_text in ('Illumina', 'Nanopore') 
        AND `property.name`="SEQ_TECH" INTERSECT
        SELECT `sample.id` from propertyView  WHERE value_text in ('USA', 'Germany') AND 
        `property.name`="COUNTRY") GROUP BY `variant.label`,`element.symbol` ORDER BY Count DESC;

        """
        correct_df_dict = {
            'complete': {
                'options': [
                    {'label': Span(children='OPG005:T22K', style={'color': '#2E91E5'}),
                     'value': 'OPG005:T22K', 'freq': 3},
                    {'label': Span(children='OPG151:L263F', style={'color': '#222A2A'}),
                     'value': 'OPG151:L263F', 'freq': 1},
                ],
                'options_2': [
                    {'label': Span(children='OPG005:T22K', style={'color': '#2E91E5'}),
                     'value': 'OPG005:T22K', 'freq': 3}],
                'freq': 3
            },
            'partial': {
                'options': [
                    {'label': Span(children='OPG005:T22K', style={'color': '#2E91E5'}),
                     'value': 'OPG005:T22K', 'freq': 13},
                    {'label': Span(children='OPG151:Q436P', style={'color': '#222A2A'}),
                     'value': 'OPG151:Q436P', 'freq': 7},
                    {'label': Span(children='OPG151:L263F', style={'color': '#222A2A'}),
                     'value': 'OPG151:L263F', 'freq': 1},
                ],
                'options_2': [
                    {'label': Span(children='OPG005:T22K', style={'color': '#2E91E5'}),
                     'value': 'OPG005:T22K', 'freq': 13},
                    {'label': Span(children='OPG151:Q436P', style={'color': '#222A2A'}),
                     'value': 'OPG151:Q436P', 'freq': 7}
                ],
                'freq': 13
            },
        }
        sorted_mutation_options, max_nb_freq, min_nb_freq = get_frequency_sorted_cds_mutation_by_filters(
            self.processed_df_dict,
            ['Illumina', 'Nanopore'],
            ['USA', 'Germany'],
            ["OPG005", "OPG151"],
            complete_partial_radio,
            2,
            self.color_dict,
            min_nb_freq=1
        )
        assert max_nb_freq == correct_df_dict[complete_partial_radio]['freq']
        for i, option in enumerate(sorted_mutation_options):
            assert option['value'] == correct_df_dict[complete_partial_radio]['options'][i]['value']
            assert option['freq'] == correct_df_dict[complete_partial_radio]['options'][i]['freq']

        sorted_mutation_options_2, max_nb_freq_2, min_nb_freq = get_frequency_sorted_cds_mutation_by_filters(
            self.processed_df_dict,
            ['Illumina', 'Nanopore'],
            ['USA', 'Germany'],
            ["OPG005", "OPG151"],
            complete_partial_radio,
            2,
            self.color_dict,
            min_nb_freq=3
        )
        assert max_nb_freq_2 == correct_df_dict[complete_partial_radio]['freq']
        for i, option in enumerate(sorted_mutation_options_2):
            assert option['value'] == correct_df_dict[complete_partial_radio]['options_2'][i]['value']
            assert option['freq'] == correct_df_dict[complete_partial_radio]['options_2'][i]['freq']

    @ parameterized.expand(
        [
            (["gene:variant", "element.symbol"], 'cds'),
            (["variant.label"], 'source')
        ]
    )
    def test_get_frequency_sorted_mutation_by_df(self, variant_columns, mut_type):
        """
        corresponding SQL query:
        SELECT DISTINCT `variant.label`, `element.symbol`, COUNT(DISTINCT propertyView.`sample.id`)
        AS Count FROM variantView LEFT JOIN propertyView ON
        (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `element.type`="cds" AND `reference.id`=2 AND propertyView.`sample.id` IN
        (SELECT `sample.id` from propertyView  WHERE value_text='complete' AND
        `property.name`="GENOME_COMPLETENESS") GROUP BY `variant.label`,`element.symbol`
        ORDER BY Count DESC;
        """
        option_dict = {'cds': {'options': [
            {'label': Span(children='OPG193:L263F', style={'color': '#EB663B'}),
             'value': 'OPG193:L263F', 'freq': 162},
            {'label': Span(children='OPG094:R194P', style={'color': '#FB0D0D'}),
             'value': 'OPG094:R194P', 'freq': 32},
            {'label': Span(children='OPG015:Q188F', style={'color': '#E15F99'}),
             'value': 'OPG015:Q188F', 'freq': 8},
            {'label': Span(children='OPG016:R84K', style={'color': '#1CA71C'}),
             'value': 'OPG016:R84K', 'freq': 7},
            {'label': Span(children='OPG005:T22K', style={'color': '#2E91E5'}),
             'value': 'OPG005:T22K', 'freq': 3},
            {'label': Span(children='OPG197:D25G', style={'color': '#511CFB'}),
             'value': 'OPG197:D25G', 'freq': 3},
        ],
            "max_freq": 162},
            'source': {'options': [
                {'label': 'G74360A', 'value': 'G74360A', 'freq': 32},
                {'label': 'C70780T', 'value': 'C70780T', 'freq': 11},
                {'label': 'del:150586-150602', 'value': 'del:150586-150602', 'freq': 5},
                {'label': 'G8020A', 'value': 'G8020A', 'freq': 2},
            ],
                "max_freq": 32}
        }
        merged_df = pd.merge(
            self.processed_df_dict['propertyView']['complete'],
            self.processed_df_dict['variantView']['complete'][2][mut_type],
            how="inner",
            on="sample.id")
        sorted_mutation_options, max_freq_nb, min_nb_freq = get_frequency_sorted_mutation_by_df(
            merged_df,
            self.color_dict,
            variant_columns,
            mut_type,
            min_nb_freq=2)
        assert max_freq_nb == option_dict[mut_type]["max_freq"]
        for i, option in enumerate(sorted_mutation_options):
            assert option['value'] == option_dict[mut_type]["options"][i]['value']
            assert option['freq'] == option_dict[mut_type]["options"][i]['freq']

    @ parameterized.expand(test_params)
    def test_get_sample_and_seqtech_df(self, aa_nt_radio, complete_partial_radio):
        """
        corresponding SQL queries:
        SELECT DISTINCT  propertyView.`sample.id` FROM variantView LEFT JOIN propertyView
        ON (variantView.`sample.id`=propertyView.`sample.id`)WHERE `element.type`="cds" AND
        `element.symbol` in ("OPG005", "OPG197", "OPG151") AND `reference.id`=2 AND
         propertyView.`sample.id` IN (SELECT `sample.id` from propertyView  WHERE
         value_text='complete' and `property.name`="GENOME_COMPLETENESS" INTERSECT
        SELECT `sample.id` FROM propertyView WHERE value_date>="2022-08-01" AND
        `property.name`="COLLECTION_DATE") ORDER BY propertyView.`sample.id` ASC;

        SELECT DISTINCT  propertyView.`sample.id` FROM variantView LEFT JOIN propertyView ON 
        (variantView.`sample.id`=propertyView.`sample.id`) WHERE `element.type`="source" AND 
        `reference.id`=2 AND propertyView.`sample.id` IN (SELECT `sample.id` FROM propertyView WHERE
        value_date>="2022-08-01" AND `property.name`="COLLECTION_DATE") ORDER BY
        propertyView.`sample.id` ASC;
         ...
        """
        cols = ['sample.id', 'SEQ_TECH']
        correct_samples = {
            'complete': {
                'cds': [235, 406, 591, 595, 682, 712, 785, 805],
                'cds_min': [712],
                'source': [
                    53, 206, 235, 248, 261, 270, 276, 348, 355, 380, 389, 416, 434, 545, 551, 556,
                    578, 584, 588, 595, 640, 676, 677, 693, 704, 705, 725, 765, 771, 772, 778, 785,
                    805, 820, 836, 843, 862, 922, 929, 932, 961, 967, 1044, 1056, 1083, 1087, 1095,
                    1169, 1181, 1184, 161472
                ],
                'source_min': [
                    53, 206, 276, 348, 380, 416, 556, 578, 584, 588, 676, 677, 705, 772, 778, 820,
                    836, 922, 932, 1083, 1095, 1169, 1181, 1184, 161472
                ]
            },

            'partial': {
                'cds': [
                    159157, 159233, 159281, 159562, 160314, 160376, 160574, 161445, 161574, 161639,
                    161887, 162340, 162438],
                'cds_min': [],
                'source': [
                    159079, 159131, 159157, 159187, 159233, 159281, 159355, 159562, 159567, 160033,
                    160041, 160102, 160314, 160317, 160319, 160376, 160498, 160574, 160603, 161337,
                    161445, 161500, 161574, 161639, 161745, 161887, 162340, 162438, 162900
                ],
                'source_min': [159079, 159187, 159355, 160102, 160319, 161337, 161500]
            }
        }
        correct_seq_techs = {
            'cds': {
                'complete': ['Illumina', 'Nanopore'], 'partial': ['Nanopore'],
                'complete_min': ['Illumina'], 'partial_min': []
            },
            'source': {
                'complete': ['Illumina', 'Nanopore'], 'partial': ['Illumina', 'Nanopore'],
                'complete_min': ['Illumina'], 'partial_min': ['Illumina', 'Nanopore'],
            },
        }
        propertyView = self.processed_df_dict['propertyView'][complete_partial_radio]
        variantView = self.processed_df_dict['variantView'][complete_partial_radio][2][aa_nt_radio]
        gene_value = ["OPG005", "OPG197",
                      "OPG151"] if aa_nt_radio == "cds" else ["no_gene_values"]
        min_date = "2022-08-01"
        df_min = get_sample_and_seqtech_df(
            variantView, propertyView, aa_nt_radio, gene_value, min_date)
        self.assertListEqual(
            list(df_min.columns),
            cols
        )
        self.assertListEqual(
            sorted(list(set(df_min['sample.id']))),
            correct_samples[complete_partial_radio][f"{aa_nt_radio}_min"]
        )
        self.assertListEqual(
            sorted(list(set(df_min['SEQ_TECH']))),
            correct_seq_techs[aa_nt_radio][f"{complete_partial_radio}_min"]
        )

        df = get_sample_and_seqtech_df(
            variantView, propertyView, aa_nt_radio,
            gene_value
        )
        self.assertListEqual(
            list(df.columns),
            cols
        )
        self.assertListEqual(
            sorted(list(set(df['sample.id']))),
            correct_samples[complete_partial_radio][aa_nt_radio]
        )
        self.assertListEqual(
            sorted(list(set(df['SEQ_TECH']))),
            correct_seq_techs[aa_nt_radio][complete_partial_radio]
        )

    @ parameterized.expand(test_params)
    def test_get_frequency_sorted_seq_techs_by_filters(self, aa_nt_radio, complete_partial_radio):
        """
        corresponding SQL queries:
        SELECT DISTINCT `value_text`, COUNT(DISTINCT propertyView.`sample.id`) AS Count FROM
        variantView LEFT JOIN propertyView ON (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `element.type`="cds" AND `element.symbol` IN ("OPG005", "OPG197", "OPG151") AND
        `reference.id`=2 AND `property.name`="SEQ_TECH" AND propertyView.`sample.id` IN
        ( SELECT `sample.id` FROM propertyView WHERE  value_date>="2022-08-01" AND
        `property.name`="COLLECTION_DATE" INTERSECT
        SELECT `sample.id` from propertyView  where value_text='complete' AND
        `property.name`="GENOME_COMPLETENESS") GROUP BY `value_text` ORDER BY Count DESC;

        SELECT DISTINCT `value_text`, COUNT(DISTINCT propertyView.`sample.id`) AS Count FROM
        variantView LEFT JOIN propertyView ON (variantView.`sample.id`=propertyView.`sample.id`)
        WHERE `element.type`="cds"  AND `element.symbol` IN ("OPG005", "OPG197", "OPG151") AND
        `reference.id`=2 AND `property.name`="SEQ_TECH"  GROUP BY `value_text` ORDER BY Count DESC;

        ...
        """

        min_date = "2022-08-01"
        correct_tech_options = {
            'complete': {
                'cds':
                [
                    {'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
                    {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': False}],
                'source': [{'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
                           {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': False}],
                'cds_min': [{'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
                            {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': True}],
                'source_min': [
                    {'label': 'Illumina',
                     'value': 'Illumina', 'disabled': False},
                    {'label': 'Nanopore',
                     'value': 'Nanopore', 'disabled': True}
                ]
            },
            'partial': {
                'cds': [
                    {'label': 'Nanopore', 'value': 'Nanopore',
                     'disabled': False},
                    {'label': 'Illumina', 'value': 'Illumina', 'disabled': False}],
                'source': [{'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
                           {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': False}],
                'cds_min': [{'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
                            {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': True}],
                'source_min': [
                    {'label': 'Illumina',
                     'value': 'Illumina', 'disabled': False},
                    {'label': 'Nanopore',
                     'value': 'Nanopore', 'disabled': False}
                ]
            }
        }
        tech_options = [
            {'label': 'Illumina', 'value': 'Illumina', 'disabled': False},
            {'label': 'Nanopore', 'value': 'Nanopore', 'disabled': False}
        ]
        gene_value = self.gene_value_cds if aa_nt_radio == "cds" else self.gene_value_source
        sorted_seq_tech_options_min = get_frequency_sorted_seq_techs_by_filters(
            self.processed_df_dict,
            tech_options,
            complete_partial_radio,
            2,
            gene_value,
            aa_nt_radio,
            min_date
        )

        for i, option in enumerate(sorted_seq_tech_options_min):
            self.assertDictEqual(
                option,
                correct_tech_options[complete_partial_radio][f"{aa_nt_radio}_min"][i]
            )

        sorted_seq_tech_options_2 = get_frequency_sorted_seq_techs_by_filters(
            self.processed_df_dict,
            tech_options,
            complete_partial_radio,
            2,
            gene_value,
            aa_nt_radio,
        )

        for i, option in enumerate(sorted_seq_tech_options_2):
            self.assertDictEqual(
                option,
                correct_tech_options[complete_partial_radio][aa_nt_radio][i]
            )

    def test_actualize_filters(self):
        pass
