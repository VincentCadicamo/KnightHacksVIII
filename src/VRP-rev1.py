import numpy as np
import os
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# (create_data_model function is unchanged)
def create_data_model(distance_matrix, num_vehicles, battery_capacity):
    """Stores the data for the problem."""
    data = {}
    data["distance_matrix"] = distance_matrix
    data["num_vehicles"] = num_vehicles
    data["depot"] = 0
    data["vehicle_capacities"] = [battery_capacity] * num_vehicles
    return data

def save_solution_npy(data, manager, routing, solution, output_file_path):
    """Saves the routes to a .npy file."""

    all_routes = []
    print("Solution found, saving to .npy file...")

    for vehicle_id in range(data["num_vehicles"]):
        route_for_vehicle = []
        index = routing.Start(vehicle_id)

        while not routing.IsEnd(index):
            node_index = manager.IndexToNode(index)
            route_for_vehicle.append(node_index)
            index = solution.Value(routing.NextVar(index))

        # Add the end node (depot)
        node_index = manager.IndexToNode(index)
        route_for_vehicle.append(node_index)

        # Add this vehicle's route to the main list
        # We only save non-empty routes (i.e., routes that are not just [0, 0])
        if len(route_for_vehicle) > 2:
            all_routes.append(route_for_vehicle)

    # Save this list of lists as a numpy file
    try:
        # We use dtype=object to allow for lists of different lengths
        np.save(output_file_path, np.array(all_routes, dtype=object))
        print(f"Successfully saved routes to {os.path.abspath(output_file_path)}")
        print(f"Total routes saved: {len(all_routes)}")
    except Exception as e:
        print(f"Error saving .npy file: {e}")

def main():
    """Entry point of the program."""

    # --- 1. DEFINE PATHS BASED ON SCRIPT LOCATION ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(root_dir, "data")
    matrix_file_path = os.path.join(data_dir, "distance_matrix.npy")

    try:
        distance_matrix = np.load(matrix_file_path)
    except FileNotFoundError:
        print(f"Error: Could not find '{matrix_file_path}'.")
        return
    except Exception as e:
        print(f"Error loading matrix: {e}")
        return
    print(f"Successfully loaded distance matrix from '{matrix_file_path}'.")

    # --- 2. DEFINE YOUR OTHER INPUTS ---
    num_drones = 4
    drone_battery_ft = 37725

    # --- 3. CREATE THE DATA MODEL ---
    data = create_data_model(distance_matrix, num_drones, drone_battery_ft)

    # --- 4. CREATE THE ROUTING MANAGER & MODEL ---
    manager = pywrapcp.RoutingIndexManager(
        len(data["distance_matrix"]), data["num_vehicles"], data["depot"]
    )
    routing = pywrapcp.RoutingModel(manager)

    # --- 5. DEFINE THE COST (OBJECTIVE) ---
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # --- 6. DEFINE THE CONSTRAINT (BATTERY) ---
    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,
        data["vehicle_capacities"][0],
        True,
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    # This line (which you added) helps balance the "time"
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # (The CumulVar loop is no longer needed here,
    # as the penalties handle the optimization objective)

    # --- 🚀 NEW: STEP 7 - MAXIMIZE COVERAGE ---
    # Give a huge penalty for not visiting a pole.
    # This must be larger than any possible route distance.
    # e.g., max_battery * num_drones
    penalty = int(drone_battery_ft * num_drones)
    print(f"Using penalty: {penalty} for each unvisited pole.")

    # Loop through ALL nodes (poles)
    for node_index in range(1, len(distance_matrix)): # Start from 1 to skip depot
        routing.AddDisjunction(
            [manager.NodeToIndex(node_index)],  # The node to visit
            penalty                           # The cost to pay if we DON'T visit it
        )
    # --- END OF NEW STEP ---

    # --- 8. SET SOLVER PARAMETERS ---
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PARALLEL_CHEAPEST_INSERTION
    )
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    # Give the solver more time, as this is a harder problem
    search_parameters.time_limit.seconds = 10

    # --- 9. SOLVE THE PROBLEM ---
    print("Solving VRP (Prize-Collecting)...")
    solution = routing.SolveWithParameters(search_parameters)

    # --- 10. SAVE THE SOLUTION ---
    if solution:
        try:
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
        except OSError as e:
            print(f"Error: Could not create directory {data_dir}. {e}")
            return
        output_file_path = os.path.join(data_dir, "routes.npy")
        save_solution_npy(data, manager, routing, solution, output_file_path)
    else:
        print("No solution found!")

if __name__ == "__main__":
    main()