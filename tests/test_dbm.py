import re

import pytest

from pathosonar.dbm import sonarDBManager


def test_fail_direct_query(testdb):
    with pytest.raises(SystemExit):
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.direct_query("DROP DATABASE IF EXISTS `mpx_4`;")


def test_add_illegal_properties(testdb):
    with pytest.raises(SystemExit):
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.add_property(
                name="SAMPLE",
                datatype="TEXT",
                querytype="TEXT",
                description="TEXT",
                subject="sample",
            )

    with pytest.raises(SystemExit):
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.add_property(
                name="!!",
                datatype="TEXT",
                querytype="TEXT",
                description="TEXT",
                subject="sample",
            )


def test_add_duplicated_reference(testdb):
    with pytest.raises(SystemExit):
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.add_reference(
                "MN908947.3",
                "Severe acute respiratory syndrome coronavirus 2 isolate Wuhan-Hu-1, complete genome",
                "Severe acute respiratory syndrome coronavirus 2",
                1,
                1,
            )


def test_insert_fail_properties(testdb):
    with pytest.raises(SystemExit):
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.insert_property(10000, "LINEAGE", "BA.5")


def test_insert_new_annotation(testdb):
    with sonarDBManager(testdb, readonly=False) as dbm:
        dbm.get_annotation_ID_by_type("New_Effect")


def test_get_annotation(testdb):
    with sonarDBManager(testdb, readonly=False) as dbm:
        id = dbm.get_annotation_ID_by_type("coding_sequence_variant")
        assert 1 == id


def test_mutation_condition_invalid_input(testdb):
    pattern_del = r"^(|[^:]+:)?([^:]+:)?del:(=?[0-9]+)(|-=?[0-9]+)?$"
    pattern_snv_indel = r"^(|[^:]+:)?([^:]+:)?([A-Z]+)([0-9]+)(=?[A-Zxn]+)$"
    string1 = "N:del:2"
    string2 = "T213F"
    match1 = re.match(pattern_del, string1)
    match2 = re.match(pattern_snv_indel, string2)
    # Test with an invalid regex match
    with pytest.raises(SystemExit):
        # Pass a match object that does not match the expected pattern
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.build_deletion_condition(match1)

    with pytest.raises(SystemExit):
        # Pass a match object that does not match the expected pattern
        with sonarDBManager(testdb, readonly=False) as dbm:
            dbm.build_snp_and_insert_condition(match2)


def test_create_genomic_element_conditions(testdb):
    with sonarDBManager(testdb, readonly=False) as dbm:
        (
            genome_element_condition,
            molecule_prefix,
        ) = dbm.create_genomic_element_conditions(["MN908947.3", "NC_063383.1"])
        print(genome_element_condition, molecule_prefix)
