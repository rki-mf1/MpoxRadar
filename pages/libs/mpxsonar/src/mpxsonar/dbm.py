#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# author: Stephan Fuchs (Robert Koch Institute, MF1, fuchss@rki.de)
# Kunaphas (RKI,HPI, kunaphas.kon@gmail.com)

from collections import defaultdict
import itertools
import os
import pkgutil
import re
import sqlite3
import sys
from urllib.parse import quote as urlquote
from urllib.parse import urlparse

from Bio.Seq import Seq
from Bio.SeqFeature import CompoundLocation
from Bio.SeqFeature import FeatureLocation
import mariadb
import pandas as pd
from tqdm import tqdm

from . import logging
from .config import DB_URL

sys.path.insert(1, "..")

# COMPATIBILITY
SUPPORTED_DB_VERSION = 1


class sonarDBManager:
    """
    This object provides a sonarDB SQLite manager handler managing connections and
    providing context-safe transaction control.

    Notes
    -----
        This object should be called using a context manager to ensure rollbacks
        on abnormal termination.

    Example
    -------

    In this example the DOCTESTDB variable store the path to a database file

    >>> dbfile = getfixture('setup_db')
    >>> with sonarDBManager(dbfile) as dbm:
    ... 	pass

    Parameters
    ----------

    dbfile : str
        define a path to an existent and valid SONAR database file. If the
        file does not exist, a SONAR database is created.
    timeout : int [ -1 ]
        define busy timeout used for the connection. Use -1 for no timeout.
    readonly : bool [ False ]
        set True if the connection should be read-only
    debug : bool [ False ]
        debug mode (print all executed sql queries)

    Attributes
    ----------
    dbfile : str
        stores the path to the used SONAR database file.
    connection : object
        stores the SQLite3 connection
    cursor : method
        stores the SQLite3 cursor
    debug: bool
        stores debug mode status

    """

    def __init__(
        self, db_url=None, timeout=-1, readonly=True, debug=False, autocreate=False
    ):
        logging.basicConfig(format="%(asctime)s %(message)s")

        if db_url is None:
            # logging.warning("No --db is given, MPXSonar use variables from .env file.")
            db_url = DB_URL

        # public attributes
        self.connection = None
        self.dbfile = db_url  # os.path.abspath(dbfile)
        self.cursor = None
        self.debug = debug

        # private attributes
        self.__timeout = timeout
        self.__mode = "ro" if readonly else "rwc"
        self.__uri = self.get_uri(db_url)
        self.db_user = self.__uri.username
        self.db_pass = self.__uri.password
        self.db_url = self.__uri.hostname
        self.db_port = self.__uri.port
        self.db_database = self.__uri.path.replace("/", "")

        self.__properties = False
        self.__references = {}
        self.__illegal_properties = {}
        self.__default_reference = False
        self.__lineage_sublineage_dict = None
        self.__rootdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.__lineagewithsublineages = os.path.join(
            self.__rootdir, "lib", "lineage.all.tsv"
        )
        self.__operators = {
            "genuine": {
                "=": "=",
                ">": ">",
                "<": "<",
                ">=": ">=",
                "<=": "<=",
                "IN": "IN",
                "LIKE": "LIKE",
                "BETWEEN": "BETWEEN",
            },
            "negated": {
                "=": "!=",
                ">": "<=",
                "<": ">=",
                ">=": "<",
                "<=": ">",
                "IN": "NOT IN",
                "LIKE": "NOT LIKE",
                "BETWEEN": "NOT BETWEEN",
            },
        }

        # checking database file
        # if not os.path.isfile(self.dbfile):
        #    if not autocreate:
        #        sys.exit("database error: database does not exists")
        #    self.setup(self.dbfile)

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
            logging.error(f"Error connecting to MariaDB Platform: {e}")
            sys.exit(1)

        # if self.debug:
        #    con.set_trace_callback(logging.debug)
        con.row_factory = self.dict_factory
        cur = con.cursor(dictionary=True)
        return con, cur

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

    def get_db_version(self):
        """get database version"""
        self.cursor.execute("SELECT `mpx`.DB_VERSION() AS version;")
        return self.cursor.fetchone()["version"]

    def check_db_compatibility(self):
        """
        checks if the version of a given database is supported.
        Returns True or exits with error message.

        >>> dbm = getfixture('init_readonly_dbm')
        >>> dbm.check_db_compatibility()
        True

        """
        dbver = self.get_db_version()
        if dbver != SUPPORTED_DB_VERSION:
            sys.exit(
                "compatibility error: the given database is not compatible with this version of sonar (database version: "
                + str(dbver)
                + "; supported database version: "
                + str(SUPPORTED_DB_VERSION)
                + ")"
            )
        return True

    @property
    def lineage_sublineage_dict(self):
        if not self.__lineage_sublineage_dict:
            df = pd.read_sql("SELECT * FROM lineages", self.connection)
            self.__lineage_sublineage_dict = dict(zip(df.lineage, df.sublineage))
        return self.__lineage_sublineage_dict

    @property
    def default_reference(self):
        """
        property storing accession of the standard reference

        >>> dbm = getfixture('init_readonly_dbm')
        >>> dbm.default_reference
        'NC_063383.1'

        """
        if self.__default_reference is False:
            sql = "SELECT accession FROM mpx.reference WHERE standard = 1 LIMIT 1"
            self.__default_reference = self.cursor.execute(sql).fetchone()["accession"]
        return self.__default_reference

    @property
    def properties(self):
        """property storing propertie data as dict of dict whrere key is property name"""
        if self.__properties is False:
            sql = "SELECT * FROM mpx.property;"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            self.__properties = {} if not rows else {x["name"]: x for x in rows}
        return self.__properties

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

    # SETUP

    @staticmethod
    def get_uri(db_url):
        """
        returns  username password host port

        >>> sonarDBManager.get_uri("test.db")
        'file:test.db'
        """
        parsed_obj = urlparse(db_url)
        return parsed_obj

    @staticmethod
    def setup(db_url, debug=False):
        """
        setup database

        >>> dbfile = getfixture('tmpfile_name')
        >>> sonarDBManager.setup(dbfile)
        """
        sql = pkgutil.get_data(__name__, "data/db.sql").decode()
        commands = sql.split(";")

        if db_url is None:
            db_url = DB_URL

        uri = sonarDBManager.get_uri(db_url)
        try:
            con = mariadb.connect(
                user=uri.username,
                password=uri.password,
                host=uri.hostname,
                port=int(uri.port),
            )
            # if debug:
            #     con.set_trace_callback(logging.debug)
            cursor = con.cursor()
            for command in tqdm(commands, total=len(commands), desc="Execute stmt."):
                # logging.debug(command)
                command = command.strip()
                if command != "":
                    if debug:
                        logging.info(command)
                    cursor.execute(command)

            con.commit()
            con.close()

        except mariadb.Error as e:
            logging.error(f"Error in MariaDB: {e}")
            sys.exit(1)
        # with sqlite3.connect(uri + "?mode=rwc", uri=True) as con:
        #    if debug:
        #        con.set_trace_callback(logging.debug)
        #    con.executescript(sql)

    def add_codon(self, translation_table, codon, aa):
        """
        add codon amino acid relationship to database

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.add_codon(11, "ATG", "M")
        """
        sql = "INSERT IGNORE INTO translation (id, codon, aa) VALUES(?, ?, ?);"
        self.cursor.execute(sql, [translation_table, codon, aa])

    def add_property(self, name, datatype, querytype, description, standard=None):
        """
        adds a new property and returns the property id.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> id = dbm.add_property("NEW_PROP", "text", "text", "my new prop stores text information")

        """
        name = name.upper()
        if name in self.__illegal_properties:
            sys.exit(
                "error: '"
                + str(name)
                + "' is reserved and cannot be used as property name"
            )
        if not re.match("^[a-zA-Z0-9_]+$", name):
            sys.exit(
                "error: invalid property name (property names can contain only letters, numbers and underscores)"
            )
        if name in self.properties:
            sys.exit(
                "error: a property named "
                + name
                + " already exists in the given database."
            )
        try:
            sql = "INSERT INTO mpx.property (name, datatype, querytype, description, standard) VALUES(?, ?, ?, ?, ?);"
            self.cursor.execute(sql, [name, datatype, querytype, description, standard])
            self.__properties = False

            pid = self.properties[name]["id"]
            if standard is not None:
                sql = (
                    "INSERT INTO mpx.sample2property (property_id, value_"
                    + self.properties[name]["datatype"]
                    + ", sample_id) SELECT ?, ?, id FROM sample WHERE 1;"
                )
                vals = [pid, standard]
                self.cursor.execute(sql, vals)
        except sqlite3.Error as error:
            sys.exit(
                "error: failed to insert data into sqlite table (" + str(error) + ")"
            )
        return pid

    def add_translation_table(self, translation_table):
        """
        add codon amino acid relationship for a given translation table to database.
        None-sense codons including gaps are assigned to a 0-lenth string.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.add_translation_table(1)

        """
        sql = "SELECT COUNT(*) FROM translation  WHERE id = ?;"
        self.cursor.execute(sql, [translation_table])
        count_result = self.cursor.fetchone()["COUNT(*)"]
        if count_result != 4096:  # TODO: need to ask Stephan  about this number.
            for codon in itertools.product("ATGCRYSWKMBDHVN-", repeat=3):
                codon = "".join(codon)
                try:
                    aa = str(Seq.translate(codon, table=translation_table))
                except Exception:
                    aa = ""
                self.add_codon(translation_table, codon, aa)

    def add_reference(
        self, accession, description, organism, translation_table, standard=0
    ):
        """
        Adds a reference to a database and returns the assidnged row id.
        None-sense codons including gaps are assigned to a 0-lenth string.
        The reference is set to the default reference if standard is 1.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.add_reference("REF1", "my new reference", "virus X", 1)

        """
        self.add_translation_table(translation_table)
        if standard:
            sql = "UPDATE reference SET standard = 0 WHERE standard != 0"
            self.cursor.execute(sql)
        sql = "INSERT INTO reference (id, accession, description, organism, translation_id, standard) VALUES(?, ?, ?, ?, ?, ?);"
        self.cursor.execute(
            sql, [None, accession, description, organism, translation_table, standard]
        )
        return self.cursor.lastrowid

    # INSERTING DATA
    def insert_property(self, sample_id, property_name, property_value):
        """
        Inserts/Updates a property value of a given sample in the database.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.insert_property(1, "LINEAGE", "BA.5")

        """
        try:
            sql = (
                "INSERT INTO sample2property (sample_id, property_id, value_"
                + self.properties[property_name]["datatype"]
                + ") VALUES(?, ?, ?)"
                + " ON DUPLICATE KEY UPDATE value_"
                + self.properties[property_name]["datatype"]
                + "=?"
            )
            # tmp solution for insert empty date
            # Incorrect date value: ''
            if self.properties[property_name]["datatype"] == "date":
                if property_value == "":
                    property_value = None

            self.cursor.execute(
                sql,
                [
                    sample_id,
                    self.properties[property_name]["id"],
                    property_value,
                    property_value,
                ],
            )
        except Exception as e:
            logging.error(e)
            logging.error(f"Sample ID:'{str(sample_id)}' cannot be processed")
            sys.exit("If you need an assistance, please contact us.")

    def insert_sequence(self, seqhash):
        """
        inserts a sequence repesented by its hash to the database. If the hash is known it is ignored.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.insert_sequence("1a1f34ef4318911c2f98a7a1d6b7e9217c4ae1d1")

        """
        sql = "INSERT IGNORE INTO sequence (seqhash) VALUES(?);"
        self.cursor.execute(sql, [seqhash])

    def insert_sample(self, sample_name, seqhash):
        """
        Inserts or updates a sample/genome in the database.
        Returns the rowid.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.insert_sample("my_new_sample", "1a1f34ef4318911c2f98a7a1d6b7e9217c4ae1d1")

        """
        self.insert_sequence(seqhash)
        # Right we use INSERT IGNORE INTO, we might want to use ON DUP in the future
        # Note: INSERT INTO ..... ON DUPLICATE KEY UPDATE name=VALUES(name), seqhash=VALUES(seqhash),
        # "REPLACE INTO sample (name, seqhash, datahash) VALUES(?, ?, ?);"

        sql = "INSERT IGNORE INTO sample (name, seqhash, datahash) VALUES(?, ?, ?);"
        self.cursor.execute(sql, [sample_name, seqhash, ""])
        sql = "SELECT id FROM sample WHERE name = ?;"
        self.cursor.execute(sql, [sample_name])
        sid = self.cursor.fetchone()
        if sid:
            sid = sid["id"]

        for pname in self.properties:
            if not self.properties[pname]["standard"] is None:
                self.insert_property(sid, pname, self.properties[pname]["standard"])
        return sid

    def delete_alignment(self, seqhash=None, element_id=None):
        condition = ""

        if seqhash:
            condition = f" seqhash = '{seqhash}'"
        if element_id:
            if condition:
                condition = condition + f" AND element_id = '{element_id}'"
            else:
                condition = f" element_id = '{element_id}'"
        if not condition:
            logging.info("Nothing to delete an alignment")
            return

        sql = f"DELETE FROM alignment WHERE {condition};"
        self.cursor.execute(sql)

    def insert_alignment(self, seqhash, element_id):
        """
        Inserts a sequence-alignment relation insert the database if not existing.
        Returns the rowid.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.insert_alignment("1a1f34ef4318911c2f98a7a1d6b7e9217c4ae1d1", 1)

        """
        # sql = "INSERT IGNORE INTO alignment (id, seqhash, element_id) VALUES(?, ?, ?);"
        # self.cursor.execute(sql, [None, seqhash, element_id])
        sql = "INSERT IGNORE INTO alignment ( seqhash, element_id) VALUES( ?, ?);"
        self.cursor.execute(sql, [seqhash, element_id])
        # print(sql, [seqhash, element_id])
        sql = "SELECT id FROM alignment WHERE element_id = ? AND seqhash = ?;"
        self.cursor.execute(sql, [element_id, seqhash])
        # print(sql, [element_id, seqhash])
        rowid = self.cursor.fetchone()
        if rowid:
            rowid = rowid["id"]
            # print("rowid", rowid)
        else:
            logging.error("Cannot get rowid:", rowid)
            sys.exit("Cannot get rowid:")
        return rowid

    def insert_molecule(
        self,
        reference_id,
        type,
        accession,
        symbol,
        description,
        segment,
        length,
        standard=0,
    ):
        """
        Inserts a molecule in the database. Molecule is set the default molecule if standard is 1.
        Returns the rowid of the inserted/updated molecule.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.insert_molecule(1, "plasmid", "CP028427.1", "pARLON1", "Gulosibacter molinativorax strain ON4 plasmid pARLON1, complete sequence", 1, 37013)

        """
        if symbol.strip() == "":
            symbol = accession
        if standard:
            # we update standard to 1 to put every molecule loaded into _source
            sql = "UPDATE molecule SET standard = ? WHERE reference_id = ? AND standard = 1"
            self.cursor.execute(sql, [0, reference_id])
        sql = "INSERT INTO molecule (id, reference_id, type, accession, symbol, description, segment, length, standard) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?);"
        self.cursor.execute(
            sql,
            [
                None,
                reference_id,
                type,
                accession,
                symbol,
                description,
                segment,
                length,
                standard,
            ],
        )
        sql = "SELECT id FROM molecule WHERE accession = ?"
        self.cursor.execute(sql, [accession])
        mid = self.cursor.fetchone()["id"]
        return mid

    def insert_element(
        self,
        molecule_id,
        type,
        accession,
        symbol,
        description,
        start,
        end,
        strand,
        sequence,
        standard=0,
        parent_id=0,
        parts=None,
    ):
        """
        Inserts a element such as a source, cds or protein in the database. Molecule is set the default molecule if standard is 1.
        If element is not linearly encoded on its molecule, list of tuples containing start and end coordinates can be provided as parts.
        Returns the rowid of the inserted/updated molecule.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.insert_element(1, "protein", "GMOLON4_3257", "NlpD", "M23/M37 family peptidase", 5579, 6199, 1, "MKGLRSSNPKGEASD")

        """
        if symbol.strip() == "":
            symbol = accession
        if standard:
            sql = (
                "UPDATE element SET standard = ? WHERE molecule_id = ? AND standard = 1"
            )
            self.cursor.execute(sql, [0, molecule_id])
        sql = "INSERT INTO element (id, molecule_id, type, accession, symbol, description, start, end, strand, sequence, standard, parent_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
        if not strand:
            strand = 0

        # print( [ molecule_id,
        #        type,
        #        accession,
        #        symbol,
        #        description,
        #        start,
        #        end,
        #        strand,
        #        standard,
        #        parent_id])
        self.cursor.execute(
            sql,
            [
                None,
                molecule_id,
                type,
                accession,
                symbol,
                description,
                start,
                end,
                strand,
                sequence,
                standard,
                parent_id,
            ],
        )
        sql = "SELECT id FROM element WHERE accession = ? AND molecule_id =?;"
        self.cursor.execute(sql, [accession, molecule_id])
        eid = self.cursor.fetchone()["id"]
        if parts is not None:
            for part in parts:
                sql = "INSERT IGNORE INTO elempart (element_id, start, end, strand, base, segment) VALUES(?, ?, ?, ?, ?, ?);"
                self.cursor.execute(sql, [eid] + part)
        return eid

    def insert_variant(
        self, alignment_id, element_id, ref, alt, start, end, label, parent_id=""
    ):
        """
        Inserts a variant if it does not exist in the database. Based on the type of the element the element id refers to,
        this variant describes a change on nucleotide (source or cds elements) or amino acid level (protein elements).
        The parent_id is supposed to store the element id of the encoding element (the corresponding source for cds and
        the corresponding cds for proteins, respectively).
        Returns the rowid of the inserted variant.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> rowid = dbm.insert_variant(1, 1, "A", "T", 0, 1, "A1T")

        """
        sql = "INSERT IGNORE INTO variant (id, element_id, start, end, ref, alt, label, parent_id) VALUES(?, ?, ?, ?, ?, ?, ?, ?);"
        self.cursor.execute(
            sql, [None, element_id, start, end, ref, alt, label, parent_id]
        )
        vid = self.get_variant_id(element_id, start, end, ref, alt)
        sql = "INSERT IGNORE INTO alignment2variant (alignment_id, variant_id) VALUES(?, ?);"
        self.cursor.execute(sql, [alignment_id, vid])
        return vid

    # DELETING DATA
    def delete_samples(self, *sample_names):
        """
        Deletes one or more given samples based on their names if existing.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.delete_samples("NC_045512")

        """
        sql = (
            "DELETE FROM sample WHERE name IN ("
            + ", ".join(["?"] * len(sample_names))
            + ");"
        )
        self.cursor.execute(sql, sample_names)

    def delete_property(self, property_name):
        """
        Deletes a property all related data linked to samples based on the property name
        from database if the property exists.

        >>> dbm = getfixture('init_writeable_dbm')
        >>> dbm.delete_property("NEW_PROP")

        """
        if property_name in self.properties:
            sql = "DELETE FROM sample2property WHERE property_id = ?;"
            self.cursor.execute(sql, [self.properties[property_name]["id"]])
            sql = "DELETE FROM property WHERE name = ?;"
            self.cursor.execute(sql, [property_name])
            del self.properties[property_name]

    def delete_reference(self, ref_accession):
        sql = "DELETE FROM reference WHERE accession = ?;"
        self.cursor.execute(sql, [ref_accession])

    def delete_seqhash(self, seqhash):
        sql = "DELETE FROM sequence WHERE seqhash = ?;"
        self.cursor.execute(sql, [seqhash])

    # SELECTING DATA
    # # Do we need this function?
    # def sample_exists(self, sample_name):
    #    """
    #    Checks if a sample name exists and returns True and False, respectively.
    #
    #    >>> dbm = getfixture('init_readonly_dbm')
    #    >>> dbm.sample_exists("seq01")
    #    True
    #
    #    """
    #    sql = "SELECT EXISTS(SELECT 1 FROM sample WHERE name=? LIMIT 1) as found"
    #    return bool(self.cursor.execute(sql, [sample_name]).fetchone()["found"])

    def get_sample_id(self, sample_name):
        """
        Returns the rowid of a sample based on its name if it exists (else None is returned).

        >>> dbm = getfixture('init_readonly_dbm')
        >>> id = dbm.get_sample_id("seq01")

        """
        sql = "SELECT id FROM sample WHERE name = ? LIMIT 1;"
        self.cursor.execute(sql, [sample_name])
        row = self.cursor.fetchone()
        return None if row is None else row["id"]

    def our_match(self):
        sql = """
            SELECT
                t1.label,
                count(*)
            FROM
                variant t1
            JOIN alignment2variant t2 ON t1.id = t2.variant_id
            JOIN alignment t3 ON t2.alignment_id = t3.id
            JOIN sequence t4 ON t3.seqhash = t4.seqhash
            JOIN sample t5 ON t4.seqhash = t5.seqhash
            GROUP BY t1.label;
        """
        self.cursor.execute(sql)
        row = self.cursor.fetchall()
        return row

    def get_sample_data(self, sample_name):
        """
        Returns a tuple of rowid and seqhash of a sample based on its name if it exists (else a tuple of Nones is returned).
        """
        sql = "SELECT id, seqhash FROM sample WHERE name = ? LIMIT 1;"
        self.cursor.execute(sql, [sample_name])
        row = self.cursor.fetchone()
        return (row["id"], row["seqhash"]) if row else (None, None)

    def get_alignment_by_seqhash(self, seqhash):
        """
        Returns the rowid of a sample based on the respective seqhash  If no
        alignment of the given sequence hash, it will return empty list.

        Check if there is a sample that doesn't align to any reference.
        """
        sql = "SELECT id FROM alignment WHERE seqhash = ? ;"
        self.cursor.execute(sql, [seqhash])
        row = self.cursor.fetchall()
        if not row:
            return []
        return [x["id"] for x in row]

    def get_alignment_id(self, seqhash, element_id):
        """
        Returns the rowid of a sample based on the respective seqhash and element. If no
        alignment of the given sequence to the given element has been stored None is returned.
        """
        sql = "SELECT id FROM alignment WHERE element_id = ? AND seqhash = ? LIMIT 1;"
        self.cursor.execute(sql, [element_id, seqhash])
        row = self.cursor.fetchone()
        return None if row is None else row["id"]

    def get_default_reference_accession(self):
        """
        Returns acession of the reference defined as default in the database.
        """
        sql = "SELECT accession FROM reference WHERE standard=1"
        self.cursor.execute(sql)
        return self.cursor.fetchone()["accession"]

    def check_sql_string(self, sql, values):
        unique = "%PARAMETER%"
        sql = sql.replace("?", unique)
        for v in values:
            sql = sql.replace(unique, repr(v), 1)
        return sql

    def get_molecule_ids(self, reference_accession=None):
        """
        Returns a dictionary with accessions as keys and respective rowids as values for
        all molecules related to a given reference
        or all references if reference_accession is None.

        standard = 1  which is default reference

        """

        if reference_accession:
            condition = "`reference.accession` = ?"
            val = [reference_accession]
        else:
            # to output all
            # condition = "`reference.standard` = ?"
            # val = [1]
            val = [1]
            condition = "1  = ?"
        sql = (
            "SELECT `molecule.accession`, `molecule.id` FROM referenceView WHERE "
            + condition
        )
        # print(sql, val)
        self.cursor.execute(sql, val)
        output = {
            x["molecule.accession"]: x["molecule.id"]
            for x in self.cursor.fetchall()
            if x is not None
        }
        # print(output)
        return output

    # Do we need this function?
    # def get_molecule_id(self, molecule_accession):
    #    """
    #    Returns the rowid of a molecule based on its accession (or None if the
    #    accession does not exist).
    #    """
    #    sql = "SELECT id FROM molecule WHERE accession = ?;"
    #    row = self.cursor.execute(sql, [molecule_accession]).fetchone()
    #    if row:
    #        row = row["id"]
    #    return row

    def get_molecule_data(self, *fields, reference_accession=None):
        """
        Returns a dictionary with molecule accessions as keys and sub-dicts as values for all molecule
        of a given (or the default) reference. The sub-dicts store all table field names
        (or, alternatively, the given table field names only) as keys and the stored data as values.
        """
        if not fields:
            fields = "*"
        elif "`molecule.accession`" not in fields:
            fields = list(fields) + ["`molecule.accession`"]
        if reference_accession:
            condition = "`reference.accession` = ?"
            vals = [reference_accession]
        else:
            condition = "`reference.standard` = ?"
            vals = [1]
        sql = (
            "SELECT "
            + ", ".join(fields)
            + " FROM referenceView WHERE "
            + condition
            + ";"
        )
        self.cursor.execute(sql, vals)
        row = self.cursor.fetchall()
        if row:
            return {x["molecule.accession"]: x for x in row}
        return {}

    def get_elements(self, molecule_id, *types):
        """
        Returns a dictionary with molecule accessions as keys and molecule data dicts as values for all molecule
        of a given (or the default) reference. By providing the respective table fields the extend of data dicts can be
        limited.
        """
        sql = "SELECT * FROM element WHERE molecule_id = ?"
        if types:
            sql += " AND type IN (" + ", ".join(["?"] * len(types)) + ");"
        row = self.cursor.execute(sql, [molecule_id] + list(types))
        row = self.cursor.fetchall()
        if not row:
            return []
        return row

    def get_element_ids(self, reference_accession=None, type=None):
        # this molecule_ids will return all ids if reference_accession is NOne
        molecule_ids = list(
            self.get_molecule_ids(reference_accession=reference_accession).values()
        )
        sql = (
            "SELECT id FROM element WHERE molecule_id IN ("
            + ", ".join(["?"] * len(molecule_ids))
            + ")"
        )
        if type:
            sql += " AND type = ?"
            molecule_ids.append(type)
        # print(sql, molecule_ids)
        self.cursor.execute(sql, molecule_ids)
        row = self.cursor.fetchall()
        if not row:
            return []
        return [x["id"] for x in row]

    def get_ele_ofref_bynoCDS(self):
        """
        get all element id of reference where ref did not contain CDS data.
        """
        sql = """SELECT t1.* FROM element t1 LEFT JOIN element t2 ON t1.id = t2.parent_id WHERE t2.id IS NULL AND t1.type = "source" """
        self.cursor.execute(sql)
        row = self.cursor.fetchall()
        return row

    def get_source(self, molecule_id):
        return self.get_elements(molecule_id, "source")[0]

    def get_annotation(
        self,
        reference_accession=None,
        molecule_accession=None,
        element_accession=None,
        element_type=None,
        fields=["*"],
    ):
        conditions = []
        vals = []
        if reference_accession:
            conditions.append("`reference.accession` = ?")
            vals.append(reference_accession)
        else:
            conditions.append("`reference.standard` = ?")
            vals.append(1)
        if molecule_accession:
            conditions.append("`molecule.accession` = ?")
            vals.append(molecule_accession)
        else:
            conditions.append("`molecule.standard` = ?")
            vals.append(1)
        if element_accession:
            conditions.append("`element.accession` = ?")
            vals.append(element_accession)
        elif not element_type:
            conditions.append("`element.type` = ?")
            vals.append("source")
        if element_type:
            conditions.append("`element.type` = ?")
            vals.append(element_type)
        sql = (
            "SELECT "
            + ", ".join(fields)
            + " FROM referenceView WHERE "
            + " AND ".join(conditions)
            + ' ORDER BY "reference.id" ASC, "molecule.id" ASC, "element.id" ASC, "element.segment" ASC;'
        )
        self.cursor.execute(sql, vals)
        rows = self.cursor.fetchall()
        print()
        return rows

    def get_samples_by_ref(self, reference_accession=None):

        if reference_accession:
            sql = "SELECT `sample.id` AS sample_ID, `sample.name` AS sample_name , `sample.seqhash` AS seqhash FROM alignmentView WHERE `reference.accession`=%s ;"
            self.cursor.execute(sql, [reference_accession])
            rows = self.cursor.fetchall()
            return rows
        else:
            return None

    def get_alignment_data(self, sample_name, reference_accession=None):
        if reference_accession is None:
            sql = "SELECT `reference.accession` as acc FROM alignmentView WHERE `sample.name` =%s LIMIT 1"
            self.cursor.execute(sql, [sample_name])
            reference_accession = self.cursor.fetchone()
            if reference_accession is None:
                return ""
            reference_accession = reference_accession["acc"]
        sql = "SELECT `element.sequence`, `element.symbol`, `element.id` FROM alignmentView WHERE `sample.name` =%s AND `reference.accession` =%s"
        self.cursor.execute(sql, [sample_name, reference_accession])
        return self.cursor.fetchall()

    def get_variant_id(self, element_id, start, end, ref, alt):
        sql = "SELECT id FROM variant WHERE element_id = ? AND start = ? AND end = ? AND ref = ? AND alt = ?;"
        self.cursor.execute(sql, [element_id, start, end, ref, alt])
        row = self.cursor.fetchone()
        return None if row is None else row["id"]

    def iter_dna_variants(self, sample_name, *element_ids):
        if len(element_ids) == 1:
            condition = " = ?"
        elif len(element_ids) > 1:
            condition = " IN (" + ", ".join(["?"] * len(element_ids)) + ")"
        else:
            condition = ""
        # print("Condition:" + condition)
        sql = (
            """ SELECT  variant.element_id as `element.id`,
                    variant.start as `variant.start`,
                    variant.end as  `variant.end`,
                    variant.ref as  `variant.ref`,
                    variant.alt as `variant.alt`
                    FROM
                        ( SELECT sample.seqhash
                        FROM sample
                        WHERE sample.name = ?
                        ) AS sample_T
                    INNER JOIN alignment
                        ON sample_T.seqhash = alignment.seqhash
                    INNER JOIN alignment2variant
                        ON alignment.id = alignment2variant.alignment_id
                    INNER JOIN	variant
                        ON alignment2variant.variant_id = variant.id
                        WHERE  variant.element_id """
            + condition
        )
        self.cursor.execute(sql, [sample_name] + list(element_ids))
        for row in self.cursor.fetchall():
            if row["variant.start"] is not None:
                yield row

    def count_samples(self):
        sql = "SELECT COUNT(*) FROM sample;"
        self.cursor.execute(sql)
        return self.cursor.fetchone()["COUNT(*)"]

    def count_sequences(self):
        sql = "SELECT COUNT(DISTINCT seqhash) FROM sample;"
        self.cursor.execute(sql)
        return self.cursor.fetchone()["COUNT(DISTINCT seqhash)"]

    def count_property(self, property_name, distinct=False, ignore_standard=False):
        d = "DISTINCT " if distinct else ""
        c = "WHERE property_id = ?"
        v = [self.properties[property_name]["id"]]
        if ignore_standard and self.properties[property_name]["standard"] is not None:
            c += " AND value_" + self.properties[property_name]["datatype"] + " != ?"
            v.append(self.properties[property_name]["standard"])
        sql = (
            "SELECT COUNT("
            + d
            + " value_"
            + self.properties[property_name]["datatype"]
            + ") as count FROM sample2property "
            + c
            + ";"
        )
        self.cursor.execute(sql, v)
        return self.cursor.fetchone()["count"]

    def get_translation_dict(self, translation_id):
        sql = "SELECT codon, aa FROM translation WHERE id = ?;"
        self.cursor.execute(sql, [translation_id])
        rows = self.cursor.fetchall()
        return {x["codon"]: x["aa"] for x in rows}

    # Do we need these functions?
    # def get_earliest_import(self):
    #    sql = "SELECT MIN(imported) as import FROM genome WHERE import IS NOT NULL;"
    #    return self.cursor.execute(sql).fetchone()["import"]

    # def get_latest_import(self):
    #    sql = "SELECT MAX(imported) as import FROM genome WHERE import IS NOT NULL;"
    #    return self.cursor.execute(sql).fetchone()["import"]

    # def get_earliest_date(self):
    #    sql = "SELECT MIN(date) as date FROM genome WHERE date IS NOT NULL;"
    #    return self.cursor.execute(sql).fetchone()["date"]

    # def get_latest_date(self):
    #    sql = "SELECT MAX(date) as date FROM genome WHERE date IS NOT NULL;"
    #    return self.cursor.execute(sql).fetchone()["date"]

    def get_element_parts(self, element_id=None):
        sql = "SELECT start, end, strand FROM elempart WHERE element_id = ? ORDER BY segment;"
        self.cursor.execute(sql, [element_id])
        return self.cursor.fetchall()

    def get_sequence(self, element_id=None):
        sql = "SELECT sequence, type FROM element WHERE id = ?;"
        self.cursor.execute(sql, [element_id])
        row = self.cursor.fetchone()
        return None if row is None else row["sequence"]

    def extract_sequence(
        self, element_id=None, translation_table=None, molecule_id=None
    ):
        sql = "SELECT sequence, type, id, parent_id FROM element WHERE id = ? AND molecule_id = ?;"
        self.cursor.execute(sql, [element_id, molecule_id])
        row = self.cursor.fetchone()
        if not row:
            return None
        element_id = row["id"]
        while row and row["type"] not in {"source", "CDS"}:
            sql = "SELECT sequence, type, parent_id FROM element WHERE id = ?;"
            # why use parent_id but WHERE id = ??ß
            self.cursor.execute(sql, [row["parent_id"]])
            row = self.cursor.fetchone()
        sequence = row["sequence"]
        parts = []
        for part in self.get_element_parts(element_id):
            parts.append(
                FeatureLocation(part["start"], part["end"], strand=part["strand"])
            )
        feat = CompoundLocation(parts) if len(parts) > 1 else parts[0]
        if translation_table is None:
            return str(feat.extract(sequence))
        return str(
            Seq(feat.extract(sequence)).translate(
                table=translation_table, stop_symbol=""
            )
        )

    # Add/Update lineages into Table
    def add_update_lineage(self, _df):
        logging.info("Prepare: %d" % len(_df))
        sql = "INSERT OR REPLACE INTO lineages (lineage, sublineage) VALUES(?, ?);"
        for ind in _df.index:
            self.cursor.execute(sql, (_df["lineage"][ind], _df["sublineage"][ind]))

    def get_conditional_expr(self, field, operator, *vals):
        condlist = []
        vallist = []

        # transforming operators
        if operator == "=" and len(vals) > 1:
            operator = "IN"
        elif operator == "!=" and len(vals) > 1:
            operator = "NOT IN"

        # creating conditions
        if operator == "IN" or operator == "NOT IN":
            condlist.append(
                field + " " + operator + "(" + ", ".join(["?"] * len(vals)) + ")"
            )
            vallist.extend(vals)

        elif operator == "BETWEEN" or operator == "NOT BETWEEN":
            for val in vals:
                condlist.append(field + " " + operator + " ? AND ?")
                vallist.extend(val)

        else:
            condlist.extend([field + " " + operator + " ?"] * len(vals))
            vallist.extend(vals)

        return condlist, vallist

    def query_numeric(self, field, *vals, link="AND"):
        link = " " + link.strip() + " "
        defaultop = "="
        op1 = re.compile(r"^(\^*)((?:>|>=|<|<=|!=|=)?)(-?[1-9]+[0-9]*)$")
        op2 = re.compile(r"^(\^*)(-?[1-9]+[0-9]*):(-?[1-9]+[0-9]*)$")
        errmsg = (
            "query error: numeric value or range expected for field " + field + "(got: "
        )
        data = defaultdict(set)
        conditions = []
        vallist = []

        for val in vals:
            val = str(val).strip()

            # single value
            if ":" not in val:
                match = op1.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                op = match.group(2) if match.group(2) else defaultop
                operator = (
                    self.__operators["negated"][op]
                    if match.group(1)
                    else self.__operators["genuine"][op]
                )
                val = match.group(3)
                data[operator].add(val)

            # range
            else:
                match = op2.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                operator = (
                    self.__operators["negated"]["BETWEEN"]
                    if match.group(1)
                    else self.__operators["genuine"]["BETWEEN"]
                )
                val = (match.group(2), match.group(3))
                data[operator].add(val)

        for operator, valset in data.items():
            condition, vals = self.get_conditional_expr(field, operator, *valset)
            conditions.extend(condition)
            vallist.extend(vals)

        return link.join(conditions), vallist

    def query_float(self, field, *vals, link="AND"):
        link = " " + link.strip() + " "
        defaultop = "="
        op1 = re.compile(r"^(\^*)((?:>|>=|<|<=|!=|=)?)(-?[1-9]+[0-9]*(?:.[0-9]+)*)$")
        op2 = re.compile(
            r"^(\^*)(-?[1-9]+[0-9]*(?:.[0-9]+)*):(-?[1-9]+[0-9]*(?:.[0-9]+)*)$"
        )
        errmsg = (
            "query error: decimal value or range expected for field " + field + "(got: "
        )
        data = defaultdict(set)
        conditions = []
        vallist = []

        for val in vals:
            val = str(val).strip()
            # single value
            if ":" not in val:
                match = op1.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                op = match.group(2) if match.group(2) else defaultop
                operator = (
                    self.__operators["negated"][op]
                    if match.group(1)
                    else self.__operators["genuine"][op]
                )
                val = match.group(3)
                data[operator].add(val)

            # range
            else:
                match = op2.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                operator = (
                    self.__operators["negated"]["BETWEEN"]
                    if match.group(1)
                    else self.__operators["genuine"]["BETWEEN"]
                )
                val = (match.group(2), match.group(3))
                data[operator].add(val)

        for operator, valset in data.items():
            condition, vals = self.get_conditional_expr(field, operator, *valset)
            conditions.extend(condition)
            vallist.extend(vals)

        return link.join(conditions), vallist

    def query_dates(self, field, *vals, link="AND"):
        link = " " + link.strip() + " "
        defaultop = "="
        op1 = re.compile(r"^(\^*)((?:>|>=|<|<=|!=|=)?)([0-9]{4}-[0-9]{2}-[0-9]{2})$")
        op2 = re.compile(
            r"^(\^*)([0-9]{4}-[0-9]{2}-[0-9]{2}):([0-9]{4}-[0-9]{2}-[0-9]{2})$"
        )
        errmsg = (
            "query error: date or date range expected for field " + field + " (got: "
        )
        data = defaultdict(set)
        conditions = []
        vallist = []

        for val in vals:
            val = str(val).strip()
            # single date
            if ":" not in val:
                match = op1.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                op = match.group(2) if match.group(2) else defaultop
                operator = (
                    self.__operators["negated"][op]
                    if match.group(1)
                    else self.__operators["genuine"][op]
                )
                val = match.group(3)
                data[operator].add(val)

            # date range
            else:
                match = op2.match(val)
                if not match:
                    sys.exit(errmsg + val + ")")
                operator = (
                    self.__operators["negated"]["BETWEEN"]
                    if match.group(1)
                    else self.__operators["genuine"]["BETWEEN"]
                )
                val = (match.group(2), match.group(3))
                data[operator].add(val)

        for operator, valset in data.items():
            condition, vals = self.get_conditional_expr(field, operator, *valset)
            conditions.extend(condition)
            vallist.extend(vals)

        return link.join(conditions), vallist

    def query_string(self, field, *vals, link="AND"):
        link = " " + link.strip() + " "
        data = defaultdict(set)
        conditions = []
        vallist = []

        for val in vals:
            if val.startswith("^"):
                val = val[1:]
                opkey = "negated"
            else:
                opkey = "genuine"
            if val.startswith("%") or val.endswith("%"):
                operator = self.__operators[opkey]["LIKE"]
            else:
                operator = self.__operators[opkey]["="]

            data[operator].add(val)

        for operator, valset in data.items():
            condition, vals = self.get_conditional_expr(field, operator, *valset)
            conditions.extend(condition)
            vallist.extend(vals)

        return link.join(conditions), vallist

    def query_zip(self, field, *vals, link="AND"):
        link = " " + link.strip() + " "
        data = defaultdict(set)
        conditions = []
        vallist = []

        for val in vals:
            if val.startswith("^"):
                val = val[1:]
                opkey = "negated"
            else:
                opkey = "genuine"
            val = val.strip("%") + "%"
            operator = self.__operators[opkey]["LIKE"]

            data[operator].add(val)

        for operator, valset in data.items():
            condition, vals = self.get_conditional_expr(field, operator, *valset)
            conditions.extend(condition)
            vallist.extend(vals)

        return link.join(conditions), vallist

    def query_metadata(self, name, *vals):
        conditions = ["`property_id` = ?"]
        valueList = [self.properties[name]["id"]]
        targetfield = "value_" + self.properties[name]["datatype"]

        # query dates
        if self.properties[name]["querytype"] == "date":
            a, b = self.query_dates(targetfield, *vals)
            conditions.append(a)
            valueList.extend(b)

        # query numeric
        elif self.properties[name]["querytype"] == "numeric":
            a, b = self.query_numeric(targetfield, *vals)
            conditions.append(a)
            valueList.extend(b)

        # query text
        elif self.properties[name]["querytype"] == "text":
            a, b = self.query_string(targetfield, *vals)
            conditions.append(a)
            valueList.extend(b)

        # query zip
        elif self.properties[name]["querytype"] == "zip":
            a, b = self.query_zip(targetfield, *vals)
            conditions.append(a)
            valueList.extend(b)
        # query float
        elif self.properties[name]["querytype"] == "float":
            a, b = self.query_float(targetfield, *vals)
            conditions.append(a)
            valueList.extend(b)
        else:
            sys.exit(
                "error: unknown query type '"
                + self.properties[name]["querytype"]
                + "' for property '"
                + name
                + "'."
            )

        return (
            "SELECT `sample_id` AS id FROM sample2property WHERE "
            + " AND ".join(conditions),
            valueList,
        )

    def get_ref_ID_base_query_profile(  # noqa: 901
        self, *vars, reference_accession=None
    ):
        iupac_nt_code = {
            "A": set("A"),
            "C": set("C"),
            "G": set("G"),
            "T": set("T"),
            "R": set("AGR"),
            "Y": set("CTY"),
            "S": set("GCS"),
            "W": set("ATW"),
            "K": set("GTK"),
            "M": set("ACM"),
            "B": set("CGTB"),
            "D": set("AGTD"),
            "H": set("ACTH"),
            "V": set("ACGV"),
            "N": set("ACGTRYSWKMBDHVN"),
            "n": set("N"),
        }
        iupac_aa_code = {
            "A": set("A"),
            "R": set("R"),
            "N": set("N"),
            "D": set("D"),
            "C": set("C"),
            "Q": set("Q"),
            "E": set("E"),
            "G": set("G"),
            "H": set("H"),
            "I": set("I"),
            "L": set("L"),
            "K": set("K"),
            "M": set("M"),
            "F": set("F"),
            "P": set("P"),
            "S": set("S"),
            "T": set("T"),
            "W": set("W"),
            "Y": set("Y"),
            "V": set("V"),
            "U": set("U"),
            "O": set("O"),
            "B": set("DNB"),
            "Z": set("EQZ"),
            "J": set("ILJ"),
            "Φ": set("VILFWYMΦ"),
            "Ω": set("FWYHΩ"),
            "Ψ": set("VILMΨ"),
            "π": set("PGASπ"),
            "ζ": set("STHNQEDKRζ"),
            "+": set("KRH+"),
            "-": set("DE-"),
            "X": set("ARNDCQEGHILKMFPSTWYVUOBZJΦΩΨπζ+-X"),
            "x": set("X"),
        }
        del_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?del:(=?[0-9]+)(|-=?[0-9]+)?$")
        snv_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?([A-Z]+)([0-9]+)(=?[A-Zxn]+)$")

        # set variants and generate sql
        base_sql = "SELECT DISTINCT(`reference.id`) AS id FROM variantView WHERE "
        intersect_sqls = []
        intersect_vals = []
        except_sqls = []
        except_vals = []
        for var in vars:
            c = []  # condition
            v = []  # variable

            if var.startswith("^"):
                var = var[1:]
                negate = True
            else:
                negate = False

            # variant typing
            if match := snv_regex.match(var):
                snv = True
            elif match := del_regex.match(var):
                snv = False
            else:
                logging.error("'" + var + "' is not a valid variant definition.")
                sys.exit(
                    "Please check the query statement,(IUPAC AA/NT codes, NT format(e.g. A3451T), AA format(e.g. S:N501Y))"
                )
            # set molecule
            if match.group(1):
                c.append("`molecule.symbol` = ?")
                v.append(match.group(1)[:-1])
            else:
                c.append("`molecule.standard` = ?")
                v.append(1)

            # set element
            if match.group(2):
                c.append("`element.type` = ?")
                v.append("cds")
                c.append("`element.symbol` = ?")
                v.append(match.group(2)[:-1])
                code = iupac_aa_code
            else:
                c.append("`element.standard` = ?")
                v.append(1)
                code = iupac_nt_code

            # snp  handling
            if snv:
                c.append("`variant.start` = ?")
                v.append(int(match.group(4)) - 1)
                c.append("`variant.end` = ?")
                v.append(int(match.group(4)))
                c.append("`variant.ref` = ?")
                v.append(match.group(3))
                try:
                    # explicit alternate allele
                    if match.group(5).startswith("="):
                        c.append("`variant.alt` = ?")
                        v.append(match.group(5)[1:])

                    # potentially ambiguous alternate snp
                    elif len(match.group(5)) == 1:
                        l = len(code[match.group(5)])
                        if l == 1:
                            match_group5 = (
                                match.group(5).upper()
                                if match.group(5) == "n" or match.group(5) == "x"
                                else match.group(5)
                            )
                            c.append("`variant.alt` = ?")
                            v.append(match_group5)
                        else:
                            c.append("`variant.alt` IN (" + ", ".join(["?"] * l) + ")")
                            v.extend(code[match.group(5)])

                    # potentially ambiguous alternate insert
                    else:
                        a = [
                            "".join(x)
                            for x in itertools.product(
                                *[code[x] for x in match.group(5)]
                            )
                        ]
                        l = len(a)
                        if l == 1:
                            a = a.upper() if a == "n" or a == "x" else a
                            c.append("`variant.alt` = ?")
                            v.extend(a)
                        else:
                            c.append("`variant.alt` IN (" + ", ".join(["?"] * l) + ")")
                            v.extend(a)
                except KeyError:
                    logging.error("'" + var + "' is not a valid input")
                    sys.exit(
                        "Please check the query statement,(IUPAC AA/NT codes, NT format(e.g. A3451T), AA format(e.g. S:N501Y))"
                    )
            # deletion handling
            else:
                s = match.group(3)
                e = match.group(4)[1:]
                # if del:=1-=60 meanse exact search del:1-60
                # del:1-60 means range search--> it could be del:1-11 or del:1-60
                if s.startswith("="):
                    s = s[1:]
                    c.append("`variant.start` = ?")
                else:
                    c.append("`variant.start` >= ?")

                if e.startswith("="):
                    e = e[1:]
                    c.append("`variant.end` = ?")
                else:
                    c.append("`variant.end` <= ?")
                v.append(int(s) - 1)
                v.append(int(e))

                c.append("`variant.alt` = ?")
                v.append(" ")

            # assemble sub-sql
            if negate:
                except_sqls.append(base_sql + " AND ".join(c))
                except_vals.extend(v)
            else:
                intersect_sqls.append(base_sql + " AND ".join(c))
                intersect_vals.extend(v)

        # assemble final sql
        if not intersect_sqls:
            intersect_sqls = [base_sql + "1"]
        # Change this
        sql = " INTERSECT ".join(intersect_sqls)

        if except_sqls:
            sql += " EXCEPT " + " EXCEPT ".join(except_sqls)

        return sql, intersect_vals + except_vals

    def query_profile(self, *vars, reference_accession=None):  # noqa: C901
        iupac_nt_code = {
            "A": set("A"),
            "C": set("C"),
            "G": set("G"),
            "T": set("T"),
            "R": set("AGR"),
            "Y": set("CTY"),
            "S": set("GCS"),
            "W": set("ATW"),
            "K": set("GTK"),
            "M": set("ACM"),
            "B": set("CGTB"),
            "D": set("AGTD"),
            "H": set("ACTH"),
            "V": set("ACGV"),
            "N": set("ACGTRYSWKMBDHVN"),
            "n": set("N"),
        }
        iupac_aa_code = {
            "A": set("A"),
            "R": set("R"),
            "N": set("N"),
            "D": set("D"),
            "C": set("C"),
            "Q": set("Q"),
            "E": set("E"),
            "G": set("G"),
            "H": set("H"),
            "I": set("I"),
            "L": set("L"),
            "K": set("K"),
            "M": set("M"),
            "F": set("F"),
            "P": set("P"),
            "S": set("S"),
            "T": set("T"),
            "W": set("W"),
            "Y": set("Y"),
            "V": set("V"),
            "U": set("U"),
            "O": set("O"),
            "B": set("DNB"),
            "Z": set("EQZ"),
            "J": set("ILJ"),
            "Φ": set("VILFWYMΦ"),
            "Ω": set("FWYHΩ"),
            "Ψ": set("VILMΨ"),
            "π": set("PGASπ"),
            "ζ": set("STHNQEDKRζ"),
            "+": set("KRH+"),
            "-": set("DE-"),
            "X": set("ARNDCQEGHILKMFPSTWYVUOBZJΦΩΨπζ+-X"),
            "x": set("X"),
        }
        del_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?del:(=?[0-9]+)(|-=?[0-9]+)?$")
        snv_regex = re.compile(r"^(|[^:]+:)?([^:]+:)?([A-Z]+)([0-9]+)(=?[A-Zxn]+)$")

        # set variants and generate sql
        base_sql = "SELECT `sample.id` AS id FROM variantView WHERE "
        intersect_sqls = []
        intersect_vals = []
        except_sqls = []
        except_vals = []
        for var in vars:
            c = []  # condition
            v = []  # variable

            if var.startswith("^"):
                var = var[1:]
                negate = True
            else:
                negate = False

            # variant typing
            if match := snv_regex.match(var):
                snv = True
            elif match := del_regex.match(var):
                snv = False
            else:
                logging.error("'" + var + "' is not a valid variant definition.")
                sys.exit(
                    "Please check the query statement,(IUPAC AA/NT codes, NT format(e.g. A3451T), AA format(e.g. S:N501Y))"
                )
            # set molecule
            if match.group(1):
                c.append("`molecule.symbol` = ?")
                v.append(match.group(1)[:-1])
            else:
                c.append("`molecule.standard` = ?")
                v.append(1)

            # set element
            if match.group(2):
                c.append("`element.type` = ?")
                v.append("cds")
                c.append("`element.symbol` = ?")
                v.append(match.group(2)[:-1])
                code = iupac_aa_code
            else:
                c.append("`element.standard` = ?")
                v.append(1)
                code = iupac_nt_code

            # snp and insert handling
            if snv:
                c.append("`variant.start` = ?")
                v.append(int(match.group(4)) - 1)
                c.append("`variant.end` = ?")
                v.append(int(match.group(4)))
                c.append("`variant.ref` = ?")
                v.append(match.group(3))
                try:
                    # explicit alternate allele
                    if match.group(5).startswith("="):
                        c.append("`variant.alt` = ?")
                        v.append(match.group(5)[1:])

                    # potentially ambiguous alternate snp
                    elif len(match.group(5)) == 1:
                        l = len(code[match.group(5)])
                        if l == 1:
                            match_group5 = (
                                match.group(5).upper()
                                if match.group(5) == "n" or match.group(5) == "x"
                                else match.group(5)
                            )
                            c.append("`variant.alt` = ?")
                            v.append(match_group5)
                        else:
                            c.append("`variant.alt` IN (" + ", ".join(["?"] * l) + ")")
                            v.extend(code[match.group(5)])

                    # potentially ambiguous alternate insert
                    else:
                        a = [
                            "".join(x)
                            for x in itertools.product(
                                *[code[x] for x in match.group(5)]
                            )
                        ]
                        l = len(a)
                        if l == 1:
                            a = a.upper() if a == "n" or a == "x" else a
                            c.append("`variant.alt` = ?")
                            v.extend(a)
                        else:
                            c.append("`variant.alt` IN (" + ", ".join(["?"] * l) + ")")
                            v.extend(a)
                except KeyError:
                    logging.error("'" + var + "' is not a valid input")
                    sys.exit(
                        "Please check the query statement,(IUPAC AA/NT codes, NT format(e.g. A3451T), AA format(e.g. S:N501Y))"
                    )
            # deletion handling
            else:
                s = match.group(3)
                e = match.group(4)[1:]
                # if del:=1-=60 meanse exact search del:1-60
                # del:1-60 means range search--> it could be del:1-11 or del:1-60
                if s.startswith("="):
                    s = s[1:]
                    c.append("`variant.start` = ?")
                else:
                    c.append("`variant.start` >= ?")

                if e.startswith("="):
                    e = e[1:]
                    c.append("`variant.end` = ?")
                else:
                    c.append("`variant.end` <= ?")
                v.append(int(s) - 1)
                v.append(int(e))

                c.append("`variant.alt` = ?")
                v.append(" ")

            # assemble sub-sql
            if negate:
                except_sqls.append(base_sql + " AND ".join(c))
                except_vals.extend(v)
            else:
                intersect_sqls.append(base_sql + " AND ".join(c))
                intersect_vals.extend(v)

        # assemble final sql
        if not intersect_sqls:
            intersect_sqls = [base_sql + "1"]

        sql = " INTERSECT ".join(intersect_sqls)

        if except_sqls:
            sql += " EXCEPT " + " EXCEPT ".join(except_sqls)

        return sql, intersect_vals + except_vals

    def get_ref_variant_ID(self, profiles, reference_accession=None):  # noqa: 901
        """Tmp patch
        Get reference ID based on variant profile.

        Return string of selected;
        """

        profile_sqls = []
        profile_vals = []
        for profile in profiles:

            sql, val = self.get_ref_ID_base_query_profile(
                *profile, reference_accession=reference_accession
            )
            profile_sqls.append(sql)
            profile_vals.extend(val)

        if len(profiles) == 1:
            profile_sqls = profile_sqls[0]
        elif len(profiles) > 1:
            profile_sqls = " UNION ".join(
                [
                    "SELECT * FROM (" + x + ") t" + str(i)
                    for i, x in enumerate(profile_sqls)
                ]
            )
        else:
            profile_sqls = ""
        if self.debug:
            logging.info(f"Reference sqls: {profile_sqls}")
            logging.info(f"Reference vals: {profile_vals}")
        if profile_sqls == "":
            logging.info("Filtered Reference ID: none")
            return []

        self.cursor.execute(profile_sqls, profile_vals)
        variant_ids = self.cursor.fetchall()
        if not variant_ids:
            logging.info("Filtered Reference ID: none")
            return []

        # TODO: deduplicate IDs
        # print(variant_ids)
        # remove None value incase there is the one, however, we should fix it at sql command.
        variant_ids = [str(i["id"]) for i in variant_ids if i["id"] is not None]
        return variant_ids

    def match(  # noqa: 901
        self,
        *profiles,
        reserved_props=None,
        properties=None,
        reference_accession=None,
        showNX=False,
        output_column="all",
        format="csv",
    ):
        """
        # TODO: 1. check if reference is not exit then we get all alignment.
        # 2. Match query or sql or step can improve.
        # 3.
        Note:
            If reference accession is None, we will query all varaints with all references.
        Return:
            list of dict
        """
        # collecting sqls for metadata-based filtering
        property_sqls = []
        property_vals = []
        # IF sublineage search is enable
        # support: include and exclude
        if "with_sublineage" in reserved_props:
            _tmp_include_lin = []  # used to keep all lienages after search.
            lineage_col = reserved_props.get("with_sublineage")
            include_lin = properties.get(lineage_col)  # get list of given lineages
            negate = False
            logging.info("sublineage search is enable on %s" % include_lin)
            while include_lin:
                in_lin = include_lin.pop(0)

                if in_lin.startswith("^"):
                    in_lin = in_lin[1:]
                    negate = True

                # have wildcard in string which mean we have to find all lineage from wildcard query
                # then we used the wildcard query result to find all sublineages agian.
                if "%" in in_lin:
                    _tobeadded_lin = self.get_list_of_lineages(in_lin)
                    for i in _tobeadded_lin:

                        # if i != in_lin: # we dont need to add same lineage agian,so we skip for the duplicate lineage.
                        if negate:  # all lineage should add not ^
                            i = "^" + i
                        include_lin.append(i)  # add more lineage to find in next round.

                value = self.lineage_sublineage_dict.get(
                    in_lin, "none"
                )  # provide a default value if the key is missing:
                # print(value)
                if value != "none":
                    if negate:
                        in_lin = "^" + in_lin
                    _tmp_include_lin.append(in_lin)

                    _list = value.split(",")
                    for i in _list:
                        if negate:  # all sublineage should add not^
                            i = "^" + i
                        include_lin.append(i)  # add more lineage to find in next round.
                        # _tmp_include_lin.append(i)
                        # if we don't find this wildcard so we discard it
                else:  # None (no child)
                    if negate:
                        in_lin = "^" + in_lin
                    _tmp_include_lin.append(in_lin)
                negate = False

            include_lin = _tmp_include_lin
            properties[lineage_col] = include_lin
        if self.debug:
            logging.info(f"List all prop.:{properties}")
        # if properties are present in query
        if properties:
            for pname, vals in properties.items():
                if vals is not None:
                    sql, val = self.query_metadata(pname, *vals)
                    property_sqls.append(sql)
                    property_vals.extend(val)

        property_sqls = " INTERSECT ".join(property_sqls)
        if self.debug:
            logging.info(f"Properties in Query: {property_sqls}")

        # collecting sqls for genomic profile based filtering
        profile_sqls = []
        profile_vals = []
        for profile in profiles:

            sql, val = self.query_profile(
                *profile, reference_accession=reference_accession
            )
            profile_sqls.append(sql)
            profile_vals.extend(val)

        if len(profiles) == 1:
            profile_sqls = profile_sqls[0]
        elif len(profiles) > 1:
            profile_sqls = " UNION ".join(
                [
                    "SELECT * FROM (" + x + ") t" + str(i)
                    for i, x in enumerate(profile_sqls)
                ]
            )
        else:
            profile_sqls = ""
        if self.debug:
            logging.info(f"Profile sqls: {profile_sqls}")
            logging.info(f"Profile vals: {profile_vals}")

        # ------------------------
        # NOTE: Find the refID, if refID is not given,
        # this will return all refIDs that match the given profiles
        if len(profiles) > 0:

            # WARN: this take only one accession ID into account at a time. *not support multiple refs.
            if reference_accession:
                selected_dict = next(
                    item
                    for item in self.references
                    if item["accession"] == reference_accession
                )
                selected_ref_ids = str(selected_dict["id"])
            else:
                ref_id_list = self.get_ref_variant_ID(profiles)
                selected_ref_ids = ", ".join([str(x) for x in ref_id_list])

            logging.info(
                f"Found Reference ID base on given profile: {selected_ref_ids}"
            )
            variant_condition_stm = " AND `reference.id` IN (" + selected_ref_ids + ")"
        else:
            variant_condition_stm = ""
        # ------
        if property_sqls and profile_sqls:
            if len(profiles) > 1:
                sample_selection_sql = (
                    property_sqls + " INTERSECT SELECT * FROM (" + profile_sqls + ")"
                )
            else:
                sample_selection_sql = property_sqls + " INTERSECT " + profile_sqls

            if reference_accession:
                sample_selection_sql = (
                    sample_selection_sql + " " + variant_condition_stm
                )
        elif property_sqls or profile_sqls:
            sample_selection_sql = property_sqls + profile_sqls
            if reference_accession:
                sample_selection_sql = (
                    sample_selection_sql + " " + variant_condition_stm
                )
        else:
            if "sample" in reserved_props:
                # if 'sample' is presented we just use only samples
                samples_condition = []
                for pname, vals in reserved_props.items():
                    print("sample" + str(vals))
                    if pname == "sample":
                        for x in vals:
                            samples_condition.append('"' + x + '"')
                sample_selection_sql = (
                    "SELECT id FROM sample WHERE name IN ("
                    + " , ".join(samples_condition)
                    + ")"
                )
                if reference_accession:
                    sample_selection_sql = (
                        sample_selection_sql + " " + variant_condition_stm
                    )
                property_sqls = []
                property_vals = []
            else:
                # in case: there is no profile in the query and no specific sample.

                # we need to check if ref accession number is given.
                if reference_accession:
                    sample_selection_sql = "SELECT DISTINCT(`sample.id`) AS id  FROM alignmentView WHERE `reference.accession`={}".format(
                        '"' + reference_accession + '"'
                    )
                else:
                    # should we use only sample or all alignment
                    sample_selection_sql = "SELECT id FROM sample"

        if self.debug:
            logging.info(f"Sample selection in sql: {sample_selection_sql}")

        genome_element_condition = [
            str(x) for x in self.get_element_ids(reference_accession, "source")
        ]
        # if enable m `molecule.symbol`, "@"
        if len(genome_element_condition) == 1:
            genome_element_condition = "`element.id` = " + genome_element_condition[0]
            m = ""
        else:
            genome_element_condition = (
                "`element.id` IN (" + ", ".join(genome_element_condition) + ")"
            )
            m = ""
            # CurrentSolution: we add reference column instead
            # m = ' `molecule.symbol`, "@" , '
        if self.debug:
            logging.info(f"Genome element in sql: {genome_element_condition}")

        if not showNX:
            nn = ' AND `variant.alt` != "N" '
            nx = ' AND `variant.alt` != "X" '
        else:
            nn = ""
            nx = ""
        # find element id for CDS
        cds_element_condition = [
            str(x) for x in self.get_element_ids(reference_accession, "cds")
        ]
        # fix all reference query when some refs they have no cds tag.
        all_refID_nocds = [str(x["id"]) for x in self.get_ele_ofref_bynoCDS()]
        all_ref_nocds = [str(x["accession"]) for x in self.get_ele_ofref_bynoCDS()]
        if not reference_accession:
            cds_element_condition.extend(all_refID_nocds)

        if len(cds_element_condition) == 1:
            cds_element_condition = "`element.id` = " + cds_element_condition[0]
            cds_element_condition = " AND " + cds_element_condition
        elif len(cds_element_condition) > 1:
            cds_element_condition = (
                "`element.id` IN (" + ", ".join(cds_element_condition) + ")"
            )
            cds_element_condition = " AND " + cds_element_condition
        else:
            cds_element_condition = ""

        # standard query
        if format == "csv" or format == "tsv":

            # select samples
            sql = sample_selection_sql
            if self.debug:
                logging.info(
                    f"Before execute 'Select Samples': {sql} with {property_vals + profile_vals}"
                )
            # this execution is based on the samples and given profiles.
            self.cursor.execute(sql, property_vals + profile_vals)
            sample_ids = self.cursor.fetchall()
            if not sample_ids:
                return []

            # TODO: deduplicate IDs
            selected_sample_ids = ", ".join([str(x["id"]) for x in sample_ids])
            if self.debug:
                logging.info(f" 'Selected Samples': {selected_sample_ids}")
            # rows = {x['id']: {"id": x['id']} for x in sample_ids}
            # print(len(sample_ids))

            #
            # Current solution:
            # After we got the selected IDs (filter by profiles)
            # We use two-stage query and then combine both results together to produce final result
            # 1. Query: get all properties based on selected IDs
            # 2. Query: get all AA/NT profile based on selected IDs and reference IDs
            # Finally, we combine 1. and 2. based on outer join.

            # output columns
            fields = ["`sample.name`"] + ["`" + x + "`" for x in self.properties]
            sql = "SELECT name as " + ", ".join(fields) + "FROM sample "

            joins = [
                "LEFT JOIN (SELECT sample_id, value_"
                + y["datatype"]
                + " as "
                + x
                + " FROM sample2property WHERE property_id = "
                + str(y["id"])
                + ") as t"
                + str(y["id"])
                + " ON sample.id = t"
                + str(y["id"])
                + ".sample_id"
                for x, y in self.properties.items()
            ]
            _1_final_sql = (
                sql
                + " ".join(joins)
                + " WHERE sample.id IN ("
                + selected_sample_ids
                + ")"
            )
            if self.debug:
                logging.info("First SQL: " + _1_final_sql)

            self.cursor.execute(_1_final_sql)
            _1_rows = self.cursor.fetchall()

            # since some samples didn't return AA mutation., so we use LEFT JOIN to NT.
            # ... and also remove unnecessay 'WHERE IN SAMPLE_IDs'
            _2_final_sql = (
                " SELECT name AS `sample.name`, nt_profile.reference_accession AS REFERENCE_ACCESSION, nt_profile._profile AS NUC_PROFILE, aa_profile._profile AS AA_PROFILE "
                + " FROM ( SELECT  `sample.id`, `reference.accession` AS reference_accession, group_concat("
                + m
                + " `variant.label`) AS _profile, `variant.id`"
                + "FROM variantView WHERE `sample.id` IN ("
                + selected_sample_ids
                + ") AND "
                + genome_element_condition
                + nn
                + variant_condition_stm
                + " GROUP BY `sample.id`, reference_accession) nt_profile "
                + " JOIN "
                + "( SELECT  `sample.id`, `reference.accession` AS reference_accession , group_concat("
                + m
                + ' `element.symbol`, ":" ,`variant.label`) AS _profile, `variant.id`'
                + " FROM variantView WHERE `sample.id` IN ( "
                + selected_sample_ids
                + ")"
                + cds_element_condition
                + nx
                + variant_condition_stm
                + " GROUP BY `sample.id`, reference_accession ) aa_profile "
                + " ON nt_profile.`sample.id` = aa_profile.`sample.id` AND nt_profile.reference_accession =aa_profile.reference_accession "
                + ", `sample` "
                + " WHERE  nt_profile.`sample.id` = `sample`.id "
            )
            """
                        2_final_sql = (
                " SELECT name AS `sample.name`, nt_profile.reference_accession AS REFERENCE_ACCESSION, nt_profile._profile AS NUC_PROFILE, aa_profile._profile AS AA_PROFILE "
                + " FROM ( SELECT  `sample.id`, `reference.accession` AS reference_accession, group_concat("
                + m
                + " `variant.label`) AS _profile, `variant.id`"
                + "FROM variantView WHERE `sample.id` IN ("
                + selected_sample_ids
                + ") AND "
                + genome_element_condition
                + nn
                + varinat_condition_stm
                + " GROUP BY `sample.id`, reference_accession) nt_profile, "
                + " ( SELECT  `sample.id`, `reference.accession` AS reference_accession , group_concat("
                + m
                + ' `element.symbol`, ":" ,`variant.label`) AS _profile, `variant.id`'
                + " FROM variantView WHERE `sample.id` IN ( "
                + selected_sample_ids
                + ")"
                + cds_element_condition
                + nx
                + varinat_condition_stm
                + " GROUP BY `sample.id`, reference_accession ) aa_profile, `sample` "
                + " WHERE nt_profile.`sample.id` = aa_profile.`sample.id` AND  nt_profile.`sample.id` = `sample`.id  "
                + " AND nt_profile.reference_accession = aa_profile.reference_accession "
                + " AND `sample`.id  IN ("
                + selected_sample_ids
                + ")"
            )
            """
            if self.debug:
                logging.info("Second SQL")
                logging.info(_2_final_sql)

            self.cursor.execute(_2_final_sql)
            _2_rows = self.cursor.fetchall()
            if len(_1_rows) != len(_2_rows):
                # logging.warning("Detects something suspicious in matching process.")
                logging.warning(
                    "Return records; between %d meta-info and %d sequence alignment"
                    % (len(_1_rows), len(_2_rows))
                )
                logging.warning(
                    "This can happen when the ID of a sample does not represent in fasta or in meta info. or there is no NT/AA profile in a sample."
                    + " It can also be the reason of one sample is aligning with more than one reference."
                )

            # print(set([ x['sample.name'] for x in _1_rows ]) ^ set([ x['name'] for x in _2_rows ]))
            # To combine:
            # We update list of dict (update on result from query #2)
            # merge all results
            # _1_rows.extend(
            #    list(
            #        map(
            #            lambda x, y: x.update(
            #                {
            #                    key: value
            #                    for key, value in y.items()
            #                    if (key == "NUC_PROFILE") or (key == "AA_PROFILE")
            #                }
            #            )
            #            if x.get("sample.name") == y.get("sample.name")
            #            else None,
            #            _1_rows,
            #            _2_rows,
            #        )
            #    )
            # )

            # _1_rows = list(filter(None, _1_rows))

            # ------ alternative solution convert to df
            df_1 = pd.DataFrame(_1_rows)
            df_1.sort_values(by=["sample.name"], inplace=True)
            if self.debug:
                logging.debug(df_1["sample.name"])
            # sample.name REFERENCE_ACCESSION NUC_PROFILE AA_PROFILE
            df_2 = pd.DataFrame(_2_rows)
            df_2.sort_values(by=["sample.name"], inplace=True)
            if self.debug:
                logging.debug(df_2.columns)
                logging.debug(df_2["sample.name"])

            """
            merge_df = pd.merge(
                df_1,
                df_2,
                how="inner",
                left_on=["sample.name"],
                right_on=["sample.name"],
            )

            """
            # [tmp solution.]- we remove unused column TODO: fix this in the future.
            # backwards compatibility
            if df_1.columns.isin(
                [
                    "NUC_PROFILE",
                    "AA_PROFILE",
                    "NUC_N_PROFILE",
                    "AA_X_PROFILE",
                ]
            ).all():
                df_1.drop(
                    columns=[
                        "NUC_PROFILE",
                        "AA_PROFILE",
                        "NUC_N_PROFILE",
                        "AA_X_PROFILE",
                    ],
                    inplace=True,
                )
            # NOTE: some samples might have only meta info, if we choose inner map
            # the result will be intersection of two datafram.
            merge_df = pd.merge(
                df_1,
                df_2,
                how="outer",
                left_on=["sample.name"],
                right_on=["sample.name"],
            )

            # fix column for ref with no CDS
            merge_df.loc[
                merge_df["REFERENCE_ACCESSION"].isin(all_ref_nocds), "AA_PROFILE"
            ] = "-"
            merge_df.fillna("-", inplace=True)
            _1_rows = merge_df.to_dict("records")
            # filter column
            if output_column != "all":
                _1_rows = [
                    {k: v for k, v in d.items() if k in output_column} for d in _1_rows
                ]

            # print(list(_1_rows))
            # since we use "update" function (i.e. extends the dict. to include all key:value from properties base on sample name)
            # at _1_rows so we can return _1_rows only a
            return _1_rows  # list(rows.values())

        elif format == "count":
            # TODO: currently we count only samples not the sample-aligned wise.
            logging.info("'--count' will return only unique sample.")
            sql = (
                "SELECT COUNT(s2p.id) AS `count` FROM ("
                + sample_selection_sql
                + ") AS s2p"
            )
        elif format == "vcf":
            sql = (
                "SELECT `element.id`,  `element.type`, `molecule.accession`, `variant.start`, `variant.ref`, `variant.alt`, `variant.label`, `sample.name` as samples FROM variantView WHERE `sample.id` IN ("
                + sample_selection_sql
                + ") AND "
                + genome_element_condition
                + nn
                + "GROUP BY `molecule.accession`, `variant.start`, `variant.ref`, `variant.alt` ORDER BY `molecule.accession`, `variant.start`"
            )
        else:
            sys.exit("error: '" + format + "' is not a valid output format")
        if self.debug:
            logging.info(
                f"Before execute 'Select Samples': {sql} with {property_vals + profile_vals}"
            )
        self.cursor.execute(sql, property_vals + profile_vals)
        return self.cursor

    def get_list_of_lineages(self, lineage):
        sql = (
            "SELECT DISTINCT lineage FROM lineages WHERE lineage LIKE '"
            + lineage
            + "';"
        )
        rows = self.cursor.execute(sql).fetchall()
        result = [i["lineage"] for i in rows]
        return result

    # MISC

    @staticmethod
    def optimize(dbfile):
        logging.WARNING(
            "Currently, we don't support this command through our application yet."
        )
        logging.info(
            "Please run: 'mysqlcheck -u [username] -p -o mpx' in your terminal instead."
        )

    @staticmethod
    def dict_factory(cursor, row):
        d = {}  # OrderedDict()
        for idx, col in enumerate(cursor.description):
            d[col[0]] = row[idx]
        return d

    # Utils.
    def get_db_size(self, decimal_places=2):
        # Execute query with fixed DB schema
        sql = "SELECT  table_schema , \
                (data_length + index_length) `size` \
                FROM information_schema.TABLES \
                WHERE table_schema = 'mpx';"

        self.cursor.execute(sql)
        size = self.cursor.fetchone()["size"]
        for unit in ["B", "KB", "MB", "GB", "TB", "PB"]:  # pragma: no cover
            if size < 1024.0:
                break
            size /= 1024.0
        return f"{size:.{decimal_places}f} {unit}"

    @staticmethod
    def upgrade_db(dbfile):
        try:
            with sqlite3.connect(dbfile) as con:
                cur = con.cursor()
                current_version = cur.execute("pragma user_version").fetchone()[0]

            logging.info(
                "Current version: %d Upgrade to: %d"
                % (current_version, SUPPORTED_DB_VERSION)
            )
            uri = "file:" + urlquote(dbfile)
            logging.info("Perform the Upgrade: %s" % uri)

            while current_version < SUPPORTED_DB_VERSION:
                next_version = current_version + 1
                file_path = os.path.join(
                    os.path.dirname(os.path.realpath(__file__)),
                    "migrate",
                    str(next_version) + ".sql",
                )
                if not os.path.isfile(file_path):
                    raise ValueError(
                        "Sorry, we cannot find %s, please contract us or reinstall software."
                        % (file_path)
                    )  # pragma: no cover

                with open(file_path, "r") as handle:
                    sql = handle.read()
                with sqlite3.connect(uri + "?mode=rwc", uri=True) as con:
                    con.executescript(sql)

                current_version = next_version

        except sqlite3.Error as er:
            con.executescript("ROLLBACK")
            raise er
        except ValueError as er:
            logging.error(er)
        finally:
            logging.info("Database now version: %d" % current_version)
            if current_version == SUPPORTED_DB_VERSION:
                logging.info("Success: Database upgrade was successfully completed")
            else:
                logging.error("Error: Upgrade was not completed")
