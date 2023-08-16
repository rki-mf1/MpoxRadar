import os
from tempfile import mkdtemp

from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DB_URL")
# FLASK APP
SECRET_KEY = os.getenv("SECRET_KEY") or "development-secret"
DEBUG = os.getenv("DEBUG") or False
# 10 = DEBUG, 20 = INFO, 30 = WARNING
LOG_LEVEL = os.getenv("LOG_LEVEL") or 20


TMP_CACHE = os.path.abspath(mkdtemp(prefix=".sonarCache_"))
