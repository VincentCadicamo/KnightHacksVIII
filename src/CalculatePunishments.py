import numpy as np
import geopandas as gpd
from shapely.geometry import LineString
from shapely.wkt import loads as wkt_loads
import os
import multiprocessing
from functools import partial

# --- WORKER FUNCTIONS (FOR MULTIPROCESSING) ---

# Re-introduce Haversine for geographic coordinates
def haversine_distance(lon1, lat1, lon2, lat2):
    """
    Calculate the great-circle distance between two points
    on the earth (specified in decimal degrees)

    Returns:
        Distance in feet.
    """
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    # Radius of earth in feet (approx 20,902,231 ft)
    r = 20902231
    return c * r

def process_row(i, locations, allowed_polygon, res_zones, res_sindex, FORBIDDEN_PENALTY, RESIDENTIAL_PENALTY):
    """
    Calculates a single row of the smart matrix using Haversine
    and assuming consistent (lon, lat) order.
    """
    num_locations = len(locations)
    row = np.zeros(num_locations, dtype=np.int64)

    # point_i is assumed (lon_i, lat_i)
    lon_i, lat_i = locations[i]

    for j in range(num_locations):
        if i == j:
            continue

        # point_j is assumed (lon_j, lat_j)
        lon_j, lat_j = locations[j]

        # Use correct Haversine distance
        distance = haversine_distance(lon_i, lat_i, lon_j, lat_j)
        cost = distance

        # Create the path using the original (lon, lat) order
        path = LineString([(lon_i, lat_i), (lon_j, lat_j)])

        # Check hard constraint (allowed region) using the SAME order
        if not path.within(allowed_polygon):
            cost = FORBIDDEN_PENALTY
        else:
            # Check soft constraint (residential zones)
            if res_zones is not None:
                path_bounds = path.bounds
                possible_hits_idx = list(res_sindex.intersection(path_bounds))

                if possible_hits_idx:
                    possible_zones = res_zones.iloc[possible_hits_idx]
                    for zone in possible_zones.geometry:
                        if path.intersects(zone):
                            cost += RESIDENTIAL_PENALTY
                            break

        row[j] = int(cost)

    if i % 100 == 0:
        print(f"  ... processed row {i} / {num_locations}")

    return row

# --- MAIN SCRIPT ---

def build_smart_matrix():
    """
    Builds a cost matrix in parallel that includes spatial constraint penalties.
    """
    print("Starting to build 'smart' cost matrix...")
    print("Using Haversine distance for geographic coordinates.")

    # --- 1. DEFINE PATHS AND PENALTIES ---
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.dirname(script_dir)
        data_dir = os.path.join(root_dir, "data")
    except NameError:
        root_dir = os.getcwd()
        data_dir = os.path.join(root_dir, "data")

    locations_file = os.path.join(data_dir, "points_lat_long.npy")
    allowed_region_file = os.path.join(data_dir, "polygon_lon_lat.wkt")
    res_zones_file = os.path.join(data_dir, "residential_zones.geojson")
    output_matrix_file = os.path.join(data_dir, "smart_matrix.npy")

    FORBIDDEN_PENALTY = 999999999
    # Setting penalty back to a more reasonable value
    RESIDENTIAL_PENALTY = 10000

    # --- 2. LOAD ALL DATA ---
    print("Loading pole locations and zone files...")
    try:
        # Load locations (assumed lon, lat)
        locations = np.load(locations_file)
    except FileNotFoundError:
        print(f"Error: Could not find {locations_file}")
        return

    try:
        with open(allowed_region_file, 'r') as f:
            # Load WKT (assumed lon, lat order based on standard)
            allowed_polygon = wkt_loads(f.read())
        print("Successfully loaded WKT allowed region.")
    except Exception as e:
        print(f"Error loading WKT file '{allowed_region_file}': {e}")
        return

    res_zones = None
    res_sindex = None
    try:
        # Load GeoJSON (assumed lon, lat order)
        res_zones = gpd.read_file(res_zones_file)
        res_sindex = res_zones.sindex
        print(f"Successfully loaded {len(res_zones)} residential penalty zones.")
    except Exception as e:
        print(f"Warning: Could not load residential zones '{res_zones_file}'.")
        print("Continuing without residential penalties.")

    # --- 3. BUILD THE MATRIX IN PARALLEL ---
    num_locations = len(locations)
    print(f"Calculating penalties for {num_locations}x{num_locations} matrix...")
    print(f"Using {multiprocessing.cpu_count()} CPU cores.")

    task_function = partial(
        process_row,
        locations=locations,
        allowed_polygon=allowed_polygon,
        res_zones=res_zones,
        res_sindex=res_sindex,
        FORBIDDEN_PENALTY=FORBIDDEN_PENALTY,
        RESIDENTIAL_PENALTY=RESIDENTIAL_PENALTY
    )

    with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
        results = pool.map(task_function, range(num_locations))

    smart_cost_matrix = np.stack(results)

    # --- 4. SAVE THE NEW MATRIX ---
    try:
        np.save(output_matrix_file, smart_cost_matrix)
        print("\n--- 🚀 SUCCESS! ---")
        print(f"New 'smart_matrix.npy' saved to:")
        print(f"{os.path.abspath(output_matrix_file)}")
    except Exception as e:
        print(f"Error saving matrix: {e}")

if __name__ == "__main__":
    build_smart_matrix()