package com.lbslabs.remote;

import android.content.Context;
import android.text.InputType;
import android.view.inputmethod.EditorInfo;
import android.view.inputmethod.InputConnection;
import android.webkit.WebView;

/**
 * WebView con tastiera "da terminale": niente suggerimenti né composizione del testo, così la tastiera
 * a schermo invia i tasti uno per uno e il computer remoto riceve esattamente ciò che si digita.
 */
public class LbsWebView extends WebView {
    public LbsWebView(Context context) {
        super(context);
    }

    @Override
    public InputConnection onCreateInputConnection(EditorInfo outAttrs) {
        InputConnection ic = super.onCreateInputConnection(outAttrs);
        if (outAttrs != null) {
            outAttrs.inputType = InputType.TYPE_CLASS_TEXT
                    | InputType.TYPE_TEXT_VARIATION_VISIBLE_PASSWORD
                    | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS;
            outAttrs.imeOptions |= EditorInfo.IME_FLAG_NO_FULLSCREEN | EditorInfo.IME_FLAG_NO_EXTRACT_UI;
        }
        return ic;
    }
}
