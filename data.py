import os
import sqlalchemy
from sqlalchemy import create_engine
from time import perf_counter
import pandas as pd
import multiprocessing as mp

tables = ['propertyView']

# pandas normally uses python strings, which have about 50 bytes overhead. that's catastrophic!
stringType = 'string[pyarrow]'
intType = 'int32'

column_dtypes = {
    'propertyView' : {
        '`sample.id`' : intType, # needed
        '`sample.name`' : stringType, # needed
        '`property.id`' : intType,
        '`property.name`' : stringType, # needed
        '`propery.querytype`' : stringType,
        '`property.datatype`' : stringType,
        '`property.standard`' : stringType,
        '`value_integer`' : intType, # needed - value_integer -> LENGTH
        '`value_float`' : 'float32',
        'value_text' : stringType, # needed - value_text -> COLLECTION_DATE, RELEASE_DATE, ISOLATE, SEQ_TECH, COUNTRY, GEO_LOCATION, HOST
        '`value_zip`' : stringType,
        '`value_varchar`' : stringType,
        '`value_blob`' : stringType, # actually "blobType"
        'value_date' : 'datetime64' # needed - value_date -> RELEASE_DATE
    }
}


### get the mpox-map-data in the same structure as the cov-map-data
### in order to plot mpox-data in covradar-app!!
needed_columns = {'propertyView' : ['`sample.id`','`sample.name`','`property.name`','value_integer','value_text','value_date']}



def get_database_connection(database_name):
    # DB configuration
    user = os.environ.get("MYSQL_USER", "root")
    ip = os.environ.get("MYSQL_HOST", "localhost")
    pw = os.environ.get("MYSQL_PW", "secret")
    return create_engine(f'mysql+pymysql://{user}:{pw}@{ip}/{database_name}')


class DataFrameLoader():
    def __init__(self, db_name, table):
        self.db_name = db_name
        self.table = tables
        self.needed_columns = needed_columns
        self.column_dtypes = column_dtypes
    def load_db_from_sql(self, db_name, table_name):
        start = perf_counter()
        db_connection = get_db_connection(db_name)
        df_dict = {}
        try:
            # we cannot use read_sql_table because it doesn't allow difining dtypes
            columns = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1;", con=db_connection).columns
            if table_name in self.needed_columns:
                columns = columns.intersection(self.needed_columns[table_name])
                types = {column : self.column_dtypes[table_name][column] for column in columns}
                queried_columns = ', '.join(columns)
            else:
                types = {column : self.column_dtypes[table_name][column] for column in columns}
                queried_columns = '*'
            df = pd.read_sql_query(f"SELECT {queried_columns} FROM {table_name};", con=db_connection, dtypes=types)

