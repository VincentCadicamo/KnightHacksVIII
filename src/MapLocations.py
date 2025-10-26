import numpy as np
import os
import folium

def load_and_map_routes():
    """
    Loads the solved routes and maps their indices to (lat, lon) coordinates.
    """

    # --- 1. SET UP FILE PATHS ---
    # Assumes this script is in root/src/
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(root_dir, "data")

    routes_file_path = os.path.join(data_dir, "routes.npy")
    locations_file_path = os.path.join(data_dir, "points_lat_long.npy")

    # --- 2. LOAD THE DATA ---
    print("Loading solved routes and location data...")

    # Load the routes (list of lists of indices)
    try:
        all_routes_indices = np.load(routes_file_path, allow_pickle=True)
    except FileNotFoundError:
        print(f"Error: 'routes.npy' not found in '{data_dir}'.")
        print("Please run the 'VRP-rev1.py' script first.")
        return

    # Load the location "key" file (the Nx2 array of coordinates)
    try:
        locations_array = np.load(locations_file_path)
    except FileNotFoundError:
        print(f"Error: 'points_lat_long.npy' not found in '{data_dir}'.")
        print("This file is required to map indices to coordinates.")
        return

    print(f"Successfully loaded {len(all_routes_indices)} routes.")
    print(f"Successfully loaded {len(locations_array)} pole locations.\n")

    # --- 3. MAP INDICES TO LOCATIONS ---

    # This list will hold the final (lat, lon) paths for visualization
    all_routes_with_locations = []

    for i, route_indices in enumerate(all_routes_indices):
        print(f"--- Route for Drone {i} ---")
        print(f"Index Path: {route_indices}")

        route_locations = []
        for pole_index in route_indices:
            try:
                # Direct array lookup:
                # Get the [lat, lon] pair from the locations array
                location_coords = locations_array[pole_index]

                lat = location_coords[0]
                lon = location_coords[1]

                route_locations.append((lat, lon))

            except IndexError:
                print(f"  -> Error: Index {pole_index} is out of bounds for 'points_lat_long.npy'!")

        all_routes_with_locations.append(route_locations)

    # This final list is what you'll use for Folium visualization
    # It's a list of lists, where each inner list contains (lat, lon) tuples
    # e.g., [ [(28.6, -81.3), (28.7, -81.4)], [(28.5, -81.2), (28.6, -81.1)] ]
    print("All route coordinates extracted and ready for visualization.")

    # You can return this list to use it in another function
    # return all_routes_with_locations
    m = folium.Map(location=(26.78740530383156, -80.1151239956276))
    trail_coordinates = [all_routes_with_locations]
    m.save("index.html")


if __name__ == "__main__":
    load_and_map_routes()