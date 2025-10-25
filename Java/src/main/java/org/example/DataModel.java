package org.example;

public class DataModel {
    public double[][] distanceMatrix;
    public int vehicleNumber = 1;
    public int depot = 0;

    public DataModel(double[][] distanceMatrix) {
        this.distanceMatrix = distanceMatrix;
    }
}
