#Author: Brent Butler 
#Contact: butlerbt.mg@gmail.com
#Date: 1/6/2021
# Purpose: Dash App displaying data and analysis from GM Maven Gig RMI project

import os
import pathlib
import re
import json
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_auth
import pandas as pd
import geopandas as gpd
from dash.dependencies import Input, Output, State
import cufflinks as cf
import jenkspy
import plotly.express as px
import json

# Initialize app
app = dash.Dash(
    __name__,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1.0"}
    ],
)
server = app.server

#Set app rooth path name dynamically so that it changes based on where it might be deployed
APP_PATH = str(pathlib.Path(__file__).parent.resolve())


#Define helper functions for use in dash clickbacks

def create_bins(color_scheme, df, value_to_map):
    """Creates income bins from data based on commonly used natural breaks algorithim

    Args:
        color_scheme (list): list of color values to map the bin values to. Usually defined as global variable COLORSCALE. 
        df (pd.dataframe): df with data to bin
        value_to_map (string): Name of a column of values that will be binned by income

    Returns:
        list: list of bin intervals 
    """
    bins = jenkspy.jenks_breaks(df[value_to_map], nb_class=(len(color_scheme)-1))
    bins = [round(i) for i in bins]
    return bins

def create_labels(bins):
    """Creates list of labels from bin values

    Args:
        bins (list): list of bin intervals

    Returns:
        list: list of labels for displaying in charts
    """
    labels= labels=[i for i,b in enumerate(bins[1:])]
    return labels

def label_data_by_bin(bins, labels, df, value_to_map):
    """Maps label values to data in dataframe so that data can then be filtered before being mapped/displayed

    Args:
        bins (list): list of income bin intervals
        labels (list): list of labels for dispalying in chart
        df (pd.DataFrame): df of data to display
        value_to_map (string): name of column to be mapped/displayed

    Returns:
        pd.DataFram: original df but with bin labels in column ['bin']
    """
    df['bin']=pd.cut(df[value_to_map], bins=bins, include_lowest=True, labels=labels, duplicates='raise')  
    return df 

def create_hover_data(df):
    """Creates data for mouse over hover functionality in map. 

    Args:
        df (pd.DataFrame): df of data to be displayed

    Returns:
        dict: dict object mapping data to specific lat long points on the map
    """
    data = [
        dict(
            lat=df["latitude_center"],
            lon=df["longitude_center"],
            text=df['hover'],
            type="scattermapbox",
            hoverinfo="text",
            marker=dict(size=5, color="white", opacity=.5),
        )
    ]
    return data

def load_data_by_jurisdiction(jurisdiction):
    """Loads in the data to be displayed in the dashboard

    Args:
        jurisdiction (string): the level of geographic parcels to be displayed. This is used to select which
        dataframe to load in from the /data/ directory.
        
    Returns:
        pd.DataFrame: DataFrame used in the visuals and graphs
    """
    #Create root path app dynamicallys so it will change based on where app is hosted
    try:
        df = pd.read_pickle(
        os.path.join(APP_PATH, os.path.join("data", f"dash_data_{jurisdiction}.pkl")
                        )
        )
        df = gpd.GeoDataFrame(df, crs="epsg:4326")
        return df
    except KeyError as ke:
        pass


def get_logins(path):
    "retrieves valid {username:password} pairs from secret file. Only to be used for development"
    with open(path) as f:
        return json.load(f)

#Global Variables 
COlORSCALE = [
    "#f2fffb",
    "#bbffeb",
    "#98ffe0",
    "#79ffd6",
    "#6df0c8",
    "#69e7c0",
    "#59dab2",
    "#45d0a5",
    "#31c194",
    "#2bb489",
    "#25a27b",
    "#1e906d",
    "#188463",
    "#157658",
    "#11684d",
    "#10523e",
]
ADOPTION_RATES = [15,25,50] #change this based on LP output scenarios that will be displayed
DEFAULT_OPACITY = 0.5
VALID_USERNAME_PASSWORD_PAIRS = get_logins(os.path.join(APP_PATH, os.path.join(".secret", "login_credentials.json")))

