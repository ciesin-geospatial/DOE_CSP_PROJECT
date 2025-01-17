import app_config
import json
import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import pandas as pd
import helpers
import pointLocationLookup

from dash.dependencies import ALL, Input, Output, State, MATCH
from dash.exceptions import PreventUpdate
from pathlib import Path

gis_data = app_config.gis_data_path
# Div for legend
# Site Selection

# TODO:
# add link (lines) and symbols for closest features
# add legend(s)
# 2. use a map-config file to load data, file locations, etc. 
# 4. transfer & adapt code to write out parameters as json
# 5. style to be consistent with menu interface

# Mapbox setup
mapbox_url = "https://api.mapbox.com/styles/v1/{id}/tiles/{{z}}/{{x}}/{{y}}{{r}}?access_token={access_token}"
# public mapbox token
mapbox_token = 'pk.eyJ1IjoiZ3lldG1hbiIsImEiOiJjanRhdDU1ejEwZHl3NDRsY3NuNDRhYXd1In0.uOqHLjY8vJEVndoGbugWWg'

# Dictionary to hold map theme labels and ID values
# add any new themes here to make them appear in the 
# list of radio buttons. note: first item is the 
# default for when map loads, change order to update. 
mapbox_ids = {
    'Satellite': 'mapbox/satellite-streets-v9', 
    'Topographic': 'mapbox/outdoors-v9',
    # 'Regulatory':'gyetman/ck7avopr400px1ilc7j49bi6j', # duplicate entry
}

MAP_ID = "map-id"
BASE_LAYER_ID = "base-layer-id"
BASE_LAYER_DROPDOWN_ID = "base-layer-drop-down-id"
SITE_DETAILS = "site-details"
USER_POINT = 'user_point'

def get_style(feature):
    return dict()
def get_d_style(feature):
    return dict(fillColor='orange', weight=2, opacity=1, color='white')

def get_info(feature=None):
    header = [html.H4("Feature Details")]
    if feature:
        if 'Technology' in list(feature[0]["properties"].keys()):
            units = 'm3/day'
        else:
            units = 'MW'
        return header + [html.B(feature[0]["properties"]["name"]), html.Br(),
            f"{float(feature[0]['properties']['capacity_mw']):,.1f} Capacity {units}"]
    else:
        return header + ["Hover over a feature"]

# load power plants JSON
power_plants = dl.GeoJSON(
    url='/assets/power_plants.geojson',
    #id='geojson_power',
    id = {'type':'json_theme','index':'geojson_power'},
    cluster=True,
    zoomToBoundsOnClick=True,
    superClusterOptions={"radius": 75},
    hoverStyle=dict(weight=5, color='#666', dashArray=''),
)

# load Desal plants
desal = dl.GeoJSON(
    url='/assets/global_desal_plants.geojson',
    id = {'type':'json_theme','index':'geojson_desal'},
    cluster=True,
    zoomToBoundsOnClick=True,
    superClusterOptions={'radius': 75},
    hoverStyle=dict(weight=5, color='#666', dashArray=''),
)

# load canals json
canals = dl.GeoJSON(
    url='/assets/canals.geojson', 
    id='geojson_canals', 
    #defaultstyle=dict(fillColor='blue', weight=2, opacity=1, color='blue'),
)

# regulatory layer from Mapbox
regulatory = dl.TileLayer(url=mapbox_url.format(id = 'gyetman/ckbgyarss0sm41imvpcyl09fp', access_token=mapbox_token))

# placeholder for mouseover data
info = html.Div(children='Hover over a Feature',
                className="mapinfo",
                style={"position": "absolute", "top": "10px", "right": "10px", "zIndex": "1000"},
                id="info")

map_navbar = dbc.NavbarSimple(
    children=[dbc.NavItem(dbc.NavLink("Site Selection"), href='/quick-analysis'),
              dbc.NavItem(dbc.NavLink("Quick Analysis", active = True))],
    brand='Site Selection',
    color='primary',
    dark=True,
    sticky='top',
    style={'margin-bottom':20}
)

legend = html.Img(
    id='legend',
    src='assets/legend_update2.png'
)

