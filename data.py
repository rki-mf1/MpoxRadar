import csv
from datetime import datetime
import multiprocessing as mp
import os
from time import perf_counter
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine

from pages.config import CACHE_DIR
from pages.config import DB_URL
from pages.config import redis_manager
from pages.utils import load_Cpickle
from pages.utils import write_Cpickle

tables = ["propertyView", "variantView", "referenceView"]

# pandas normally uses python strings, which have about 50 bytes overhead. that's catastrophic!
stringType = "string[pyarrow]"
intType = "int32"

column_dtypes = {
    "propertyView": {
        "sample.id": intType,  # needed
        "sample.name": stringType,  # needed
        "property.id": intType,
        "property.name": stringType,  # needed
        "propery.querytype": stringType,
        "property.datatype": stringType,
        "property.standard": stringType,  # ---- this one is always NULL
        "value_integer": stringType,  # needed - value_integer -> LENGTH
        # ^^^^^^^^^^^ this one is often NULL !!!! so I set it to stringType instead of intType
        "value_float": "float32",
        "value_text": stringType,
        # needed - value_text -> COLLECTION_DATE, RELEASE_DATE, ISOLATE, SEQ_TECH, COUNTRY, GEO_LOCATION, HOST
        "value_zip": stringType,
        "value_varchar": stringType,
        "value_blob": stringType,  # actually "blobType"
        "value_date": stringType,  # needed - value_date -> RELEASE_DATE, dateime coversion introduces errors
    },
    "variantView": {
        "sample.id": intType,  # needed
        "sample.name": stringType,  # needed
        "sample.seqhash": stringType,
        "reference.id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
        "reference.accession": stringType,
        "reference.standard": stringType,
        "molecule.id": intType,
        "molecule.accession": stringType,
        "molecule.standard": stringType,
        "element.id": intType,
        "element.accession": stringType,
        "element.symbol": stringType,  # needed = Gene Name
        "element.standard": stringType,
        "element.type": stringType,  # cds (=AA mutations) or source (=Nt mutations)
        "variant.id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
        "variant.ref": stringType,
        "variant.start": stringType,
        "variant.end": stringType,
        "variant.alt": stringType,
        "variant.label": stringType,  # needed mutation name
        "variant.parent_id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
    },
    "referenceView": {
        "reference.id": intType,  # needed
        "reference.accession": stringType,
        "reference.description": stringType,
        "reference.organism": stringType,
        "reference.standard": intType,
        "translation.id": intType,
        "molecule.id": intType,
        "molecule.type": stringType,
        "molecule.accession": stringType,
        "molecule.symbol": stringType,
        "molecule.description": stringType,
        "molecule.length": intType,
        "molecule.segment": intType,
        "molecule.standard": intType,
        "element.id": intType,
        "element.type": stringType,  # needed
        "element.accession": stringType,
        "element.symbol": stringType,  # needed gene name
        "element.description": stringType,
        "element.start": intType,  # needed = start gene name
        "element.end": intType,  # end gene cds
        "element.strand": intType,
        "element.sequence": stringType,
        "elempart.start ": intType,
        "elempart.end ": intType,
        "elempart.strand ": intType,
        "elempart.segment ": intType,
    },
}

needed_columns = {
    "propertyView": [
        "sample.id",
        "sample.name",
        "property.name",
        "value_text",
        "value_date",
    ],
    "variantView": [
        "sample.id",
        "sample.name",
        "reference.id",
        "reference.accession",
        "variant.id",
        #  "variant.ref",
        "variant.label",
        #  "variant.parent_id"
        "element.type",
        "element.symbol",
    ],
    "referenceView": [
        "reference.id",
        "element.type",
        "element.symbol",
        "element.start",
        "element.end",
    ],
}


