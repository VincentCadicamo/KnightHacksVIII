package org.example;
import java.io.BufferedReader;
import java.io.FileReader;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;


public class convertToCoor {

 

    public static void main(String[] args) {
        

        ArrayList<float[]> points = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader("points_lat_long.csv"))) {
                String line;
                while ((line = br.readLine()) != null) {
                String[] t = line.split(",");
                float lon = Float.parseFloat(t[0]);
                float lat = Float.parseFloat(t[1]);
                points.add(new float[]{lon, lat});
            }
        }catch (IOException e) {
            System.err.println("Error reading CSV file: " + e.getMessage());
        }

        String logLine = "0 (Dist:0) -> 1820 (Dist:111) -> 1867 (Dist:114) -> 1822 (Dist:153) -> 1872 (Dist:156)";

        // --- Extract only the indices ---
        List<Integer> indices = new ArrayList<>();
        for (String chunk : logLine.split("->")) {
            chunk = chunk.trim();
            Matcher m = Pattern.compile("^(\\d+)").matcher(chunk);
            if (m.find()) {
                indices.add(Integer.parseInt(m.group(1)));
            }
        }

         for (int idx : indices) {
            if (idx >= 0 && idx < points.size()) {
                float[] coord = points.get(idx);
                
            } 
        }

        
       

        
    }

    
}
