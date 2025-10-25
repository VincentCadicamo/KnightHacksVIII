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
     * Loads a binary file (created by convert_npy_to_bin.py, using int16)
     * as a 2D short array. This is the most memory-efficient method.
     *
     * @param path Path to the .bin file, relative to the repo root.
     * @return A 2D short array (short[][]).
     * @throws Exception If the file cannot be read.
     */
    public static short[][] loadBinAs2DShortArray(String path) throws Exception {
        Path repoRoot = repoRootFromClasses();
        Path binPath = repoRoot.resolve(path);

        try (InputStream is = new FileInputStream(binPath.toFile());
             DataInputStream dis = new DataInputStream(new BufferedInputStream(is))) {
            
            // 1. Read rows (4 bytes, little-endian)
            byte[] intBytes = new byte[4];
            dis.readFully(intBytes);
            int rows = ByteBuffer.wrap(intBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            // 2. Read cols (4 bytes, little-endian)
            dis.readFully(intBytes);
            int cols = ByteBuffer.wrap(intBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            if (rows <= 0 || cols <= 0) {
                throw new IOException("Invalid matrix dimensions read from file: " + rows + "x" + cols);
            }
            
            // --- KEY CHANGE ---
            // Create a short[][] array (2 bytes per element)
            short[][] matrix = new short[rows][cols];
            
            // 3. Read matrix data (2 bytes per short, little-endian)
            byte[] shortBytes = new byte[2]; // Read 2 bytes at a time
            for (int i = 0; i < rows; i++) {
                for (int j = 0; j < cols; j++) {
                    dis.readFully(shortBytes);
                    // --- KEY CHANGE ---
                    // Convert bytes to a short
                    matrix[i][j] = ByteBuffer.wrap(shortBytes).order(ByteOrder.LITTLE_ENDIAN).getShort();
                }
            }
            
            return matrix;
        }
    }

    /**
     * Loads a .npy file as a 2D double array (JSON method).
     * Only use for small test files.
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
    
    // ... (isWindows and repoRootFromClasses are unchanged)
    
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

