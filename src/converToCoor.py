import numpy as np
import re
import json


#open file
with open('data/final_flyable_routes.json') as file:
    data = json.load(file)

# storing data into trips
trips = data["flyable_trips"]
arr_Num_Count = len(trips)

all_trips = []
for trip in trips:
    # storing index, lon, lat
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