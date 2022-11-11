import argparse

from dash import Dash
from dash import dcc
from dash import html
from dash import Input
from dash import Output
from dash import State
import dash_table
from dash import callback_context
import folium
import pandas as pd
from covsonar.app_controller import get_freq_mutation
from covsonar.app_controller import match_controller
from covsonar.app_controller import sonarBasics
from covsonar.sonar import parse_args
import base64








import io
import folium.plugins

boston = pd.read_csv("https://gitlab.com/dacs-hpi/covradar/-/raw/master/backend/data/location_coordinates.csv")
boston["Employees"] = [500]*len(boston)
boston = boston.head()

map = folium.Map([boston.lon.mean(), boston.lat.mean(), ], zoom_start=12)

incidents2 = folium.plugins.MarkerCluster().add_to(map)

for latitude, longitude, employees in zip(boston.lat, boston.lon, boston.Employees):
    print(latitude, longitude, employees)
    folium.vector_layers.CircleMarker(
        location=[latitude, longitude],
        tooltip=str(employees),
        radius=employees/10,
        color='#3186cc',
        fill=True,
        fill_color='#3186cc'
    ).add_to(incidents2)

map.add_child(incidents2)
map.save('map.html')








custom_db = "https://admin:password@localhost:3306/mpx"

DF = pd.DataFrame()

'''
city_coordinates_list = [ 52.4, 13.06 ]
map=folium.Map(location=city_coordinates_list)
map.save('map.html')

image_filename = 'assets/monkey.jpg' # replace with your own image
encoded_image = base64.b64encode(open(image_filename, 'rb').read())
'''

app = Dash(__name__)

app.layout = html.Div(
    children=[
        html.H2("Welcome to MPXsonar!"),
        html.P("This is just a test version of our web-part, but you can try it right now! Just DO it!"),
        html.Br(),
        html.Br(),
        html.P("Use this buttons for custom comands"),
        html.Button('Count all mutations', id='btn-1', n_clicks=0),
        html.Button('make a match', id='btn-2', n_clicks=0),
        html.Button('mutations-labs', id='btn-3', n_clicks=0),
        html.Div(id='container'),
        html.Label("Output:"),
        html.Div(id="my-output", children=""),
        html.Div(id="my-output1", children=""),
        html.Div(
            [
                dash_table.DataTable(
                    id="my-output-df",
                    page_current=0,
                    page_size=10,
                    style_table={
                        'maxHeight': '50ex',
                        'overfrlowY': 'scroll',
                        'width': '40%',
                        'minWidth': '40%'
                    }
                ),
            ]
        ),
        html.Div(
            children=[html.H1('map.html'),
            html.Iframe(id='map', srcDoc = open("map.html", 'r').read(), width="40%", height="300")],
            style={'padding': 10, 'flex': 1}),
        #html.Img(src=image_filename),
        html.Div(
            [
                html.Button('Download CSV', id='csv-download'),
                dcc.Download(id='df-download')
            ]
        )
    ]
)



@app.callback(
    Output(component_id="my-output", component_property="children"),
    Output(component_id="my-output-df", component_property="data"),
    Output(component_id="my-output-df", component_property="columns"),
    [
        Input('btn-1', 'n_clicks'),
        Input('btn-2', 'n_clicks'),
        Input('btn-3', 'n_clicks'),
    ],
)


def func(*args):
    trigger = callback_context.triggered[0]
    clicked = trigger["prop_id"].split(".")[0]

    data = None
    columns = None
    output = None

    if clicked == 'btn-1':
        cmd_args = parse_args("mut_counters --db https://admin:password@localhost:3306/mpx".split())
        df = get_freq_mutation(cmd_args)
        columns = [{"name": col, "id": col} for col in df.columns]
        global DF
        DF = df.copy()
        data = df.to_dict(orient="records")
        output = "hahaha"
    elif clicked == 'btn-2':
        cmd_args = parse_args("match --count --db https://admin:password@localhost:3306/mpx".split())
        _tmp_output = match_controller(cmd_args)
        if type(_tmp_output) == int:
            output = _tmp_output
        else:
            df = _tmp_output
            columns = [{"name": col, "id": col} for col in df.columns]
            data = df.to_dict(orient="records")
    elif clicked == 'btn-3':
        pass


    return output, data, columns



@app.callback(
    Output('df-download', 'data'),
    Input('csv-download', 'n_clicks'),
)
def func(n_clicks):
    trigger = callback_context.triggered[0]
    clicked = trigger["prop_id"].split(".")[0]

    if clicked == 'csv-download':
        return dcc.send_data_frame(DF.to_csv, "mycsv.csv")



if __name__ == "__main__":
    app.run_server(debug=True, host="127.0.0.1")
