"""
class RedisManger(object):
    def __init__(self, db_url=None, readonly=True):
        if db_url is None:
            db_url = DB_URL

        self.db_user = self.__uri.username
        self.db_pass = self.__uri.password
        self.db_url = self.__uri.hostname
        self.db_port = self.__uri.port
        self.db_database = self.__uri.path.replace("/", "")

    def __enter__(self):
        "establish connection and start transaction when class is initialized"
        self.connection, self.cursor = self.connect()
        self.start_transaction()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        "close connection and - if errors occured - rollback when class is exited"
        if [exc_type, exc_value, exc_traceback].count(None) != 3:
            if self.__mode == "rwc":
                print("Rollback database", file=sys.stderr)
                self.rollback()
        elif self.__mode == "rwc":
            self.commit()
        self.close()

    def __del__(self):
        "close connection when class is deleted"
        if self.connection:
            # self.close()
            self.conection = None
            # logging.debug("Connection Closed")

    def connect(self):
        "connect to database"
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

"""
