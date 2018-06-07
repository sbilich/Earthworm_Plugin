package Highlighter;

import com.intellij.codeInsight.daemon.DaemonCodeAnalyzer;
import com.intellij.codeInsight.daemon.RelatedItemLineMarkerInfo;
import com.intellij.codeInsight.daemon.RelatedItemLineMarkerProvider;
import com.intellij.openapi.editor.Document;
import com.intellij.openapi.editor.impl.DocumentMarkupModel;
import com.intellij.openapi.editor.markup.MarkupModel;
import com.intellij.openapi.project.Project;
import com.intellij.openapi.project.ProjectManager;
import com.intellij.openapi.util.Key;
import com.intellij.psi.PsiDocumentManager;
import com.intellij.psi.PsiElement;
import com.intellij.psi.PsiFile;
import org.jetbrains.annotations.NotNull;

import java.util.Collection;
import java.util.Iterator;
import java.util.Set;

public class EarthwormLineMarkerProvider extends RelatedItemLineMarkerProvider {
    static final Key<RelatedItemLineMarkerInfo> EARTHWORM_MARKER = new Key<>("Earthworm.Linemarker");
    static long cachedFile = -1;

    @Override
    protected void collectNavigationMarkers(@NotNull PsiElement element,
                                            Collection<? super RelatedItemLineMarkerInfo> result) {

        Set<Suggestion> lines = EarthwormHighlighterManager.getSuggestions();

        Document doc = PsiDocumentManager.getInstance(element.getProject()).getDocument(element.getContainingFile());
        Project p = element.getProject();

        long cur = doc.getModificationStamp();

        if (cachedFile != -1 && cur != cachedFile) {
            EarthwormHighlighterManager.clearSuggestions();

            /* Restart file to update line markers */
            DaemonCodeAnalyzer d = DaemonCodeAnalyzer.getInstance(p);
            PsiFile psi_file = element.getContainingFile();
            d.restart(psi_file);
        }

        for (Suggestion s : lines) {
            RelatedItemLineMarkerInfo r = EarthwormHighlighterManager.getLineMarker(s);
            element.putUserData(EARTHWORM_MARKER, r);

            if (!containsLineMarker(result, r)) {
                result.add(r);
            }
        }

        cachedFile = cur;
    }

    private static boolean containsLineMarker(Collection<? super RelatedItemLineMarkerInfo> c, RelatedItemLineMarkerInfo r) {
        Iterator<? super RelatedItemLineMarkerInfo> iter = c.iterator();
        while (iter.hasNext()) {
            Object item = iter.next();
            if (item instanceof RelatedItemLineMarkerInfo) {
                RelatedItemLineMarkerInfo marker = (RelatedItemLineMarkerInfo) item;

                /* check element */
                if (!marker.getElement().equals(r.getElement())) {
                    continue;
                }

                /* check icon */
                if (!marker.canMergeWith(r)) {
                    continue;
                }

                /* check updatePass */
                if (marker.updatePass != r.updatePass) {
                    continue;
                }

                /* check toolTip provider */
                if (!marker.getLineMarkerTooltip().equals(r.getLineMarkerTooltip())) {
                    continue;
                }

                /* |r| and |marker| refer to the same marker */
                return true;
            }
        }

        return false;
    }
}