def get_database_connection():
    # DB configuration
    parsed_db_url = urlparse(DB_URL)
    user = parsed_db_url.username
    ip = parsed_db_url.hostname
    pw = parsed_db_url.password
    # port = parsed_db_url.port
    db_database = parsed_db_url.path.replace("/", "")
    return create_engine(f"mysql+pymysql://{user}:{pw}@{ip}/{db_database}")


class DataFrameLoader:
    def __init__(self):
        self.tables = tables
        self.needed_columns = needed_columns
        self.column_dtypes = column_dtypes

    def load_db_from_sql(self, table_name):
        start = perf_counter()
        db_connection = get_database_connection()
        # df_dict = {}
        try:
            # we cannot use read_sql_table because it doesn't allow difining dtypes
            columns = pd.read_sql_query(
                f"SELECT * FROM {table_name} LIMIT 1;", con=db_connection
            ).columns
            if table_name in self.needed_columns:
                columns = columns.intersection(self.needed_columns[table_name])
                types = {
                    column: self.column_dtypes[table_name][column] for column in columns
                }
                # a '.' in the column names implies ``-quoting the column name for a mariadb-query
                quoted_column_names = []
                for column in columns:
                    if "." in column:
                        column = "`" + column + "`"
                    quoted_column_names.append(column)
                ###
                queried_columns = ", ".join(quoted_column_names)
            else:
                types = {
                    column: self.column_dtypes[table_name][column] for column in columns
                }
                queried_columns = "*"
            # here is the download!
            if table_name == "variantView":
                with open(".cache/variantView.csv", "w") as tmpfile:
                    outcsv = csv.writer(tmpfile, lineterminator="\n")
                    query = f"SELECT {queried_columns} FROM {table_name};"
                    engine = db_connection
                    connection = engine.connect()
                    cursor = connection.execute(query)
                    headers = []
                    for columns in cursor.keys():
                        headers.append(columns)
                    # dump column titles
                    outcsv.writerows([headers])

                    # dump rows
                    outcsv.writerows(cursor.fetchall())

                # df = pd.read_csv(f'.cache/{table_name}.csv')
            else:
                df = pd.read_sql_query(
                    f"SELECT {queried_columns} FROM {table_name};",
                    con=db_connection,
                    dtype=types,
                )
                # FIXME: should put , doublequote=True, or
                df.to_csv(f".cache/{table_name}.csv", index=False)
        # missing table
        except sqlalchemy.exc.ProgrammingError:
            print(f"table {table_name} not in database.")
            df = pd.DataFrame()
        print(f"Loading time {table_name}: {(perf_counter() - start):.4f} sec.")
        # FIXME: should return file path.
        return {table_name: f".cache/{table_name}.csv"}
        """
        if not df.empty:
            df_dict[table_name] = df
            print(df_dict)
            print("After this")
            return df_dict
        """

    def load_from_sql_db(self):

        # NOTE: WARN:
        """
        Avoid shifting large amounts of data between processes.
        multiprocessing.Pool relies on a locked buffer (an OS Pipe/CPU type.)
        to distribute the tasks between the workers and retrieve their results.
        If an object larger than the buffer is pushed trough the pipe,
        there are chances the logic might hang. We can dump the job result to files
        (e.g., using pickle) and return/send the filename.
        We can prevent logic from getting stuck and pipe becomes a severe bottleneck.
        (Hopefully notice speed improvements as well)
        """
        pool = mp.Pool(mp.cpu_count())
        # FIXME: should store file path.
        dict_list = pool.starmap(
            self.load_db_from_sql,
            [[table] for table in self.tables],
        )
        pool.close()  # tells the pool not to accept any new job.
        pool.terminate()
        pool.join()  # tells the pool to wait until all jobs finished then exit
        # blocking the parent process is just a side effect of what pool.join is doing.
        """
        with WorkerPool() as pool:
            dict_list = pool.map( self.load_db_from_sql,
            [table for table in self.tables], progress_bar=True)
        """

        # NOTE: HARD CODE
        # read results back.
        print(dict_list)
        for i, _dict in enumerate(dict_list):
            for k, v in _dict.items():
                dict_list[i][k] = pd.read_csv(v)
        df_dict = {}
        for df_d in dict_list:
            if df_d is not None:
                df_dict.update(df_d)
        del dict_list
        return df_dict


