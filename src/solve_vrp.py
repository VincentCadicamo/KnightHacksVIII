"""
Solves the Vehicle Routing Problem (VRP) for the drone fleet.

This script finds the optimal *sequence* of nodes for the drones to visit.
It saves the resulting plan to 'data/route_plan.json' for post-processing.
"""

import os
import json  # Import json for saving the output
import time  # Import time for measuring runtime
import numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import multiprocessing


def create_data_model():
    """Loads and stores the data for the problem."""
    print("Stage 1: Loading data model...")
    data = {}
    
    npy_file_path = os.path.join("data", "distance_matrix.npy")
    
    try:
        matrix = np.load(npy_file_path)
    except FileNotFoundError:
        print(f"ERROR: Cannot find {npy_file_path}.")
        return None

    data["distance_matrix"] = matrix.astype(int)
    # Use all nodes as potential "vehicles" to allow for any number of trips
    data["num_vehicles"] = len(data["distance_matrix"]) 
    data["depot"] = 0
    
    # SET YOUR DRONE'S BATTERY/RANGE LIMIT HERE
    data["battery_limit"] = 37725  

    print(f"Data loaded: {len(data['distance_matrix'])} nodes.")
    return data


def save_solution_to_file(data, manager, routing, solution, solve_time):
    """
    Saves the simplified route plan to a JSON file.
    This is the "handoff" for the expansion script.
    """
    print("Stage 4: Saving route plan to JSON...")
    
    plan = {"trips": []}
    distance_dimension = routing.GetDimensionOrDie("Distance")

    for vehicle_id in range(data["num_vehicles"]):
        index = routing.Start(vehicle_id)

        # Check if the vehicle is used at all
        if routing.IsEnd(solution.Value(routing.NextVar(index))):
            continue
            
        trip = {
            "trip_id": vehicle_id,
            "node_sequence": [],
            "total_distance": 0
        }
        
        route_distance = 0
        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            trip["node_sequence"].append(node_index)
            
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )

        # Add the final depot node
        node_index = manager.IndexToNode(index)
        trip["node_sequence"].append(node_index)
        
        trip["total_distance"] = route_distance
        plan["trips"].append(trip)

    # Save the plan to a file in the data directory
    output_path = os.path.join("data", "route_plan.json")
    try:
        with open(output_path, 'w') as f:
            json.dump(plan, f, indent=4)
        
        # --- THIS IS THE CHANGE ---
        # Print a final summary of the run
        num_trips = len(plan["trips"])
        print("\n--- Solver Summary ---")
        print(f"Total Solve Time: {solve_time:.2f} seconds")
        print(f"Total Trips Created: {num_trips}")
        print("----------------------\n")
        print(f"Successfully saved plan to {output_path}")
        # --- END OF CHANGE ---
        
    except Exception as e:
        print(f"ERROR: Could not save plan file: {e}")


def main():
    """Entry point of the program."""
    
    # 1. Instantiate the data problem.
    data = create_data_model()
    if data is None:
        return

    # 2. Create the routing index manager.
    print("Stage 2: Initializing routing model...")
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )

    # 3. Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # 4. Create and register a transit callback.
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # 5. Add Distance constraint.
    routing.AddDimension(
        transit_callback_index, 0, data["battery_limit"],
        True, "Distance"
    )

    # 6. Set search parameters
    print("Stage 3: Setting search parameters (time limit)...")
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    
    search_parameters.time_limit.FromSeconds(120)  # 2-minute time limit
    search_parameters.log_search = False

    num_cores_to_use = 1 

    # 7. Solve the problem.
    print(f"Solver started on {num_cores_to_use} core. This will take up to 120 seconds. Please wait...")
    print("-------------------- SOLVER RUNNING --------------------")
    
    # --- THIS IS THE CHANGE ---
    start_time = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    end_time = time.time()
    solve_time = end_time - start_time
    # --- END OF CHANGE ---
    
    print("-------------------- SOLVER FINISHED -------------------")


    # 8. Save solution.
    if solution:
        print(f"Solver found a solution in {solve_time:.2f} seconds!")
        # --- THIS IS THE CHANGE ---
        # Pass the solve_time to the save function
        save_solution_to_file(data, manager, routing, solution, solve_time)
        # --- END OF CHANGE ---
    else:
        print("No solution found (or solver timed out)!")


if __name__ == "__main__":
    main()

