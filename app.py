import dash
from dash import Dash
from dash import dcc
from dash import html

app = Dash(__name__, use_pages=True)
app.layout = html.Div(
    [
        html.H1("MonkeyPox Radar", style={'display':'inline-block'}),
        
        html.Img(src=r'assets/hpi_logo.png',alt='Img_HPI', style={'float':'right', 'height':'15%', 'width':'15%'}),
        html.Img(src=r'assets/rki_logo.png',alt='Img_RKI', style={'float':'right', 'height':'15%', 'width':'15%'}),
        html.Img(src=r'assets/DAKI-FWS_logo.png',alt='Img_DAKI-FWS', style={'float':'right', 'height':'15%', 'width':'15%'}),
        
        html.Div("A genomic surveillance dashboard for the MonkeyPox virus."),
        html.Br(),
        html.Div(
            [
                html.Div(
                    dcc.Link(
                        html.A(f"{page['name']}"), href=page["relative_path"], style={'color':'black', 'display':'inline-block'}
                    )
                        #f"{page['name']}", href=page["relative_path"]
                )
                for page in dash.page_registry.values()
            ]
        ),
        html.Br(),
        html.Br(),
        dash.page_container,
        html.Hr(),
        html.Br(),
        # style={'height':'99999999px;', 'width':'100%', 'bottom':'0', 'left':'0', 'position':'absolute'}
        html.Footer([
            html.A("About MPXRadar", href="About", style={'color':'black', 'display':'inline-block'}),
            html.Div(children="Supported by:", style={'float':'right', "margin-right": "250px"}),
            html.Br(),
            html.A("Contact Us", href="Contact", style={'color':'black'}),
            html.Br(),
            html.A("Imprint", href="Home", style={'color':'black'}),
            html.Br(),
            html.A("App:", href="Tool", style={'color':'black'}),



            html.Img(src=r'assets/denbi_cloud_logo.png',alt='Img_RKI', style={'float':'right', 'height':'15%', 'width':'15%'}),
            html.Div(children="on the basis of a decision"),
            html.Div(children="by the German Bundestag"),
            html.Img(src=r'assets/Bundesministerium_für_Wirtschaft_und_Energie_Logo.svg.png',alt='Img_RKI', style={'float':'right', 'height':'15%', 'width':'15%'}),]),
    ]
)

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0")
