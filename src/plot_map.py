from shapely import wkt, Point
from pathlib import Path
from shapely.geometry import Polygon, LineString
import geopandas as gpd
import plotly.express as px
import pandas as pd
import sys, json, numpy as np

try:
    from createIndicesDF import all_trip_dfs, all_photo_dfs, all_waypoint_dfs, all_assets_df, asset_coords
except ImportError:
    print("Error: Could not import 'createIndicesDF'.")
    print("Make sure 'createIndicesDF.py' is in the same directory as this script (src/).")
    sys.exit(1)


import dash
from dash import dcc
from dash import html

project_root = Path(__file__).resolve().parent.parent
wkt_file_path = project_root / 'data' / 'polygon_lon_lat.wkt'
points_file_path = project_root / 'data' / 'points_lat_long.npy'
photo_indexes_file_path = project_root / 'data' / 'photo_indexes.npy'

try:
    with open(wkt_file_path) as f:
        polygon_wkt_string = f.read()
except FileNotFoundError:
    print(f"ERROR: Data file not found at {wkt_file_path}")
    sys.exit(1)
allowed_flight_zone = wkt.loads(polygon_wkt_string)

zone_gdf = gpd.GeoDataFrame(geometry=[allowed_flight_zone], crs="EPSG:4326")

UTM_CRS = "EPSG:32617"

zone_projected = zone_gdf.to_crs(UTM_CRS)

center_projected = zone_projected.centroid

center_lon_lat = center_projected.to_crs("EPSG:4326")

center_lat = center_lon_lat.y.mean()
center_lon = center_lon_lat.x.mean()

fig = px.choropleth_mapbox(
    zone_gdf,
    geojson=zone_gdf.geometry.__geo_interface__,
    locations=zone_gdf.index,

    color_discrete_sequence=['green'],
    opacity=1,

    center={"lat": center_lat, "lon": center_lon},
    mapbox_style="open-street-map",
    zoom=14,
    title="Allowed Drone Flight Zone and Mission Path"
)

fig.update_traces(name='Allowed Flight Zone', selector=dict(type='choroplethmapbox'))

fig.update_geos(fitbounds="locations", visible=False)
colors = ['blue', 'red', 'green', 'yellow', 'pink', 'purple', 'orange', 'magenta', 'gold', 'black']
i = 0

for master_df in all_trip_dfs:
    mission_points_coords = master_df[['lon', 'lat']].values.tolist()

    mission_path = LineString(mission_points_coords)

    path_gdf = gpd.GeoDataFrame(geometry=[mission_path], crs="EPSG:4326")

    lon_coords = path_gdf.geometry.iloc[0].xy[0].tolist()
    lat_coords = path_gdf.geometry.iloc[0].xy[1].tolist()

    fig.add_scattermapbox(
        lat=lat_coords,
        lon=lon_coords,
        mode='lines',
        line=dict(width=3, color=colors[i % 10]),
        name=f'Mission Path {i + 1}'
    )
    i += 1

all_photos_combined_df = pd.concat(all_photo_dfs, ignore_index=True)
fig.add_scattermapbox(
    lat=all_photos_combined_df['lat'],
    lon=all_photos_combined_df['lon'],
    mode='markers',
    marker={
        'size': 8,
        'color': 'pink',
        'symbol': 'circle'
    },
    name='Photo'
)

fig.add_scattermapbox(
    lat=all_assets_df['lat'],
    lon=all_assets_df['lon'],
    mode='markers',
    marker={
        'size': 8,
        'color': 'blue',
        'symbol': 'circle'
    },
    name='Asset'
)

all_waypoints_combined_df = pd.concat(all_waypoint_dfs, ignore_index=True)
fig.add_scattermapbox(
    lat=all_waypoints_combined_df['lat'],
    lon=all_waypoints_combined_df['lon'],
    mode='markers',
    marker={
        'size': 8,
        'color': 'yellow',
        'symbol': 'circle'
    },
    name='Waypoint'
)

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1(children='Drone Mission Visualization', style={'textAlign': 'center'}),

    dcc.Graph(
        id='drone-map-graph',
        figure=fig,
        style={'height': '80vh'}
    )
])

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)