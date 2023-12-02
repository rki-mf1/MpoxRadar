from pathlib import Path
import re

import pytest

from pathosonar import sonar


def split_cli(s):
    """Split a string into a list of individual arguments, respecting quotes"""
    return re.findall(r'(?:[^\s,"]|"(?:\\.|[^"])*")+', s)


def run_cli(s):
    """Helper function to simulate running the command line ./sonar <args>"""
    return sonar.main(sonar.parse_args(split_cli(s)))


def test_help():
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_cli("--help")
    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 0


def test_info(capfd, testdb):
    code = run_cli(f" info --db {testdb}")
    out, err = capfd.readouterr()
    assert "Version:" in out
    assert code == 0


@pytest.mark.order(1)
def test_add_ref(monkeypatch, capfd, testdb):
    monkeypatch.chdir(Path(__file__).parent)
    new_ref_file = "data/mpox/NC_063383.1.gb"
    code = run_cli(f" add-ref --db {testdb} --gbk {new_ref_file} ")
    out, err = capfd.readouterr()
    assert "The reference has been added successfully." in out
    assert code == 0


def test_list_ref(capfd, testdb):
    code = run_cli(f" list-ref --db {testdb}")
    out, err = capfd.readouterr()
    assert "NC_063383.1" in out
    assert code == 0


def test_list_prop(capfd, testdb):
    code = run_cli(f" list-prop --db {testdb}  ")
    out, err = capfd.readouterr()
    assert "--IMPORTED" in out
    assert code == 0


@pytest.mark.order(2)
def test_add_prop(capfd, testdb):
    # add the redundant prop.
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        run_cli(f"add-prop --db {testdb} --name LINEAGE --dtype text --descr descr")
        out, err = capfd.readouterr()
        assert "a property named LINEAGE already exists in the given database." in err
        assert pytest_wrapped_e.type == SystemExit

    code = run_cli(
        f"add-prop --db {testdb} --name AGE --dtype float --descr for_testing"
    )
    assert code == 0

    code = run_cli(
        f'add-prop --db {testdb} --name TEST_123 --dtype text --descr "JUST FOR FUN" '
    )
    assert code == 0

    run_cli(f" list-prop --db {testdb}  ")
    out, err = capfd.readouterr()
    assert "AGE" in out
    assert "LINEAGE" in out
    assert "TEST_123" in out


def test_del_prop(monkeypatch, capfd, testdb):

    run_cli(f"delete-prop --db {testdb} --force --name TEST_123")
    monkeypatch.setattr("builtins.input", lambda _: "YES")

    run_cli(f" list-prop --db {testdb}  ")
    out, err = capfd.readouterr()

    assert "TEST_123" not in out


def test_db_optimize(capfd, testdb):
    code = run_cli(f" optimize --db {testdb}  ")
    out, err = capfd.readouterr()
    assert "Done" in out
    assert code == 0


def test_import(monkeypatch, testdb, tmpfile_name):
    "Test import command for covid19"
    monkeypatch.chdir(Path(__file__).parent)

    code = run_cli(
        f"import --db {testdb} -r MN908947.3 --method 2 --fasta data/covid19/seqs.fasta.gz --tsv data/covid19/meta.tsv --cache {tmpfile_name} --cols sample=IMS_ID --threads 2 --auto-link"
    )
    assert code == 0


@pytest.mark.order(3)
def test_import_with_diff_ref(monkeypatch, testdb, tmpfile_name):
    monkeypatch.chdir(Path(__file__).parent)
    code = run_cli(
        f"import --db {testdb} -r NC_063383.1 --fasta data/mpox/1.complete.fasta --csv data/mpox/1.complete.csv --cache {tmpfile_name} --cols sample=ID --threads 2 --auto-link --auto-anno"
    )
    assert code == 0


def test_import_bad_fasta(monkeypatch, testdb, tmpfile_name):
    monkeypatch.chdir(Path(__file__).parent)
    with pytest.raises(SystemExit):
        run_cli(
            f"import --db {testdb} -r MN908947.3 --fasta data/covid19/bad.fasta --cache {tmpfile_name} --cols sample=ID"
        )


