#!/usr/bin/env python3

import os
from urllib.parse import urlparse

from sqlalchemy import create_engine
import subprocess
import sys
import time

import requests
from tqdm import tqdm



def printerr(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)


def download_file(url, out_file):
    file_name_part = out_file + ".prt"
    with requests.get(url, stream=True) as response:
        response.raise_for_status()
        file_size_mbyte = int(float(response.headers['Content-Length']) / 1024 / 1024)

        printerr(f"Downloading: {out_file}, size: {file_size_mbyte} MB")
        with open(file_name_part, 'wb') as handle:
            with tqdm(total=file_size_mbyte, position=0, leave=True, unit="MB") as pbar:
                for chunk in response.iter_content(chunk_size=1024 * 1024):  # 1 MB chunk size
                    if chunk:  # filter out keep-alive new chunks
                        handle.write(chunk)
                        chunk_size_mb = round(len(chunk) / 1024 / 1024, 2)
                        pbar.update(chunk_size_mb)
    os.rename(file_name_part, out_file)
    return os.path.abspath(out_file)


def download_spike_dump(test_db_dir):
    # download mpx db dump, covradar dump stored at "https://osf.io/hyxfp/download",
    # saved here: os.path.join(test_db_dir, "Spike.sql")
    url = ""
    printerr("Downloading sql dump...")
    spike_dump = download_file(url, os.path.join(test_db_dir, "Mpox.sql"))
    # -e script, --expression=script: add the script to the commands to be executed
    # s/utf8mb4_0900_ai_ci/utf8mb4_unicode_ci/g = test for correct mysql versions?
    subprocess.check_call(["sed", "-i", spike_dump, "-e", 's/utf8mb4_0900_ai_ci/utf8mb4_unicode_ci/g'])
    return spike_dump


class SqlServerWrapper:
    sql_is_initializing = False
    test_db_dir = os.path.join(os.path.dirname(__file__), "sql_dumps")

    def __init__(self, datadir, password, server_log_file="mariadb.log", host="127.0.0.1", user="root"):
        self.datadir = os.path.abspath(datadir)
        self.daemon = None
        self.log = os.path.abspath(server_log_file)
        self._log_fd = None
        self.user = user
        self.host = host
        self.pw = password

        if not self.sql_is_initializing:
            if not os.path.exists(datadir) or (len(os.listdir(self.datadir)) == 0):
                self.__class__.sql_is_initializing = True
                try:
                    self.init_sql_db()
                except Exception as e:
                    self.__class__.sql_is_initializing = False
                    raise e

    def get_database_connection(self, user=None, password=None, host=None):
        if user is None:
            user = self.user
        if password is None:
            password = self.pw
        if host is None:
            host = self.host
        return create_engine(f'mysql+pymysql://{user}:{password}@{host}')

    def init_sql_db(self):
        # initialize sql db
        # init sql data dir
        if not os.path.exists(self.datadir):
            printerr("Creatind directory:", self.datadir)
            os.mkdir(self.datadir)
        # initialize DB without root pw
        subprocess.check_call(["mysql_install_db", "--auth-root-authentication-method=normal", "--datadir", self.datadir])
        self.lock_down_db()
        if not os.path.exists(os.path.join(self.test_db_dir, "Spike.sql")):
            download_spike_dump(self.test_db_dir)

    def lock_down_db(self):
        with self:
            # Make sure that NOBODY can access the server without a password
            printerr("setting sql pw")
            conn = self.get_database_connection(password="")
            query = f"ALTER USER 'root'@'localhost' IDENTIFIED BY '{self.pw}'"
            conn.execute(query)
            # Make changes take effect
            printerr("flushing privileges")
            conn = self.get_database_connection()
            query = "FLUSH PRIVILEGES"
            conn.execute(query)
            # Any subsequent tries to run queries this way will get access denied because lack of usr/pwd param

    def load_dump(self, db_name, dump_file, drop_if_exists=True):
        if not self.is_alive():
            raise Exception(f"sql daemon not running! Did you surround you code with 'with {self.__class__.__name__}'")
        # dump DB if present
        conn = self.get_database_connection(self.user, self.pw, self.host)
        if drop_if_exists:
            conn.execute(f"DROP DATABASE IF EXISTS {db_name};")

        query = f"CREATE DATABASE {db_name};"
        printerr(f"Creating database:", query)
        conn.execute(query)
        os.environ["MYSQL_PWD"] = self.pw
        cmd = ["mysql", "-u", self.user, "--database", db_name]
        printerr("loading sql dump:", dump_file)
        printerr("MySQL command:", *cmd)
        with open(dump_file, "rb") as handle:
            result = subprocess.run(cmd, input=handle.read(), capture_output=True)
            if result.stdout:
                print(result.stdout.decode('utf-8'))
            if result.stderr:
                print(result.stderr.decode('utf-8'), file=sys.stderr)

    def load_all_test_dumps(self):
        for f in os.listdir(self.test_db_dir):
            if f.endswith(".sql"):
                db_name = os.path.splitext(os.path.basename(f))[0]
                self.load_dump(db_name, os.path.join(self.test_db_dir, f))

    def is_alive(self):
        return_code = subprocess.call(["mysqladmin", "ping", "-h", self.host, "-u", self.user, "--silent"],
                                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
        if return_code == 0:
            return True
        else:
            return False

    def __enter__(self):
        self.start()

    def __exit__(self, type, value, traceback):
        self.stop()

    def start(self):
        args = ["mysqld", "--datadir", self.datadir, "--user", self.user]
        printerr("Starting MySQL-Server: '", " ".join(args), "'", sep='')
        printerr(f"Writing log to: {self.log}")
        self._log_fd = open(self.log, "w")

        self.daemon = subprocess.Popen(args, stderr=self._log_fd)
        max_tries = 5
        tries = 0
        while not self.is_alive():
            tries += 1
            if tries >= max_tries:
                raise subprocess.SubprocessError(f"Failed to start mysql daemon. Check log: {self.log}")
            time.sleep(1)

    def stop(self):
        # send term signal to mysqld
        printerr("Shutting down MySQL-Server... ", end='')
        self.daemon.terminate()
        self.daemon.communicate()
        self.daemon = None
        self._log_fd.close()
        printerr("Done!")


def main():
    sql_datadir = "frontend/tests/.sql_datadir"
    mysql_credentials = get_mysql_credentials()
    sql_db = SqlServerWrapper(sql_datadir, password=mysql_credentials["MYSQL_PW"])
    if not sql_db.is_alive():
        sql_db.start()
    sql_db.load_all_test_dumps()
    if any(cred not in os.environ for cred in mysql_credentials):
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "env.sh")
        printerr(f"Writing mysql credentials to file\nLoad with: 'source {env_file}'")
        write_env_file(mysql_credentials, env_file)
    printerr("MySQL daemon running in background. Shutdown:\n"
             "     mysqladmin shutdown -u $MYSQL_USER -h $MYSQL_HOST --password=$MYSQL_PW")


def write_env_file(credential_dict, file_path):
    with open(file_path, "w") as f:
        for env_var, value in credential_dict.items():
            f.write(f"export {env_var}={value}\n")


def get_mysql_credentials():
    DB_URL = os.getenv("DB_URL")
    parsed_db_url = urlparse(DB_URL)
    # port = parsed_db_url.port
    cred = {"MYSQL_USER": parsed_db_url.username,
            "MYSQL_PW": parsed_db_url.password,
            "MYSQL_HOST": parsed_db_url.hostname,
            }
    return cred


if __name__ == "__main__":
    main()
