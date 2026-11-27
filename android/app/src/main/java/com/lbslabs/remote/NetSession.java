package com.lbslabs.remote;

import java.io.BufferedInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.ConnectException;
import java.net.InetSocketAddress;
import java.net.Socket;
import java.net.SocketTimeoutException;
import java.net.UnknownHostException;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import org.json.JSONException;
import org.json.JSONObject;

/**
 * Connessione all'agente remoto, con riconnessione automatica (porting di lbsremote/client.py).
 * Gira in thread propri. Gli eventi arrivano al Listener da un thread di rete.
 *
 * Eventi (kind → data): connected → JSONObject hello · failed → String · reconnecting → String ·
 * reconnected → JSONObject hello · notice → JSONObject · closed → String.
 */
public final class NetSession {
    public interface Listener {
        void onEvent(NetSession session, String kind, Object data);
    }

    private static final int CONNECT_TIMEOUT_MS = 4000;
    private static final int RECV_TIMEOUT_MS = 6000;      // nessun dato (frame o pong) per 6 s => connessione persa
    private static final long RECONNECT_WINDOW_MS = 15000;
    private static final long RECONNECT_DELAY_MS = 2500;
    private static final long PING_INTERVAL_MS = 1000;
    private static final long MIN_SESSION_MS = 5000;      // una sessione più breve è "caduta subito"
    private static final int MAX_QUICK_DROPS = 3;         // dopo tante cadute immediate di fila si smette

    public final String host;
    public final int port;
    private final JSONObject remoteConfig;
    private final Listener listener;

    public volatile JSONObject hello = new JSONObject();
    private volatile String lastNotice = "";
    public volatile double rttMs = -1;
    public volatile double fps = 0;
    public volatile int frameWidth = 0;
    public volatile int frameHeight = 0;

    private volatile Socket socket;
    private volatile boolean stopped = false;

    // ultimo frame JPEG ricevuto; chi lo mostra attende il successivo
    private final Object frameLock = new Object();
    private byte[] frame;
    private long frameSeq = 0;
    private int fpsCount = 0;
    private long fpsT0 = System.nanoTime();

    private final LinkedBlockingQueue<byte[]> sendQueue = new LinkedBlockingQueue<>();

    public NetSession(String host, int port, JSONObject remoteConfig, Listener listener) {
        this.host = host;
        this.port = port;
        this.remoteConfig = remoteConfig == null ? new JSONObject() : remoteConfig;
        this.listener = listener;
    }

    // --- API per l'interfaccia ---
    public void start() {
        Thread t = new Thread(this::run, "net-session");
        t.setDaemon(true);
        t.start();
    }

    public void stop() {
        stopped = true;
        Socket s = socket;
        if (s != null) {
            try {
                s.close();
            } catch (IOException ignored) {
                // già chiuso
            }
        }
        synchronized (frameLock) {
            frameLock.notifyAll();
        }
    }

    public boolean isStopped() {
        return stopped;
    }

    public void sendInput(JSONObject event) {
        sendQueue.offer(Protocol.pack(Protocol.MSG_INPUT, event.toString()));
    }

