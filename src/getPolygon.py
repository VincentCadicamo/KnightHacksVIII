from shapely import wkt, Point
from pathlib import Path
from shapely.geometry import Polygon, LineString
import geopandas as gpd
import plotly.express as px
import pandas as pd
import sys, json, numpy as np


project_root = Path(__file__).resolve().parent.parent
wkt_file_path = project_root / 'data' / 'polygon_lon_lat.wkt'
file = project_root / 'data' / 'points_lat_long.npy'

try:
    with open(wkt_file_path) as f:
        polygon_wkt_string = f.read()
except FileNotFoundError: 
    print(f"ERROR: Data file not found at {wkt_file_path}")

allowed_flight_zone = wkt.loads(polygon_wkt_string)
# TO-DO: import points after path generation from optimized algorithm
# TO-DO: check if points are .contains within flight zone
# put zone coordinates into geodataframe and set correct coordinate system
zone_gdf = gpd.GeoDataFrame(geometry=[allowed_flight_zone], crs="EPSG:4326")
# example long-lat coordinates, change to imported coordinates
# 2. Swap columns: [:, [1, 0]] means select all rows (:) 
#    and columns in the order: index 1 (Lon), then index 0 (Lat)
mission_points_coords = np.load(file).tolist()

# Create a LineString for the path
mission_path = LineString(mission_points_coords)

for coordinate in mission_points_coords:
    currentCoordinate = Point(coordinate)
    if(allowed_flight_zone).contains(currentCoordinate):
        print("coordinate in bounds")

if(allowed_flight_zone.contains(mission_path)): 
    print("mission path in bounds")

# Create a GeoDataFrame for the path
path_gdf = gpd.GeoDataFrame(geometry=[mission_path], crs="EPSG:4326")
# TO-DO: display points on network map with polygon as overlay on a map of the specified area

# 1. Define the Projected CRS (UTM Zone 17N)
UTM_CRS = "EPSG:32617" 

# 2. Create a temporary projected GeoDataFrame
# Use .to_crs() to re-project the polygon from Lon/Lat (4326) to Meters (32617)
zone_projected = zone_gdf.to_crs(UTM_CRS)

# 3. Calculate the accurate centroid on the projected data (in meters)
# The warning will disappear here because the units are now linear (meters)
center_projected = zone_projected.centroid

# 4. Convert the calculated centroid back to Lon/Lat (4326) for Plotly
# Use .to_crs() again to transform the calculated center point back to Lon/Lat degrees
center_lon_lat = center_projected.to_crs("EPSG:4326")

# 5. Use the correct Lon/Lat coordinates in your plot
center_lat = center_lon_lat.y.mean()
center_lon = center_lon_lat.x.mean()

# Use the GeoDataFrame directly with Plotly Express
# The 'geojson' parameter tells Plotly how to draw the shape.
fig = px.choropleth_mapbox(
    zone_gdf, 
    geojson=zone_gdf.geometry.__geo_interface__,
    locations=zone_gdf.index,
    # Set the color/opacity for the polygon fill
    color_discrete_sequence=['green'],
    opacity=1, # show allowed area
    
    # Map configuration
    center={"lat": center_lat, "lon": center_lon},
    mapbox_style="open-street-map", # Use a free, high-quality map tile style
    zoom=14, # adjust zoom
    title="Allowed Drone Flight Zone and Mission Path"
)

# Set the map tiles to cover the entire area without cutting off
fig.update_geos(fitbounds="locations", visible=False)

# Extract the Lon/Lat pairs for the path
lon_coords = path_gdf.geometry.iloc[0].xy[0].tolist()
lat_coords = path_gdf.geometry.iloc[0].xy[1].tolist()

fig.add_scattermapbox(
    lat=lat_coords,
    lon=lon_coords,
    mode='lines',
    line=dict(width=3, color='red'), # Style the line
    name='Mission Path'
)

# Create a DataFrame for the points to easily plot them with labels
points_df = pd.DataFrame({
    'lat': lat_coords,
    'lon': lon_coords,
    'label': ['Depot (Start)'] + [f'Waypoint {i}' for i in range(1, len(lon_coords) - 1)] + ['Depot (End)']
})

fig.add_scattermapbox(
    lat=points_df['lat'],
    lon=points_df['lon'],
    mode='markers+text',
    marker=dict(size=10, color='blue'), # Style the points
    text=points_df['label'],
    textposition='top right',
    name='Waypoints'
)

# Show the interactive figure
fig.show()