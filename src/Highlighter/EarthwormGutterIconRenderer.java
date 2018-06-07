package Highlighter;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.editor.markup.MarkupModel;
import com.intellij.openapi.editor.markup.RangeHighlighter;
import com.intellij.openapi.util.IconLoader;

import com.intellij.openapi.editor.markup.GutterIconRenderer;
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.Nullable;

import javax.swing.*;

/* This class currently isn't being used but could be utilized
    in the future if the plugin switches back to highlighters.
 */
public class EarthwormGutterIconRenderer extends GutterIconRenderer {
    private final Icon icon = IconLoader.getIcon("/images/worm.png");
    private Suggestion suggestion = null;
    private boolean enabled;
    private RangeHighlighter highlighter;
    private MarkupModel markupModel;

    public EarthwormGutterIconRenderer(Suggestion suggestion, RangeHighlighter highlighter, MarkupModel m) {
        this.suggestion = suggestion;
        this.enabled = true;
        this.highlighter = highlighter;
        this.markupModel = m;
    }

    public int getLine() {
        return suggestion.getLine();
    }

    public boolean isEnabled() {
        return this.enabled;
    }

    @Nullable
    public AnAction getClickAction() {
        System.out.println("Hi from the gutter!!");
        this.enabled = false;
        return null;
    }

    @NotNull
    @Override
    public Icon getIcon() {
        return icon;
    }

    @Override
    public int hashCode() {
        return getIcon().hashCode();
    }

    @Override
    @Nullable
    public String getTooltipText() {
        return this.suggestion.getText();
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        EarthwormGutterIconRenderer that = (EarthwormGutterIconRenderer) o;
        return icon.equals(that.getIcon());
    }
}