    /** Attende un frame più recente di afterSeq. Restituisce {seq, jpeg} oppure jpeg = null. */
    public Object[] waitFrame(long afterSeq, long timeoutMs) {
        synchronized (frameLock) {
            if (frameSeq <= afterSeq && !stopped) {
                try {
                    frameLock.wait(timeoutMs);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }
            return new Object[] {frameSeq, frame};
        }
    }

    public long currentSeq() {
        synchronized (frameLock) {
            return frameSeq;
        }
    }

    // --- interno ---
    private void post(String kind, Object data) {
        try {
            listener.onEvent(this, kind, data);
        } catch (RuntimeException e) {
            // un errore nella gestione dell'evento non deve fermare la rete
        }
    }

    /** Una connessione + handshake. Restituisce null se ok, altrimenti il motivo. */
    private String connectOnce() {
        Socket s = null;
        try {
            s = new Socket();
            s.connect(new InetSocketAddress(host, port), CONNECT_TIMEOUT_MS);
            s.setTcpNoDelay(true);
            s.setKeepAlive(true);
            s.setSoTimeout(RECV_TIMEOUT_MS);
            DataInputStream in = new DataInputStream(new BufferedInputStream(s.getInputStream(), 64 * 1024));
            Protocol.Message m = Protocol.read(in, port);
            JSONObject h = m.type == Protocol.MSG_HELLO ? new JSONObject(m.text()) : new JSONObject();
            if (!Protocol.APP_ID.equals(h.optString("app"))) {
                throw new Protocol.ForeignServiceException(Protocol.describeForeignService(new byte[0], port));
            }
            if (remoteConfig.length() > 0) {
                OutputStream out = s.getOutputStream();
                out.write(Protocol.pack(Protocol.MSG_CONFIG, remoteConfig.toString()));
                out.flush();
            }
            socket = s;
            hello = h;
            readerStreams = in;
            return null;
        } catch (UnknownHostException e) {
            closeQuietly(s);
            return "invalid address or unknown computer name.";
        } catch (ConnectException e) {
            closeQuietly(s);
            return "connection refused: LBS Labs Remote is not running on that computer (port " + port + ").";
        } catch (SocketTimeoutException e) {
            closeQuietly(s);
            return "no response. Is the computer on and connected to the network? Is LBS Labs Remote "
                    + "installed on it? Is a firewall blocking the connection?";
        } catch (IOException | JSONException e) {
            closeQuietly(s);
            String msg = e.getMessage();
            return msg == null || msg.isEmpty() ? e.getClass().getSimpleName() : msg;
        }
    }

    private volatile DataInputStream readerStreams;

    private static void closeQuietly(Socket s) {
        if (s != null) {
            try {
                s.close();
            } catch (IOException ignored) {
                // niente da fare
            }
        }
    }

    private void run() {
        String err = connectOnce();
        if (err != null) {
            post("failed", err);
            return;
        }
        post("connected", hello);
        int quickDrops = 0;
        while (!stopped) {
            long started = System.currentTimeMillis();
            String[] result = serve();
            if (stopped) return;
            if ("bye".equals(result[0])) {
                post("closed", result[1]);
                return;
            }
            quickDrops = System.currentTimeMillis() - started < MIN_SESSION_MS ? quickDrops + 1 : 0;
            if (quickDrops >= MAX_QUICK_DROPS) {
                // Il computer remoto chiude la connessione appena creata: riprovare di continuo è inutile.
                String detail = lastNotice.isEmpty() ? "" : " (" + lastNotice + ")";
                post("closed", "The remote computer keeps closing the connection right after it is established"
                        + detail + ". Check LBS Labs Remote on that computer, then connect again.");
                return;
            }
            post("reconnecting", result[1]);
            long deadline = System.currentTimeMillis() + RECONNECT_WINDOW_MS;
            err = result[1];
            while (!stopped && System.currentTimeMillis() < deadline) {
                try {
                    Thread.sleep(RECONNECT_DELAY_MS);          // pausa prima di ogni tentativo
                } catch (InterruptedException e) {
                    return;
                }
                if (stopped) return;
                err = connectOnce();
                if (err == null) break;
            }
            if (stopped) return;
            if (err != null) {
                post("closed", "Connection to " + host + " lost: " + err);
                return;
            }
            post("reconnected", hello);
        }
    }

    private void onFrame(byte[] jpeg) {
        int[] size = Protocol.jpegSize(jpeg);
        if (size != null) {
            frameWidth = size[0];
            frameHeight = size[1];
        }
        synchronized (frameLock) {
            frame = jpeg;
            frameSeq++;
            frameLock.notifyAll();
        }
        fpsCount++;
        long now = System.nanoTime();
        if (now - fpsT0 >= 1_000_000_000L) {
            fps = fpsCount * 1e9 / (now - fpsT0);
            fpsCount = 0;
            fpsT0 = now;
        }
    }

    /** Serve la connessione finché cade. Restituisce {"bye"|"lost", motivo}. */
    private String[] serve() {
        final Socket s = socket;
        final DataInputStream in = readerStreams;
        sendQueue.clear();                              // gli input accodati durante la disconnessione sono obsoleti
        final Thread sender = new Thread(() -> senderLoop(s), "net-sender");
        sender.setDaemon(true);
        sender.start();
        try {
            while (!stopped) {
                Protocol.Message m = Protocol.read(in, port);
                switch (m.type) {
                    case Protocol.MSG_FRAME:
                        onFrame(m.payload);
                        break;
                    case Protocol.MSG_PONG: {
                        double ts = new JSONObject(m.text()).getDouble("ts");
                        double rtt = (System.nanoTime() / 1e9 - ts) * 1000.0;
                        rttMs = rttMs < 0 ? rtt : rttMs * 0.7 + rtt * 0.3;
                        break;
                    }
                    case Protocol.MSG_NOTICE: {
                        JSONObject notice = new JSONObject(m.text());
                        String text = notice.optString("text", "");
                        lastNotice = text.length() > 200 ? text.substring(0, 200) : text;
                        post("notice", notice);
                        break;
                    }
                    case Protocol.MSG_BYE: {
                        String reason = new JSONObject(m.text()).optString("reason", "");
                        return new String[] {"bye", reason.isEmpty() ? "Session closed by the remote computer." : reason};
                    }
                    default:
                        break;
                }
            }
            return new String[] {"stopped", ""};
        } catch (SocketTimeoutException e) {
            return new String[] {"lost", "no data from the remote computer for several seconds"};
        } catch (IOException | JSONException e) {
            String msg = e.getMessage();
            return new String[] {"lost", msg == null || msg.isEmpty() ? e.getClass().getSimpleName() : msg};
        } finally {
            closeQuietly(s);
            sender.interrupt();
        }
    }

    private void senderLoop(Socket s) {
        long nextPing = 0;
        try {
            OutputStream out = s.getOutputStream();
            while (!stopped && !s.isClosed()) {
                long now = System.nanoTime();
                if (now >= nextPing) {
                    JSONObject ping = new JSONObject();
                    ping.put("ts", now / 1e9);
                    out.write(Protocol.pack(Protocol.MSG_PING, ping.toString()));
                    out.flush();
                    nextPing = now + PING_INTERVAL_MS * 1_000_000L;
                }
                long waitMs = Math.max(10, (nextPing - System.nanoTime()) / 1_000_000L);
                byte[] msg = sendQueue.poll(waitMs, TimeUnit.MILLISECONDS);
                if (msg != null) {
                    out.write(msg);
                    out.flush();
                }
            }
        } catch (IOException | JSONException e) {
            closeQuietly(s);                            // sblocca il thread di ricezione
        } catch (InterruptedException e) {
            // connessione chiusa: fine
        }
    }
}
