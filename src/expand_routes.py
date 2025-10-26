"""
Expands the simple route plan into a full, flyable GPS path.

This script loads the 'route_plan.json' (from the solver) and
uses 'predecessors.npy' and 'points_lat_long.npy' to generate
the final, high-resolution flight paths.
"""

import os
import json
import numpy as np

# --- THIS IS THE CHANGE ---
# Get the directory of the current script (src)
script_dir = os.path.dirname(os.path.abspath(__file__))
# Get the base directory (one level up)
base_dir = os.path.dirname(script_dir)
# Define the data directory path
data_dir = os.path.join(base_dir, "data")
# --- END OF CHANGE ---


def load_files():
    """Loads all necessary files from the data directory."""
    print("Loading route plan and .npy files...")
    
    # --- THIS IS THE CHANGE ---
    plan_path = os.path.join(data_dir, "route_plan.json")
    preds_path = os.path.join(data_dir, "predecessors.npy")
    points_path = os.path.join(data_dir, "points_lat_long.npy")
    # --- END OF CHANGE ---
    
    try:
        with open(plan_path, 'r') as f:
            plan = json.load(f)
        
        predecessors = np.load(preds_path)
        points_lat_long = np.load(points_path)
        
    except FileNotFoundError as e:
        print(f"ERROR: Missing file: {e.filename}")
        print("Please ensure 'route_plan.json', 'predecessors.npy', and 'points_lat_long.npy' are in the 'data' folder.")
        return None, None, None
        
    print("All files loaded. Starting path expansion...")
    return plan, predecessors, points_lat_long


def expand_full_path(predecessors, from_node, to_node):
    """
    Finds the full sequence of nodes between two points
    using the predecessors matrix.
    """
    from_node = int(from_node)
    to_node = int(to_node)
    
    path = [to_node]
    current = to_node
    
    while current != from_node:
        current = int(predecessors[from_node, current])
        path.append(current)
        if len(path) > 1000:
             print(f"Warning: Path from {from_node} to {to_node} seems too long. Breaking.")
             break
             
    return list(reversed(path))


def save_final_routes(plan, predecessors, points_lat_long):
    """
    Loops through the simple plan, expands all paths,
    and saves the final flyable GPS routes.
    """
    
    final_plan = {"flyable_trips": []}

    for original_trip in plan["trips"]:
        print(f"Expanding Trip {original_trip['trip_id']}...")
        
        trip = {
            "trip_id": int(original_trip['trip_id']),
            "total_distance_from_plan": int(original_trip['total_distance']),
            "flyable_path_gps": []
        }
        
        original_sequence = original_trip["node_sequence"]
        full_path_indices = []
        
        for i in range(len(original_sequence) - 1):
            from_node = original_sequence[i]
            to_node = original_sequence[i+1]
            expanded_leg = expand_full_path(predecessors, from_node, to_node)[:-1]
            full_path_indices.extend(expanded_leg)
        
        full_path_indices.append(original_sequence[-1])

        for node_index in full_path_indices:
            lon, lat = points_lat_long[node_index]
            trip["flyable_path_gps"].append((int(node_index), float(lon), float(lat)))
            
        final_plan["flyable_trips"].append(trip)
        
    # --- THIS IS THE CHANGE ---
    output_path = os.path.join(data_dir, "final_flyable_routes.json")
    # --- END OF CHANGE ---
    try:
        with open(output_path, 'w') as f:
            json.dump(final_plan, f, indent=4)
        print(f"Successfully saved all flyable routes to {output_path}")
    except Exception as e:
        print(f"ERROR: Could not save final output file: {e}")
        

def main():
    """Entry point for the expansion script."""
    print("--- Route Expansion Script ---")
    plan, predecessors, points_lat_long = load_files()
    
    if plan:
        save_final_routes(plan, predecessors, points_lat_long)

if __name__ == "__main__":
    main()