"""
def test_delete_ref(monkeypatch, capfd, testdb):
    code = run_cli(
        f"delete-ref --db {testdb} -r NC_063383.1"
    )
    monkeypatch.setattr("builtins.input", lambda _: "YES")
    assert code == 0

    code = run_cli(f"list-ref --db {testdb}")
    out, err = capfd.readouterr()
    assert 'NC_063383.1' not in out
    assert code == 0

    # alignment count remained only five.
    code = run_cli(f"direct-query --db {testdb} --sql \"SELECT count(*) FROM alignment\" ")
    out, err = capfd.readouterr()
    lines = out.splitlines()

    assert '5' == lines[-1]
    assert code == 0
"""


def test_direct_sql(capfd, testdb):
    code = run_cli(f'direct-query --db {testdb} --sql "SELECT count(*) FROM sample" ')
    out, err = capfd.readouterr()

    # sample count is 8.
    lines = out.splitlines()
    assert "8" == lines[-1]
    assert code == 0


def test_match_with_output(capfd, testdb, tmpfile_name):
    # tsv
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile C193688T --format tsv"
    )
    assert code == 0
    # csv
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile C193688T --format csv"
    )
    assert code == 0
    # vcf
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile C193688T --format vcf"
    )
    assert code == 0


def test_match_specialcase(capfd, testdb, tmpfile_name):
    # show NX
    code = run_cli(f"match --db {testdb} -r NC_063383.1 --profile C83326T --showNX")
    assert code == 0
    # output some columns
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile C83326T  --out-cols SEQ_TECH"
    )
    assert code == 0


