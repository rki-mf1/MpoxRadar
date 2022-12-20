import dash
from dash import html

dash.register_page(__name__, path="/")

layout = html.Div(
    children=[
        html.H1(children="Welcome"),
        html.Div(
            children="""
                Simply click a button to navigate webpage.
            """
        ),
    ]
)
