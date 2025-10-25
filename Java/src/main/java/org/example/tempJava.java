package org.example;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;
import com.google.ortools.constraintsolver.main;

import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter; // Import FileWriter
import java.io.IOException;
import java.io.PrintWriter; // Import PrintWriter
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.logging.Logger;
import java.util.stream.Collectors;

/**
 * Solves the Drone Challenge (CVRP) using the provided data files.
 *
 * This program implements Step 4 of the suggested workflow:
 * "Respect battery limits"
 *
 * It reads the full distance matrix and the list of photo waypoints,
 * builds a smaller, specialized matrix for the solver, and then
 * solves the Capacitated Vehicle Routing Problem (CVRP) to find
 * the most efficient set of drone missions.
 *
 * NEW: It also saves the mission plan to 'missions.csv'.
 */
public class tempJava {
  private static final Logger logger = Logger.getLogger(tempJava.class.getName());

  // --- File Names (must match your .csv files) ---
  private static final String FULL_MATRIX_FILE = "distance_matrix.csv";
  private static final String PHOTO_INDEXES_FILE = "photo_indexes.csv";
  private static final String OUTPUT_MISSIONS_FILE = "missions.csv"; // Output file

  // --- Solver Data Wrapper ---
  static class SolverData {
    public final long[][] solverMatrix; 
    public final Map<Integer, Integer> solverIndexToNodeIndex; 
    public final Map<Integer, Integer> nodeIndexToSolverIndex; 

    SolverData(long[][] matrix, Map<Integer, Integer> map, Map<Integer, Integer> reverseMap) {
      this.solverMatrix = matrix;
      this.solverIndexToNodeIndex = map;
      this.nodeIndexToSolverIndex = reverseMap;
    }
  }

  // --- Data Model for the Solver ---
  static class DataModel {
    public final long[][] distanceMatrix; 
    public final int depot = 0; 
    public final int vehicleNumber; 
    public final long droneBatteryCapacity = 37725L; // 37,725 feet

    public DataModel(long[][] solverMatrix) {
      this.distanceMatrix = solverMatrix;
      this.vehicleNumber = solverMatrix.length; 
    }
  }

