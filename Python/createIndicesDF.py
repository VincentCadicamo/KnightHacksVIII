import numpy as np
from pathlib import Path
import sys, json
import pandas as pd
from converToCoor import all_trips

# set up file paths
project_root = Path(__file__).resolve().parent.parent
points_file_path = project_root / 'data' / 'points_lat_long.npy'
photo_indexes_file_path = project_root / 'data' / 'photo_indexes.npy'
asset_indexes_file_path = project_root/ 'data' / 'asset_indexes.npy'
waypoints_indexes_file_path = project_root / 'data' / 'waypoint_indexes.npy'

# load file for points
coords_array = np.load(points_file_path)
# get max index value for coordinate pairs
N = coords_array.shape[0]
# set up master_df to store coordinate info
i = 0
all_coord_values = coords_array.tolist()

#asset index value
VAL = 3544

asset_coords = [
    coord for i, coord in enumerate(all_coord_values) if i > VAL
]

# load file for slices
photo_index_slice = np.load(photo_indexes_file_path)
asset_index_slice = np.load(asset_indexes_file_path)
waypoints_index_slice = np.load(waypoints_indexes_file_path)

# Generate the complete list of required indices (inclusive of the last index)
all_photo_indices = np.arange(photo_index_slice[0], photo_index_slice[1] + 1)
all_asset_indices = np.arange(asset_index_slice[0], asset_index_slice[1] + 1)
all_waypoint_indices = np.arange(waypoints_index_slice[0], waypoints_index_slice[1] + 1)

# only includes indices within bounds
valid_photo_indices = all_photo_indices[all_photo_indices < N]
valid_asset_indices = all_asset_indices[all_asset_indices < N]
valid_waypoint_indices = all_waypoint_indices[all_waypoint_indices < N]

all_trip_dfs = []
for trip_idx, trip in enumerate(all_trips): 
    master_df = pd.DataFrame(trip, columns=['index','lon', 'lat'])
    all_trip_dfs.append(master_df)


all_photo_dfs = []
all_waypoint_dfs = []
for master_df in all_trip_dfs: 
    # Create a Boolean Series (a mask) that is True only for specific Location indices
    is_photo_location_mask = master_df['index'].isin(valid_photo_indices)
    is_waypoint_location_mask = master_df['index'].isin(valid_waypoint_indices)

    # Use .loc with the mask to set the 'type' column for those specific rows
    master_df.loc[is_photo_location_mask, 'type'] = 'photo'
    master_df.loc[is_waypoint_location_mask, 'type'] = 'waypoint'

    photo_df = master_df[master_df['type'] == 'photo'].copy()
    asset_df = master_df[master_df['type'] == 'asset'].copy()
    waypoint_df = master_df[master_df['type'] == 'waypoint'].copy()
    all_photo_dfs.append(photo_df)
    all_waypoint_dfs.append(waypoint_df)


# get all asset values wihin bounds
asset_indices_to_extract = valid_asset_indices
asset_lon_lat_data = coords_array[asset_indices_to_extract]

all_assets_df = pd.DataFrame(
    asset_lon_lat_data,
    columns=['lon', 'lat']
)

all_assets_df['index'] = asset_indices_to_extract