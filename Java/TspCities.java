package com.google.ortools.constraintsolver.samples;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;
import com.google.ortools.constraintsolver.main;
import java.util.logging.Logger;

// distance_matrix.npy Symmetric matrix of door-to-door flight distances between waypoints computed inside the polygon. Use this as the cost matrix in your optimizer. || `predecessors.npy` 
//photo_indexes.csv
//predecessors.npy NumPy array (N x N) | For each pair of nodes `(i, j)`, stores the predecessor index on the shortest path from `i` to `j`. Use `scipy.sparse.csgraph.dijkstra` conventions to expand indirect legs back into actual waypoint sequences. |
// points_lat_long.npy NumPy array (N x 2) | Geographic coordinates (longitude, latitude) for every waypoint index. Index into this after planning to obtain real-world coordinates. |
//asset_indexes.npy NumPy array | Subset of waypoint indices corresponding to electrical assets (i.e. poles), formatted as a slice: `[first index, last index]`. |
// photo_indexes.npy  Subset of waypoint indices for the 4 photo points around each asset, formatted as a slice: `[first index, last index]`.  |
// polygon_lon_lat.wkt  WKT polygon describing the allowed flight region. Use Shapely/GeoPandas to visualize or enforce constraints. |

//missions.csv

/** Minimal TSP using distance matrix. */
public class TspCities {
  private static final Logger logger = Logger.getLogger(TspCities.class.getName());

  static class DataModel {
    // 1. Data from original TSP
    public final float[][] distanceMatrix = PythonNumpyHelper.loadNpyAs2DArray("data/distance_matrix.npy");
    public final int depot = 0;
    public final long droneBatteryCapacity = 37725L; // 37,725 feet

    // 3. VRP Configuration
    // We set a max number of missions. The solver will try to use fewer.
    public final int vehicleNumber; // Max number of missions

    public DataModel() {
      // All data is loaded at declaration.
      // Set max vehicles to the total number of nodes (minus depot).
      // This is the "worst-case" for a VRP visiting all nodes.
      // The solver will automatically find the *minimum* number required.
      if (this.distanceMatrix != null && this.distanceMatrix.length > 0) {
        this.vehicleNumber = this.distanceMatrix.length - 1;
      } else {
        this.vehicleNumber = 0; // Or 1, if you want a default
      }

      if (this.vehicleNumber < 1) {
        this.vehicleNumber = 1; // Ensure at least one vehicle
      }
      logger.info("Setting max vehicles (missions) to: " + this.vehicleNumber);
    }
  }

  static void printSolution(
      DataModel data, RoutingModel routing, RoutingIndexManager manager, Assignment solution) {
    // Solution cost.
    logger.info("Objective: " + solution.objectiveValue() + " total units (feet)");

    // Inspect solution.
    long totalRouteDistance = 0;
    int missionsUsed = 0;

    for (int i = 0; i < data.vehicleNumber; ++i) {
      long index = routing.start(i);
      if (routing.isEnd(index)) {
        continue; // This mission is not used
      }

      missionsUsed++;
      logger.info("Mission " + missionsUsed + ":");
      String route = "";
      long routeDistance = 0;

      long previousIndex = index;
      while (!routing.isEnd(index)) {
        route += manager.indexToNode(index) + " -> ";
        previousIndex = index;
        index = solution.value(routing.nextVar(index));
        routeDistance += routing.getArcCostForVehicle(previousIndex, index, 0);
      }
      route += manager.indexToNode(routing.end(i)); // Add the end node (depot)

      logger.info(route);
      logger.info("Mission distance: " + routeDistance + " units");
      totalRouteDistance += routeDistance;
    }
    logger.info("Total missions: " + missionsUsed);
    logger.info("Total route distance: " + totalRouteDistance + " units");
  }

  public static void main(String[] args) throws Exception {
    Loader.loadNativeLibraries();
    // Instantiate the data problem.
    final DataModel data = new DataModel();

    // --- Create Routing Index Manager for VRP ---
    // We need to define start and end nodes for *all* vehicles.
    int[] starts = new int[data.vehicleNumber];
    int[] ends = new int[data.vehicleNumber];
    Arrays.fill(starts, data.depot);
    Arrays.fill(ends, data.depot);

    RoutingIndexManager manager =
        new RoutingIndexManager(data.distanceMatrix.length, data.vehicleNumber, starts, ends);

    // Create Routing Model.
    RoutingModel routing = new RoutingModel(manager);

    // --- Transit Callback (same as before) ---
    // The cost is still based on the direct distance_matrix.
    final int transitCallbackIndex =
        routing.registerTransitCallback((long fromIndex, long toIndex) -> {
          // Convert from routing variable Index to user NodeIndex.
          int fromNode = manager.indexToNode(fromIndex);
          int toNode = manager.indexToNode(toIndex);
          return (long) data.distanceMatrix[fromNode][toNode];
        });

    // Define cost of each arc.
    routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

    // --- Battery Constraint (same as before) ---
    // This dimension now applies to *each vehicle* (mission).
    routing.addDimension(transitCallbackIndex, 0, data.droneBatteryCapacity,
        true, // start cumul to zero
        "Distance");
    RoutingDimension distanceDimension = routing.getMutableDimension("Distance");
    // This helps the solver minimize the *total* distance, not just the longest route.
    // distanceDimension.setGlobalSpanCostCoefficient(100);

    // --- NEW: Add Constraints to Visit ALL Nodes (TSP) ---
    // We add a "disjunction" for each node to force the solver to visit it.
    long penalty = 1_000_000_000; // A huge penalty
    for (int node = 0; node < data.distanceMatrix.length; node++) {
        if (node == data.depot) continue; // Skip depot, it's start/end
        long[] nodeIndices = { manager.nodeToIndex(node) };
        // This forces the solver to include this node in the route
        // or pay a massive penalty (which it will avoid).
        routing.addDisjunction(nodeIndices, penalty);
    }

    // Setting first solution heuristic.
    RoutingSearchParameters searchParameters =
        main.defaultRoutingSearchParameters()
            .toBuilder()
            .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
            // .setLocalSearchMetaheuristic(LocalSearchMetaheuristic.Value.GUIDED_LOCAL_SEARCH)
            // .setTimeLimit(new Duration(30, 0)) // Set a time limit
            .build();
            
    // Solve the problem.
    Assignment solution = routing.solveWithParameters(searchParameters);

    // Print solution on console.
    if (solution != null) {
      printSolution(data, routing, manager, solution);
    } else {
      logger.severe("No solution found!");
      logger.severe(
          "This could mean the problem is impossible (e.g., battery is too low to even reach a single node, "
              + "or a node is unreachable).");
    }
  }
}


