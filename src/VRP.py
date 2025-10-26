import json, os, numpy as np
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

def extract_vehicle_routes(data, manager, routing, solution):
    routes = []
    for v in range(data["num_vehicles"]):
        start_idx = routing.Start(v)
        if routing.IsEnd(solution.Value(routing.NextVar(start_idx))):
            continue
        r = [manager.IndexToNode(start_idx)]
        idx = start_idx
        while not routing.IsEnd(idx):
            idx = solution.Value(routing.NextVar(idx))
            r.append(manager.IndexToNode(idx))
        routes.append(r)  # each r starts/ends at depot
    return routes

def combine_routes_with_single_depot_separator(routes, depot=0, keep_final_depot=True):
    combo = []
    for i, r in enumerate(routes):
        if i < len(routes) - 1:
            combo.extend(r[:-1])  # drop trailing depot between sorties
        else:
            combo.extend(r if keep_final_depot else r[:-1])
    return combo

def route_distance(route, D):
    return int(sum(D[route[i]][route[i+1]] for i in range(len(route)-1)))

def compute_metrics(routes, D, depot=0, speed_ft_s=75.0, recharge_s=15*60):
    """Return dict with coverage, distances, times."""
    n = len(D)
    customers = set(range(n)) - {depot}
    visited = set()
    per_sortie = []
    total_dist = 0
    total_flight_s = 0.0
    for r in routes:
        # mark visited customers (exclude depots on ends)
        for node in r[1:-1]:
            if node != depot:
                visited.add(node)
        d = route_distance(r, D)
        t = d / max(speed_ft_s, 1e-9)
        per_sortie.append({"route": r, "distance_ft": d, "flight_s": t})
        total_dist += d
        total_flight_s += t

    num_recharges = max(0, len(routes) - 1)
    total_recharge_s = num_recharges * recharge_s
    makespan_s = total_flight_s + total_recharge_s

    coverage = 100.0 * len(visited) / max(1, len(customers))
    return {
        "coverage_pct": coverage,
        "served": len(visited),
        "total_customers": len(customers),
        "num_sorties": len(routes),
        "total_distance_ft": int(total_dist),
        "total_flight_time_s": total_flight_s,
        "total_recharge_time_s": total_recharge_s,
        "mission_makespan_s": makespan_s,
        "per_sortie": per_sortie,
    }

def save_artifacts(routes, combined, metrics, out_dir="output"):
    os.makedirs(out_dir, exist_ok=True)

    with open(os.path.join(out_dir,"combined_route.json"), "w", encoding="utf-8") as f:
        json.dump(combined, f)

    with open(os.path.join(out_dir,"metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)

    # CSV summary (one row per sortie)
    with open(os.path.join(out_dir,"sorties.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["sortie_idx","route","distance_ft","flight_s"])
        for i, s in enumerate(metrics["per_sortie"], 1):
            w.writerow([i, " ".join(map(str, s["route"])), s["distance_ft"], round(s["flight_s"],2)])

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

    data["num_vehicles"] = len(D) - 1

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
    search_parameters.time_limit.FromSeconds(60)
    search_parameters.log_search = True

    # Solve the problem.
    print("[Solving Solution]")
    solution = routing.SolveWithParameters(search_parameters)

    # Print solution on console.
    if solution:
        print_solution(data, manager, routing, solution)

        routes = extract_vehicle_routes(data, manager, routing, solution)
        combined = combine_routes_with_single_depot_separator(routes, depot=data["depot"])

        # 2) compute metrics (set your true speed/recharge)
        D = data["distance_matrix"]
        metrics = compute_metrics(
            routes, D,
            depot=data["depot"],
            speed_ft_s=75.0,  # ← your drone speed
            recharge_s=15 * 60  # ← recharge duration
        )

        # 3) save artifacts
        save_artifacts(routes, combined, metrics, out_dir="output")

        print(f"[coverage] {metrics['coverage_pct']:.2f}% "
              f"({metrics['served']}/{metrics['total_customers']})")
        print(f"[distance] total={metrics['total_distance_ft']} ft  "
              f"sorties={metrics['num_sorties']}")
        print(f"[time] flight={metrics['total_flight_time_s']:.1f}s  "
              f"recharge={metrics['total_recharge_time_s']:.1f}s  "
              f"makespan={metrics['mission_makespan_s']:.1f}s")
    else:
        print("No solution found !")


if __name__ == "__main__":
    main()