def create_property_view(df, dummy_date="2021-12-31"):
    #  start = perf_counter()
    df["value_text"] = df.apply(
        lambda row: row["value_date"]
        if row["property.name"] in ["COLLECTION_DATE", "RELEASE_DATE"]
        else row["value_text"],
        axis=1,
    )
    df = df.drop(columns=["value_date"], axis=1)
    c = ["sample.id", "sample.name"]
    df = df.set_index(["property.name"] + c).unstack("property.name")
    df = df.value_text.rename_axis([None], axis=1).reset_index()
    df["COLLECTION_DATE"] = df[["COLLECTION_DATE"]].fillna(dummy_date)
    df["COLLECTION_DATE"] = df["COLLECTION_DATE"].apply(
        lambda d: datetime.strptime(d, "%Y-%m-%d").date()
    )
    df["SEQ_TECH"] = df["SEQ_TECH"].replace([np.nan, ""], "undefined")
    #  print(f"time pre-processing PropertyView final: {(perf_counter()-start)} sec.")
    #  print(print(tabulate(df[0:10], headers='keys', tablefmt='psql')))
    return df


def create_variant_view(df):
    df["reference.id"] = df["reference.id"].astype(float).astype("Int64")
    df["variant.id"] = df["variant.id"].astype(float).astype("Int64")
    return df


def create_reference_view(df):
    """
    reference.id, element.type, element.symbol, element.start, element.end
    """
    df = df[(df["element.type"] == "cds")]
    return df


def load_all_sql_files():
    loader = DataFrameLoader()

    # NOTE:
    # 1. Using Pickle should only be used on 100% trusted data
    # 2. msgpack can be other options.
    # check if df_dict is load or not?
    if redis_manager and redis_manager.exists("df_dict"):
        print("Load data from cache")
        # df_dict = decompress_pickle(os.path.join(CACHE_DIR,"df_dict.pbz2"))
        # df_dict = pickle.loads(redis_manager.get("df_dict"))
        df_dict = load_Cpickle(os.path.join(CACHE_DIR, "df_dict.pickle"))
    else:
        # PROBLEM: query for variantView tooo long.
        print("Load data from database...")
        df_dict = loader.load_from_sql_db()
        df_dict["propertyView"] = create_property_view(df_dict["propertyView"])
        df_dict["variantView"] = create_variant_view(df_dict["variantView"])
        df_dict["referenceView"] = create_reference_view(df_dict["referenceView"])
        print("Data preprocessing...")
        if redis_manager:
            print("Create a new cache")
            # NOTE: set pickle cache, however the limitation of redis
            # is.... the tool can store data size up to 512MB
            # 1 sec
            # redis_manager.set("df_dict", pickle.dumps(df_dict), ex=3600 * 23)

            # HACK: 1. SpaceSaving, so we use the another method, using Cpickle + BZ2 compression.
            # WARN: the performance is limited by compression algorithm and stroage I/O type.
            # 40 secs, 40 MB
            # redis_manager.set("df_dict", "1", ex=3600 * 23)
            # compressed_pickle(os.path.join(CACHE_DIR,"df_dict.pbz2"),df_dict)

            # HACK: 2. Using Cpickle only
            # 30 secs, 419 MB
            write_Cpickle(os.path.join(CACHE_DIR, "df_dict.pickle"), df_dict)
            redis_manager.set("df_dict", 1, ex=3600 * 23)

            # df_dict["propertyView"].to_pickle(".cache/propertyView.pkl")
            # df_dict["variantView"].to_pickle(".cache/variantView.pkl")
            # df_dict["referenceView"].to_pickle(".cache/referenceView.pkl")

    return df_dict
