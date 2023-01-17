# just in case for some query we can use a direct connect to database.
import sys
from urllib.parse import urlparse

import mariadb

from .config import DB_URL
from .config import logging_radar


class DBManager(object):
    """
    This object provides a DB manager handler managing connections and
    providing context-safe transaction control.
    """

    def __init__(self, db_url=None, readonly=True):

        if db_url is None:
            db_url = DB_URL

        # public attributes
        self.connection = None
        self.dbfile = db_url  # os.path.abspath(dbfile)
        self.cursor = None
        self.__references = {}
        self.__uri = self.get_uri(db_url)
        self.__mode = "ro" if readonly else "rwc"
        self.db_user = self.__uri.username
        self.db_pass = self.__uri.password
        self.db_url = self.__uri.hostname
        self.db_port = self.__uri.port
        self.db_database = self.__uri.path.replace("/", "")

    def __enter__(self):
        """establish connection and start transaction when class is initialized"""
        self.connection, self.cursor = self.connect()
        self.start_transaction()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        """close connection and - if errors occured - rollback when class is exited"""
        if [exc_type, exc_value, exc_traceback].count(None) != 3:
            if self.__mode == "rwc":
                print("Rollback database", file=sys.stderr)
                self.rollback()
        elif self.__mode == "rwc":
            self.commit()
        self.close()

    def __del__(self):
        """close connection when class is deleted"""
        if self.connection:
            # self.close()
            self.conection = None
            # logging.debug("Connection Closed")

    def connect(self):
        """connect to database"""
        # con = sqlite3.connect(
        #    self.__uri + "?mode=" + self.__mode,
        #    self.__timeout,
        #    isolation_level=None,
        #    uri=True,
        # )
        try:
            db_user = self.db_user
            db_pass = self.db_pass
            db_url = self.db_url
            db_port = self.db_port
            db_database = self.db_database
            # logging.debug(f"{db_user}, {db_url}, {db_port}, {db_database}")
            con = mariadb.connect(
                user=db_user,
                password=db_pass,
                host=db_url,
                port=db_port,
                database=db_database,
            )
        except mariadb.Error as e:
            logging_radar.error(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        # if self.debug:
        #    con.set_trace_callback(logging.debug)
        con.row_factory = self.dict_factory
        # always return as a dictionary
        cur = con.cursor(dictionary=True)
        return con, cur

    @staticmethod
    def dict_factory(cursor, row):
        d = {}  # OrderedDict()
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    def get_uri(self, db_url):
        """
        returns  username password host port

        """
        parsed_obj = urlparse(db_url)
        return parsed_obj

    def start_transaction(self):
        self.cursor.execute("START TRANSACTION;")

    def new_transaction(self):
        """commit and start new transaction"""
        self.commit()
        self.start_transaction()

    def commit(self):
        """commit"""
        self.connection.commit()

    def rollback(self):
        """roll back"""
        self.connection.rollback()

    def close(self):
        """close database connection"""
        self.cursor.close()
        self.connection.close()

    @property
    def references(self):
        """
        return all references

        """
        if self.__references == {}:
            sql = "SELECT `id`, `accession`, `description`, `organism` FROM reference;"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            if rows:
                self.__references = rows
            else:
                self.__references = {}
        return self.__references

    def get_all_SeqTech(self):
        sql = "SELECT DISTINCT(value_text) FROM propertyView WHERE `property.name` = 'SEQ_TECH' ORDER BY value_text;"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows

    def get_high_mutation(self):
        """
        List only NT mutations that have freq. 500

        SELECT  `variant.label`  , COUNT(*) AS Freq
            FROM   variantView
            WHERE `element.type` = "source"
            Group By `variant.label`
            HAVING Freq > 500
            ORDER BY Freq DESC
        """
        sql = "SELECT `variant.label`, COUNT(*) AS Freq FROM variantView WHERE `element.type` = 'source' Group By `variant.label`  HAVING Freq > 1000 ORDER BY Freq DESC ;"
        self.cursor.execute(sql)
        rows = self.cursor.fetchall()
        return rows

    def count_all_samples(self):
        """ """
        sql = "SELECT COUNT(id) AS count FROM sample;"
        self.cursor.execute(sql)
        number_of_rows = self.cursor.fetchone()["count"]
        return number_of_rows

    def count_lastAdded30D_sample(self):
        """
        we use fix id (8 = release date)
        """
        sql = (
            "SELECT COUNT(sample_id) AS count "
            "FROM sample2property "
            "WHERE property_id = 8 AND DATE(VALUE_DATE) >=  DATE(NOW() - INTERVAL 30 DAY)"
        )
        self.cursor.execute(sql)
        number_of_rows = self.cursor.fetchone()["count"]
        return number_of_rows

    def count_all_country(self):
        """ """
        sql = (
            "SELECT COUNT(DISTINCT value_text) AS count "
            "FROM sample2property "
            "WHERE property_id = 12;"
        )
        self.cursor.execute(sql)
        number_of_rows = self.cursor.fetchone()["count"]
        return number_of_rows

    def count_top3_country(self):
        """
        we use fix id (8 = release date)
        """
        sql = (
            "SELECT  value_text , COUNT(value_text) AS count "
            "FROM sample2property "
            "WHERE property_id = 12 GROUP BY value_text ORDER BY count DESC LIMIT 3;"
        )
        self.cursor.execute(sql)
        _rows = self.cursor.fetchall()
        return _rows

    def count_unique_MutRef(self):
        """
        "Number of mutations", i.e., min and max of number of unique mutations
        (compared to each reference genome). So if with ref-genome-1,
        there are 100 mutations and with ref-2, there are 220 and with ref-3 there are 60 mutation,
        then this field will show: "60 - 220"
        """

        sql = (
            "SELECT `reference.accession` , MAX(T1.Freq) AS max_each_ref "
            "FROM ( "
            "SELECT `reference.accession`,  COUNT(`variant.label`) AS Freq "
            "From   variantView "
            "WHERE `element.type` = 'cds' "
            "Group By `reference.accession` "
            "ORDER BY Freq DESC) AS T1 "
            "Group BY `reference.accession` "
            "ORDER BY max_each_ref DESC;"
        )
        self.cursor.execute(sql)
        _rows = self.cursor.fetchall()
        return _rows