  // --- Load Full Matrix ---
  static long[][] loadFullMatrixFromCsv(String filePath) throws IOException, NumberFormatException {
    logger.info("Loading full distance matrix from " + filePath + "...");
    List<long[]> rows = new ArrayList<>();
    try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
      String line;
      while ((line = br.readLine()) != null) {
        if (line.trim().isEmpty()) continue;
        String[] values = line.split(",");
        long[] row = new long[values.length];
        for (int i = 0; i < values.length; i++) {
          row[i] = (long) Double.parseDouble(values[i].trim());
        }
        rows.add(row);
      }
    }
    logger.info("Loaded matrix with " + rows.size() + " rows/cols.");
    return rows.toArray(new long[0][]);
  }

  // --- Load Photo Indices ---
  static List<Integer> loadIndexListFromCsv(String filePath) throws IOException, NumberFormatException {
    logger.info("Loading photo indices from " + filePath + "...");
    List<Integer> indices = new ArrayList<>();
    try (BufferedReader br = new BufferedReader(new FileReader(filePath))) {
      String line = br.readLine();
      if (line != null && !line.trim().isEmpty()) {
        String[] values = line.split(",");
        for (String val : values) {
          indices.add((int) Double.parseDouble(val.trim()));
        }
      }
    }
    logger.info("Loaded " + indices.size() + " photo indices to visit.");
    return indices;
  }

  // --- Build Solver Data ---
  static SolverData buildSolverData(long[][] fullMatrix, List<Integer> photoIndices) {
    logger.info("Building solver-specific matrix...");
    
    Map<Integer, Integer> solverIndexToNodeIndex = new HashMap<>();
    Map<Integer, Integer> nodeIndexToSolverIndex = new HashMap<>();

    solverIndexToNodeIndex.put(0, 0); // Depot
    nodeIndexToSolverIndex.put(0, 0);

    int solverIndex = 1;
    for (int nodeIndex : photoIndices) {
      if (nodeIndex >= 0 && nodeIndex < fullMatrix.length) {
        if (!nodeIndexToSolverIndex.containsKey(nodeIndex)) { 
          solverIndexToNodeIndex.put(solverIndex, nodeIndex);
          nodeIndexToSolverIndex.put(nodeIndex, solverIndex);
          solverIndex++;
        }
      } else {
        logger.warning("Skipping photo index " + nodeIndex + ": out of bounds.");
      }
    }

    int finalSolverSize = solverIndexToNodeIndex.size();
    long[][] solverMatrix = new long[finalSolverSize][finalSolverSize];
    
    for (int i = 0; i < finalSolverSize; i++) {
      for (int j = 0; j < finalSolverSize; j++) {
        int realIndexI = solverIndexToNodeIndex.get(i);
        int realIndexJ = solverIndexToNodeIndex.get(j);
        solverMatrix[i][j] = fullMatrix[realIndexI][realIndexJ];
      }
    }

    logger.info("New solver matrix built with size " + finalSolverSize + "x" + finalSolverSize);
    return new SolverData(solverMatrix, solverIndexToNodeIndex, nodeIndexToSolverIndex);
  }


  // --- Print Solution (to console) ---
  static void printSolution(
      DataModel data, RoutingModel routing, RoutingIndexManager manager, Assignment solution,
      Map<Integer, Integer> solverIndexToNodeIndex) {
    
    logger.info("Objective (Total Distance): " + solution.objectiveValue() + " feet");
    long totalDistance = 0;
    int missions = 0;

    for (int i = 0; i < data.vehicleNumber; ++i) {
      long index = routing.start(i);
      if (routing.isEnd(solution.value(routing.nextVar(index)))) {
        continue;
      }
      
      missions++;
      logger.info("--- Drone Mission " + missions + " ---");
      String route = "";
      long routeDistance = 0;

      while (!routing.isEnd(index)) {
        int solverNode = manager.indexToNode(index);
        int realNode = solverIndexToNodeIndex.get(solverNode);
        route += realNode + " -> ";
        long previousIndex = index;
        index = solution.value(routing.nextVar(index));
        routeDistance += routing.getArcCostForVehicle(previousIndex, index, i);
      }
      int finalSolverNode = manager.indexToNode(index);
      int finalRealNode = solverIndexToNodeIndex.get(finalSolverNode);
      route += finalRealNode;
      logger.info("Route: " + route);
      logger.info(String.format("Mission distance: %d feet", routeDistance));
      totalDistance += routeDistance;
    }
    logger.info("====================================");
    logger.info("Total missions: " + missions);
    logger.info(String.format("Total distance (all missions): %d feet", totalDistance));
  }
  
  // --- NEW: Save Solution (to file) ---
  /**
   * Saves the routes to a simple CSV file.
   * Each line is one mission, e.g.: "0,150,153,152,0"
   */
  static void saveSolutionToCsv(
      DataModel data, RoutingModel routing, RoutingIndexManager manager, Assignment solution,
      Map<Integer, Integer> solverIndexToNodeIndex, String filePath) {
    
    logger.info("Saving mission plan to " + filePath + "...");
    try (PrintWriter out = new PrintWriter(new FileWriter(filePath))) {
      for (int i = 0; i < data.vehicleNumber; ++i) {
        long index = routing.start(i);
        if (routing.isEnd(solution.value(routing.nextVar(index)))) {
          continue; // Skip empty routes
        }
        
        List<String> routeIndices = new ArrayList<>();
        while (!routing.isEnd(index)) {
          int solverNode = manager.indexToNode(index);
          int realNode = solverIndexToNodeIndex.get(solverNode);
          routeIndices.add(String.valueOf(realNode)); // Add real node index
          index = solution.value(routing.nextVar(index));
        }
        // Add the final depot node
        int finalSolverNode = manager.indexToNode(index);
        int finalRealNode = solverIndexToNodeIndex.get(finalSolverNode);
        routeIndices.add(String.valueOf(finalRealNode));
        
        // Write the mission as a single comma-separated line
        out.println(String.join(",", routeIndices));
      }
      logger.info("Successfully saved missions.");
    } catch (IOException e) {
      logger.severe("Could not save missions to file: " + e.getMessage());
    }
  }

  // --- Main Function ---
  public static void main(String[] args) throws Exception {
    Loader.loadNativeLibraries();

    // 2. Load Data
    long[][] fullDistanceMatrix;
    List<Integer> photoIndices;
    try {
      fullDistanceMatrix = loadFullMatrixFromCsv(FULL_MATRIX_FILE);
      photoIndices = loadIndexListFromCsv(PHOTO_INDEXES_FILE);
      if (photoIndices.isEmpty()) {
          logger.severe("No photo indices loaded. Check " + PHOTO_INDEXES_FILE);
          return;
      }
    } catch (IOException | NumberFormatException e) {
      logger.severe("Failed to load data files: " + e.getMessage());
      e.printStackTrace();
      return;
    }

    // 3. Build Solver Data
    SolverData solverData = buildSolverData(fullDistanceMatrix, photoIndices);

    // 4. Create Data Model
    final DataModel data = new DataModel(solverData.solverMatrix);

    // 5. Create Routing Manager
    RoutingIndexManager manager =
        new RoutingIndexManager(data.distanceMatrix.length, data.vehicleNumber, data.depot);

    // 6. Create Routing Model
    RoutingModel routing = new RoutingModel(manager);

    // 7. Cost Callback
    final int transitCallbackIndex =
        routing.registerTransitCallback((long fromIndex, long toIndex) -> {
          int fromNode = manager.indexToNode(fromIndex);
          int toNode = manager.indexToNode(toIndex);
          return data.distanceMatrix[fromNode][toNode];
        });
    routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

    // 8. Battery Constraint
    final int demandCallbackIndex =
        routing.registerTransitCallback((long fromIndex, long toIndex) -> {
          int fromNode = manager.indexToNode(fromIndex);
          int toNode = manager.indexToNode(toIndex);
          return data.distanceMatrix[fromNode][toNode];
        });
    long[] vehicleCapacities = new long[data.vehicleNumber];
    Arrays.fill(vehicleCapacities, data.droneBatteryCapacity);
    routing.addDimensionWithVehicleCapacity(
        demandCallbackIndex, 0, vehicleCapacities, true, "Distance");

    // 9. Search Parameters
    RoutingSearchParameters searchParameters =
        main.defaultRoutingSearchParameters()
            .toBuilder()
            .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
            .build();

    // 10. Solve
    logger.info("Starting solver...");
    Assignment solution = routing.solveWithParameters(searchParameters);

    // 11. Print and Save Solution
    if (solution != null && solution.objectiveValue() > 0) {
      logger.info("Solver found a solution.");
      // Print to console
      printSolution(data, routing, manager, solution, solverData.solverIndexToNodeIndex);
      // NEW: Save to file
      saveSolutionToCsv(data, routing, manager, solution, 
                        solverData.solverIndexToNodeIndex, OUTPUT_MISSIONS_FILE);
    } else {
      logger.warning("No solution found!");
    }
  }
}

