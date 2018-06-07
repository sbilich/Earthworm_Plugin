package Highlighter;

public class Suggestion {
    private int line;
    private String text;

    public Suggestion(int line, String text) {
        this.line = line;
        this.text = text;
    }

    public int getLine() {
        return line;
    }

    public String getText() {
        return text;
    }

    @Override
    public boolean equals(Object obj) {
        System.out.println("here");
        if (this == obj) {
            return true;
        }

        if (!(obj instanceof Suggestion)) {
            return false;
        }

        Suggestion s = (Suggestion) obj;
        return s.getText().equals(this.text) && s.getLine() == this.line;
    }
}
