import os

import dash
from dash import html
from dash import dcc
import dash_bootstrap_components as dbc
import dash_mantine_components as dmc

import plotly.express as px
import pandas as pd


dash.register_page(__name__, path="/Tool")

######### added by Jorge ##########
## inspired by covradar/server.py ##
#
from data import load_all_sql_files, get_database_connection
#
# possible ToDo's:
#
#    pickle files
#    register_callbacks_report_latest 
#    register_dashapp (see covradar/frontend/app/__init__.py)
#
if 'MYSQL_DB' in os.environ:
    db_name = os.environ.get('MYSQL_DB')
    db_connection = get_database_connection(db_name)
    df_dict_mpox = load_all_sql_files(db_name)
else:
    df_dict_mpox = pd.read_csv("df_mpox['propertyView'].csv")
#
#### shaping the data for the map:
#### and experimentation !
## db = mpox_testdata@asusdebian ##
import numpy as np
mpox_testdata = df_dict_mpox['propertyView']
alpha = mpox_CONTRY_absolute_counts = mpox_testdata[mpox_testdata['property.name'] == 'COUNTRY']['value_text'].value_counts()
betha = pd.DataFrame(data=np.array([alpha.index, alpha.values]), index = ['COUNTRY', 'OCCURRENCES']).T
betha['OCCURRENCES'] = betha['OCCURRENCES'].astype(str).astype(int)
#
mpox_fig = px.scatter_geo(
    betha,
    locations='COUNTRY',
    locationmode='country names',
    #color='MUTATION',
    size='OCCURRENCES'#,
#    title="first sample on"+QUERY+"last sample on"+QUERY
)
mpox_fig_2 = px.choropleth(
    data_frame=betha,
    locations='COUNTRY',
    locationmode='country names',
    color='OCCURRENCES',
    color_continuous_scale='sunsetdark', # brwnyl burg burgyl darkmint jet oranges reds sunsetdark turbo ylorbr matter balance
    center=None#,
#    center=dict(lat=51.5, lon=10.5), 
#    hover_name=None, hover_data=None, custom_data=None,
#    animation_frame=None, animation_group=None,
#    category_orders=None, labels=None, color_discrete_sequence=None, color_discrete_map=None,
#    range_color=None, color_continuous_midpoint=None,projection=None, scope=None, 
#    fitbounds=None, basemap_visible=None, title=None, template=None, width=None, height=None
)
import plotly.graph_objects as go
mpox_fig_3 = go.Figure(
    data = go.Choropleth(
        locations = betha['COUNTRY'],
        z = betha['OCCURRENCES'],
        locationmode = 'country names',
        colorscale = 'Reds',
        colorbar_title = 'OCCURRENCES'
))
mpox_fig_2.update_layout(
    geo=dict(scope='world'),
#    autosize=False,
    margin=dict(l=30,r=0,b=0,t=30)#,
)
##################################


###mutations and countries####
new_data = pd.read_csv(os.getcwd()+'/pages/out.csv') # changed to relative by Jorge

new_fig = px.scatter_geo(
    new_data,
    locations='COUNTRY',
    locationmode='country names',
    color='MUTATION',
    size='OCCURENCES'
)
##############################

####example data for example map######
Sample_data = px.data.carshare()

fig = px.scatter_mapbox(
    Sample_data,
    lat="centroid_lat",
    lon="centroid_lon",
    color="peak_hour", size="car_hours",
    color_continuous_scale=px.colors.cyclical.IceFire,
    size_max=15,
    zoom=10,
    mapbox_style="carto-positron"
)
#######################################

####example data for example 2map######
url = "https://raw.githubusercontent.com/hflabs/city/master/city.csv"
geodata = pd.read_csv(url)

fig_ = px.scatter_mapbox(
    geodata,
    lat="geo_lat",
    lon="geo_lon",
    size="population",
    color_continuous_scale=px.colors.cyclical.IceFire,
    size_max=15,
    zoom=10,
    mapbox_style="carto-positron"
)
#######################################


card = dbc.Card(
    dbc.CardBody(
        [
            html.Div(
                [
                    html.Div(
                        [
                            "direct MPXSonar query: ",
                            html.Br(),
                            dcc.Input(
                                id="my-input", type="text", size="100"
                            ),
                            html.Button('Run direct MPXSonar query', id='btn-1', n_clicks=0),
                        ]
                    )
                ]
            )
        ]
    ),
    style={"width": "18rem"},
)



layout = html.Div(
    [
        #check box with references
        html.Div(
            style={'width':'10%', 'height':'100%','float':'left'},
            children=[
                dcc.Checklist(
                    className ='checkbox_1',
                    id='references-list',
                    options=[
                        {'label': 'some-ref-gen', 'value': 'I1ST2'},
                        {'label': 'some-ref-gen', 'value': 'I2ST2'},
                        {'label': 'some-ref-gen', 'value': 'I3ST2'},
                        {'label': 'ssome-ref-gen', 'value': 'I4ST2'},
                    ],
                    labelStyle={'display': 'block'}
            )
        ]
    ),

        #checkbox with mutations
        html.Div(
            style={'width':'10%', 'height':'100%','float':'left'},
            children=[
                dcc.Checklist(
                    className ='checkbox_1',
                    id='mutation-list',
                    options=[
                        {'label': 'some mutation', 'value': 'I1ST2'},
                        {'label': 'some mutation', 'value': 'I2ST2'},
                        {'label': 'some mutation', 'value': 'I3ST2'},
                        {'label': 'some mutation', 'value': 'I4ST2'},
                    ],
                    labelStyle={'display': 'block'}
            )
        ]
    ),

        html.Div(
            style={'width':'15%', 'height':'190%','float':'left'},
            children=[
                dcc.Checklist(
                    className ='checkbox_1',
                    id='vizual-method-list',
                    options=[
                            {'label': 'Frequencies', 'value': 'freq'},
                            {'label': 'Increasing Trend', 'value': 'trend-inc'},
                            {'label': 'Decreasing Trend', 'value': 'trend-dec'},
                            {'label': 'Constant Trend', 'value': 'trend-const'}
                    ],
                    value=['I1MT'],
                    labelStyle={'display': 'block'}
                )
            ]
        ),
        html.Br(style={'line-height': '10'}),
        card,
        html.Br(style={'line-height': '10'}),
        html.Div(
            [
                html.Br(),
                html.H1("Here is a map with static mpox_testdata"),
                dcc.Graph(figure=mpox_fig_2),
                html.Br(),
                html.Div(
                    [
                        html.Button('Download CSV', id='csv-download'),
                        dcc.Download(id='df-download')
                    ]
                )
            ]
        )
    ]
)


