package org.example;

import java.io.*;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import com.google.gson.Gson;

public final class PythonNumpyHelper {
    private static final Gson GSON = new Gson();

    private PythonNumpyHelper() {}

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
