import numpy as np
from pathlib import Path
import sys, json
import pandas as pd
from converToCoor import coords

project_root = Path(__file__).resolve().parent.parent
points_file_path = project_root / 'data' / 'points_lat_long.npy'
photo_indexes_file_path = project_root / 'data' / 'photo_indexes.npy'
asset_indexes_file_path = project_root/ 'data' / 'asset_indexes.npy'
waypoints_indexes_file_path = project_root / 'data' / 'waypoint_indexes.npy'

coords_array = np.load(points_file_path)
N = coords_array.shape[0]
master_df = pd.DataFrame(coords, columns=['lon', 'lat'])

master_df['index'] = master_df.index
photo_index_slice = np.load(photo_indexes_file_path)
asset_index_slice = np.load(asset_indexes_file_path)
waypoints_index_slice = np.load(waypoints_indexes_file_path)

# Extract the values
first_photo_index = photo_index_slice[0]
last_photo_index = photo_index_slice[1]

# Generate the complete list of required indices (inclusive of the last index)
all_photo_indices = np.arange(photo_index_slice[0], photo_index_slice[1] + 1)
all_asset_indices = np.arange(asset_index_slice[0], asset_index_slice[1] + 1)
all_waypoint_indices = np.arange(waypoints_index_slice[0], waypoints_index_slice[1] + 1)

# only includes indices within bounds
valid_photo_indices = all_photo_indices[all_photo_indices < N]
valid_asset_indices = all_asset_indices[all_asset_indices < N]
valid_waypoint_indices = all_waypoint_indices[all_waypoint_indices < N]

# Create a Boolean Series (a mask) that is True only for specific Location indices
is_photo_location_mask = master_df['index'].isin(valid_photo_indices)
is_asset_location_mask = master_df['index'].isin(valid_asset_indices)
is_waypoint_location_mask = master_df['index'].isin(valid_waypoint_indices)

# Use .loc with the mask to set the 'type' column for those specific rows
master_df.loc[is_photo_location_mask, 'type'] = 'photo'
master_df.loc[is_asset_location_mask, 'type'] = 'asset'
master_df.loc[is_waypoint_location_mask, 'type'] = 'waypoint'

photo_df = master_df[master_df['type'] == 'photo'].copy()
asset_df = master_df[master_df['type'] == 'asset'].copy()
waypoint_df = master_df[master_df['type'] == 'waypoint'].copy()