radios = dbc.FormGroup([
    dbc.RadioItems(
        id='theme-dropdown',
        options=[{'label':'Canals', 'value':'canals'},
                    {'label':'Power Plants', 'value':'pplants'},
                    {'label':'Desalination Plants', 'value':'desal'},
                    {'label': 'Regulatory', 'value':'regulatory'}],
        labelStyle={'display': 'inline-block'},
        value='canals',
        inline=True
    ),
    dbc.RadioItems(
        id=BASE_LAYER_DROPDOWN_ID,
        options = [
            {'label': name, 'value': mapbox_url.format(id = url, access_token=mapbox_token)}
            for name,url in mapbox_ids.items()
        ],
        labelStyle={'display': 'inline-block'},
        # use the first item as the default
        value=mapbox_url.format(id=next(iter(mapbox_ids.values())), access_token=mapbox_token),
        inline=True
    ),
],row=True)

def render_map():
    return [
        map_navbar,
        dbc.Row([
            dbc.Col([
                site_selection_map,
                dbc.Row([
                    dbc.Col(radios, width=7),
                    dbc.Col(legend)
                ]),
                html.Div(id='next-button'),
            ],width=8),
            dbc.Col([
                html.H3('Quick analysis:', className='text-success'),
                html.Div(id=SITE_DETAILS)
            ],width=3)
        ],style={'padding':20})
    ]


theme_ids = {
    'canals': html.Div([canals]),
    'pplants': html.Div([power_plants, info]),
    'desal': html.Div([desal, info]),
    'regulatory': regulatory
}

def register_map(app):
    @app.callback(Output(BASE_LAYER_ID, "url"),
                [Input(BASE_LAYER_DROPDOWN_ID, "value")])
    def set_baselayer(url):
        return url

    @app.callback(Output('theme-layer','children'),
                 [Input('theme-dropdown', 'value')])
    def set_theme_layer(theme):
        return theme_ids[theme]

    @app.callback(Output(USER_POINT, 'position'),
                  [Input(MAP_ID, 'click_lat_lng')])
    def click_coord(coords):
    # '''
    # Callback for updating the map after a user click 
    # TODO: in addition to returning 0,0, update icon
    # to be "invisible".
    # '''
        if not coords:
            return [0,0]
        else:
            return coords

    @app.callback([Output(SITE_DETAILS, 'children'),Output("closest-facilities", 'children')],
                  [Input(MAP_ID, 'click_lat_lng')],prevent_initial_call=True)

    def get_point_info(lat_lng):
        ''' callback to update the site information based on the user selected point'''
        if lat_lng is None:
            return('Click on the Map to see site details.'), [0,0]
        else:
            markdown = dcc.Markdown(str(pointLocationLookup.lookupLocation(lat_lng)))
            closest = pointLocationLookup.getClosestInfrastructure(lat_lng)
            if not closest:
                return markdown, [None,None,None,None]
            elif 'plant' in closest.keys():
                desal = dl.Polyline(positions=[lat_lng,closest['desal']], color='#FF0000', children=[dl.Tooltip("Desal Plant")])          
                plant = dl.Polyline(positions=[lat_lng,closest['plant']], color='#ffa500', children=[dl.Tooltip("Power Plant")])
                canal = dl.Polyline(positions=[lat_lng,closest['canal']], color='#add8e6', children=[dl.Tooltip("Canal/Piped Water")])
                water = dl.Polyline(positions=[lat_lng,closest['water']], color='#000000', children=[dl.Tooltip("Water Network Proxy")])
                return markdown, [desal,plant,canal,water]
            elif 'desal' in closest.keys():
                desal = dl.Polyline(positions=[lat_lng,closest['desal']], color='#FF0000', children=[dl.Tooltip("Desal Plant")])
                return markdown, [desal,None,None,None]
            else:
                return markdown, [None,None,None,None]

            
    @app.callback(
        Output(component_id='next-button',component_property='children'),
        [Input(component_id=SITE_DETAILS,component_property='children')],
        [State(MAP_ID,'children')],
        prevent_initial_call=True
    )
    def enableButton(site,site_properties):
        ''' output to enable next button after a site has been selected '''
        if site == 'Click on the Map to see site details.':
            raise PreventUpdate
        else:
            return(
                html.Div([
                    html.Div(id='button-div'),
                    dbc.Button('Select Models', color="primary",
                            href='http://127.0.0.1:8077/model-selection'), 
                ], className='row',
                ) 
            )


    @app.callback(Output('info', 'children'),
            [Input({'type':'json_theme', 'index': ALL}, 'hover_feature')]
        )
    def info_hover(feature):
        ''' callback for feature hover '''
        return(get_info(feature))


external_stylesheets = [dbc.themes.FLATLY]
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.title = 'Site Selection (Beta)'
app.layout = html.Div(
    render_map()
)
register_map(app)

if __name__ == '__main__':
    app.run_server(debug=True, port=8150)


