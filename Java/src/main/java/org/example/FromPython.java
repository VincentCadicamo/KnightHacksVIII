package org.example;


import java.nio.file.Path;
import java.nio.file.Paths;

public class FromPython {
    public static void main(String[] args) throws Exception {

        //Example usage of the hepler i made to read the npym files using my PythonNumpyHelper
        float[][] arr = PythonNumpyHelper.loadNpyAs2DArray("data/distance_matrix.npy");
        System.out.println("Rows: " + arr.length + ", Cols: " + arr[0].length);
        System.out.println("First row: " + java.util.Arrays.toString(arr[0]));
        System.out.println("Second row: " + java.util.Arrays.toString(arr[1]));
    }
}