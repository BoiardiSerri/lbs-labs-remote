package com.lbslabs.remote;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.SocketTimeoutException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.json.JSONObject;

/** Ascolta gli annunci broadcast UDP degli agenti in rete (vedi lbsremote/discovery.py). */
public final class Discovery {
    public static final class Server {
        public final String ip;
        public final int port;
        public final String name;
        public final boolean busy;
        final long seen;

        Server(String ip, int port, String name, boolean busy, long seen) {
            this.ip = ip;
            this.port = port;
            this.name = name;
            this.busy = busy;
            this.seen = seen;
        }
    }

    private static final long MAX_AGE_MS = 7000;

    private final int udpPort;
    private final Map<String, Server> servers = new LinkedHashMap<>();
    private volatile boolean stopped = false;
    private volatile DatagramSocket socket;
    public volatile String error;

    public Discovery(int udpPort) {
        this.udpPort = udpPort;
    }

    public void start() {
        Thread t = new Thread(this::run, "discovery");
        t.setDaemon(true);
        t.start();
    }

    public void stop() {
        stopped = true;
        DatagramSocket s = socket;
        if (s != null) s.close();
    }

    private void run() {
        DatagramSocket s;
        try {
            s = new DatagramSocket(null);
            s.setReuseAddress(true);
            s.setBroadcast(true);
            s.bind(new InetSocketAddress(udpPort));
            s.setSoTimeout(500);
        } catch (Exception e) {
            error = "auto-discovery not available (" + e.getMessage() + ")";
            return;
        }
        socket = s;
        byte[] buf = new byte[2048];
        while (!stopped) {
            try {
                DatagramPacket p = new DatagramPacket(buf, buf.length);
                s.receive(p);
                handle(new String(p.getData(), 0, p.getLength(), StandardCharsets.UTF_8), p.getAddress());
            } catch (SocketTimeoutException ignored) {
                // si riprova
            } catch (Exception e) {
                if (stopped) break;
            }
        }
        s.close();
    }

    private void handle(String text, InetAddress from) {
        try {
            JSONObject o = new JSONObject(text);
            if (!Protocol.APP_ID.equals(o.optString("app"))) return;
            int port = o.getInt("port");
            String ip = from.getHostAddress();
            String name = o.optString("name", ip);
            if (name.length() > 64) name = name.substring(0, 64);
            synchronized (servers) {
                servers.put(ip + ":" + port, new Server(ip, port, name, o.optBoolean("busy"), System.currentTimeMillis()));
            }
        } catch (Exception ignored) {
            // pacchetto di un altro programma
        }
    }

    /** Server visti negli ultimi secondi, ordinati per nome. */
    public List<Server> servers() {
        long now = System.currentTimeMillis();
        List<Server> out;
        synchronized (servers) {
            for (Iterator<Server> it = servers.values().iterator(); it.hasNext(); ) {
                if (now - it.next().seen > MAX_AGE_MS) it.remove();
            }
            out = new ArrayList<>(servers.values());
        }
        Collections.sort(out, (a, b) -> {
            int c = a.name.compareToIgnoreCase(b.name);
            return c != 0 ? c : a.ip.compareTo(b.ip);
        });
        return out;
    }
}
