package Highlighter;

import java.io.BufferedReader;
import java.io.IOException;

public class EarthwormParser {
    public static Suggestion parse(String str, BufferedReader reader) throws IOException {
        Suggestion s = null;

        /* matches one-line suggestion */
        if (str.matches("\tline \\d+: (.*?)")) {
            String[] tokens = str.split(" ");
            String t = tokens[1];
            String line = t.substring(0, t.length()-1);
            int num = Integer.parseInt(line);

            String[] parts = str.split(":");
            s = new Suggestion(num-1, parts[1]);
        } else if (str.matches("line \\d+-\\d+ [(](.*)[)]:")) { /* matches multi-line suggestion */
            String[] tokens = str.split(" ");
            String[] range = (tokens[1]).split("-");
            int line = Integer.parseInt(range[0]);

            String text = "Refactor lines " + line + "-" + range[1] + " into new function: \n";
            String readLine =  reader.readLine();

            while (!readLine.equals("")) {
                text += readLine + "\n";
                readLine = reader.readLine();
            }

            s = new Suggestion(line-1, text);
        }

        return s;
    }


}
