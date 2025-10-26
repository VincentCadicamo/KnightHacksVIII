import os
import json
import time
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import multiprocessing

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
data_dir = os.path.join(base_dir, "data")
os.makedirs(data_dir, exist_ok=True)
def create_data_model():
    print("Stage 1: Loading data model...")
    data = {}

    npy_file_path = os.path.join(data_dir, "distance_matrix.npy")
    
    try:
        matrix = np.load(npy_file_path)
    except FileNotFoundError:
        print(f"ERROR: Cannot find {npy_file_path}.")
        return None

    data["distance_matrix"] = matrix.astype(int)
    data["num_vehicles"] = len(data["distance_matrix"]) 
    data["depot"] = 0
    data["battery_limit"] = 37725  

    print(f"Data loaded: {len(data['distance_matrix'])} nodes.")
    return data


def save_solution_to_file(data, manager, routing, solution, solve_time):
    print("Stage 4: Saving route plan to JSON...")
    
    plan = {"trips": []}
    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)
        if routing.IsEnd(solution.Value(routing.NextVar(index))):
            continue
            
        trip = {"trip_id": vehicle_id, "node_sequence": [], "total_distance": 0}
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            trip["node_sequence"].append(node_index)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        node_index = manager.IndexToNode(index)
        trip["node_sequence"].append(node_index)
        trip["total_distance"] = route_distance
        plan["trips"].append(trip)

    output_path = os.path.join(data_dir, "route_plan.json")
    
    try:
        with open(output_path, 'w') as f:
            json.dump(plan, f, indent=4)
        
        num_trips = len(plan["trips"])
        print("\n--- Solver Summary ---")
        print(f"Total Solve Time: {solve_time:.2f} seconds")
        print(f"Total Trips Created: {num_trips}")
        print("----------------------\n")
        print(f"Successfully saved plan to {output_path}")
        
    except Exception as e:
        print(f"ERROR: Could not save plan file: {e}")


def main():
    data = create_data_model()
    if data is None:
        return

    print("Stage 2: Initializing routing model...")
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    routing.AddDimension(
        transit_callback_index, 0, data["battery_limit"],
        True, "Distance"
    )

    print("Stage 3: Setting search parameters (time limit)...")
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_parameters.time_limit.FromSeconds(120)
    search_parameters.log_search = False
    num_cores_to_use = 1 

    print(f"Solver started on {num_cores_to_use} core. This will take up to 120 seconds. Please wait...")
    print("-------------------- SOLVER RUNNING --------------------")
    
    start_time = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    end_time = time.time()
    solve_time = end_time - start_time
    
    print("-------------------- SOLVER FINISHED -------------------")

    if solution:
        print(f"Solver found a solution in {solve_time:.2f} seconds!")
        save_solution_to_file(data, manager, routing, solution, solve_time)
    else:
        print("No solution found (or solver timed out)!")
        fallback_path = os.path.join(data_dir, "route_plan.json")
        try:
            with open(fallback_path, 'w') as f:
                json.dump({"trips": [], "error": "No solution found (or solver timed out)"}, f, indent=4)
            print(f"Wrote fallback (empty) plan to {fallback_path}")
        except Exception as e:
            print(f"ERROR: Could not write fallback plan file: {e}")

if __name__ == "__main__":
    main()