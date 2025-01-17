import dash
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate
import dash_core_components as dcc
import dash_html_components as html
import json
import pandas as pd
import plotly.graph_objs as go
import numpy as np

CENTER_LAT=32.7767
CENTER_LON=-96.7970

external_stylesheet = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_key = 'pk.eyJ1IjoiZ3lldG1hbiIsImEiOiJjanRhdDU1ejEwZHl3NDRsY3NuNDRhYXd1In0.uOqHLjY8vJEVndoGbugWWg'
app = dash.Dash(__name__, external_stylesheets=external_stylesheet)

# load data
df = pd.read_csv('./GISData/borehold_data.csv')
df['text'] = '$' + df['MEAN_ind_rate'].round(3).astype(str) + '/kWH'

#load geoJSON geometries for price data (zip codes)
with open('./gisData/zcta.geojson','r') as f:
    geoj = json.load(f)

userPoint = go.Scattermapbox(
    name='Selected Site',
    lat=[0],
    lon=[0],
    # replaced None object with 'none', confusing but that turns it off!  
    hoverinfo='none',
    mode='markers',
    marker=dict(
        size=13,
    ),
    showlegend=False,
    visible=False,

)

priceData = go.Choroplethmapbox(
    name='Industrial Electric Prices',
    geojson=geoj, 
    locations=df.ZCTA5CE10, 
    # featureidkey='ZCTA5CE10',
    z=df.MEAN_ind_rate,
    colorscale="Viridis", 
    colorbar=dict(
        title='Price $/kWH',
    ),
    marker_opacity=1, 
    marker_line_width=0,
    text=df.text,
    hoverinfo='text',
    visible=True,
    # TODO: add year to map GUI (year of data)
    )

data = [priceData,userPoint] # sets the order

layout = go.Layout(
    height=600,
    width=800,
    autosize=True,
    #hovermode='closest',
    #clickmode='text',
    title='Average Industrial Electric Rate by Zip Code, 2018',
    showlegend=True,
    legend_orientation='h',
    mapbox=dict(
            accesstoken=mapbox_key,
            zoom=5,
            center=dict(
                lat=CENTER_LAT,
                lon=CENTER_LON
            ),
    )
)

# placeholder for output text
markdownText = '''

'''

fig = go.Figure(dict(data=data, layout=layout))
app.title = 'Electric Rates'
app.layout = html.Div(children=[
    html.Div([
        html.Div([
            html.H3(children='Site Exploration and Selection'),
             dcc.Graph(
                id='map', figure=fig
            )], className='row'
        ),
        html.Div([
            html.Div(id='callback-div'),
            dcc.Markdown(children=markdownText)
            ], className='row'
        )

    ], className='row'),
    html.Div([
        html.Div(id='next-button'),
        dcc.Link(html.Button('Select Models'), href='http://127.0.0.1:8073/model-selection')
    ], className='row'
    )

])


@app.callback(
    Output(component_id='callback-div', component_property='children'),
    [Input(component_id='map', component_property='clickData')]
)
def output_site_attributes(clicks):
    # grab the attributes to show in the click data in the second div
    if clicks is None:
        print('empty click')
        raise PreventUpdate
    if 'points' not in set(clicks.keys()):
        raise PreventUpdate
    else:
        ptID = clicks['points'][0]['location']
        # TODO: add the vars to a dict as keys, then iterate to get values
        # convert formatting to function and return string for markdown. 

        # TODO: Show only mean. Figure out why the variance. 
        # Can we link directly to the database? 

        # TODO: add zip code to pop-up, and name, and state abbreviation

        # TODO: replace "Site Details" with description & data source (hyperlink)

        #maxIndRate = df.loc[df.ZCTA5CE10 == ptID]['MAX_ind_rate'].values[0]
        #minIndRate = df.loc[df.ZCTA5CE10 == ptID]['MIN_ind_rate'].values[0]
        avgIndRate = df.loc[df.ZCTA5CE10 == ptID]['MEAN_ind_rate'].values[0]

        #maxCommRate = df.loc[df.ZCTA5CE10 == ptID]['MAX_comm_rate'].values[0]
        #minCommRate = df.loc[df.ZCTA5CE10 == ptID]['MIN_comm_rate'].values[0]
        avgCommRate = df.loc[df.ZCTA5CE10 == ptID]['MEAN_comm_rate'].values[0]

        #maxResRate = df.loc[df.ZCTA5CE10 == ptID]['MAX_res_rate'].values[0]
        #minResRate = df.loc[df.ZCTA5CE10 == ptID]['MIN_res_rate'].values[0]
        avgResRate = df.loc[df.ZCTA5CE10 == ptID]['MEAN_res_rate'].values[0]

        mdText = "###### Site Details\n\n"
        #mdText += 'Minimum Industrial Rate: ${:0.4f}/kWH\n\n'.format(minIndRate)
        mdText += 'Average Industrial Rate: ${:0.4f}/kWH\n\n'.format(avgIndRate)
        #mdText += 'Maximum Industrial Rate: ${:0.4f}/kWH\n\n'.format(maxIndRate)

        #mdText += 'Minimum Commercial Rate: ${:0.4f}/kWH\n\n'.format(minCommRate)
        mdText += 'Average Commercial Rate: ${:0.4f}/kWH\n\n'.format(avgCommRate)
        #mdText += 'Maximum Commercial Rate: ${:0.4f}/kWH\n\n'.format(maxCommRate)

        #mdText += 'Minimum Residential Rate: ${:0.4f}/kWH\n\n'.format(minResRate)
        mdText += 'Average Residential Rate: ${:0.4f}/kWH\n\n'.format(avgResRate)
        #mdText += 'Maximum Residential Rate: ${:0.4f}/kWH\n\n'.format(maxResRate)

        return(dcc.Markdown(mdText))

if __name__ == '__main__':
    app.run_server(debug=True, port=8058)
    