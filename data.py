from datetime import datetime
import multiprocessing as mp
from time import perf_counter
from urllib.parse import urlparse

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine

from pages.config import DB_URL

tables = ["propertyView", "variantView"]

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
        "value_text": stringType,  # needed - value_text -> COLLECTION_DATE, RELEASE_DATE, ISOLATE, SEQ_TECH, COUNTRY, GEO_LOCATION, HOST
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
        "element.symbol": stringType,
        "element.standard": stringType,
        "element.type": stringType,
        "variant.id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
        "variant.ref": stringType,
        "variant.start": stringType,
        "variant.end": stringType,
        "variant.alt": stringType,
        "variant.label": stringType,
        "variant.parent_id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
    },
}


### get the mpox-map-data in the same structure as the cov-map-data
### in order to plot mpox-data in covradar-app!!
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
        df_dict = {}
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
                ### a '.' in the column names implies ``-quoting the column name for a mariadb-query
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
            df = pd.read_sql_query(
                f"SELECT {queried_columns} FROM {table_name};",
                con=db_connection,
                dtype=types,
            )
        # missing table
        except sqlalchemy.exc.ProgrammingError:
            print(f"table {table_name} not in database.")
            df = pd.DataFrame()
        print(f"Loading time {table_name}: {(perf_counter()-start):.3f} sec.")
        if not df.empty:
            df_dict[table_name] = df
            return df_dict

    def load_from_sql_db(self):
        pool = mp.Pool(mp.cpu_count())
        dict_list = pool.starmap(
            self.load_db_from_sql,
            [[table] for table in self.tables],
        )
        pool.close()
        pool.terminate()
        pool.join()
        df_dict = {}
        for df_d in dict_list:
            if df_d is not None:
                df_dict.update(df_d)
        return df_dict


def create_property_view(df, dummy_date="2021-12-31"):
    df = (
        df.set_index(
            ["sample.id", "sample.name", "property.name", "value_date"], drop=True
        )
        .unstack("property.name")
        .reset_index()
    )
    sub_df = df[["sample.id", "sample.name", "value_date"]]
    sub_df.columns = ["sample.id", "sample.name", "value_date"]
    df = pd.concat([sub_df, df["value_text"]], axis=1).reindex()
    df = df.drop(columns=["COLLECTION_DATE"], axis=1)
    df = df.rename(columns={"value_date": "COLLECTION_DATE"})
    df["COLLECTION_DATE"] = df[["COLLECTION_DATE"]].fillna(dummy_date)
    df["COLLECTION_DATE"] = df["COLLECTION_DATE"].apply(
        lambda d: datetime.strptime(d, "%Y-%m-%d").date()
    )
    return df


def create_variant_view(df):
    df["reference.id"] = df["reference.id"].astype(float).astype("Int64")
    df["variant.id"] = df["variant.id"].astype(float).astype("Int64")
    # df = df[df['element.type']=='cds'].reset_index(drop=True)
    return df


def load_all_sql_files():
    loader = DataFrameLoader()
    df_dict = loader.load_from_sql_db()
    # TODO query for variantView tooo long. Add sample_id alignment table? (seqhash joining is very expensive), molecule_id == reference_id ?
    df_dict["propertyView"] = create_property_view(df_dict["propertyView"])
    df_dict["variantView"] = create_variant_view(df_dict["variantView"])
    return df_dict