def test_match_sample(capfd, testdb):
    # X SNV
    code = run_cli(f"match --db {testdb} -r NC_063383.1 --profile C193688T --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "3" == lines[-1]
    assert code == 0

    # X INS
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile A173314ATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATA --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "1" == lines[-1]
    assert code == 0

    # X OR X
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile A173314ATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATATA --profile T124690C --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "2" == lines[-1]
    assert code == 0

    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile C193688T --profile del:593-595 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "3" == lines[-1]
    assert code == 0

    # X del
    code = run_cli(f"match --db {testdb} -r NC_063383.1 --profile del:593-595 --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "2" == lines[-1]
    assert code == 0

    # X AND X AA
    code = run_cli(
        f"match --db {testdb} -r NC_063383.1 --profile OPG098:E162K OPG197:del:19-19 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "1" == lines[-1]
    assert code == 0

    # X OR (X AND X)
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --profile S:del:69-69 ORF8:D63N --profile C7303T --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "2" == lines[-1]
    assert code == 0

    # ref
    code = run_cli(f"match --db {testdb} -r NC_063383.1 --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "3" == lines[-1]
    assert code == 0

    # ref
    code = run_cli(f"match --db {testdb} -r MN908947.3 --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "5" == lines[-1]
    assert code == 0


def test_match_prop(capfd, testdb):
    # X
    code = run_cli(f"match --db {testdb} -r NC_063383.1 --COUNTRY USA --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "1" == lines[-1]
    assert code == 0

    # X
    code = run_cli(f"match --db {testdb} -r MN908947.3 --SEQ_TYPE ION_TORRENT --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "1" == lines[-1]
    assert code == 0

    # Date X OR X
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --PROCESSING_DATE 2021-04-06 2021-02-19 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "2" == lines[-1]
    assert code == 0

    # X AND X
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --SEQ_TYPE ILLUMINA --PROCESSING_DATE 2021-03-12:2021-04-01 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "2" == lines[-1]
    assert code == 0

    # ZIP
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --SEQUENCING_LAB_PC 12333 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "0" == lines[-1]
    assert code == 0

    # Float
    code = run_cli(f"match --db {testdb} -r MN908947.3  --AGE 23.5 --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "0" == lines[-1]
    assert code == 0

    # INT RANGE
    code = run_cli(f"match --db {testdb} -r MN908947.3 --LENGTH 1000:199999 --count")
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "0" == lines[-1]
    assert code == 0
    # LINEAGE widecard...

    """
    # test match ZIP (w REF)
    sonar match -r MN908947.3 --SEQUENCING_LAB_PC 04779
    # test match INT (w REF)

    # test match TEXT LINAGE (w REF)
    sonar match -r NC_063383.1 --COUNTRY Germany
    # test match RANGE (w REF)
    """


def test_match_sample_prop(capfd, testdb):
    # X --prop AND --profile
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --PROCESSING_DATE 2021-03-01:2021-03-08 --profile S:del:69-69 --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "1" == lines[-1]
    assert code == 0

    # --prop AND --profile  (X OR X)
    code = run_cli(
        f"match --db {testdb} -r MN908947.3 --DATE_DRAW 2021-02-01:2021-03-30 --profile S:del:69-69 --profile C10186T --count"
    )
    out, err = capfd.readouterr()
    lines = out.splitlines()
    assert "4" == lines[-1]
    assert code == 0


def test_restore_sample(testdb, capfd):
    code = run_cli(
        f"restore --db {testdb} --sample IMS-10004-CVDP-0672526C-BAEA-4FE9-A57B-941CBCC13343 "
    )
    out, err = capfd.readouterr()
    assert "IMS-10004-CVDP-0672526C-BAEA-4FE9-A57B-941CBCC13343" in out
    assert code == 0


def test_delete_sample(monkeypatch, capfd, testdb):
    code = run_cli(
        f"delete --db {testdb} --sample IMS-10004-CVDP-0672526C-BAEA-4FE9-A57B-941CBCC13343 IMS-10013-CVDP-37E0BD5A-03D8-42CE-95C0-7B900B714B95"
    )
    monkeypatch.setattr("builtins.input", lambda _: "YES")

    out, err = capfd.readouterr()
    lines = out.splitlines()

    assert "6 samples remain in the database." == lines[-1]
    assert code == 0


"""


# The following two tests run the commands from the example test script, but
# are split in two to skip the "import" command which is currently causing a
# crash when run via pytest
def test_valid_beginning(tmp_path, monkeypatch):
    "The test example provided by other devs, up to the import command"
    monkeypatch.chdir(Path(__file__).parent)

    db_path = str(tmp_path / "test.db")
    sonar.main(sonar.parse_args(split_cli(f"setup --db {db_path}")))

    run_cli(f"add-prop --db {db_path} --name SENDING_LAB --dtype integer --descr descr")
    run_cli(f"add-prop --db {db_path} --name DATE_DRAW --dtype date --descr descr")
    run_cli(f"add-prop --db {db_path} --name SEQ_TYPE --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name SEQ_REASON --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name SAMPLE_TYPE --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name OWN_FASTA_ID --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name DOWNLOAD_ID --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name DEMIS_ID --dtype integer --descr descr")
    run_cli(f"add-prop --db {db_path} --name RECEIVE_DATE --dtype date --descr descr")
    run_cli(
        f"add-prop --db {db_path} --name PROCESSING_DATE --dtype date --descr descr"
    )
    run_cli(
        f"add-prop --db {db_path} --name PUBLICATION_STATUS --dtype text --descr descr"
    )
    run_cli(
        f"add-prop --db {db_path} --name HASHED_SEQUENCE --dtype text --descr descr"
    )
    run_cli(f"add-prop --db {db_path} --name TIMESTAMP --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name STUDY --dtype text --descr descr")
    run_cli(
        f"add-prop --db {db_path} --name DOWNLOADING_TIMESTAMP --dtype text --descr descr"
    )
    run_cli(f"add-prop --db {db_path} --name SENDING_LAB_PC --dtype zip --descr descr")
    run_cli(f"add-prop --db {db_path} --name DEMIS_ID_PC --dtype zip --descr descr")
    run_cli(f"add-prop --db {db_path} --name VERSION --dtype integer --descr descr")
    run_cli(f"add-prop --db {db_path} --name DESH_QC_PASSED --dtype text --descr descr")
    run_cli(
        f"add-prop --db {db_path} --name DESH_REJECTION_REASON --dtype text --descr descr"
    )
    run_cli(f"add-prop --db {db_path} --name DUPLICATE_ID --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name LINEAGE --dtype text --descr descr")
    run_cli(f"add-prop --db {db_path} --name AGE --dtype float --descr for_testing")

    run_cli(f"update-lineage-info --db {db_path}")



def test_valid_end(tmp_path, monkeypatch):
    "The test example provided by other devs, after the import command"
    monkeypatch.chdir(Path(__file__).parent)

    db_path_orig = Path("data/test-with-seqs.db")
    db_path = tmp_path / "test-with-seqs.db"
    shutil.copy(db_path_orig, db_path)
    run_cli(f"match --db {db_path} --profile ^A3451T A3451TGAT -o {tmp_path}/temp1.tsv")
    run_cli(
        f"match --db {db_path} --profile del:28363-28371  --profile A3451N -o {tmp_path}/temp2.tsv"
    )
    run_cli(f"match --db {db_path} --profile ^S:A67X S:E484K -o {tmp_path}/temp.tsv")
    run_cli(
        f"match --db {db_path} --profile S:A67G --profile S:N501Y --debug -o {tmp_path}/temp3.tsv"
    )
    run_cli(
        f"match --db {db_path} --profile S:A67G --DEMIS_ID 10013 --debug -o {tmp_path}/temp4.tsv"
    )
    run_cli(
        f"match --db {db_path} --DATE_DRAW 2021-03-01:2022-03-15 -o {tmp_path}/temp5.tsv"
    )
    run_cli(f"match --db {db_path} --LINEAGE B.1.1.7 --with-sublineage LINEAGE --count")


# the following functions, we try to extend the test cases to make
# covsonar executes all command tools and also increase test coverage.(test reliability )
# However, the test is not for assessment validity.
def test_valid_extend(tmp_path, monkeypatch):
    monkeypatch.chdir(Path(__file__).parent)

    db_path = "data/test-with-seqs.db"
    # sonar.parse_args(["--version"])
    run_cli(
        f"match --db {db_path} --LINEAGE ^B.1.1.7 --with-sublineage LINEAGE --count -o {tmp_path}/temp.tsv"
    )
    run_cli(
        f"match --db {db_path} --LINEAGE ^B.1.1% AY.4% --with-sublineage LINEAGE -o {tmp_path}/temp1.tsv "
    )
    run_cli(f"match --db {db_path} --format csv -o {tmp_path}/out.csv")
    run_cli(f"match --db {db_path} --format vcf -o {tmp_path}/out.vcf")
    run_cli(
        f"restore --db {db_path} --sample IMS-10025-CVDP-00960 IMS-10087-CVDP-D484F3AD-CD8F-473C-8A5E-DB5D6A710BE5 IMS-10004-CVDP-0672526C-BAEA-4FE9-A57B-941CBCC13343 IMS-10013-CVDP-69DF29F4-D7E3-4954-94F4-65C20BE7B850 IMS-10013-CVDP-37E0BD5A-03D8-42CE-95C0-7B900B714B95 > {tmp_path}/out.fasta"
    )

    assert filecmp.cmp(f"{tmp_path}/out.csv", "data/out.csv")
    assert filecmp.cmp(f"{tmp_path}/out.vcf", "data/out.vcf")


def test_valid_extend2(monkeypatch, capsys):
    "complex query"
    monkeypatch.chdir(Path(__file__).parent)
    db_path = "data/test-with-seqs.db"
    # float
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--AGE",
            "<30",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "1"
    # float AND OR
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--AGE",
            "<30.0",
            "^67.89",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "1"

    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--AGE",
            "30:55",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "2"
    # numeric
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--HEIGHT",
            "185:190",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "2"
    # numeric AND OR

    # zip
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--SENDING_LAB_PC",
            "^86154",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "4"
    # zip AND OR
    # date

    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--DATE_DRAW",
            "2021-03-18",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "1"


def test_valid_extend3(monkeypatch, capsys):
    monkeypatch.chdir(Path(__file__).parent)
    db_path = "data/test-with-seqs.db"
    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--LINEAGE",
            "^BA.5",
            "--with-sublineage",
            "LINEAGE",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "3"

    parsed_args = sonar.parse_args(
        [
            "match",
            "--db",
            db_path,
            "--sample",
            "IMS-10013-CVDP-37E0BD5A-03D8-42CE-95C0-7B900B714B95",
            "IMS-10025-CVDP-00960",
            "--count",
        ]
    )
    result = sonar.main(parsed_args)
    captured = capsys.readouterr()
    assert result == 0
    assert captured.out.strip() == "2"

"""
