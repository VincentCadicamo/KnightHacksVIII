import json, os, numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def extract_vehicle_routes(data, manager, routing, solution):
    routes = []
    for v in range(data["num_vehicles"]):
        start_idx = routing.Start(v)
        if routing.IsEnd(solution.Value(routing.NextVar(start_idx))):
            continue
        route = [manager.IndexToNode(start_idx)]
        idx = start_idx
        while not routing.IsEnd(idx):
            idx = solution.Value(routing.NextVar(idx))
            route.append(manager.IndexToNode(idx))
        routes.append(route)
    return routes

def combine_routes_with_single_depot_separator(routes, depot=0):
    combined = []
    for i, r in enumerate(routes):
        if i < len(routes) - 1:
            combined.extend(r[:-1])
        else:
            combined.extend(r)
    return combined
def create_data_model():
    data = {}

    npy_file_path = os.path.join("data", "distance_matrix.npy")

    try:
        matrix = np.load(npy_file_path)
    except FileNotFoundError:
        print(f"ERROR: Data file not found at {npy_file_path}")
        return None

    D = matrix.astype(int)
    data["distance_matrix"] = D
    print("[Loaded distance matrix]")

    n = len(D)
    num_customers = n - 1

    data["distance_cap_ft"] = 37725


    depot = 0
    infeasible_nodes = []
    for i in range(1, n):
        rt = int(D[depot][i]) + int(D[i][depot])
        if rt > data["distance_cap_ft"]:
            infeasible_nodes.append((i, rt))
    if infeasible_nodes:
        print("[Infeasible] These nodes cannot be served within the per-sortie cap:")
        for i, rt in infeasible_nodes:
            print(f"  node {i}: depot->i->depot = {rt} > cap {data['distance_cap_ft']}")
        return None  # or handle by allowing drops (see below)

    data["num_vehicles"] = max(1, min(num_customers, 8))

    data["depot"] = depot
    return data


def print_solution(data, manager, routing, solution):
    print(f"Objective: {solution.ObjectiveValue()}")
    max_route_distance = 0
    for vehicle_id in range(data["num_vehicles"]):
        if not routing.IsVehicleUsed(solution, vehicle_id):
            continue
        index = routing.Start(vehicle_id)
        plan_output = f"Route for vehicle {vehicle_id}:\n"
        route_distance = 0
        while not routing.IsEnd(index):
            plan_output += f" {manager.IndexToNode(index)} -> "
            previous_index = index
            index = solution.Value(routing.NextVar(index))
            route_distance += routing.GetArcCostForVehicle(
                previous_index, index, vehicle_id
            )
        plan_output += f"{manager.IndexToNode(index)}\n"
        plan_output += f"Distance of the route: {route_distance}m\n"
        print(plan_output)
        max_route_distance = max(route_distance, max_route_distance)
    print(f"Maximum of the route distances: {max_route_distance}m")


def main():
    data = create_data_model()


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
        0,
        int(data["distance_cap_ft"]),
        True,
        dimension_name,
    )
    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    routing.SetFixedCostOfAllVehicles(500)

    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_parameters.time_limit.seconds = 15  # <-- hard stop
    search_parameters.log_search = True

    # Solve the problem.
    print("[Solving Solution]")
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)

        routes = extract_vehicle_routes(data, manager, routing, solution)
        combined = combine_routes_with_single_depot_separator(routes, depot=data["depot"])

        os.makedirs("output", exist_ok=True)
        out_path = os.path.join("output", "combined_route.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(combined, f)
    else:
        print("No solution found !")


if __name__ == "__main__":
    main()