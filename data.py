from collections import defaultdict
import csv
from datetime import datetime
import multiprocessing as mp
import os
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse

import numpy as np
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy import exc

from pages.app_controller import calculate_mutation_sig
from pages.app_controller import calculate_tri_mutation_sig
from pages.app_controller import create_snp_table
from pages.config import CACHE_DIR
from pages.config import DB_URL
from pages.config import redis_manager
from pages.utils import load_Cpickle
from pages.utils import write_Cpickle

tables = ["propertyView", "variantView"]

# pandas normally uses python strings, which have about 50 bytes overhead. that's catastrophic!
STRINGTYPE = "string[pyarrow]"
INTTYPE = "int32"

column_dtypes = {
    "propertyView": {
        "sample.id": INTTYPE,  # needed
        "sample.name": STRINGTYPE,  # needed
        "property.id": INTTYPE,
        # needed: COUNTRY, IMPORTED, COLLECTION_DATE, RELEASE_DATE, ISOLATE, LENGTH, SEQ_TECH, COUNTRY, GEO_LOCATION, HOST, GENOME_COMPLETENESS
        "property.name": STRINGTYPE,
        "propery.querytype": STRINGTYPE,
        "property.datatype": STRINGTYPE,
        "property.standard": STRINGTYPE,  # this one is always NULL
        # needed - value_integer -> LENGTH, this one is often NULL -> stringType instead of intType
        "value_integer": STRINGTYPE,
        "value_float": "float32",
        # needed - value_text -> COLLECTION_DATE, RELEASE_DATE, ISOLATE, SEQ_TECH, COUNTRY, GEO_LOCATION, HOST
        "value_text": STRINGTYPE,
        "value_zip": STRINGTYPE,
        "value_varchar": STRINGTYPE,
        "value_blob": STRINGTYPE,  # actually "blobType"
        # needed - value_date -> RELEASE_DATE, dateime coversion introduces errors
        "value_date": STRINGTYPE,
    },
    "variantView": {
        "sample.id": INTTYPE,  # needed
        "sample.name": STRINGTYPE,  # needed
        "sample.seqhash": STRINGTYPE,
        # Cannot convert non-finite values (NA or inf) to integer
        "reference.id": STRINGTYPE,
        "reference.accession": STRINGTYPE,
        "reference.standard": STRINGTYPE,
        "molecule.id": INTTYPE,
        "molecule.accession": STRINGTYPE,
        "molecule.standard": STRINGTYPE,
        "element.id": INTTYPE,
        "element.accession": STRINGTYPE,
        "element.symbol": STRINGTYPE,  # needed = Gene Name
        "element.standard": STRINGTYPE,
        "element.type": STRINGTYPE,  # cds (=AA mutations) or source (=Nt mutations)
        # Cannot convert non-finite values (NA or inf) to integer --> STRINGTYPE
        "variant.id": STRINGTYPE,
        "variant.ref": STRINGTYPE,
        "variant.start": STRINGTYPE,
        "variant.end": STRINGTYPE,
        "variant.alt": STRINGTYPE,
        "variant.label": STRINGTYPE,  # needed mutation name
        # Cannot convert non-finite values (NA or inf) to integer --> STRINGTYPE
        "variant.parent_id": STRINGTYPE,
    },
    "referenceView": {
        "reference.id": INTTYPE,  # needed
        "reference.accession": STRINGTYPE,
        "reference.description": STRINGTYPE,
        "reference.organism": STRINGTYPE,
        "reference.standard": INTTYPE,
        "translation.id": INTTYPE,
        "molecule.id": INTTYPE,
        "molecule.type": STRINGTYPE,
        "molecule.accession": STRINGTYPE,
        "molecule.symbol": STRINGTYPE,
        "molecule.description": STRINGTYPE,
        "molecule.length": INTTYPE,
        "molecule.segment": INTTYPE,
        "molecule.standard": INTTYPE,
        "element.id": INTTYPE,
        "element.type": STRINGTYPE,  # needed
        "element.accession": STRINGTYPE,
        "element.symbol": STRINGTYPE,  # needed gene name
        "element.description": STRINGTYPE,
        "element.start": INTTYPE,  # needed = start gene name
        "element.end": INTTYPE,  # end gene cds
        "element.strand": INTTYPE,
        "element.sequence": STRINGTYPE,
        "elempart.start ": INTTYPE,
        "elempart.end ": INTTYPE,
        "elempart.strand ": INTTYPE,
        "elempart.segment ": INTTYPE,
    },
}

