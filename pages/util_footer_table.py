from dash import html


row1 = html.Tr(
    [
        html.Td(
            html.Ul(
                [
                    html.Li(
                        [
                            html.A(
                                "About MpoxRadar",
                                href="About",
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
            html.Ul(
                [
                    html.Li([html.Div(children="Supported by:")]),
                    html.Li(
                        [
                            html.Img(
                                src=r"assets/Bundesministerium_für_Wirtschaft_und_Energie_Logo.svg.png",
                                alt="Img_RKI",
                                style={
                                    "marginTop": "-10px",
                                    "height": "auto",
                                    "minWidth": "100%",
                                },
                                className="responsive",
                            )
                        ],
                    ),
                    html.Li(
                        [html.Div(children="on the basis of a decision")],
                        style={"marginTop": "-20px"},
                    ),
                    html.Li([html.Div(children="by the German Bundestag")]),
                ],
                style={"listStyleType": "none", "textAlign": "center"},
            ),
            style={"width": "15%"},
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