#set CSS style sheets
styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}

#mapbox variables
mapbox_style = "mapbox://styles/butlerbt/ckhma6w7n12ic19pghqpyanfq"
mapbox_access_token = "pk.eyJ1IjoiYnV0bGVyYnQiLCJhIjoiY2s2aDJqNzl2MDBqdDNqbWlzdWFqYjZnOCJ9.L4RJNdK2aqr6kHcHZxksXw"
px.set_mapbox_access_token(mapbox_access_token)

#login for use in development - to be removed when launched live
auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

#html layout of app
app.layout = html.Div(
    children=[
        html.Div(
            id="root",
            children=[
                html.Div(
                id="header",
                    children=[
                        html.Img(id="logo", src=app.get_asset_url("rmi-logo.svg")),
                        html.H4(children="Los Angeles EV TNC Modeling"),
                        ],
                    ),
                html.Div(
                    id="dropdown-container",
                    children=[
                        html.H3(children="Select the metric to be displayed:"),
                        dcc.Dropdown(
                            id="map-dropdown",
                            options=[
                            {'label': 'Observed ICE VMT', 'value': 'ice_vmt'},
                            {'label': 'Observed EV VMT', 'value': 'ev_vmt'},
                            {'label': 'Observed ICE Stops', 'value': 'ice_stop_count'},
                            {'label': 'Domicile Stops', 'value': 'Domicile Stops'},
                            {'label': 'Median Income', 'value': 'MHI2016'},
                            {'label': 'Population', 'value': 'Pop_16'},
                            {'label': 'Population Density', 'value': 'Pop_Den'},
                            {'label': 'Number of Level 2 Plugs', 'value': 'Level 2'},
                            {'label': 'Number of DCFC Plugs', 'value': 'DCFC Level 3'}
                            ],
                            value='ice_vmt'
                                ),
                        html.H3(children='Select the level of jurisdiction to display:'),
                        dcc.Dropdown(
                            id="jurisdiction-dropdown",
                            options=[
                                {'label': 'Neighborhood', 'value':'neighborhood'},
                                {'label':'City', 'value':'city'},
                                {'label':'Zip Code', 'value':'zip_code'},
                                {'label': 'Census Tracts', 'value':'census'},
                            ],
                            value='neighborhood'
                        ),
                        html.P(
                            id="demo-text",
                            children=""
                        )    
                            ],
                        ),
                    ],
                ),
                html.Div(
                className="row",
                    id='top-row',
                    children=[
                        html.Div(
                            id="map-container",
                            children=[
                                html.H3('Observed data from TNC company operating in Los Angeles'),
                                html.P(
                                "Los Angeles map",
                                id="heatmap-title"
                                ),
                                dcc.Graph(
                                id="county-choropleth",
                                figure=dict(
                                    layout=dict(
                                        mapbox=dict(
                                            layers=[],
                                            accesstoken=mapbox_access_token,
                                            style=mapbox_style,
                                            center=dict(
                                                lat=34.0522, lon=-118.2437
                                            ),
                                            pitch=0,
                                            zoom=7.5,
                                            ),
                                        autosize=True,
                                        ),
                                    ),
                                ),
                            ],
                        ),
                    html.Div(
                        id='right-column',
                        children=[
                            html.H3('Observed Metrics by Income Bracket'),
                            html.P(
                                "Los Angeles bar graphs",
                                id="chart-title"
                                ),
                            dcc.Graph(
                                id="selected-data-1",
                                figure=dict(
                                data=[dict(x=0, y=0)],
                                layout=dict(
                                paper_bgcolor="#F4F4F8",
                                plot_bgcolor="#F4F4F8",
                                autofill=True,
                                margin=dict(t=75, r=50, b=100, l=50),
                                        ),
                                    ),
                                ),  
                            ],
                        ),
                    ],
                ),
        html.Div(
            id="lower-app",
            children=[
                html.Div(
                    id="slider-container",
                    children=[
                        html.H3('Optimzed Fast Charging Infrastructure Needs'),
                        html.P(
                            id="'slider-text'",
                            children="Drag the slider to select the EV Adoption Rate:",
                        ),
                        dcc.Slider(
                                id="rate-slider",
                                min=min(ADOPTION_RATES),
                                max=max(ADOPTION_RATES),
                                value=min(ADOPTION_RATES),
                                marks={
                                str(rate): {
                                    "label": str(rate)+'%',
                                    "style": {"color": "#7fafdf"},
                                }
                                for rate in ADOPTION_RATES
                                    }
                                ),
                            ],
                        ),
                html.Div(
                    id="lp-map-container",
                    children=[
                        dcc.Graph(
                        id="lp-output-choropleth",
                        figure=dict(
                            layout=dict(
                                mapbox=dict(
                                    layers=[],
                                    accesstoken=mapbox_access_token,
                                    style=mapbox_style,
                                    center=dict(
                                        lat=34.0522, lon=-118.2437
                                        ),
                                    pitch=0,
                                    zoom=7.5,
                                    ),
                                    autosize=True,
                                    ),
                                ),
                            ),
                        ],
                    ),
                html.Div(
                id='low-right-column',
                children=[
                    html.H3('Optimzed charger station plugs by income bracket'),
                    html.P(
                        "Select the data in the above map using lasso or box selector tool",
                        id="lp-chart-title"
                        ),
                    dcc.Graph(
                        id="selected-data-2",
                        figure=dict(
                            data=[dict(x=0, y=0)],
                            layout=dict(
                            paper_bgcolor="#F4F4F8",
                            plot_bgcolor="#F4F4F8",
                            autofill=True,
                            margin=dict(t=75, r=50, b=100, l=50),
                                ),
                            ),
                        ),  
                    ],
                ),    
            ],
        ),
    ],
)

