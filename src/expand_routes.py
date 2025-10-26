"""
Expands the VRP solver's route plan into a full, flyable GPS path.

This script loads the 'routes.npy' (from the VRP-rev2 solver) and
uses 'predecessors.npy' and 'points_lat_long.npy' to generate
the final, high-resolution flight paths.
"""

import os
import json
import numpy as np

# Get the directory of the current script (src)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the base directory (one level up)
base_dir = os.path.dirname(script_dir)
# Define the data directory path
data_dir = os.path.join(base_dir, "data")


def load_files():
    """Loads all necessary files from the data directory."""
    print("Loading route plan and .npy files...")

    # --- MODIFICATION ---
    # Changed from 'route_plan.json' to 'routes.npy'
    plan_path = os.path.join(data_dir, "routes.npy")
    preds_path = os.path.join(data_dir, "predecessors.npy")
    points_path = os.path.join(data_dir, "points_lat_long.npy")
    # --- END OF MODIFICATION ---

    try:
        # --- MODIFICATION ---
        # Load the .npy file. allow_pickle=True is needed because
        # the routes are saved as an array of lists (objects).
        plan = np.load(plan_path, allow_pickle=True)
        # --- END OF MODIFICATION ---

        predecessors = np.load(preds_path)
        points_lat_long = np.load(points_path)

    except FileNotFoundError as e:
        print(f"ERROR: Missing file: {e.filename}")
        # --- MODIFICATION ---
        print("Please ensure 'routes.npy', 'predecessors.npy', and 'points_lat_long.npy' are in the 'data' folder.")
        # --- END OF MODIFICATION ---
        return None, None, None

    print("All files loaded. Starting path expansion...")
    return plan, predecessors, points_lat_long


def expand_full_path(predecessors, from_node, to_node):
    """
    Finds the full sequence of nodes between two points
    using the predecessors matrix.
    (This function is unchanged)
    """
    from_node = int(from_node)
    to_node = int(to_node)

    path = [to_node]
    current = to_node

    while current != from_node:
        # Ensure predecessor is treated as an integer
        current = int(predecessors[from_node, current])
        if current == -9999: # Safety check for no path
             print(f"Error: No path found in predecessors from {from_node} to {to_node}")
             return [from_node] # Return start node to avoid infinite loop

        path.append(current)

        if len(path) > 2000: # Increased safety break
             print(f"Warning: Path from {from_node} to {to_node} seems too long (>2000 steps). Breaking.")
             break

    return list(reversed(path))


def save_final_routes(route_plan_npy, predecessors, points_lat_long):
    """
    Loops through the simple plan from routes.npy, expands all paths,
    and saves the final flyable GPS routes.
    """

    final_plan = {"flyable_trips": []}

    # --- MODIFICATION ---
    # We now iterate over the numpy array of routes directly.
    # 'enumerate' provides the trip_id.
    for trip_index, original_sequence in enumerate(route_plan_npy):
        print(f"Expanding Trip {trip_index}...")

        trip = {
            "trip_id": int(trip_index),
            # The .npy file doesn't contain total distance, so we remove that field.
            # "total_distance_from_plan": ...
            "flyable_path_gps": []
        }

        # 'original_sequence' is now the list of nodes, e.g., [0, 5, 12, 0]
        full_path_indices = []

        for i in range(len(original_sequence) - 1):
            from_node = original_sequence[i]
            to_node = original_sequence[i+1]

            # Find the expanded path between these two nodes
            # We use [:-1] to avoid duplicating the 'to_node'
            # (it will be the 'from_node' in the next iteration)
            expanded_leg = expand_full_path(predecessors, from_node, to_node)

            if i < len(original_sequence) - 2:
                full_path_indices.extend(expanded_leg[:-1])
            else:
                # For the last leg, add the full path
                full_path_indices.extend(expanded_leg)

        # De-duplicate nodes while preserving order (in case of overlap)
        final_path_indices = []
        seen = set()
        for node_index in full_path_indices:
            if node_index not in seen:
                seen.add(node_index)
                final_path_indices.append(node_index)

        # Convert the final list of node indices to GPS coordinates
        for node_index in final_path_indices:
            lon, lat = points_lat_long[node_index]
            trip["flyable_path_gps"].append((int(node_index), float(lon), float(lat)))

        final_plan["flyable_trips"].append(trip)
    # --- END OF MODIFICATION ---

    output_path = os.path.join(data_dir, "final_flyable_routes.json")
    try:
        with open(output_path, 'w') as f:
            json.dump(final_plan, f, indent=4)
        print(f"Successfully saved all flyable routes to {output_path}")
    except Exception as e:
        print(f"ERROR: Could not save final output file: {e}")


def main():
    """Entry point for the expansion script."""
    print("--- Route Expansion Script ---")

    # --- MODIFICATION ---
    # Renamed variable to reflect it's from the .npy file
    route_plan_npy, predecessors, points_lat_long = load_files()

    if route_plan_npy is not None:
        save_final_routes(route_plan_npy, predecessors, points_lat_long)
    # --- END OF MODIFICATION ---

if __name__ == "__main__":
    main()
