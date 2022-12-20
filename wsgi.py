# from example_app import server as application
from app import app as application

from app import server

if __name__ == "__main__":
    application.run_server(host="localhost")