#Dash callbacks
@app.callback(
    Output("county-choropleth", "figure"),
    [
        Input("map-dropdown", "value"),
        Input("jurisdiction-dropdown", "value")
        ],
    [State("county-choropleth", "figure")],
)
def display_map(value, jurisdiction, figure):
    """display map based on selection of jurisdiction and metric/value to be displayed"""
    df = load_data_by_jurisdiction(jurisdiction)
    bins = create_bins(color_scheme=COlORSCALE, df = df, value_to_map=value)
    labels = create_labels(bins=bins)
    label_data_by_bin(bins=bins, labels=labels, df = df, value_to_map=value)
    cm = dict(zip(bins, COlORSCALE))
    data = create_hover_data(df)
    annotations = [
            dict(
                showarrow=False,
                align="right",
                text=f"<b>{value}</b>",
                font=dict(color="#1f2630"),
                x=0.95,
                y=0.95,
            )
        ]
    
    for i, bin in enumerate(reversed(bins)):
        color = cm[bin]
        annotations.append(
            dict(
                arrowcolor=color,
                text=bin,
                x=0.95,
                y=0.85 - (i / 20),
                ax=-60,
                ay=0,
                arrowwidth=5,
                arrowhead=0,
                font=dict(color="#1f2630"),
            )
        )

    if "layout" in figure:
        lat = figure["layout"]["mapbox"]["center"]["lat"]
        lon = figure["layout"]["mapbox"]["center"]["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]
    else:
        lat = 34.0522
        lon = -118.2437
        zoom = 6.5

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode="lasso",
    )
    
    for label, bin in enumerate(bins):
        geo_layer = dict(
            sourcetype="geojson",
            source=json.loads(df.loc[df['bin']==label]['geometry'].to_json()),
            type="fill",
            color=cm[bin],
            opacity=DEFAULT_OPACITY,
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    fig = dict(data=data, layout=layout)
    return fig

@app.callback(Output("heatmap-title", "children"), 
              [Input("map-dropdown", "value")])

def update_map_title(value):
    """ Updates title of map based on selected metric """
    if value == 'OBJECTID':
        return 'Los Angeles TNC Data'
    else:
        return "Los Angeles TNC Data: {0}".format(
            value
        )

@app.callback(
    Output("selected-data-1", "figure"),
    [
        Input("county-choropleth", "selectedData"),
        Input("map-dropdown", "value"),
        Input('jurisdiction-dropdown','value')
    ],
)

def display_selected_data(selectedData, data_dropdown, jurisdiction):
    """Produces bar charts from selected data in Map """
    df = load_data_by_jurisdiction(jurisdiction)
    if selectedData is None:
        return dict(
            data=[dict(x=0, y=0)],
            layout=dict(
                title="Click-drag on the map to select regions",
                paper_bgcolor="#1f2630",
                plot_bgcolor="#1f2630",
                font=dict(color="#2cfec1"),
                margin=dict(t=75, r=50, b=100, l=75),
            ),
        )
    pts = selectedData["points"]
    tract_nums = [pt.get('pointIndex') for pt in pts]
    filtered_df = df.iloc[tract_nums]

    counts_by_income = filtered_df.groupby("med_income_cat")[data_dropdown].sum()
    fig = counts_by_income.iplot(
        kind="bar", y=data_dropdown, title=data_dropdown, asFigure=True
    )
    fig_layout = fig["layout"]
    fig_data = fig["data"]

    fig_data[0]["text"] = [round(i) for i in counts_by_income.values.tolist()]
    fig_data[0]["marker"]["color"] = "#2cfec1"
    fig_data[0]["marker"]["opacity"] = 1
    fig_data[0]["marker"]["line"]["width"] = 0
    fig_data[0]["textposition"] = "outside"
    fig_layout["paper_bgcolor"] = "#1f2630"
    fig_layout["plot_bgcolor"] = "#1f2630"
    fig_layout["font"]["color"] = "#2cfec1"
    fig_layout["title"]["font"]["color"] = "#2cfec1"
    fig_layout["xaxis"]["tickfont"]["color"] = "#2cfec1"
    fig_layout["yaxis"]["tickfont"]["color"] = "#2cfec1"
    fig_layout["xaxis"]["gridcolor"] = "#5b5b5b"
    fig_layout["yaxis"]["gridcolor"] = "#5b5b5b"
    fig_layout["margin"]["t"] = 75
    fig_layout["margin"]["r"] = 50
    fig_layout["margin"]["b"] = 100
    fig_layout["margin"]["l"] = 50
    return fig


@app.callback(
    Output("lp-output-choropleth", "figure"),
    [
        Input("rate-slider", "value"),
        Input("jurisdiction-dropdown", "value")
        ],
    [State("lp-output-choropleth", "figure")],
)
def display_lp_map(value, jurisdiction, figure):
    """ display map of LP model outputs""" 
    df = load_data_by_jurisdiction(jurisdiction)
    value = "pct"+str(value)+"_plugs"
    bins = create_bins(color_scheme=COlORSCALE, df = df, value_to_map=value)
    labels = create_labels(bins=bins[1:])
    label_data_by_bin(bins=bins[1:], labels=labels, df = df, value_to_map=value)
    cm = dict(zip(bins, COlORSCALE))
    data = create_hover_data(df)
    annotations = [
            dict(
                showarrow=False,
                align="right",
                text=f"<b>{value}</b>",
                font=dict(color="#1f2630"),
                x=0.95,
                y=0.95,
            )
        ]
    
    for i, bin in enumerate(reversed(bins)):
        color = cm[bin]
        annotations.append(
            dict(
                arrowcolor=color,
                text=bin,
                x=0.95,
                y=0.85 - (i / 20),
                ax=-60,
                ay=0,
                arrowwidth=5,
                arrowhead=0,
                font=dict(color="#1f2630"),
            )
        )

    if "layout" in figure:
        lat = figure["layout"]["mapbox"]["center"]["lat"]
        lon = figure["layout"]["mapbox"]["center"]["lon"]
        zoom = figure["layout"]["mapbox"]["zoom"]
    else:
        lat = 34.0522
        lon = -118.2437
        zoom = 6.5

    layout = dict(
        mapbox=dict(
            layers=[],
            accesstoken=mapbox_access_token,
            style=mapbox_style,
            center=dict(lat=lat, lon=lon),
            zoom=zoom,
        ),
        hovermode="closest",
        margin=dict(r=0, l=0, t=0, b=0),
        annotations=annotations,
        dragmode="lasso",
    )
    
    for label, bin in enumerate(bins):
        geo_layer = dict(
            sourcetype="geojson",
            source=json.loads(df.loc[df['bin']==label]['geometry'].to_json()),
            type="fill",
            color=cm[bin],
            opacity=DEFAULT_OPACITY,
            fill=dict(outlinecolor="#afafaf"),
        )
        layout["mapbox"]["layers"].append(geo_layer)

    fig = dict(data=data, layout=layout)
    return fig

@app.callback(
    Output("selected-data-2", "figure"),
    [
        Input("lp-output-choropleth", "selectedData"),
        Input("rate-slider", "value"),
        Input('jurisdiction-dropdown','value')
    ],
)
def display_selected_data(selectedData, slider, jurisdiction):
    """ Creates bar charts from selected data from LP Output map""" 
    df = load_data_by_jurisdiction(jurisdiction)
    slider="pct"+str(slider)+"_plugs"
    if selectedData is None:
        return dict(
            data=[dict(x=0, y=0)],
            layout=dict(
                title="Click-drag on the map to select regions",
                paper_bgcolor="#1f2630",
                plot_bgcolor="#1f2630",
                font=dict(color="#2cfec1"),
                margin=dict(t=75, r=50, b=100, l=75),
            ),
        )
    pts = selectedData["points"]
    # tract_nums = [str(pt["text"].split(" ")[2]) for pt in pts]
    tract_nums = [pt.get('pointIndex') for pt in pts]
    filtered_df = df[df["OBJECTID"].isin(tract_nums)]

    counts_by_income = filtered_df.groupby("med_income_cat")[slider].sum()
    fig = counts_by_income.iplot(
        kind="bar", y=slider, title=slider, asFigure=True
    )
    fig_layout = fig["layout"]
    fig_data = fig["data"]

    fig_data[0]["text"] = [round(i) for i in counts_by_income.values.tolist()]
    fig_data[0]["marker"]["color"] = "#2cfec1"
    fig_data[0]["marker"]["opacity"] = 1
    fig_data[0]["marker"]["line"]["width"] = 0
    fig_data[0]["textposition"] = "outside"
    fig_layout["paper_bgcolor"] = "#1f2630"
    fig_layout["plot_bgcolor"] = "#1f2630"
    fig_layout["font"]["color"] = "#2cfec1"
    fig_layout["title"]["font"]["color"] = "#2cfec1"
    fig_layout["xaxis"]["tickfont"]["color"] = "#2cfec1"
    fig_layout["yaxis"]["tickfont"]["color"] = "#2cfec1"
    fig_layout["xaxis"]["gridcolor"] = "#5b5b5b"
    fig_layout["yaxis"]["gridcolor"] = "#5b5b5b"
    fig_layout["margin"]["t"] = 75
    fig_layout["margin"]["r"] = 50
    fig_layout["margin"]["b"] = 100
    fig_layout["margin"]["l"] = 50
    return fig

#uncomment if debugging locally:
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port = 3002)
    
#uncomment if deploying:
# if __name__ == '__main__':
#     app.run_server(debug=True)