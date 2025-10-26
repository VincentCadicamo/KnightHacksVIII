
import os
import json
import numpy as np


script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
data_dir = os.path.join(base_dir, "data")


def load_files():
    print("Loading route plan and .npy files...")

    plan_path = os.path.join(data_dir, "route_plan.json")
    preds_path = os.path.join(data_dir, "predecessors.npy")
    points_path = os.path.join(data_dir, "points_lat_long.npy")
    
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

    output_path = os.path.join(data_dir, "final_flyable_routes.json")
    try:
        with open(output_path, 'w') as f:
            json.dump(final_plan, f, indent=4)
        print(f"Successfully saved all flyable routes to {output_path}")
    except Exception as e:
        print(f"ERROR: Could not save final output file: {e}")
        

def main():
    print("--- Route Expansion Script ---")
    plan, predecessors, points_lat_long = load_files()
    
    if plan:
        save_final_routes(plan, predecessors, points_lat_long)

if __name__ == "__main__":
    main()

