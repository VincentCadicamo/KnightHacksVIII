"""
Expands the simple route plan into a full, flyable GPS path.

This script loads the 'route_plan.json' (from the solver) and
uses 'predecessors.npy' and 'points_lat_long.npy' to generate
the final, high-resolution flight paths.
"""

import os
import json
import numpy as np


def load_files():
    """Loads all necessary files from the data directory."""
    print("Loading route plan and .npy files...")
    
    plan_path = os.path.join("data", "route_plan.json")
    preds_path = os.path.join("data", "predecessors.npy")
    points_path = os.path.join("data", "points_lat_long.npy")
    
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
    # We cast all node indices to standard Python `int`
    # to prevent any numpy.int32 types.
    from_node = int(from_node)
    to_node = int(to_node)
    
    path = [to_node]
    current = to_node
    
    while current != from_node:
        # Get the predecessor (which is a numpy.int32)
        # and cast it to a standard Python `int`
        current = int(predecessors[from_node, current])
        path.append(current)
        
        # Safety break to prevent infinite loops
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
        
        # Cast trip_id and total_distance to standard `int`
        # just in case they are numpy types.
        trip = {
            "trip_id": int(original_trip["trip_id"]),
            "total_distance_from_plan": int(original_trip["total_distance"]),
            "flyable_path_gps": []
        }
        
        original_sequence = original_trip["node_sequence"]
        full_path_indices = []
        
        for i in range(len(original_sequence) - 1):
            from_node = original_sequence[i]
            to_node = original_sequence[i+1]
            
            # Get the expanded path, but drop the last node
            # to avoid duplicates (e.g., A->B, B->C)
            expanded_leg = expand_full_path(predecessors, from_node, to_node)[:-1]
            full_path_indices.extend(expanded_leg)
        
        # Add the very last node of the trip
        full_path_indices.append(original_sequence[-1])

        # Convert the full list of indices to GPS coordinates
        for node_index in full_path_indices:
            # node_index is a Python `int`
            lon, lat = points_lat_long[node_index]
            
            # --- THIS IS THE CHANGE ---
            # Save the coordinate as (id, longitude, latitude)
            trip["flyable_path_gps"].append((int(node_index), float(lon), float(lat)))
            # --- END OF CHANGE ---
            
        final_plan["flyable_trips"].append(trip)
        
    # Save the final file
    output_path = os.path.join("data", "final_flyable_routes.json")
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

