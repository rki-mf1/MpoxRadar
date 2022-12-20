import multiprocessing as mp
import os
from time import perf_counter

import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine

tables = ["propertyView"]

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
        "value_date": "datetime64",  # needed - value_date -> RELEASE_DATE
    }
}


### get the mpox-map-data in the same structure as the cov-map-data
### in order to plot mpox-data in covradar-app!!
needed_columns = {
    "propertyView": [
        "sample.id",
        "sample.name",
        "property.name",
        "value_integer",
        "value_text",
        "value_date",
    ]
}


def get_database_connection(database_name):
    # DB configuration
    user = os.environ.get("MYSQL_USER", "root")
    ip = os.environ.get("MYSQL_HOST", "localhost")
    pw = os.environ.get("MYSQL_PW", "secret")
    return create_engine(f"mysql+pymysql://{user}:{pw}@{ip}/{database_name}")


class DataFrameLoader:
    def __init__(self, db_name, table):
        self.db_name = db_name
        self.tables = tables
        self.needed_columns = needed_columns
        self.column_dtypes = column_dtypes

    def load_db_from_sql(self, db_name, table_name):
        start = perf_counter()
        db_connection = get_database_connection(db_name)
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
        print(f"Loading time {table_name}: {(perf_counter()-start)} sec.")
        if not df.empty:
            df_dict[table_name] = df
            return df_dict

    def load_from_sql_db(self):
        pool = mp.Pool(mp.cpu_count())
        dict_list = pool.starmap(
            self.load_db_from_sql,
            [(self.db_name, table_name) for table_name in self.tables],
        )
        pool.close()
        pool.terminate()
        pool.join()
        df_dict = {}
        for df_d in dict_list:
            if df_d is not None:
                df_dict.update(df_d)
        return df_dict


def load_all_sql_files(db_name):
    loader = DataFrameLoader(db_name, tables)
    df_dict = loader.load_from_sql_db()
    return df_dict
