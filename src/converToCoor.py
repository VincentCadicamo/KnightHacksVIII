import os

import numpy as np
import re
import json

ffr_path = os.path.join("data/final_flyable_routes.json")
with open(ffr_path) as file:
    data = json.load(file)

trips = data["flyable_trips"]
arr_Num_Count = len(trips)

all_trips = []
for trip in trips:
    coords = [[idx, lon, lat] for idx, lon, lat in trip["flyable_path_gps"]]
    all_trips.append(coords)

# Print to console
'''
for trip_idx, trip in enumerate(all_trips):
    print(f"\nTrip {trip_idx}:")
    for idx, lon, lat in trip:
        print(f" {idx}, {lon:.6f}, {lat:.6f}")


# Write to file
with open("trips_output.txt", "w") as f:
    for trip_idx, trip in enumerate(all_trips):
        f.write(f"Trip {trip_idx}:\n")
        for idx, lon, lat in trip:
            f.write(f"  {idx}, Lon: {lon:.6f}, Lat: {lat:.6f}\n")
        f.write("\n")
'''