package Highlighter;

import java.io.*;
import java.util.ArrayList;
import java.util.Map;

public class EarthwormRunner {

    /*
     * Receives |flags| which are input into running the Earthworm process.
     * Returns the list of suggestions for the file.
     */
    public static ArrayList<Suggestion> runEarthworm(ArrayList<String> flags, String file_path, String version) {
        File env_file = new File(EarthwormRunner.class.getClassLoader().getResource("/thesis/decomposer.sh").getPath());

        ProcessBuilder pb =
                new ProcessBuilder("python"+version, "-m", "src.decomposer", file_path);

        Map workerEnv = pb.environment();
        workerEnv.put("PYTHONPATH", env_file.getParent());

        ArrayList<Suggestion> suggestions = new ArrayList<Suggestion>();

        try {
            Process p = pb.start();
            BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
            String readline;
            while ((readline = reader.readLine()) != null) {
                Suggestion s = EarthwormParser.parse(readline, reader);
                if (s != null) {
                    suggestions.add(s);
                }
            }
        } catch (IOException e) {
            System.out.println("Earthworm unable to run: " + e);
        }

        return suggestions;
    }
}