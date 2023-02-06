import logging
import os
from urllib.parse import urlparse
from uuid import uuid4

from dash import CeleryManager
from dash import DiskcacheManager
from dash.long_callback import CeleryLongCallbackManager
from dotenv import load_dotenv
from flask_caching import Cache
import pandas as pd
import plotly.express as px
import redis
import tomli

load_dotenv()

# CONFIG
SERVER = os.getenv("SERVER")
DEBUG = os.getenv("DEBUG")
DB_URL = os.getenv("DB_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL")
# REDIS_URL =  os.getenv("REDIS_URL")
REDIS_BACKEND_URL = os.path.join(os.getenv("REDIS_URL"), os.getenv("REDIS_DB_BACKEND"))
REDIS_BROKER_URL = os.path.join(os.getenv("REDIS_URL"), os.getenv("REDIS_DB_BROKER"))


def get_module_logger(mod_name):
    """
    format="MPXRadar:%(asctime)s %(levelname)-4s: %(message)s",
    level=LOG_LEVEL,
    datefmt="%Y-%m-%d %H:%M:%S",
    """
    logger = logging.getLogger(mod_name)
    if not logger.handlers:
        # Prevent logging from propagating to the root logger
        logger.propagate = 0
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "MPXRadar:%(asctime)s %(levelname)-4s: %(message)s", "%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(LOG_LEVEL)
    return logger


logging_radar = get_module_logger("MPXRadar")
# The implication of this cache_by function is that the cache is shared across all invocations
# of the callback across all user sessions that are handled by a single server instance.
# Each time a server process is restarted, the cache is cleared and a new UUID is generated.
launch_uid = uuid4()
# Determine version using pyproject.toml file
try:
    from importlib.metadata import version, PackageNotFoundError  # type: ignore
except ImportError:  # pragma: no cover
    from importlib_metadata import version, PackageNotFoundError  # type: ignore


try:
    __version__ = version(__name__)
except PackageNotFoundError:  # pragma: no cover
    with open("pyproject.toml", mode="rb") as pyproject:
        pkg_meta = tomli.load(pyproject)["tool"]["poetry"]
        __version__ = str(pkg_meta["version"])


if "REDIS_URL" in os.environ:
    logging_radar.info("Use Redis & Celery")
    # Use Redis & Celery if REDIS_URL set as an env variable
    from celery import Celery  # type: ignore

    # Redis server
    # TODO: reorganize cache loading.
    try:
        __uri = urlparse(REDIS_BACKEND_URL)
        db_user = __uri.username
        db_pass = __uri.password
        db_url = __uri.hostname
        db_port = __uri.port
        db_database = __uri.path.replace("/", "")
        pool = redis.ConnectionPool(host=db_url, port=db_port, db=db_database)
        redis_manager = redis.Redis(connection_pool=pool)
    except (ConnectionError, TimeoutError, ValueError) as e:
        redis_manager = None
        logging_radar.error(f"Error connecting to Redis: {e}")
        logging_radar.warn("No Redis system is used")
        # sys.exit(1)

    celery_app = Celery(
        __name__, broker=REDIS_BROKER_URL, backend=REDIS_BROKER_URL, expire=60
    )

    background_manager = CeleryManager(celery_app, cache_by=[lambda: launch_uid])

    background_callback_manager = CeleryLongCallbackManager(celery_app, expire=300)

    cache = Cache(
        config={
            "CACHE_TYPE": "RedisCache",
            # this is fine since cache is only invalid after pipeline run
            "CACHE_DEFAULT_TIMEOUT": 60 * 60 * 23,
            "CACHE_REDIS_HOST": db_url,
            "CACHE_REDIS_PORT": db_port or 6379,
            "CACHE_REDIS_DB": db_database or 1,
            "CACHE_REDIS_PASSWORD": db_pass or "",
            "CACHE_REDIS_USER": db_user or "",
            # if the source code changes, the cache is invalidated
            "CACHE_SOURCE_CHECK": True,
            "DEBUG": True if os.environ.get("DEBUG_REDIS") == "true" else False,
        }
    )

else:
    # Diskcache for non-production apps when developing locally
    logging_radar.info("Diskcache")
    logging_radar.warning("Diskcache for non-production apps")
    import diskcache  # type: ignore

    cache = diskcache.Cache("/tmp/.mpoxradar_cache")
    background_callback_manager = DiskcacheManager(
        cache, expire=200, cache_by=[lambda: launch_uid]
    )


# STRING

# load all data once
location_coordinates = pd.read_csv("data/location_coordinates.csv")


# 56 colors

color_schemes = (
    px.colors.cyclical.Twilight
    + px.colors.cyclical.IceFire
    + px.colors.cyclical.Phase
    + px.colors.cyclical.Edge
)
