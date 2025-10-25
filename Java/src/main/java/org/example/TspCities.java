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

/**
 * Solves the Vehicle Routing Problem (VRP) with distance constraints.
 * This can be used to model a drone with a limited battery,
 * which must return to a depot to charge.
 */
public class TspCities {
    private static final Logger logger = Logger.getLogger(TspCities.class.getName());

    static class DataModel {
        public final double[][] distanceMatrix;
        
        // 1. VEHICLE_NUMBER: This is the *maximum number of trips* the drone can make.
        //    Set this to a high number (e.g., the number of locations) to ensure all are visited.
        public final int vehicleNumber;
        
        // 2. BATTERY_LIMIT: This is the maximum distance a drone can travel in a *single trip*
        //    before it *must* return to the depot.
        //    !!! YOU MUST CHANGE THIS VALUE to your drone's actual range.
        public final long batteryLimit; // Example: 5000 units
        
        public final int depot = 0; // The depot is node 0 (the charging station)

        public DataModel(double[][] distanceMatrix) {
            this.distanceMatrix = distanceMatrix;
            
            // Set the max number of trips to be the number of locations.
            // This is a safe upper bound, meaning the solver can create
            // up to this many trips if needed.
            this.vehicleNumber = distanceMatrix.length; 
            
            // !!! IMPORTANT !!!
            // Set your drone's battery limit here. I'm using 50000 as a placeholder.
            // The unit (e.g., meters, feet) must match your distance_matrix.
            this.batteryLimit = 50000; 
        }
    }

    /// @brief Print the solution.
    static void printSolution(
            DataModel data, RoutingModel routing, RoutingIndexManager manager, Assignment solution) {
        
        // Get the "Distance" dimension we created in main()
        RoutingDimension distanceDimension = routing.getMutableDimension("Distance");
        long totalDistance = 0;
        
        // Loop through all "vehicles" (trips)
        for (int i = 0; i < data.vehicleNumber; ++i) {
            long index = routing.start(i);
            
            // Skip this trip if it's not used (i.e., it just goes depot -> depot)
            if (routing.isEnd(solution.value(routing.nextVar(index)))) {
                continue;
            }

            logger.info("Drone Trip " + i + ":");
            String route = "";
            long routeDistance = 0;

            while (!routing.isEnd(index)) {
                // Get the distance variable for this node
                long nodeDistance = solution.min(distanceDimension.cumulVar(index));
                
                route += manager.indexToNode(index) + " (Dist:" + nodeDistance + ") -> ";
                
                long previousIndex = index;
                index = solution.value(routing.nextVar(index));
                routeDistance += routing.getArcCostForVehicle(previousIndex, index, i);
            }
            
            // Add the final depot node
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

        // 3. Load the *new binary file*. This will be very fast.
        double[][] matrix = PythonNumpyHelper.loadBinAs2DArray("data/distance_matrix.bin");
        
        // (You can switch back to this line to run your small test)
        // double[][] matrix = PythonNumpyHelper.loadNpyAs2DArray("data/test_matrix.npy");

        // 4. Instantiate the data problem, passing the loaded matrix.
        final DataModel data = new DataModel(matrix);

        // Create Routing Index Manager
        // This now manages all nodes, all "vehicles" (trips), and the depot.
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
                    // Cast the double to a long for OR-Tools
                    return (long) data.distanceMatrix[fromNode][toNode];
                });

        // Define cost of each arc.
        routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

        // 5. ADD THE BATTERY_LIMIT (Distance Constraint)
        // This is the magic part. We add a "dimension" to track the
        // distance of each trip.
        routing.addDimension(
                transitCallbackIndex,
                0, // 0 "slack" (no waiting time)
                data.batteryLimit, // The maximum distance for one trip
                true, // Start counting distance at 0
                "Distance"); // Name for this dimension

        // Setting first solution heuristic.
        RoutingSearchParameters searchParameters =
                main.defaultRoutingSearchParameters()
                        .toBuilder()
                        .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
                        // Add a time limit, as this is a very hard problem
                        // .setLocalSearchMetaheuristic(LocalSearchMetaheuristic.Value.GUIDED_LOCAL_SEARCH)
                        // .setTimeLimit(Duration.newBuilder().setSeconds(30).build())
                        .build();

        // Solve the problem.
        logger.info("Solver started... (this may take a few minutes for 2600 nodes)");
        Assignment solution = routing.solveWithParameters(searchParameters);

        // 6. Print the solution.
        if (solution != null) {
            logger.info("Solver found a solution.");
            printSolution(data, routing, manager, solution);
        } else {
            logger.warning("No solution found !");
        }
    }
}

