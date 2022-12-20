import dash
from dash import Dash
from dash import html
import dash_bootstrap_components as dbc
import tomli

from pages.util_footer_table import row1

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

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
app = Dash(
    __name__, use_pages=True, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc_css]
)
server = app.server
table_body = [html.Tbody([row1])]

table = dbc.Table(table_body, bordered=True)

app.layout = html.Div(
    [
        html.H1("MpoxRadar", style={"display": "inline-block"}),
        html.Img(
            src=r"assets/hpi_logo.png",
            alt="Img_HPI",
            style={"float": "right", "height": "10%", "width": "10%"},
            className="responsive",
        ),
        html.Img(
            src=r"assets/rki_logo.png",
            alt="Img_RKI",
            style={
                "float": "right",
                "height": "10%",
                "width": "10%",
                "margin-top": "50px",
                "margin-right": "20px",
            },
            className="responsive",
        ),
        html.Img(
            src=r"assets/DAKI-FWS_logo.png",
            alt="Img_DAKI-FWS",
            style={"float": "right", "height": "10%", "width": "10%"},
            className="responsive",
        ),
        html.Div("An interactive dashboard for genomic surveillance of mpox."),
        html.Br(),
        html.Div(
            [
                dbc.Button(
                    "About",
                    href="About",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    "Tool", href="Tool", outline=True, color="primary", className="me-1"
                ),
                dbc.Button(
                    "Help", href="Help", outline=True, color="primary", className="me-1"
                ),
                dbc.Button(
                    "Imprint & Privacy Policy",
                    href="Imprint",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
                dbc.Button(
                    "Contact",
                    href="Contact",
                    outline=True,
                    color="primary",
                    className="me-1",
                ),
            ]
        ),
        html.Br(),
        html.Br(),
        dash.page_container,
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Div(["Version = " + __version__]),
        html.Div([html.Hr(), html.Footer([table])], className="app_footer"),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
