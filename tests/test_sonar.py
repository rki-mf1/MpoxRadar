import logging
from pathlib import Path

import pytest
from src.pathosonar import sonar


def test_check_file_not_exist():
    fname = "no/real/file/existence"
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        sonar.check_file(fname)
    assert pytest_wrapped_e.type == SystemExit
    assert (
        pytest_wrapped_e.value.code == "Error: The file '" + fname + "' does not exist."
    )


def test_check_file_exist(monkeypatch):
    monkeypatch.chdir(Path(__file__).parent)
    fname = "data/covid19/test.fasta"
    assert sonar.check_file(fname) is True


def test_check_db_not_exist():
    parsed_args = sonar.parse_args(
        ["info", "--db", "https://admin11:password@localhost:3327/patho_test"]
    )

    with pytest.raises(SystemExit) as pytest_wrapped_e:
        sonar.main(parsed_args)
    assert pytest_wrapped_e.type == SystemExit


def test_unknown_properties(testdb):
    parsed_args = sonar.parse_args(
        ["delete-prop", "--db", testdb, "--name", "WHAT_IS_THIS"]
    )
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        sonar.main(parsed_args)
    assert pytest_wrapped_e.type == SystemExit


def test_import_data(monkeypatch, testdb, tmpfile_name):
    monkeypatch.chdir(Path(__file__).parent)
    test_fasta = "data/covid19/test.fasta"
    test_meta = "data/covid19/meta.tsv"
    parsed_args = sonar.parse_args(
        [
            "import",
            "--db",
            testdb,
            "-r",
            "MN908947.3",
            "--fasta",
            test_fasta,
            "--tsv",
            test_meta,
            "--cache",
            tmpfile_name,
            "--auto-link",
            "--cols",
            "sample=IMS_ID",
            "--thread",
            "2",
        ]
    )

    assert sonar.main(parsed_args) == 0


def test_match_count_with_sample(monkeypatch, testdb, capfd):
    """
    checking whether sonar program can successfully perform a match-count.
    """
    # sonar match -r MN908947.3 --profile del:21763-21768 --count
    monkeypatch.chdir(Path(__file__).parent)
    sample_file = "data/covid19/sample_list.txt"
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            testdb,
            "-r",
            "MN908947.3",
            "--sample",
            "seq01",
            "--sample-file",
            sample_file,
            "--count",
        ]
    )
    assert sonar.main(parsed_args) == 0
    out, err = capfd.readouterr()
    # Split the 'out' string into lines
    lines = out.splitlines()

    # Check if the last line contains the number 1
    assert "1" == lines[-1]


def test_delete_nothing(monkeypatch, testdb, caplog):
    monkeypatch.chdir(Path(__file__).parent)
    sample_file = "data/covid19/sample_list.txt"

    parsed_args = sonar.parse_args(
        [
            "delete",
            "--db",
            testdb,
            "--sample",
            "nothing_to_delete",
            "--sample-file",
            sample_file,
        ]
    )
    # with caplog.at_level(logging.INFO):
    assert sonar.main(parsed_args) == 0
    # assert '0 of 3 samples found and deleted.
    # 4 samples remain in the database.' in caplog.text
    parsed_args = sonar.parse_args(
        [
            "delete",
            "--db",
            testdb,
        ]
    )
    with caplog.at_level(logging.INFO):
        assert sonar.main(parsed_args) == 0
        assert "Nothing to delete." in caplog.text


def test_no_args():
    """ """
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        sonar.main(None)

    assert pytest_wrapped_e.type == SystemExit


def test_debug(testdb, capfd):
    """ """
    parsed_args = sonar.parse_args(["match", "--db", testdb, "--debug"])
    assert sonar.main(parsed_args) == 0


def test_no_db_path():
    parsed_args = sonar.parse_args(
        [
            "info",
        ]
    )
    assert sonar.main(parsed_args) == 0


# test unrecognize args
"""
def test_upgrade_db(tmp_path, monkeypatch, logger, caplog):
    monkeypatch.chdir(Path(__file__).parent)
    db_path_orig = Path("data/test.old.db")
    db_path = os.path.join(tmp_path, "test.old.db")

    shutil.copy(db_path_orig, db_path)

    # detect fail case
    parsed_args = sonar.parse_args(
        [
            "info",
            "--db",
            db_path,
        ]
    )
    with caplog.at_level(logging.INFO, logger="covsonar"), pytest.raises(
        SystemExit
    ) as pytest_wrapped_e:
        sonar.main(parsed_args)
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
        assert (
            "The given database is not compatible with this version of sonar "
            in caplog.text
        )

    # perform upgrade
    parsed_args_upgrade = sonar.parse_args(
        [
            "db-upgrade",
            "--db",
            db_path,
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _: "YES")
    with caplog.at_level(logging.ERROR, logger=logger.name), pytest.raises(
        SystemExit
    ) as pytest_wrapped_e:
        assert sonar.main(parsed_args_upgrade) == 0
        assert (
            "Sorry, but automated migration does not support databases of version 3."
            == caplog.records[-1].message
        )
        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code
"""
