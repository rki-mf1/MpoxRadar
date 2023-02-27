import dash
from dash import html

dash.register_page(__name__, path="/Home")

layout = html.Div(
    children=[
        html.H1(children="Welcome"),
        html.Div(
            children="""
                Simply click a button to navigate webpage. We confirm that this website is free and open to all users and there is no login requirement.
            """
        ),
    ]
)
