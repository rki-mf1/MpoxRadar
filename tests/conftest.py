from pathlib import Path
import tempfile

import pytest

from pathosonar.dbm import sonarDBManager
from pathosonar.utils import sonarUtils


# PYTEST FIXTURES
@pytest.fixture(autouse=True)
def mock_workerpool_imap_unordered(monkeypatch):
    """Mock mpire's WorkerPool.imap_unordered function

    This is necessary to work around crashes caused by trying to calculate
    coverage with multiprocess subprocesses, and also to make the tests
    reproducible (ordered).
    """
    monkeypatch.setattr(
        "mpire.WorkerPool.imap_unordered",
        lambda self, func, args=(), kwds={}, callback=None, error_callback=None: (
            func(arg) for arg in args
        ),
    )


@pytest.fixture(scope="session")
def setup_db():
    """Fixture to set up a temporay session-lasting test database with test data"""
    data_dir = Path(__file__).parent

    dbfile = "https://admin:password@localhost:3306/patho_test"
    default_props = True
    gbk = f"{data_dir}/data/covid19/ref.cov19.gb"
    db_sql_script = f"{data_dir}/data/db.test.sql"

    sonarUtils.setup_db(dbfile, db_sql_script, default_props, reference_gb=gbk)

    with sonarDBManager(dbfile, readonly=False) as dbm:
        dbm.add_property("SEQUENCING_LAB_PC", "zip", "zip", " ", "sample")
        dbm.add_property("Ct", "integer", "integer", " ", "sample")
        dbm.add_property("DATE_DRAW", "date", "date", " ", "sample")
        dbm.add_property("RECEIVE_DATE", "date", "date", " ", "sample")
        dbm.add_property("SEQ_TYPE", "text", "text", " ", "sample")

    return dbfile


@pytest.fixture
def tmpfile_name(tmpdir_factory):
    my_tmpdir = str(
        tmpdir_factory.mktemp("dbm_test").join(next(tempfile._get_candidate_names()))
    )
    print("tmp_path:", my_tmpdir)

    yield my_tmpdir

    # if os.path.exists(my_tmpdir):
    #    shutil.rmtree(my_tmpdir)


@pytest.fixture(scope="session")
def testdb(setup_db):
    return setup_db


"""
@pytest.fixture(scope="session")
def testdb(setup_db):
    db = setup_db
    script_dir = os.path.dirname(os.path.abspath(__file__))
    fasta = os.path.join(script_dir, "data", "test.fasta")
    sonarBasics.import_data(
        db,
        fasta=[fasta],
        tsv=[],
        cols={},
        cachedir=None,
        autodetect=True,
        progress=False,
        update=True,
        debug=False,
        quiet=True,
    )

"""


@pytest.fixture
def init_readonly_dbm(testdb):
    """Fixture to set up a read-only dbm object"""
    with sonarDBManager(testdb, readonly=True) as dbm:
        yield dbm


@pytest.fixture
def init_writeable_dbm(testdb):
    """Fixture to set up a wirte-able dbm object"""
    with sonarDBManager(testdb, readonly=False) as dbm:
        yield dbm
