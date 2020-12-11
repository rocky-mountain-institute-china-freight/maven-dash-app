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

# Load data

APP_PATH = str(pathlib.Path(__file__).parent.resolve())

json_path = os.path.join(APP_PATH, os.path.join("data", "ev_vmt"))
with open(json_path) as geofile:
    geojson_layer = json.load(geofile)
    
df_ev_vmt = pd.read_pickle(
    os.path.join(APP_PATH, os.path.join("data", "ev_vmt.pkl"))
)
df_ev_vmt = gpd.GeoDataFrame(df_ev_vmt)

with open(os.path.join(APP_PATH, os.path.join("data", "la_geojson.txt"))) as json_file:
    geo_data = json.load(json_file)

def create_bins(color_scheme, df, value_to_map):
    bins = jenkspy.jenks_breaks(df[value_to_map], nb_class=(len(color_scheme)-1))
    bins = [round(i) for i in bins]
    return bins

def create_labels(bins):
    labels= labels=[i for i,b in enumerate(bins[1:])]
    return labels

def label_data_by_bin(bins, labels, df, value_to_map):
    df['bin']=pd.cut(df[value_to_map], bins=bins, include_lowest=True, labels=labels, duplicates='raise')  
    return df 

def create_hover_data(df):
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

def filter_json_by_bin(geojson, label, df):
    indxs = df.loc[df['bin']==label].index.to_list()
    list_of_feats = []
    for feat in geojson['features']:
        if feat['properties']['poly_id'] in indxs:
            list_of_feats.append(feat)
    #return geojson in formatted way
    return {'type': 'FeatureCollection','features':list_of_feats}

def get_logins(path):
    "retrieves valid username:password pairs from secret file"
    with open(path) as f:
        return json.load(f)

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
RATES = [15,25,50]
DEFAULT_OPACITY = 0.5
VALID_USERNAME_PASSWORD_PAIRS = get_logins(os.path.join(APP_PATH, os.path.join(".secret", "login_credentials.json")))
HOVER_DATA = create_hover_data(df_ev_vmt)

