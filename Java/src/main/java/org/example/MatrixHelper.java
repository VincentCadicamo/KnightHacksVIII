package org.example;

import com.google.gson.Gson;

import java.io.*;
import java.net.URI;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;

public class MatrixHelper {
    private static final Gson GSON = new Gson();

    public static long[][] roundMatrix(float[][] floatMatrix) {
        if (floatMatrix == null) {
            return null;
        }

        long[][] longMatrix = new long[floatMatrix.length][];

        for (int i = 0; i < floatMatrix.length; i++) {
            if (floatMatrix[i] != null) {
                longMatrix[i] = new long[floatMatrix[i].length];
                for (int j = 0; j < floatMatrix[i].length; j++) {
                    longMatrix[i][j] = Math.round(floatMatrix[i][j]);
                }
            }
        }
        return longMatrix;
    }

    public static double[][] loadBinAs2DArray(String path) throws Exception {
        Path repoRoot = repoRootFromClasses();
        Path binPath = repoRoot.resolve(path);

        try (InputStream is = new FileInputStream(binPath.toFile());
             DataInputStream dis = new DataInputStream(new BufferedInputStream(is))) {

            byte[] rowBytes = new byte[4];
            dis.readFully(rowBytes);
            int rows = ByteBuffer.wrap(rowBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            byte[] colBytes = new byte[4];
            dis.readFully(colBytes);
            int cols = ByteBuffer.wrap(colBytes).order(ByteOrder.LITTLE_ENDIAN).getInt();

            if (rows <= 0 || cols <= 0) {
                throw new IOException("Invalid matrix dimensions read from file: " + rows + "x" + cols);
            }

            double[][] matrix = new double[rows][cols];

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

    public static float[][] loadNpyAs2DArray(String path) throws Exception {
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

        return GSON.fromJson(output.toString(), float[][].class);
    }

    private static boolean isWindows() {
        return System.getProperty("os.name").toLowerCase().contains("win");
    }

    static Path repoRootFromClasses() {
        try {
            URI loc = MatrixHelper.class.getProtectionDomain().getCodeSource().getLocation().toURI();
            Path classes = Paths.get(loc).toAbsolutePath();
            Path javaModule = classes.getParent().getParent();
            Path repo = javaModule.getParent();
            return repo.normalize();
        } catch (Exception e) {
            return Paths.get(System.getProperty("user.dir")).toAbsolutePath().normalize();
        }
    }
}
