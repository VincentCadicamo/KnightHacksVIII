package org.example;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingDimension;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;
import com.google.ortools.constraintsolver.main;
import java.util.logging.Logger;

public class TspCities {
    private static final Logger logger = Logger.getLogger(TspCities.class.getName());

    static class DataModel {
        // --- KEY CHANGE ---
        // Use short[][] (2-byte int) instead of double[][] (8-byte)
        public final short[][] distanceMatrix; 
        
        public final int vehicleNumber;
        public final long batteryLimit; 
        public final int depot = 0;

        // --- KEY CHANGE ---
        // Constructor now accepts a short[][]
        public DataModel(short[][] distanceMatrix) {
            this.distanceMatrix = distanceMatrix;
            this.vehicleNumber = distanceMatrix.length; 
            
            // Set your drone's battery limit here
            this.batteryLimit = 50000; 
        }
    }

    /// @brief Print the solution. (Unchanged)
    static void printSolution(
            DataModel data, RoutingModel routing, RoutingIndexManager manager, Assignment solution) {
        
        RoutingDimension distanceDimension = routing.getMutableDimension("Distance");
        long totalDistance = 0;
        
        for (int i = 0; i < data.vehicleNumber; ++i) {
            long index = routing.start(i);
            
            if (routing.isEnd(solution.value(routing.nextVar(index)))) {
                continue;
            }

            logger.info("Drone Trip " + i + ":");
            String route = "";
            long routeDistance = 0;

            while (!routing.isEnd(index)) {
                long nodeDistance = solution.min(distanceDimension.cumulVar(index));
                
                route += manager.indexToNode(index) + " (Dist:" + nodeDistance + ") -> ";
                
                long previousIndex = index;
                index = solution.value(routing.nextVar(index));
                routeDistance += routing.getArcCostForVehicle(previousIndex, index, i);
            }
            
            long endNodeDistance = solution.min(distanceDimension.cumulVar(index));
            route += manager.indexToNode(index) + " (Dist:" + endNodeDistance + ")";
            
            logger.info(route);
            logger.info("Distance for this trip: " + routeDistance);
            
            totalDistance += routeDistance;
        }
        logger.info("--------------------");
        logger.info("Total distance of all trips: " + totalDistance);
        logger.info("Solver objective (min total distance): " + solution.objectiveValue());
    }

    public static void main(String[] args) throws Exception {
        Loader.loadNativeLibraries();

        // --- KEY CHANGE ---
        // Call the new helper method and load the new _int16.bin file
        short[][] matrix = PythonNumpyHelper.loadBinAs2DShortArray("data/distance_matrix_int16.bin");
        
        // (You can still use this line for your small test file)
        // double[][] matrix = PythonNumpyHelper.loadNpyAs2DArray("data/test_matrix.npy");

        // --- KEY CHANGE ---
        // Pass the short[][] matrix to the DataModel
        final DataModel data = new DataModel(matrix);

        // Create Routing Index Manager (Unchanged)
        RoutingIndexManager manager =
                new RoutingIndexManager(data.distanceMatrix.length, data.vehicleNumber, data.depot);

        // Create Routing Model. (Unchanged)
        RoutingModel routing = new RoutingModel(manager);

        // Create and register a transit callback.
        final int transitCallbackIndex =
                routing.registerTransitCallback((long fromIndex, long toIndex) -> {
                    // Convert from routing variable Index to user NodeIndex.
                    int fromNode = manager.indexToNode(fromIndex);
                    int toNode = manager.indexToNode(toIndex);
                    
                    // --- KEY CHANGE (Implicit) ---
                    // data.distanceMatrix[fromNode][toNode] is now a 'short',
                    // which casts perfectly to a 'long' for the solver.
                    // No code change is needed here!
                    return data.distanceMatrix[fromNode][toNode];
                });

        // Define cost of each arc. (Unchanged)
        routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

        // Add the distance constraint (Unchanged)
        routing.addDimension(
                transitCallbackIndex,
                0, 
                data.batteryLimit,
                true,
                "Distance");

        // Setting first solution heuristic. (Unchanged)
        RoutingSearchParameters searchParameters =
                main.defaultRoutingSearchParameters()
                        .toBuilder()
                        .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
                        .build();

        // Solve the problem.
        logger.info("Solver started... (Loading from int16 file)");
        Assignment solution = routing.solveWithParameters(searchParameters);

        // Print solution. (Unchanged)
        if (solution != null) {
            logger.info("Solver found a solution.");
            printSolution(data, routing, manager, solution);
        } else {
            logger.warning("No solution found !");
        }
    }
}

