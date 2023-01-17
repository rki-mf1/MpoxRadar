import os
from uuid import uuid4

import dash
from dash import CeleryManager
from dash import Dash
from dash import DiskcacheManager
from dash import html
import dash_bootstrap_components as dbc
import tomli

from pages.config import logging_radar
from pages.util_footer_table import footer_table

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
    from celery import Celery

    celery_app = Celery(
        __name__, broker=os.environ["REDIS_URL"], backend=os.environ["REDIS_URL"]
    )
    background_callback_manager = CeleryManager(
        celery_app, cache_by=[lambda: launch_uid]
    )

else:
    # Diskcache for non-production apps when developing locally
    logging_radar.info("Diskcache")
    import diskcache

    cache = diskcache.Cache("/tmp/.mpoxradar_cache")
    background_callback_manager = DiskcacheManager(
        cache, expire=200, cache_by=[lambda: launch_uid]
    )

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[dbc.themes.ZEPHYR, dbc.icons.BOOTSTRAP],
    background_callback_manager=background_callback_manager,
)
server = app.server

app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1("MpoxRadar", style={"display": "inline-block"}),
                        html.Div(
                            "An interactive dashboard for genomic surveillance of mpox."
                        ),
                    ]
                ),
                dbc.Col(
                    [
                        html.Img(
                            src=r"assets/hpi_logo.png",
                            alt="Img_HPI",
                            style={"float": "right", "width": "25%", "height": "auto"},
                            className="responsive",
                        ),
                        html.Img(
                            src=r"assets/rki_logo.png",
                            alt="Img_RKI",
                            style={
                                "float": "right",
                                "width": "25%",
                                "height": "auto",
                                "marginTop": "20px",
                                "marginRight": "20px",
                            },
                            className="responsive",
                        ),
                        html.Img(
                            src=r"assets/DAKI-FWS_logo.png",
                            alt="Img_DAKI-FWS",
                            style={"float": "right", "width": "25%", "height": "auto"},
                            className="responsive",
                        ),
                    ]
                ),
            ]
        ),
        html.Hr(className="my-2"),
        html.Div(
            [
                dbc.Button(
                    [html.I(className="bi bi-info-circle-fill me-2"), "About"],
                    href="About",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-file-bar-graph me-2"),
                        "Tool",
                        dbc.Badge(
                            "Click Here",
                            color="info",
                            text_color="white",
                            className="ms-1",
                        ),
                    ],
                    href="Tool",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [html.I(className="bi bi-card-list me-2"), "Help"],
                    href="Help",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-send-check-fill me-2"),
                        "Imprint & Privacy Policy",
                    ],
                    href="Imprint",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    [
                        html.I(className="bi bi-envelope-plus-fill me-2"),
                        "Contact",
                    ],
                    href="Contact",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
            ]
        ),
        html.Br(),
        dash.page_container,
        html.Br(),
        html.Div(
            [
                html.Hr(),
                html.Div(["Version = " + __version__]),
                html.Footer([footer_table]),
            ],
            className="",
        ),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
