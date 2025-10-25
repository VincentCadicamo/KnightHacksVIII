package org.example;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;
import com.google.ortools.constraintsolver.main;
import java.util.logging.Logger;


/** Minimal TSP using distance matrix. */
public class TspCities {
  private static final Logger logger = Logger.getLogger(TspCities.class.getName());

  static class DataModel {
    public final float[][] distanceMatrix = PythonNumpyHelper.loadNpyAs2DArray("data/distance_matrix.npy");
    public final int vehicleNumber = 1;
    public final int depot = 0;
  }

  /// @brief Print the solution.
  static void printSolution(
      RoutingModel routing, RoutingIndexManager manager, Assignment solution) {
    // Solution cost.
    logger.info("Objective: " + solution.objectiveValue() + "miles");
    // Inspect solution.
    logger.info("Route:");
    long routeDistance = 0;
    String route = "";
    long index = routing.start(0);
    while (!routing.isEnd(index)) {
      route += manager.indexToNode(index) + " -> ";
      long previousIndex = index;
      index = solution.value(routing.nextVar(index));
      routeDistance += routing.getArcCostForVehicle(previousIndex, index, 0);
    }
    route += manager.indexToNode(routing.end(0));
    logger.info(route);
    logger.info("Route distance: " + routeDistance + "miles");
  }

  public static void main(String[] args) throws Exception {
    Loader.loadNativeLibraries();
    // Instantiate the data problem.
    final DataModel data = new DataModel();

    // Create Routing Index Manager
    RoutingIndexManager manager =
        new RoutingIndexManager(data.distanceMatrix.length, data.vehicleNumber, data.depot);

    // Create Routing Model.
    RoutingModel routing = new RoutingModel(manager);

    // Create and register a transit callback.
    final int transitCallbackIndex =
        routing.registerTransitCallback((long fromIndex, long toIndex) -> {
          // Convert from routing variable Index to user NodeIndex.
          int fromNode = manager.indexToNode(fromIndex);
          int toNode = manager.indexToNode(toIndex);
          return data.distanceMatrix[fromNode][toNode];
        });

    // Define cost of each arc.
    routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

    // Setting first solution heuristic.
    RoutingSearchParameters searchParameters =
        main.defaultRoutingSearchParameters()
            .toBuilder()
            .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
            .build();

    // Solve the problem.
    Assignment solution = routing.solveWithParameters(searchParameters);

    // Print solution on console.
    printSolution(routing, manager, solution);
  }
}