package org.example;

import java.io.*;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import com.google.gson.Gson;

public final class PythonNumpyHelper {
    private static final Gson GSON = new Gson();

    private PythonNumpyHelper() {}

    /**
     * Loads a binary file (created by convert_npy_to_bin.py) as a 2D double array.
     * This is much more efficient for large files than the JSON method.
     *
     * @param path Path to the .bin file, relative to the repo root.
     * @return A 2D double array (double[][]).
     * @throws Exception If the file cannot be read.
     */
    public static double[][] loadBinAs2DArray(String path) throws Exception {
        Path repoRoot = repoRootFromClasses();
        Path binPath = repoRoot.resolve(path);

        try (InputStream is = new FileInputStream(binPath.toFile());
             DataInputStream dis = new DataInputStream(new BufferedInputStream(is))) {
            
            // The Python script writes integers in 'little-endian' format.
            // Java's DataInputStream reads in 'big-endian' by default.
            // We must read the bytes and convert them.

            // 1. Read the number of rows (4 bytes, little-endian)
            byte[] rowBytes = new byte[4];
            dis.readFully(rowBytes);
            int rows = ByteBuffer.wrap(rowBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            // 2. Read the number of columns (4 bytes, little-endian)
            byte[] colBytes = new byte[4];
            dis.readFully(colBytes);
            int cols = ByteBuffer.wrap(colBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            if (rows <= 0 || cols <= 0) {
                throw new IOException("Invalid matrix dimensions read from file: " + rows + "x" + cols);
            }
            
            double[][] matrix = new double[rows][cols];
            
            // 3. Read the matrix data (8 bytes per double, little-endian)
            byte[] doubleBytes = new byte[8];
            for (int i = 0; i < rows; i++) {
                for (int j = 0; j < cols; j++) {
                    dis.readFully(doubleBytes);
                    matrix[i][j] = ByteBuffer.wrap(doubleBytes).order(ByteOrder.LITTLE_ENDIAN).getDouble();
                }
            }
            
            return matrix;
        }
    }


    /**
     * Loads a .npy file as a 2D double array by shelling out to a Python script (JSON method).
     * This is simple, but very slow and memory-intensive. Only use for small test files.
     *
     * @param path Path to the .npy file, relative to the repo root.
     * @return A 2D double array (double[][]).
     * @throws Exception If the Python script fails or the output cannot be parsed.
     */
    public static double[][] loadNpyAs2DArray(String path) throws Exception {
        Path repoRoot = repoRootFromClasses();
        Path pythonDir = repoRoot.resolve("Python");

        Path venvPy = isWindows()
                ? pythonDir.resolve(".venv/Scripts/python.exe")
                : pythonDir.resolve(".venv/bin/python");

        String python = Files.isRegularFile(venvPy)
                ? venvPy.toString()
                : (isWindows() ? "python.exe" : "python3");

        Path script = pythonDir.resolve("readData.py");

        Path npyPath = repoRoot.resolve(path);

        List<String> cmd = List.of(python, "-u", script.toString(), npyPath.toString());
        ProcessBuilder pb = new ProcessBuilder(cmd)
                .directory(pythonDir.toFile())
                .redirectErrorStream(true);

        pb.environment().putIfAbsent("PYTHONUNBUFFERED", "1");

        Process p = pb.start();

        // Warning: This can OOM if the JSON string is too large.
        StringBuilder output = new StringBuilder();
        try (BufferedReader r = new BufferedReader(
                new InputStreamReader(p.getInputStream(), StandardCharsets.UTF_8))) {
            String line;
            while ((line = r.readLine()) != null) {
                output.append(line);
            }
        }

        int code = p.waitFor();
        if (code != 0)
            throw new RuntimeException("Python exited with code " + code + "\nOutput:\n" + output);

        return GSON.fromJson(output.toString(), double[][].class);
    }

    private static boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    private static Path repoRootFromClasses() {
        try {
            URI loc = PythonNumpyHelper.class.getProtectionDomain().getCodeSource().getLocation().toURI();
            Path classes = Paths.get(loc).toAbsolutePath();
            Path javaModule = classes.getParent().getParent();
            Path repo = javaModule.getParent();
            return repo.normalize();
        } catch (Exception e) {
            return Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        }
    }
}

