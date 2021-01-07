utils.py

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

def load_data_by_jurisdiction(jurisdiction):
    try:
        df = pd.read_pickle(
        os.path.join(APP_PATH, os.path.join("data", f"dash_data_{jurisdiction}.pkl")
                        )
        )
        df = gpd.GeoDataFrame(df, crs="epsg:4326")
        return df
    except KeyError as ke:
        pass

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