import pytest
import os

from tests.setup_test_sql_db import SqlServerWrapper


@pytest.fixture(scope="session")
def sql_test_db(tmpdir_factory):
    data_dir = tmpdir_factory.mktemp("db_dir")
    sql_db = SqlServerWrapper(data_dir)
    sql_db.start()
    # export db params
    os.environ['MYSQL_USER'] = "root"
    os.environ['MYSQL_HOST'] = "127.0.0.1"
    os.environ['MYSQL_PW'] = ""
    print("fixture")
    print(sql_db)
    yield sql_db
    sql_db.stop()
