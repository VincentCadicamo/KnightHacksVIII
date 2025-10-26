import numpy as np
import os
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def create_data_model(distance_matrix, num_vehicles, battery_capacity):
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

        node_index = manager.IndexToNode(index)
        route_for_vehicle.append(node_index)

        if len(route_for_vehicle) > 2:
            all_routes.append(route_for_vehicle)

    try:
        np.save(output_file_path, np.array(all_routes, dtype=object))
        print(f"Successfully saved routes to {os.path.abspath(output_file_path)}")
        print(f"Total routes saved: {len(all_routes)}")
    except Exception as e:
        print(f"Error saving .npy file: {e}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(root_dir, "data")

    matrix_file_path = os.path.join(data_dir, "smart_matrix.npy")
    photo_indexes_file = os.path.join(data_dir, "photo_indexes.npy")

    try:
        distance_matrix = np.load(matrix_file_path)
        photo_indexes = np.load(photo_indexes_file)
        # Convert photo_indexes to a set for fast lookups
        photo_indexes_set = set(int(idx) for idx in photo_indexes)
    except FileNotFoundError as e:
        print(f"Error: Could not find a required .npy file.")
        print(e)
        return
    except Exception as e:
        print(f"Error loading files: {e}")
        return

    num_drones = 30
    drone_battery_ft = 37725

    data = create_data_model(distance_matrix, num_drones, drone_battery_ft)

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

    dimension_name = "Distance"
    routing.AddDimension(
        transit_callback_index,
        0,  # no slack
        data["vehicle_capacities"][0],  # vehicle battery capacity
        True,  # start cumul to zero
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    # This coefficient balances the cost of travel vs. the penalty of skipping nodes
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # --- ROBUST PRIZE-COLLECTING LOGIC ---
    # This is the correct combination of VRP-rev1 and VRP-rev2

    # Give a huge penalty for not visiting a *desired* pole.
    # This must be larger than any possible route distance.
    penalty = int(drone_battery_ft * num_drones)

    depot_index = data["depot"]
    total_nodes_in_matrix = len(data["distance_matrix"])
    poles_as_prizes = 0

    print(f"Total nodes in distance matrix: {total_nodes_in_matrix}")
    print(f"Total Photo Poles to visit (as prizes): {len(photo_indexes_set)}")

    for node_index in range(total_nodes_in_matrix):
        if node_index == depot_index:
            continue

        # If the node IS a photo pole, add it as an optional "prize".
        if node_index in photo_indexes_set:
            routing.AddDisjunction(
                [manager.NodeToIndex(node_index)],
                penalty
            )
            poles_as_prizes += 1
        else:
            # If it's NOT a photo pole, forbid all vehicles from visiting it.
            routing.SetAllowedVehiclesForIndex(
                [], manager.NodeToIndex(node_index)
            )

    print(f"Added {poles_as_prizes} photo poles as 'prizes'.")
    print(f"Forbidden {total_nodes_in_matrix - poles_as_prizes - 1} non-photo-pole nodes.")
    # --- END OF LOGIC ---

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()

    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )

    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC
    )
    search_parameters.time_limit.seconds = 120
    search_parameters.log_search = True

    print("Solving VRP (Prize-Collecting for Photo Poles)...")
    solution = routing.SolveWithParameters(search_parameters)

    if solution:
        print("Solution found! Saving all visited poles.")
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
        print("This is unexpected for a prize-collecting model.")
        print("Check if the depot is isolated or constraints are too tight.")


if __name__ == "__main__":
    main()

