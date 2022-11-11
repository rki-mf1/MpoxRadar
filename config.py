import os

from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_DATABASE = os.getenv("DB_DATABASE")
DB_PORT = os.getenv("DB_PORT")
# FLASK APP
SECRET_KEY = os.getenv("SECRET_KEY") or "development-secret"
DEBUG = os.getenv("DEBUG") or False
