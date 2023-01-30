import logging
import os

from dotenv import load_dotenv
import pandas as pd
import plotly.express as px


load_dotenv()

# CONFIG
SERVER = os.getenv("SERVER")
DEBUG = os.getenv("DEBUG")
DB_URL = os.getenv("DB_URL")
LOG_LEVEL = os.getenv("LOG_LEVEL")


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
