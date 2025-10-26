import numpy as np
import folium
import os

def visualize_routes():

    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        data_dir = os.path.join(root_dir, "data")
        output_dir = os.path.join(root_dir, "output")
    except NameError:
        print("Running in interactive mode. Using current working directory.")
        root_dir = os.getcwd()
        data_dir = os.path.join(root_dir, "data")
        output_dir = os.path.join(root_dir, "output")

    routes_file_path = os.path.join(data_dir, "routes.npy")
    locations_file_path = os.path.join(data_dir, "points_lat_long.npy")
    output_map_path = os.path.join(output_dir, "drone_map.html")

    print("Loading solved routes and location data...")

    try:
        all_routes_indices = np.load(routes_file_path, allow_pickle=True)
    except FileNotFoundError:
        print(f"Error: 'routes.npy' not found at '{routes_file_path}'.")
        return

    try:
        locations_array = np.load(locations_file_path)
    except FileNotFoundError:
        print(f"Error: 'points_lat_long.npy' not found at '{locations_file_path}'.")
        return

    all_routes_with_locations = []
    for i, route_indices in enumerate(all_routes_indices):
        route_locations = []
        for pole_index in route_indices:
            try:
                location_coords = locations_array[pole_index]

                flipped_coords = (location_coords[1], location_coords[0])
                route_locations.append(flipped_coords)
            except IndexError:
                print(f"Warning: Index {pole_index} in routes.npy is out of bounds!")

        all_routes_with_locations.append(route_locations)

    if len(locations_array) > 0:
        map_center = locations_array.mean(axis=0)
    else:
        map_center = [0, 0]

    m = folium.Map(location=(map_center[1], map_center[0]), zoom_start=14)

    poles_group = folium.FeatureGroup(name="All Poles").add_to(m)

    if len(locations_array) > 0:
        depot_coords = locations_array[0]
        folium.Marker(
            location=(depot_coords[1], depot_coords[0]),
            popup="Depot (Node 0)",
            icon=folium.Icon(color='green', icon='home', prefix='fa')
        ).add_to(poles_group)

    for i, coords in enumerate(locations_array[1:], start=1):
        folium.CircleMarker(
            location=(coords[1], coords[0]),
            radius=4,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.8,
            popup=f"Pole {i}"
        ).add_to(poles_group)

    routes_group = folium.FeatureGroup(name="Drone Routes").add_to(m)

    colors = ['red', 'blue', 'orange', 'purple', 'black', 'darkgreen', 'cyan']

    for i, route_coords in enumerate(all_routes_with_locations):
        if not route_coords:
            continue

        color = colors[i % len(colors)]

        folium.PolyLine(
            locations=route_coords,
            color=color,
            weight=3,
            opacity=0.9,
            popup=f"Drone {i+1} Route"
        ).add_to(routes_group)

    folium.LayerControl().add_to(m)

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    except OSError as e:
        print(f"Error: Could not create output directory {output_dir}. {e}")
        return

    m.save(output_map_path)


if __name__ == "__main__":
    visualize_routes()