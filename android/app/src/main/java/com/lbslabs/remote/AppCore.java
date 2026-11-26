package com.lbslabs.remote;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

/**
 * Logica dell'app per tablet, indipendente da Android: stesso "api" che sul desktop offre viewer.py
 * (get_state, connect, disconnect, send_input, get_servers, set_fullscreen, set_capture).
 * Le risposte sono stringhe JSON; gli eventi verso l'interfaccia passano da Host.emit().
 */
public final class AppCore implements NetSession.Listener {
    public interface Host {
        /** Invia all'interfaccia un evento (JSON), da chiamare come LBS.onEvent(evento). */
        void emit(String eventJson);

        void setFullscreen(boolean on);

        void log(String message);
    }

    public interface Store {
        String load();

        void save(String json);
    }

    private final Host host;
    private final Store store;
    private final String version;
    private final String platform;
    private final String connectNow;
    private final JSONObject cfg;
    private final Discovery discovery;
    private final ScheduledExecutorService stats = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "stats");
        t.setDaemon(true);
        return t;
    });

    private volatile NetSession session;
    private String connectText = "";
    private Set<String> localIps = new HashSet<>();
    private long localIpsAt = 0;
    private boolean firstFrameLogged = false;

    public AppCore(Host host, Store store, String version, String platform, String connectNow) {
        this.host = host;
        this.store = store;
        this.version = version;
        this.platform = platform;
        this.connectNow = connectNow == null ? "" : connectNow;
        this.cfg = loadConfig();
        int discoveryPort = cfg.optInt("discovery_port", Protocol.DISCOVERY_PORT);
        this.discovery = new Discovery(discoveryPort);
        this.discovery.start();
        stats.scheduleWithFixedDelay(this::pushStats, 500, 500, TimeUnit.MILLISECONDS);
    }

    public void shutdown() {
        NetSession s = session;
        session = null;
        if (s != null) s.stop();
        discovery.stop();
        stats.shutdownNow();
    }

    public NetSession session() {
        return session;
    }

    // --- configurazione ---
    private JSONObject loadConfig() {
        JSONObject c;
        try {
            String stored = store.load();
            c = stored == null || stored.isEmpty() ? new JSONObject() : new JSONObject(stored);
        } catch (JSONException e) {
            c = new JSONObject();
        }
        try {
            if (!c.has("port")) c.put("port", Protocol.DEFAULT_PORT);
            if (!c.has("quality")) c.put("quality", "Automatic");
            if (!c.has("fps")) c.put("fps", "Default");
            if (!c.has("max_width")) c.put("max_width", "Default");
            if (!c.has("last_host")) c.put("last_host", "");
        } catch (JSONException ignored) {
            // chiavi fisse: non succede
        }
        return c;
    }

    private void saveConfig() {
        store.save(cfg.toString());
    }

    private static JSONObject qualityPreset(String name) throws JSONException {
        JSONObject o = new JSONObject();
        if ("Low".equals(name)) o.put("quality", 35).put("adaptive", false);
        else if ("Medium".equals(name)) o.put("quality", 55).put("adaptive", false);
        else if ("High".equals(name)) o.put("quality", 75).put("adaptive", false);
        else if ("Maximum".equals(name)) o.put("quality", 90).put("adaptive", false);
        return o;                                       // "Automatic": predefiniti dell'agente
    }

    private static JSONObject remoteConfig(JSONObject settings) throws JSONException {
        JSONObject cfg = qualityPreset(settings.optString("quality", "Automatic"));
        String fps = settings.optString("fps", "");
        if (fps.matches("\\d+")) cfg.put("fps", Integer.parseInt(fps));
        String width = settings.optString("max_width", "");
        if ("Original".equals(width)) cfg.put("max_width", 0);
        else if (width.matches("\\d+")) cfg.put("max_width", Integer.parseInt(width));
        return cfg;
    }

    // --- chiamate dall'interfaccia ---
    /** Punto d'ingresso unico: metodo + argomenti JSON → risposta JSON ("null" se nessuna). */
    public String call(String method, String argsJson) {
        try {
            JSONArray args = argsJson == null || argsJson.isEmpty() ? new JSONArray() : new JSONArray(argsJson);
            switch (method) {
                case "get_state":
                    return state().toString();
                case "connect":
                    return connect(args.optString(0, ""), args.optJSONObject(1)).toString();
                case "disconnect":
                    disconnect();
                    return "null";
                case "send_input":
                    sendInput(args.optJSONArray(0));
                    return "null";
                case "get_servers":
                    return servers().toString();
                case "set_fullscreen":
                    host.setFullscreen(args.optBoolean(0));
                    return "null";
                case "set_capture":
                    return "null";
                default:
                    return "null";
            }
        } catch (JSONException e) {
            return "null";
        }
    }

    private JSONObject state() throws JSONException {
        JSONObject st = new JSONObject();
        st.put("version", version);
        st.put("platform", platform);
        st.put("mobile", true);
        st.put("discovery", discovery.error == null);
        st.put("last_host", cfg.optString("last_host", ""));
        st.put("connect_now", connectNow);
        JSONObject settings = new JSONObject();
        for (String k : new String[] {"port", "quality", "fps", "max_width"}) settings.put(k, cfg.get(k));
        st.put("settings", settings);
        NetSession s = session;
        if (s != null && s.hello.length() > 0) {
            JSONObject sess = new JSONObject();
            sess.put("host", s.host).put("state", "connected").put("hello", s.hello);
            st.put("session", sess);
        }
        return st;
    }

    private JSONObject connect(String text, JSONObject settings) throws JSONException {
        JSONObject res = new JSONObject();
        if (session != null) return res.put("error", "Already connected.");
        if (settings == null) settings = new JSONObject();
        int port;
        try {
            port = settings.has("port") ? settings.getInt("port") : Protocol.DEFAULT_PORT;
            if (port < 1 || port > 65535) throw new NumberFormatException();
        } catch (JSONException | NumberFormatException e) {
            return res.put("error", "The port must be a number between 1 and 65535.");
        }
        Object[] hp;
        try {
            hp = Protocol.parseHostPort(text, port);
        } catch (IllegalArgumentException e) {
            return res.put("error", "Invalid address: " + e.getMessage() + ".");
        }
        for (String k : new String[] {"quality", "fps", "max_width"}) {
            if (settings.has(k)) cfg.put(k, settings.get(k));
        }
        cfg.put("port", port);
        saveConfig();
        connectText = text;
        firstFrameLogged = false;
        NetSession s = new NetSession((String) hp[0], (Integer) hp[1], remoteConfig(settings), this);
        session = s;
        s.start();
        return res.put("host", hp[0]);
    }

    private void disconnect() {
        NetSession s = session;
        session = null;
        if (s != null) s.stop();
    }

    private void sendInput(JSONArray events) {
        NetSession s = session;
        if (s == null || events == null) return;
        for (int i = 0; i < events.length(); i++) {
            JSONObject ev = events.optJSONObject(i);
            if (ev != null) s.sendInput(ev);
        }
    }

    private JSONArray servers() throws JSONException {
        long now = System.currentTimeMillis();
        if (now - localIpsAt > 10_000) {
            localIps = localAddresses();
            localIpsAt = now;
        }
        JSONArray out = new JSONArray();
        for (Discovery.Server sv : discovery.servers()) {
            if (localIps.contains(sv.ip) || sv.ip.startsWith("127.")) continue;
            String target = sv.port == Protocol.DEFAULT_PORT ? sv.ip : sv.ip + ":" + sv.port;
            out.put(new JSONObject().put("name", sv.name).put("target", target).put("busy", sv.busy));
        }
        return out;
    }

    private static Set<String> localAddresses() {
        Set<String> ips = new HashSet<>();
        try {
            for (NetworkInterface ni : Collections.list(NetworkInterface.getNetworkInterfaces())) {
                for (InetAddress a : Collections.list(ni.getInetAddresses())) {
                    if (a instanceof Inet4Address) ips.add(a.getHostAddress());
                }
            }
        } catch (Exception ignored) {
            // nessuna interfaccia leggibile
        }
        return ips;
    }

    // --- eventi dalla rete ---
    @Override
    public void onEvent(NetSession s, String kind, Object data) {
        if (s != session) return;
        try {
            JSONObject ev = new JSONObject();
            switch (kind) {
                case "connected":
                    cfg.put("last_host", connectText.isEmpty() ? s.host : connectText);
                    saveConfig();
                    host.log("connected host=" + s.host + " name=" + ((JSONObject) data).optString("name"));
                    ev.put("type", "connected").put("host", s.host).put("hello", data);
                    break;
                case "failed":
                    session = null;
                    host.log("failed " + data);
                    ev.put("type", "failed").put("host", s.host).put("message", String.valueOf(data));
                    break;
                case "closed":
                    session = null;
                    host.log("closed " + data);
                    ev.put("type", "closed").put("message", String.valueOf(data));
                    break;
                case "reconnecting":
                case "reconnected":
                    host.log(kind);
                    ev.put("type", kind);
                    break;
                case "notice": {
                    JSONObject n = (JSONObject) data;
                    ev.put("type", "notice").put("level", n.optString("level", "warning")).put("text", n.optString("text", ""));
                    break;
                }
                default:
                    return;
            }
            host.emit(ev.toString());
        } catch (JSONException ignored) {
            // evento mal formato: ignorato
        }
    }

    private void pushStats() {
        NetSession s = session;
        if (s == null || s.hello.length() == 0) return;
        if (!firstFrameLogged && s.currentSeq() > 0) {
            firstFrameLogged = true;
            host.log("first frame " + s.frameWidth + "x" + s.frameHeight);
        }
        try {
            JSONObject ev = new JSONObject().put("type", "stats").put("fps", s.fps)
                    .put("width", s.frameWidth).put("height", s.frameHeight);
            if (s.rttMs >= 0) ev.put("rtt", s.rttMs);
            host.emit(ev.toString());
        } catch (JSONException ignored) {
            // numeri non validi: ignorati
        }
    }
}
