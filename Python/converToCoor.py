import numpy as np
import re
import json




#
with open('data/final_flyable_routes.json') as file:
    data = json.load(file)
# 
trips = data["flyable_trips"]
arr_Num_Count = len(trips)

all_trips = []
for trip in trips:
    coords = [[lon, lat] for _, lon, lat in trip ["flyable_path_gps"]]
    all_trips.append(coords)


for trip_idx, trip in enumerate(all_trips):
    print(f"\nTrip {trip_idx}:")
    for lon, lat in trip:
        print(f" {lon:.6f}, {lat:.6f}")

with open("trips_output.txt", "w") as f:
    for trip_idx, trip in enumerate(all_trips):
        f.write(f"Trip {trip_idx}:\n")
        for lon, lat in trip:
            f.write(f"  Lon: {lon:.6f}, Lat: {lat:.6f}\n")
        f.write("\n")