needed_columns = {
    "propertyView": [
        "sample.id",
        "sample.name",
        "property.name",
        "value_text",
        "value_date",
        "value_integer",
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
}


def get_database_connection(db_name: str):
    """
    connect to SQL DB based on environment var DB_URL and given db_name
    return: database connection
    """
    # DB configuration
    parsed_db_url = urlparse(DB_URL)
    user = parsed_db_url.username
    ip = parsed_db_url.hostname
    pw = parsed_db_url.password
    # port = parsed_db_url.port
    return create_engine(f"mysql+pymysql://{user}:{pw}@{ip}/{db_name}")


class DataFrameLoader:
    """
    connect to DB and loading of DB entires into panda dataframes
    loaded are the column of tables (defined in table) -> defined in variable needed_columns
    data types used for download from DB and reading from csv -> defined in variable column_dtypes
    two different download funtions for test DB and normal DB
    parallel loading of different tables (not for test DBs)
    writes downloaded tables as csv to .cache (not for test DBs)

    ...
    Attributes
    ----------
    db_name : str
        name of database to connect with
    tables: list[str]
        list of tables to download
    needed_columns: dict
        dict{table_name: list of needed columns for website}
    column_dtypes: dict(dict)
        dict{table_name: dict{column name: data type}}

    """

    def __init__(self, db_name: str):
        self.db_name = db_name
        self.tables = tables
        self.needed_columns = needed_columns
        self.column_dtypes = column_dtypes

    def define_sql_query_and_get_dtypes(self, table_name: str) -> (str, dict):
        """
        :return: SQL query for table with selection of needed columns and added correct quoting
        :return: dict for data types of selected columns
        """
        db_connection = get_database_connection(self.db_name)
        # we cannot use read_sql_table because it doesn't allow difining dtypes
        columns = pd.read_sql_query(
            f"SELECT * FROM {table_name} LIMIT 1;", con=db_connection
        ).columns
        if table_name in self.needed_columns.keys():
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
            queried_columns = ", ".join(quoted_column_names)
        else:
            types = {
                column: self.column_dtypes[table_name][column] for column in columns
            }
            queried_columns = "*"
        query = f"SELECT {queried_columns} FROM {table_name};"
        return query, types

    def load_db_from_sql(self, table_name: str) -> (str, dict):
        """
        download table of DB and write .csv into .cache

        :param table_name: name of the DB table to query
        :return: (path to csv, dtypes dict {column_name: dtype (from column_dtypes)})
        """
        # cpu_number=  mp.current_process().name.split("-")[-1]  # Get the CPU number
        # print(cpu_number)
        start = perf_counter()
        db_connection = get_database_connection(self.db_name)
        try:
            query, types = self.define_sql_query_and_get_dtypes(table_name)
            # we cannot use read_sql_table because it doesn't allow defining dtypes
            path_to_csv = f".cache/{table_name}.csv"
            if table_name == "variantView":
                with open(path_to_csv, "w") as tmpfile:
                    outcsv = csv.writer(tmpfile, lineterminator="\n")
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
            else:
                df = pd.read_sql_query(
                    query,
                    con=db_connection,
                    dtype=types,
                )
                # FIXME: should put , doublequote=True, or
                df.to_csv(path_to_csv, index=False)
        # missing table
        except exc.ProgrammingError:
            print(f"table {table_name} not in database.")
        print(f"Loading time {table_name}: {(perf_counter() - start):.4f} sec.")
        return path_to_csv, types

    def load_from_sql_db(self) -> dict:
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

        :return: df_dict {table_name: pandas dataframe}
        """
        pool = mp.Pool(mp.cpu_count())
        path_to_csv_types_list = pool.starmap(
            self.load_db_from_sql, [[table] for table in self.tables]
        )
        pool.close()  # tells the pool not to accept any new job.
        pool.terminate()
        pool.join()  # tells the pool to wait until all jobs finished then exit
        # blocking the parent process is just a side effect of what pool.join is doing.

        # NOTE: HARD CODE
        # read results back.
        df_dict = {}
        for path, types in path_to_csv_types_list:
            df_dict[Path(path).stem] = pd.read_csv(path, dtype=types)
        return df_dict

    def load_db_from_test_db(self) -> dict:
        """
        loading of test db without writing csv to cache

        :return: df_dict {table_name: pandas dataframe}
        """
        db_connection = get_database_connection(self.db_name)
        df_dict = {}
        for table in self.needed_columns.keys():
            try:
                query, types = self.define_sql_query_and_get_dtypes(table)
                df = pd.read_sql_query(
                    sql=query,
                    con=db_connection,
                    dtype=types,
                )
            except exc.ProgrammingError:
                print(f"table {table} not in database.")
                df = pd.DataFrame()
            df_dict[table] = df
        return df_dict


def create_property_view(df: pd.DataFrame) -> pd.DataFrame:
    """
    unstacking properties of propertyView:
    creating new columns for different property.name values by following steps:
    1. add values from value_date and value_integer to value_text column
    if property.name = "COLLECTION_DATE", "RELEASE_DATE", "IMPORTED", "LENGTH"
    2. unstacking property.name
    3. if no COLLECTION_DATE -> fill COLLECTION_DATE with RELEASE_DATE,
    delete row if both dates are not present
    4. fill empty entries with "undefined

    :param df: dataframe with columns
        ['sample.id', 'sample.name', 'property.name', 'value_integer', 'value_text', 'value_date']
    :return: df with columns
        ['sample.id', 'sample.name', 'COLLECTION_DATE', 'COUNTRY', 'GENOME_COMPLETENESS',
        'GEO_LOCATION', 'HOST', 'IMPORTED', 'ISOLATE', 'LENGTH', 'RELEASE_DATE', 'SEQ_TECH']
    """
    #  all dates and integer values into value_date column for unstacking
    df["value_text"] = df.apply(
        lambda row: row["value_date"]
        if row["property.name"] in ["COLLECTION_DATE", "RELEASE_DATE", "IMPORTED"]
        else row["value_text"],
        axis=1,
    )
    df = df.drop(columns=["value_date"], axis=1)
    df["value_text"] = df.apply(
        lambda row: row["value_integer"]
        if row["property.name"] in ["LENGTH"]
        else row["value_text"],
        axis=1,
    )
    df = df.drop(columns=["value_integer"], axis=1)
    cols = ["sample.id", "sample.name"]
    df = df.set_index(["property.name"] + cols).unstack("property.name")
    df = df.value_text.rename_axis([None], axis=1).reset_index()
    df["COLLECTION_DATE"].fillna(df["RELEASE_DATE"], inplace=True)
    # delete entries without collection and release date else nan errors:
    df = df.dropna(subset=["COLLECTION_DATE"])
    # delete entries without collection and release date else nan errors:
    df = df.dropna(subset=["COLLECTION_DATE"])
    df["COLLECTION_DATE"] = df["COLLECTION_DATE"].apply(
        lambda d: datetime.strptime(d, "%Y-%m-%d").date()
    )
    df["SEQ_TECH"] = df["SEQ_TECH"].replace([np.nan, ""], "undefined")
    df["COUNTRY"] = df["COUNTRY"].replace([np.nan, ""], "undefined")
    df["LENGTH"] = df["LENGTH"].astype(float).astype("Int64")
    #  print(f"time pre-processing PropertyView final: {(perf_counter()-start)} sec.")
    #  print(tabulate(df[0:10], headers='keys', tablefmt='psql'))
    return df


def create_variant_view(df: pd.DataFrame, propertyView_samples: set) -> pd.DataFrame:
    """
    change dtypes of "reference.id" and "variant.id" to int
    remove entries with sample ids not contained in propertyView
    :return: variantView
    """
    df["reference.id"] = df["reference.id"].astype(float).astype("Int64")
    df["variant.id"] = df["variant.id"].astype(float).astype("Int64")
    df = df[df["sample.id"].isin(propertyView_samples)]
    return df


def remove_x_appearing_variants(world_df: pd.DataFrame, nb: int = 1) -> pd.DataFrame:
    """
    currently not used
    function to remove all variants, that are present <= given number nb
    :return: world df without variants, that appear maximum nb-times
    """
    df2 = world_df.groupby(["gene:variant"]).sum(numeric_only=True).reset_index()
    variants_to_remove = df2[df2["number_sequences"] <= nb]["gene:variant"].tolist()
    if variants_to_remove:
        world_df = world_df[~world_df["gene:variant"].isin(variants_to_remove)]
        world_df = world_df[~world_df["gene:variant"].isin(variants_to_remove)]
    return world_df


def create_world_map_df(
    variantView: pd.DataFrame, propertyView: pd.DataFrame
) -> pd.DataFrame:
    """
    created df used for explorer tool by following steps:
    1. merge propertyView and variatView df
    2. concat all strain_ids into one comma separated string list if they have the same
    location_ID, date, amino_acid-variant --> new column sample_id_list
    3. count samples with same properties --> new column number_sequences
    4. combine element.symbol:variant.label to new column gene:variant

    :return: world_df with columns []"COUNTRY", "COLLECTION_DATE", "SEQ_TECH", "sample_id_list",
            "variant.label", "number_sequences", "element.symbol", "gene:variant"]
    """
    df = pd.merge(
        variantView[["sample.id", "variant.label", "element.symbol"]],
        propertyView[["sample.id", "COUNTRY", "COLLECTION_DATE", "SEQ_TECH"]],
        how="inner",
        on="sample.id",
    )[
        [
            "sample.id",
            "COUNTRY",
            "COLLECTION_DATE",
            "variant.label",
            "SEQ_TECH",
            "element.symbol",
        ]
    ]
    # same location_ID, date, amino_acid --> concat all strain_ids into comma separated string list
    df = (
        df.groupby(
            [
                "COUNTRY",
                "COLLECTION_DATE",
                "variant.label",
                "SEQ_TECH",
                "element.symbol",
            ],
            dropna=False,
        )["sample.id"]
        .apply(lambda x: ",".join([str(y) for y in set(x)]))
        .reset_index(name="sample_id_list")
    )
    # add sequence count
    df["number_sequences"] = df["sample_id_list"].apply(lambda x: len(x.split(",")))
    df["gene:variant"] = (
        df["element.symbol"].astype(str) + ":" + df["variant.label"].astype(str)
    )
    df = df[
        [
            "COUNTRY",
            "COLLECTION_DATE",
            "SEQ_TECH",
            "sample_id_list",
            "variant.label",
            "number_sequences",
            "element.symbol",
            "gene:variant",
        ]
    ]
    # df = remove_x_appearing_variants(df, 1)
    return df


def remove_seq_errors_and_add_gene_var_column(
    variantView: pd.DataFrame, reference_id: int, seq_type: str
) -> pd.DataFrame:
    """
    remove sequencing errors from variantView table:
    X for amino acid variants, N for nucleotide variants
    split variantView table based on reference_id and element.type into multiple tables
    combine element.symbol and variant.label to new column gene:variant

    :param variantView: complete or partial variantView dataframe
    :param reference_id: id of reference sequence
    :param seq_type: "cds" or "source"
    :return: variantView df
    for nucleotide variants with columns:
        ['sample.id', 'sample.name', 'reference.id', 'reference.accession','element.symbol',
        'element.type', 'variant.id', 'variant.label']
    for protein variants:
        additional column 'gene:variant'
    """
    df = variantView[
        (variantView["reference.id"] == reference_id)
        & (variantView["element.type"] == seq_type)
    ].reset_index(drop=True)
    if seq_type == "source":
        # unknown_nt = ['N', 'V', 'D', 'H', 'B', 'K', 'M', 'S', 'W']
        df = df[~df["variant.label"].str.contains("N")]
    # B, Z, J not in DB, X always at the end, all undefined nucleotides translated to X
    elif seq_type == "cds":
        df = df[~df["variant.label"].str.endswith("X")]
        df["gene:variant"] = (
            df["element.symbol"].astype(str) + ":" + df["variant.label"].astype(str)
        )
    return df


def create_empty_processed_df(reference_ids: list[int]) -> dict:
    """
    create needed structure of processed_df_dict
    """
    processed_df_dict = defaultdict(dict)
    for completeness in ["complete", "partial"]:
        processed_df_dict["variantView"][completeness] = {}
        processed_df_dict["world_map"][completeness] = {}
        for reference_id in reference_ids:
            processed_df_dict["variantView"][completeness][reference_id] = {}
    return processed_df_dict


def load_all_sql_files(  # noqa: C901
    db_name: str = None, test_db: bool = False
) -> dict:
    """
    load SQL DB into dict of pandas dfs
    to handle big db size: DB tables are splitted into multiple tables in processed_df_dict:
        processed_df_dict["propertyView"]["complete" OR "partial"]
        processed_df_dict["variantView"]["complete" OR "partial"][reference_id][seq_type]

    for website running db_name is parsed from env var DB_URL, for test DB params are used

    :param db_name: for test databases name is given
    :param test_db: for tests databases test_db=True
    :return: complete pre processed DB dictionary
    """
    if not db_name:
        db_name = urlparse(DB_URL).path.replace("/", "")
    path_to_cache = CACHE_DIR
    loader = DataFrameLoader(db_name)

    # NOTE:
    # TODO automated update of pickle file with new database
    # 1. Using Pickle should only be used on 100% trusted data
    # 2. msgpack can be other options.
    # check if df_dict is load or not?
    if redis_manager and redis_manager.exists("df_dict") and not test_db:
        # if True:
        print("Load data from cache...")
        # df_dict = decompress_pickle(os.path.join(CACHE_DIR,"df_dict.pbz2"))
        # df_dict = pickle.loads(redis_manager.get("df_dict"))
        processed_df_dict = load_Cpickle(os.path.join(path_to_cache, "df_dict.pickle"))
    else:
        if test_db:
            print("Load data from test database")
            loaded_df_dict = loader.load_db_from_test_db()
        else:
            print("Load data from database...")
            loaded_df_dict = loader.load_from_sql_db()

        # df preprocessing
        print("Data preprocessing...")
        # TODO why NaN in reference --> database error?
        reference_ids = [
            int(ref)
            for ref in loaded_df_dict["variantView"]["reference.id"].dropna().unique()
        ]
        processed_df_dict = create_empty_processed_df(reference_ids)
        # propertyView
        processed_propertyView = create_property_view(loaded_df_dict["propertyView"])
        for completeness in ["complete", "partial"]:
            processed_df_dict["propertyView"][completeness] = processed_propertyView[
                processed_propertyView["GENOME_COMPLETENESS"] == completeness
            ].reset_index(drop=True)
        del processed_propertyView
        del loaded_df_dict["propertyView"]
        # variantView
        for completeness in ["complete", "partial"]:
            processed_variantView = create_variant_view(
                loaded_df_dict["variantView"],
                set(processed_df_dict["propertyView"][completeness]["sample.id"]),
            )
            for reference_id in reference_ids:
                for seq_type in ["source", "cds"]:
                    processed_df_dict["variantView"][completeness][reference_id][
                        seq_type
                    ] = remove_seq_errors_and_add_gene_var_column(
                        processed_variantView, reference_id, seq_type
                    )
            del processed_variantView
        del loaded_df_dict["variantView"]
        # worldMap
        for completeness in ["complete", "partial"]:
            for reference_id in reference_ids:
                processed_df_dict["world_map"][completeness][
                    reference_id
                ] = create_world_map_df(
                    processed_df_dict["variantView"][completeness][reference_id]["cds"],
                    processed_df_dict["propertyView"][completeness],
                )

        if redis_manager:
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
            if not test_db:
                print("Create a new cache")
                write_Cpickle(
                    os.path.join(path_to_cache, "df_dict.pickle"), processed_df_dict
                )
                redis_manager.set("df_dict", 1, ex=3600 * 23)

            # df_dict["propertyView"].to_pickle(".cache/propertyView.pkl")
            # df_dict["variantView"].to_pickle(".cache/variantView.pkl")
            # df_dict["referenceView"].to_pickle(".cache/referenceView.pkl")

    return processed_df_dict


if __name__ == "__main__":
    print("Build a new cache")
    load_all_sql_files()
    create_snp_table()
    calculate_tri_mutation_sig()
    calculate_mutation_sig()
    print("--- Complete ----")
