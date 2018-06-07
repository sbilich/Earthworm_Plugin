package Highlighter;

import com.intellij.codeHighlighting.Pass;
import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer;
import com.intellij.codeInsight.daemon.GutterIconNavigationHandler;
import com.intellij.codeInsight.daemon.RelatedItemLineMarkerInfo;
import com.intellij.codeInsight.navigation.NavigationGutterIconBuilder;
import com.intellij.navigation.GotoRelatedItem;
import com.intellij.openapi.actionSystem.AnAction;
import com.intellij.openapi.actionSystem.AnActionEvent;
import com.intellij.openapi.actionSystem.CommonDataKeys;
import com.intellij.openapi.actionSystem.LangDataKeys;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.Editor;
import com.intellij.openapi.editor.impl.DocumentMarkupModel;
import com.intellij.openapi.editor.markup.GutterIconRenderer;
import com.intellij.openapi.editor.markup.MarkupModel;
import com.intellij.openapi.fileEditor.FileDocumentManager;
import com.intellij.openapi.module.Module;
import com.intellij.openapi.module.ModuleUtil;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.project.ProjectManager;
import com.intellij.openapi.projectRoots.Sdk;
import com.intellij.openapi.roots.ModuleRootManager;
import com.intellij.openapi.util.IconLoader;
import com.intellij.openapi.util.NotNullLazyValue;
import com.intellij.openapi.vfs.VirtualFile;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import com.intellij.util.Function;
import org.jetbrains.annotations.NotNull;

import javax.swing.*;
import java.awt.event.MouseEvent;
import java.util.*;

public class EarthwormHighlighterManager extends AnAction {
    private static final Icon icon = IconLoader.getIcon("/images/worm.png");
    private static ArrayList<Suggestion> suggestions = new ArrayList<>();
    private static Map<Suggestion, PsiElement> elm_lis = new HashMap<>();

    public void actionPerformed(AnActionEvent event) {
        final Editor editor = event.getData(CommonDataKeys.EDITOR);
        Document document = editor.getDocument();

        Project p = ProjectManager.getInstance().getOpenProjects()[0];
        MarkupModel markupModel = DocumentMarkupModel.forDocument(document, p, true);

        /* save any unsaved changes to the current document */
        FileDocumentManager.getInstance().saveDocument(document);

        /* Runs Earthworm */
        ArrayList<String> flags = new ArrayList<String>();
        VirtualFile file = FileDocumentManager.getInstance().getFile(document);

        Module module = ModuleUtil.findModuleForFile(file, p);
        ModuleRootManager moduleRootManager = ModuleRootManager.getInstance(module);
        Sdk SDK = moduleRootManager.getSdk();
        System.out.println("sdk is " + SDK);

        suggestions = EarthwormRunner.runEarthworm(flags, file.getPath(), "");
        elm_lis = new HashMap<>();

        /* removes all existing Highlighters */
        markupModel.removeAllHighlighters();

        PsiFile psi_file = event.getData(LangDataKeys.PSI_FILE);

        /* draw each suggestion */
        drawSuggestions(document, psi_file);

        /* Restart file to update line markers */
        DaemonCodeAnalyzer d = DaemonCodeAnalyzer.getInstance(p);
        d.restart(psi_file);
    }

    public static void runHighlighter(AnActionEvent event, String pythonVersion) {
        final Editor editor = event.getData(CommonDataKeys.EDITOR);
        Document document = editor.getDocument();

        Project p = ProjectManager.getInstance().getOpenProjects()[0];
        MarkupModel markupModel = DocumentMarkupModel.forDocument(document, p, true);

        /* save any unsaved changes to the current document */
        FileDocumentManager.getInstance().saveDocument(document);

        /* Runs Earthworm */
        ArrayList<String> flags = new ArrayList<String>();
        VirtualFile file = FileDocumentManager.getInstance().getFile(document);
        suggestions = EarthwormRunner.runEarthworm(flags, file.getPath(), pythonVersion);
        elm_lis = new HashMap<>();

        /* removes all existing Highlighters */
        markupModel.removeAllHighlighters();

        PsiFile psi_file = event.getData(LangDataKeys.PSI_FILE);

        /* draw each suggestion */
        drawSuggestions(document, psi_file);

        /* Restart file to update line markers */
        DaemonCodeAnalyzer d = DaemonCodeAnalyzer.getInstance(p);
        d.restart(psi_file);
    }

    private static void drawSuggestions(Document d, PsiFile p) {
        for (Suggestion s : suggestions) {

            int startOffset = d.getLineStartOffset(s.getLine());
            PsiElement elm = p.findElementAt(startOffset);

            if (d.getLineNumber(elm.getTextOffset()) != s.getLine()) {
                elm = elm.getNextSibling();
            }

            elm_lis.put(s, elm);
        }
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

    public static RelatedItemLineMarkerInfo getLineMarker(Suggestion s) {

        PsiElement elm = elm_lis.get(s);
        NotNullLazyValue<Collection<? extends GotoRelatedItem>> gotoTargets = new NotNullLazyValue<Collection<? extends GotoRelatedItem>>() {
            @NotNull
            @Override
            protected Collection<? extends GotoRelatedItem> compute() {
                return Collections.emptyList();
            }
        };

        return new RelatedItemLineMarkerInfo<PsiElement>(elm, elm.getTextRange(), icon, Pass.UPDATE_ALL,
                new Function<PsiElement, String>() {
                    @Override
                    public String fun(PsiElement element) {
                        return s.getText();
                    }
                },
                new GutterIconNavigationHandler<PsiElement>() {
                    @Override
                    public void navigate(MouseEvent e, PsiElement elt) {
                        elm_lis.remove(s);

                        /* Restart file to update line markers */
                        Project p = ProjectManager.getInstance().getOpenProjects()[0];
                        DaemonCodeAnalyzer d = DaemonCodeAnalyzer.getInstance(p);
                        PsiFile psi_file = elt.getContainingFile();
                        d.restart(psi_file);
                    }
                },
                GutterIconRenderer.Alignment.LEFT,
                gotoTargets
        );
    }

    public static Set<Suggestion> getSuggestions() {
        return elm_lis.keySet();
    }

    public static void clearSuggestions() {
        elm_lis.clear();
    }
}
