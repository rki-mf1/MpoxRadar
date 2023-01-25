import multiprocessing as mp
from datetime import datetime
from time import perf_counter
from urllib.parse import urlparse
import pandas as pd
import numpy as np
import sqlalchemy
from sqlalchemy import create_engine
from tabulate import tabulate

from pages.config import DB_URL

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
        "element.symbol": stringType,
        "element.standard": stringType,
        "element.type": stringType,
        "variant.id": stringType,  # Cannot convert non-finite values (NA or inf) to integer
        "variant.ref": stringType,
        "variant.start": stringType,
        "variant.end": stringType,
        "variant.alt": stringType,
        "variant.label": stringType,
        "variant.parent_id": stringType  # Cannot convert non-finite values (NA or inf) to integer
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
        "element.symbol": stringType,  # needed
        "element.description": stringType,
        "element.start": intType,  # needed
        "element.end": intType,
        "element.strand": intType,
        "element.sequence": stringType,
        "elempart.start ": intType,
        "elempart.end ": intType,
        "elempart.strand ": intType,
        "elempart.segment ": intType,
    }
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
        "element.type"
    ],
    "referenceView": [
        "reference.id",
        "element.type",
        "element.symbol",
        "element.start",
        "element.end"
    ]
}


def get_database_connection():
    # DB configuration
    parsed_db_url = urlparse(DB_URL)
    user = parsed_db_url.username
    ip = parsed_db_url.hostname
    pw = parsed_db_url.password
    port = parsed_db_url.port
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
            df = pd.read_sql_query(
                f"SELECT {queried_columns} FROM {table_name};",
                con=db_connection,
                dtype=types,
            )
        # missing table
        except sqlalchemy.exc.ProgrammingError:
            print(f"table {table_name} not in database.")
            df = pd.DataFrame()
        print(f"Loading time {table_name}: {(perf_counter() - start)} sec.")
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
    #  start = perf_counter()
    df['value_text'] = df.apply(lambda row: row["value_date"] if row["property.name"] in
                                ['COLLECTION_DATE', 'RELEASE_DATE'] else row["value_text"], axis=1)
    df = df.drop(columns=["value_date"], axis=1)
    c = ['sample.id', 'sample.name']
    df = df.set_index(['property.name'] + c).unstack('property.name')
    df = df.value_text.rename_axis([None], axis=1).reset_index()
    df['COLLECTION_DATE'] = df[['COLLECTION_DATE']].fillna(dummy_date)
    df['COLLECTION_DATE'] = df['COLLECTION_DATE'].apply(lambda d: datetime.strptime(d, "%Y-%m-%d").date())
    df['SEQ_TECH'] = df['SEQ_TECH'].replace([np.nan, ""], 'undefined')
    #  print(f"time pre-processing PropertyView final: {(perf_counter()-start)} sec.")
    #  print(print(tabulate(df[0:10], headers='keys', tablefmt='psql')))
    return df


def create_variant_view(df):
    #  start = perf_counter()
    df['reference.id'] = df['reference.id'].astype(float).astype("Int64")
    df['variant.id'] = df['variant.id'].astype(float).astype("Int64")
    # print(f"time pre-processing VariantView: {(perf_counter()-start)} sec.")
    # print(print(tabulate(df[0:10], headers='keys', tablefmt='psql')))
    # df = df[df['element.type']=='cds'].reset_index(drop=True)
    return df


# TODO correct? now very very error prone, e.g. overlapping genes, duplicate entries, defnitly wrong (all mut in first 3 genes)
def create_reference_view(df):
    df = df[(df["element.type"] == "cds")]
    grouped_df = df.groupby(["reference.id"])
    aa_start = []
    aa_end = []
    for name, group in grouped_df:
        aa_start_pos=1
        for start, end in zip(group['element.start'], group["element.end"]):
            aa_end_pos = int((end-start)/3) + aa_start_pos - 1
            aa_start.append(aa_start_pos)
            aa_end.append(aa_end_pos)
            aa_start_pos = aa_end_pos + 1
    df["aa_start"] = aa_start
    df["aa_end"] = aa_end
    print(f"refview.")
    print(print(tabulate(df[df["reference.id"]==2][0:20], headers='keys', tablefmt='psql')))
    return df


def load_all_sql_files():
    loader = DataFrameLoader()
    df_dict = loader.load_from_sql_db()
    # TODO query for variantView tooo long.
    df_dict["propertyView"] = create_property_view(df_dict["propertyView"])
    df_dict["variantView"] = create_variant_view(df_dict["variantView"])
    df_dict["referenceView"] = create_reference_view(df_dict["referenceView"])
    return df_dict
