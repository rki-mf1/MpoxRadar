from dash import html
import dash_bootstrap_components as dbc

row1 = html.Tr(
    [
        html.Td(
            html.Ul(
                [
                    html.Li(
                        [
                            html.A(
                                "About MpoxRadar",
                                href="",
                                style={"color": "black"},
                            )
                        ],
                        style={"marginBottom": "10px"},
                    ),
                    html.Li(
                        [html.A("Tool", href="Tool", style={"color": "black"})],
                        style={"marginBottom": "10px"},
                    ),
                    html.Li(
                        [html.A("Help", href="Help", style={"color": "black"})],
                        style={"marginBottom": "10px"},
                    ),
                    html.Li(
                        [
                            html.A(
                                "Imprint & Privacy Policy",
                                href="Imprint",
                                style={"color": "black"},
                            )
                        ],
                        style={"marginBottom": "10px"},
                    ),
                    html.Li(
                        [html.A("Contact", href="Contact", style={"color": "black"})]
                    ),
                ],
                style={"listStyleType": "none"},
            ),
            style={"textAlign": "left", "width": "60%"},
            className="responsive",
        ),
        html.Td(
            html.Img(
                src=r"assets/BMWK_Logo_en.png",
                alt="BMWK_logo",
                style={"height": "auto", "minWidth": "100%", "marginTop": "10px"},
                className="responsive",
            ),
            style={"textAlign": "left", "width": "15%"},
            className="responsive",
        ),
        html.Td(
            html.Img(
                src=r"assets/denbi_cloud_logo.png",
                alt="Img_RKI",
                style={"height": "auto", "minWidth": "60%", "marginTop": "130px"},
                className="responsive",
            ),
            style={"textAlign": "left", "width": "15%"},
            className="responsive",
        ),
    ],
    style={"orderStyle": "none"},
)

table_body = [html.Tbody([row1])]

footer_table = dbc.Table(table_body, bordered=True)