styles = {
    'pre': {
        'border': 'thin lightgrey solid',
        'overflowX': 'scroll'
    }
}
mapbox_style = "mapbox://styles/butlerbt/ckhma6w7n12ic19pghqpyanfq"
mapbox_access_token = "pk.eyJ1IjoiYnV0bGVyYnQiLCJhIjoiY2s2aDJqNzl2MDBqdDNqbWlzdWFqYjZnOCJ9.L4RJNdK2aqr6kHcHZxksXw"
px.set_mapbox_access_token(mapbox_access_token)
df_ev_vmt['geometry'] = df_ev_vmt['geometry'].simplify(.01)

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)

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
                        html.P(
                            id="'demo-text'",
                            children="Select the value to be mapped:",
                        ),
                        dcc.Dropdown(
                            id="map-dropdown",
                            options=[
                            # {'label': 'LA Neighborboods', 'value': 'OBJECTID'},
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
                            ],
                        ),
                    ],
                ),
                html.Div(
                className="row",
                    id='top-row',
                    children=[
                        # Formation bar plots
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
                        html.P(
                            id="'slider-text'",
                            children="Drag the slider to the EV Adoption Rate:",
                        ),
                        dcc.Slider(
                                id="rate-slider",
                                min=min(RATES),
                                max=max(RATES),
                                value=min(RATES),
                                marks={
                                str(rate): {
                                    "label": str(rate)+'%',
                                    "style": {"color": "#7fafdf"},
                                }
                                for rate in RATES
                                    }
                                ),
                            ],
                        ),
                html.Div(
                    id="lp-map-container",
                    children=[
                        html.H3('Optimized charger locations proposed based models from observed TNC data'),
                        html.P(
                        "Select the rate of adoption to visualize the proposed infrastructure",
                        id="lp-heatmap-title"
                        ),
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
 

@app.callback(
    Output("county-choropleth", "figure"),
    [Input("map-dropdown", "value")],
    [State("county-choropleth", "figure")],
)
def display_map(value, figure):
    # fig = px.choropleth_mapbox(df_ev_vmt[value],
    #                        geojson=df_ev_vmt.geometry,
    #                        locations=df_ev_vmt.index,
    #                        color=value,
    #                        center={"lat": 34.0522, "lon": -118.2437},
    #                        mapbox_style=mapbox_style,
    #                        zoom=8.5)
    BINS = create_bins(color_scheme=COlORSCALE, df = df_ev_vmt, value_to_map=value)
    labels = create_labels(bins=BINS)
    label_data_by_bin(bins=BINS, labels=labels, df = df_ev_vmt, value_to_map=value)
    cm = dict(zip(BINS, COlORSCALE))

    data = [
        dict(
            lat=df_ev_vmt["latitude_center"],
            lon=df_ev_vmt["longitude_center"],
            text=df_ev_vmt['hover'],
            type="scattermapbox",
            hoverinfo="text",
            marker=dict(size=5, color="white", opacity=.5),
        )
    ]
    if value == 'OBJECTID':
        annotations = [None]
    else:
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
    
        for i, bin in enumerate(reversed(BINS)):
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
    
    for label, bin in enumerate(BINS):
        geo_layer = dict(
            sourcetype="geojson",
            source=json.loads(df_ev_vmt.loc[df_ev_vmt['bin']==label]['geometry'].to_json()),
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
        Input("map-dropdown", "value")
    ],
)
def display_selected_data(selectedData, data_dropdown):
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
    tract_nums = [str(pt["text"].split(" ")[2]) for pt in pts]
    dff = df_ev_vmt[df_ev_vmt["OBJECTID"].isin(tract_nums)]

    title = data_dropdown
    counts_by_income = dff.groupby("med_income_cat")[data_dropdown].sum()
    fig = counts_by_income.iplot(
        kind="bar", y=data_dropdown, title=title, asFigure=True
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
    [Input("rate-slider", "value")],
    [State("lp-output-choropleth", "figure")],
)
def display_lp_map(value, figure):
    value = "pct"+str(value)+"_plugs"
    BINS = create_bins(color_scheme=COlORSCALE, df = df_ev_vmt, value_to_map=value)
    print(BINS[1:])
    labels = create_labels(bins=BINS[1:])
    label_data_by_bin(bins=BINS[1:], labels=labels, df = df_ev_vmt, value_to_map=value)
    cm = dict(zip(BINS, COlORSCALE))

    data = [
        dict(
            lat=df_ev_vmt["latitude_center"],
            lon=df_ev_vmt["longitude_center"],
            text=df_ev_vmt['hover'],
            type="scattermapbox",
            hoverinfo="text",
            marker=dict(size=5, color="white", opacity=.5),
        )
    ]
    if value == 'OBJECTID':
        annotations = [None]
    else:
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
    
        for i, bin in enumerate(reversed(BINS)):
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
    
    for label, bin in enumerate(BINS):
        geo_layer = dict(
            sourcetype="geojson",
            source=json.loads(df_ev_vmt.loc[df_ev_vmt['bin']==label]['geometry'].to_json()),
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
        Input("rate-slider", "value")
    ],
)
def display_selected_data(selectedData, slider):
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
    tract_nums = [str(pt["text"].split(" ")[2]) for pt in pts]
    dff = df_ev_vmt[df_ev_vmt["OBJECTID"].isin(tract_nums)]

    title = slider
    counts_by_income = dff.groupby("med_income_cat")[slider].sum()
    fig = counts_by_income.iplot(
        kind="bar", y=slider, title=title, asFigure=True
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

###uncomment if debugging locally:
if __name__ == "__main__":
    app.run_server(debug=True, host='0.0.0.0', port = 3002)

# if __name__ == '__main__':
#     app.run_server(debug=True)