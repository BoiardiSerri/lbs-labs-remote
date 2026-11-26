package com.lbslabs.remote;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;

/**
 * Protocollo di rete di LBS Labs Remote (vedi lbsremote/protocol.py, che è la specifica).
 * Ogni messaggio: 4 byte big-endian con la lunghezza del payload + 1 byte di tipo + payload.
 * Per i frame video il payload è direttamente il JPEG; gli altri messaggi sono JSON UTF-8.
 * Java puro, senza dipendenze da Android: si prova anche su un computer normale.
 */
public final class Protocol {
    private Protocol() {}

    public static final String APP_ID = "lbslabs-remote";
    public static final int DEFAULT_PORT = 5970;
    public static final int DISCOVERY_PORT = 5901;
    public static final long MAX_MESSAGE_SIZE = 64L * 1024 * 1024;

    // server -> client
    public static final int MSG_HELLO = 1;
    public static final int MSG_FRAME = 2;
    public static final int MSG_PONG = 3;
    public static final int MSG_NOTICE = 4;
    public static final int MSG_BYE = 5;
    // client -> server
    public static final int MSG_INPUT = 10;
    public static final int MSG_PING = 11;
    public static final int MSG_CONFIG = 12;

    /** Un messaggio ricevuto. */
    public static final class Message {
        public final int type;
        public final byte[] payload;

        Message(int type, byte[] payload) {
            this.type = type;
            this.payload = payload;
        }

        public String text() {
            return new String(payload, StandardCharsets.UTF_8);
        }
    }

    /** Sulla porta risponde un altro programma (VNC, HTTP, SSH…). */
    public static final class ForeignServiceException extends IOException {
        public ForeignServiceException(String message) {
            super(message);
        }
    }

    public static byte[] pack(int type, byte[] payload) {
        byte[] out = new byte[5 + payload.length];
        int n = payload.length;
        out[0] = (byte) (n >>> 24);
        out[1] = (byte) (n >>> 16);
        out[2] = (byte) (n >>> 8);
        out[3] = (byte) n;
        out[4] = (byte) type;
        System.arraycopy(payload, 0, out, 5, n);
        return out;
    }

    public static byte[] pack(int type, String json) {
        return pack(type, json.getBytes(StandardCharsets.UTF_8));
    }

    /** Legge un messaggio completo. Se l'altro capo non parla questo protocollo lancia ForeignServiceException. */
    public static Message read(DataInputStream in, int port) throws IOException {
        byte[] head = new byte[5];
        in.readFully(head);
        if (looksForeign(head)) {
            throw new ForeignServiceException(describeForeignService(head, port));
        }
        long len = ((head[0] & 0xFFL) << 24) | ((head[1] & 0xFFL) << 16) | ((head[2] & 0xFFL) << 8) | (head[3] & 0xFFL);
        if (len > MAX_MESSAGE_SIZE) {
            throw new ForeignServiceException(describeForeignService(head, port));
        }
        byte[] payload = new byte[(int) len];
        in.readFully(payload);
        return new Message(head[4] & 0xFF, payload);
    }

    private static boolean looksForeign(byte[] h) {
        return startsWith(h, "RFB") || startsWith(h, "HTTP") || startsWith(h, "SSH-");
    }

    private static boolean startsWith(byte[] h, String prefix) {
        for (int i = 0; i < prefix.length(); i++) {
            if (i >= h.length || h[i] != (byte) prefix.charAt(i)) return false;
        }
        return true;
    }

    public static String describeForeignService(byte[] firstBytes, int port) {
        if (startsWith(firstBytes, "RFB")) {
            return "another remote control program (VNC, e.g. macOS Screen Sharing) is answering on port "
                    + port + ", not LBS Labs Remote. Update LBS Labs Remote to the latest version on both "
                    + "computers, or turn off Screen Sharing on the remote computer.";
        }
        return "another program is answering on port " + port + ", not LBS Labs Remote.";
    }

    /** Larghezza e altezza di un JPEG leggendo l'intestazione (senza decodificarlo), o null. */
    public static int[] jpegSize(byte[] d) {
        int i = 2;
        int n = d.length;
        while (i + 9 < n) {
            if ((d[i] & 0xFF) != 0xFF) {
                i++;
                continue;
            }
            int marker = d[i + 1] & 0xFF;
            if (marker == 0xC0 || marker == 0xC1 || marker == 0xC2) {
                int h = ((d[i + 5] & 0xFF) << 8) | (d[i + 6] & 0xFF);
                int w = ((d[i + 7] & 0xFF) << 8) | (d[i + 8] & 0xFF);
                return new int[] {w, h};
            }
            if (marker == 0xD8 || marker == 0x01 || (marker >= 0xD0 && marker <= 0xD7)) {
                i += 2;
                continue;
            }
            i += 2 + (((d[i + 2] & 0xFF) << 8) | (d[i + 3] & 0xFF));
        }
        return null;
    }

    /** "192.168.1.5" → (host, default); "192.168.1.5:6000" → (host, 6000); "[::1]:5970". */
    public static Object[] parseHostPort(String text, int defaultPort) {
        text = text == null ? "" : text.trim();
        if (text.isEmpty()) throw new IllegalArgumentException("empty address");
        if (text.startsWith("[")) {
            int close = text.indexOf(']');
            if (close < 0) throw new IllegalArgumentException("invalid address");
            String host = text.substring(1, close);
            String rest = text.substring(close + 1);
            int port = rest.startsWith(":") ? parsePort(rest.substring(1)) : defaultPort;
            return new Object[] {host, port};
        }
        int colons = text.length() - text.replace(":", "").length();
        if (colons == 1) {
            String[] parts = text.split(":", 2);
            return new Object[] {parts[0].trim(), parsePort(parts[1])};
        }
        return new Object[] {text, defaultPort};
    }

    private static int parsePort(String s) {
        s = s.trim();
        if (!s.matches("\\d{1,5}")) throw new IllegalArgumentException("invalid port");
        int p = Integer.parseInt(s);
        if (p < 1 || p > 65535) throw new IllegalArgumentException("invalid port");
        return p;
    }

    static DataInputStream wrap(InputStream in) {
        return new DataInputStream(in);
    }
}
