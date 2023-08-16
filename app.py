import logging
import os
from dash import Dash
from data_management.data_manager import DataManager

import dash_bootstrap_components as dbc

from layouts import MAIN_LAYOUT


class MPoxRadar:
    def __init__(self):
        # TODO-smc needed?
        # self.dbc_css = (
        #    "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
        # )
        data_manager = DataManager.get_instance()
        self.app = Dash(
            __name__,
            use_pages=True,
            external_stylesheets=[
                dbc.themes.ZEPHYR,
                dbc.icons.BOOTSTRAP,
                dbc.icons.FONT_AWESOME,
            ],
            long_callback_manager=data_manager.background_callback_manager,
            background_callback_manager=data_manager.background_manager,
            suppress_callback_exceptions=True,
        )
        self.server = self.app.server
        # cache.init_app(server)
        self.app.layout = MAIN_LAYOUT


def initialize_logging():
    log_level = logging.DEBUG
    if "LOG_LEVEL" in os.environ:
        log_level = os.environ["LOG_LEVEL"]
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        handlers=[logging.StreamHandler()],
    )


if __name__ == "__main__":
    mpox_radar = MPoxRadar()
    mpox_radar.app.run(debug=True)
