package Highlighter;

import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.Editor;

public class EarthwormPython3Runner extends AnAction {

    public void actionPerformed(AnActionEvent event) {
        EarthwormHighlighterManager.runHighlighter(event, "3");
    }

    /* disable Earthworm until BOTH editor and document are available */
    public void update(AnActionEvent e) {
        e.getPresentation().setVisible(false);
        e.getPresentation().setEnabled(false);

        final Editor editor = e.getData(CommonDataKeys.EDITOR);
        if (editor != null) {
            Document document = editor.getDocument();
            if (document != null) {
                e.getPresentation().setVisible(true);
                e.getPresentation().setEnabled(true);
            }
        }
    }
}
