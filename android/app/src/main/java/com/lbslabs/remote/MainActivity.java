package com.lbslabs.remote;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Context;
import android.content.SharedPreferences;
import android.content.pm.PackageInfo;
import android.graphics.Color;
import android.net.Uri;
import android.net.wifi.WifiManager;
import android.os.Build;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.view.WindowInsets;
import android.view.WindowInsetsController;
import android.webkit.JavascriptInterface;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.webkit.WebViewAssetLoader;

import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Finestra dell'app Android: mostra l'interfaccia web (assets/www, la stessa del desktop) e collega
 * la pagina al codice di rete (AppCore). I frame arrivano con la stessa richiesta "frame?after=N" del
 * desktop, servita direttamente da qui senza passare da un server.
 */
public class MainActivity extends Activity {
    private static final String TAG = "LBS";
    private static final String ASSET_HOST = "appassets.androidplatform.net";

    private LbsWebView web;
    private AppCore core;
    private WebViewAssetLoader assetLoader;
    private WifiManager.MulticastLock multicastLock;
    // una sola coda: l'ordine degli input (pressione/rilascio) deve essere rispettato
    private final ExecutorService calls = Executors.newSingleThreadExecutor();

    @SuppressLint({"SetJavaScriptEnabled", "AddJavascriptInterface"})
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        web = new LbsWebView(this);
        setContentView(web);

        WebSettings ws = web.getSettings();
        ws.setJavaScriptEnabled(true);
        ws.setAllowFileAccess(false);
        ws.setAllowContentAccess(false);
        ws.setSupportZoom(false);
        ws.setBuiltInZoomControls(false);
        ws.setTextZoom(100);
        ws.setCacheMode(WebSettings.LOAD_NO_CACHE);
        web.setBackgroundColor(getResources().getColor(R.color.bg_window, getTheme()));
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);
        web.setLongClickable(false);
        web.setHapticFeedbackEnabled(false);

        assetLoader = new WebViewAssetLoader.Builder()
                .setDomain(ASSET_HOST)
                .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
                .build();
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                if (ASSET_HOST.equals(uri.getHost()) && "/assets/www/frame".equals(uri.getPath())) {
                    return frameResponse(uri);
                }
                return assetLoader.shouldInterceptRequest(uri);
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return !ASSET_HOST.equals(request.getUrl().getHost());   // la pagina non esce mai dall'app
            }
        });

        String version = "0";
        try {
            PackageInfo pi = getPackageManager().getPackageInfo(getPackageName(), 0);
            version = pi.versionName;
        } catch (Exception ignored) {
            // versione non leggibile: solo informativa
        }
        final SharedPreferences prefs = getSharedPreferences("lbs", MODE_PRIVATE);
        core = new AppCore(new AppCore.Host() {
            @Override
            public void emit(String eventJson) {
                web.post(() -> web.evaluateJavascript("window.LBS&&window.LBS.onEvent(" + eventJson + ")", null));
            }

            @Override
            public void setFullscreen(boolean on) {
                runOnUiThread(() -> applyFullscreen(on));
            }

            @Override
            public void log(String message) {
                Log.i(TAG, message);
            }
        }, new AppCore.Store() {
            @Override
            public String load() {
                return prefs.getString("config", "");
            }

            @Override
            public void save(String json) {
                prefs.edit().putString("config", json).apply();
            }
        }, version, "android", getIntent().getStringExtra("connect"));
        web.addJavascriptInterface(new Bridge(), "LBSAndroid");

        WifiManager wm = (WifiManager) getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        if (wm != null) {
            multicastLock = wm.createMulticastLock("lbs-discovery");
            multicastLock.setReferenceCounted(false);
            multicastLock.acquire();                    // per ricevere gli annunci broadcast degli agenti
        }

        web.loadUrl("https://" + ASSET_HOST + "/assets/www/index.html");
    }

    /** Chiamate JavaScript → Java. Le risposte tornano con LBSNative.resolve(id, json). */
    private final class Bridge {
        @JavascriptInterface
        public void call(final int id, final String method, final String args) {
            calls.execute(() -> {
                String result = core.call(method, args);
                final String js = "window.LBSNative&&window.LBSNative.resolve(" + id + "," + JSONObject.quote(result) + ")";
                web.post(() -> web.evaluateJavascript(js, null));
            });
        }
    }

    /** Risposta alla richiesta "frame?after=N": attende un frame più recente (fino a 1 s). */
    private WebResourceResponse frameResponse(Uri uri) {
        NetSession s = core == null ? null : core.session();
        Map<String, String> headers = new HashMap<>();
        headers.put("Cache-Control", "no-store");
        if (s == null) {
            return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", headers,
                    new ByteArrayInputStream(new byte[0]));
        }
        long after = 0;
        try {
            after = Long.parseLong(uri.getQueryParameter("after"));
        } catch (Exception ignored) {
            // si parte da zero
        }
        if (after > s.currentSeq()) after = 0;          // sessione nuova
        Object[] r = s.waitFrame(after, 1000);
        long seq = (Long) r[0];
        byte[] jpeg = (byte[]) r[1];
        if (jpeg == null || seq <= after) {
            return new WebResourceResponse("image/jpeg", null, 204, "No Content", headers,
                    new ByteArrayInputStream(new byte[0]));
        }
        headers.put("X-Seq", Long.toString(seq));
        return new WebResourceResponse("image/jpeg", null, 200, "OK", headers, new ByteArrayInputStream(jpeg));
    }

    private void applyFullscreen(boolean on) {
        if (Build.VERSION.SDK_INT >= 30) {
            WindowInsetsController c = getWindow().getInsetsController();
            if (c == null) return;
            if (on) {
                c.hide(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
                c.setSystemBarsBehavior(WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
            } else {
                c.show(WindowInsets.Type.statusBars() | WindowInsets.Type.navigationBars());
            }
        } else {
            View d = getWindow().getDecorView();
            d.setSystemUiVisibility(on
                    ? View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    : View.SYSTEM_UI_FLAG_VISIBLE);
        }
    }

    @Override
    public void onBackPressed() {
        // Durante il controllo remoto "Indietro" non disconnette per sbaglio: esce solo dallo schermo intero.
        web.evaluateJavascript(
                "(function(){return typeof S==='undefined'?'connect':(S.mode==='remote'?(S.fullscreen?'fs':'remote'):'connect')})()",
                value -> {
                    if ("\"fs\"".equals(value)) {
                        web.evaluateJavascript("setFullscreen(false)", null);
                    } else if (!"\"remote\"".equals(value)) {
                        MainActivity.super.onBackPressed();
                    }
                });
    }

    @Override
    protected void onPause() {
        web.onPause();
        super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        web.onResume();
    }

    @Override
    protected void onDestroy() {
        if (core != null) core.shutdown();
        if (multicastLock != null && multicastLock.isHeld()) multicastLock.release();
        calls.shutdownNow();
        web.destroy();
        super.onDestroy();
    }
}
