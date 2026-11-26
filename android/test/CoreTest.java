import com.lbslabs.remote.AppCore;
import com.lbslabs.remote.NetSession;
import com.lbslabs.remote.Protocol;
import java.util.concurrent.CopyOnWriteArrayList;
import org.json.JSONArray;
import org.json.JSONObject;

/** Prova su JVM del codice di rete dell'app Android contro un agente vero (o di prova). */
public class CoreTest {
    static final CopyOnWriteArrayList<String> events = new CopyOnWriteArrayList<>();
    static String stored = "";

    static boolean waitFor(String type, long ms) throws Exception {
        long end = System.currentTimeMillis() + ms;
        while (System.currentTimeMillis() < end) {
            for (String e : events) if (e.contains("\"type\":\"" + type + "\"")) return true;
            Thread.sleep(50);
        }
        return false;
    }

    static String find(String type) {
        for (String e : events) if (e.contains("\"type\":\"" + type + "\"")) return e;
        return null;
    }

    public static void main(String[] args) throws Exception {
        String scenario = args[0];
        String target = args.length > 1 ? args[1] : "127.0.0.1";
        AppCore core = new AppCore(new AppCore.Host() {
            public void emit(String json) { if (!json.contains("\"stats\"")) { events.add(json); System.out.println("EVENT " + json); } else events.add(json); }
            public void setFullscreen(boolean on) { System.out.println("FULLSCREEN " + on); }
            public void log(String m) { System.out.println("LOG " + m); }
        }, new AppCore.Store() {
            public String load() { return stored; }
            public void save(String j) { stored = j; }
        }, "9.9.9", "android", "");
        JSONObject settings = new JSONObject().put("port", args.length > 2 ? Integer.parseInt(args[2]) : 5970)
                .put("quality", "Medium").put("fps", "15").put("max_width", "1280");
        System.out.println("STATE " + core.call("get_state", "[]"));
        String res = core.call("connect", new JSONArray().put(target).put(settings).toString());
        System.out.println("CONNECT -> " + res);
        boolean ok = true;
        switch (scenario) {
            case "ok": {
                ok &= waitFor("connected", 6000);
                Thread.sleep(2500);
                NetSession s = core.session();
                System.out.println("frames seq=" + s.currentSeq() + " size=" + s.frameWidth + "x" + s.frameHeight + " fps=" + s.fps + " rtt=" + s.rttMs);
                ok &= s.currentSeq() > 3 && s.frameWidth > 0 && s.rttMs >= 0;
                // l'agente ha ricevuto CONFIG (max_width 1280): lo si vede dalla dimensione del frame
                // input: click nel campo di testo, digitazione, doppio click
                String in = "[{\"t\":\"move\",\"x\":0.30,\"y\":0.30},{\"t\":\"btn\",\"b\":\"left\",\"d\":1,\"x\":0.30,\"y\":0.30,\"n\":1},{\"t\":\"btn\",\"b\":\"left\",\"d\":0,\"x\":0.30,\"y\":0.30,\"n\":1},"
                        + "{\"t\":\"key\",\"d\":1,\"c\":\"L\"},{\"t\":\"key\",\"d\":0,\"c\":\"L\"},{\"t\":\"key\",\"d\":1,\"c\":\"B\"},{\"t\":\"key\",\"d\":0,\"c\":\"B\"},"
                        + "{\"t\":\"key\",\"d\":1,\"c\":\"S\"},{\"t\":\"key\",\"d\":0,\"c\":\"S\"},{\"t\":\"key\",\"d\":1,\"s\":\"enter\"},{\"t\":\"key\",\"d\":0,\"s\":\"enter\"},"
                        + "{\"t\":\"move\",\"x\":0.39,\"y\":0.49},{\"t\":\"btn\",\"b\":\"left\",\"d\":1,\"x\":0.39,\"y\":0.49,\"n\":2},{\"t\":\"btn\",\"b\":\"left\",\"d\":0,\"x\":0.39,\"y\":0.49,\"n\":2},"
                        + "{\"t\":\"scroll\",\"dx\":0,\"dy\":2}]";
                core.call("send_input", "[" + in + "]");
                Thread.sleep(1000);
                System.out.println("SAVED CONFIG " + stored);
                ok &= stored.contains("\"last_host\":\"" + target + "\"") && stored.contains("\"quality\":\"Medium\"");
                core.call("disconnect", "[]");
                break;
            }
            case "fail": {
                ok &= waitFor("failed", 8000);
                break;
            }
            case "reconnect": {
                ok &= waitFor("connected", 6000);
                System.out.println("READY");
                ok &= waitFor("reconnecting", 20000);
                ok &= waitFor("reconnected", 25000);
                long seq = core.session().currentSeq();
                Thread.sleep(2500);
                System.out.println("frames before=" + seq + " after=" + core.session().currentSeq());
                ok &= core.session().currentSeq() > seq;
                break;
            }
            case "takeover": {
                ok &= waitFor("connected", 6000);
                System.out.println("READY");
                ok &= waitFor("closed", 20000);
                String c = find("closed");
                ok &= c != null && c.contains("taken control");
                break;
            }
            default:
                ok = false;
        }
        System.out.println(ok ? "RESULT PASS" : "RESULT FAIL");
        core.shutdown();
        System.exit(ok ? 0 : 1);
    }
}
