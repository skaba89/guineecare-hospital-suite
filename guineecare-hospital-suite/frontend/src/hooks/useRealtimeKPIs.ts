/**
 * Realtime WebSocket hook — v1.3.0
 *
 * Connects to WS /api/v1/realtime/ws?token=<JWT> and exposes:
 * - connection status (connecting | connected | disconnected)
 * - the latest event received (filtered by type prefix)
 * - a subscribe() helper to register custom listeners
 *
 * Auto-reconnects with exponential backoff (1s → 2s → 4s → 8s → max 30s).
 *
 * Usage:
 *   const { status, lastEvent } = useRealtimeKPIs();
 *
 *   // Filtered by event type prefix:
 *   const { lastEvent: admissionKpi } = useRealtimeKPIs({ typePrefix: "kpi.admissions" });
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { getToken } from "../services/api";

export type RealtimeStatus = "idle" | "connecting" | "connected" | "disconnected";

export type RealtimeEvent = {
  type: string;
  payload: Record<string, any>;
  facility_id: string;
  ts: string;
};

type UseRealtimeOptions = {
  /** If set, only events whose `type` starts with this prefix are surfaced via `lastEvent`. */
  typePrefix?: string;
  /** Disable the hook (e.g. when not logged in). */
  enabled?: boolean;
};

const MAX_RECONNECT_DELAY = 30_000;
const BASE_RECONNECT_DELAY = 1_000;

export function useRealtimeKPIs(options: UseRealtimeOptions = {}) {
  const { typePrefix, enabled = true } = options;
  const [status, setStatus] = useState<RealtimeStatus>("idle");
  const [lastEvent, setLastEvent] = useState<RealtimeEvent | null>(null);
  const [events, setEvents] = useState<RealtimeEvent[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const connect = useCallback(() => {
    const token = getToken();
    if (!token) {
      setStatus("disconnected");
      return;
    }

    // Build WS URL — same origin as the API
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    const host = window.location.host;
    const url = `${proto}//${host}/api/v1/realtime/ws?token=${encodeURIComponent(token)}`;

    setStatus("connecting");
    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.warn("[realtime] WebSocket construction failed:", e);
      scheduleReconnect();
      return;
    }
    wsRef.current = ws;

    ws.onopen = () => {
      reconnectAttempts.current = 0;
      setStatus("connected");
    };

    ws.onmessage = (msg) => {
      try {
        const event: RealtimeEvent = JSON.parse(msg.data);
        // Skip pings
        if (event.type === "ping") return;

        // Filter by type prefix if specified
        if (typePrefix && !event.type.startsWith(typePrefix)) return;

        setLastEvent(event);
        // Keep a sliding window of the last 50 events
        setEvents((prev) => [...prev.slice(-49), event]);
      } catch (e) {
        console.warn("[realtime] Failed to parse message:", e);
      }
    };

    ws.onerror = (e) => {
      console.warn("[realtime] WebSocket error:", e);
    };

    ws.onclose = () => {
      setStatus("disconnected");
      wsRef.current = null;
      scheduleReconnect();
    };
  }, [typePrefix]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
    const attempt = reconnectAttempts.current++;
    const delay = Math.min(
      BASE_RECONNECT_DELAY * Math.pow(2, attempt),
      MAX_RECONNECT_DELAY
    );
    reconnectTimer.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect]);

  const disconnect = useCallback(() => {
    if (reconnectTimer.current) {
      clearTimeout(reconnectTimer.current);
      reconnectTimer.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "client disconnect");
      wsRef.current = null;
    }
    setStatus("idle");
  }, []);

  useEffect(() => {
    if (!enabled) {
      disconnect();
      return;
    }
    connect();
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, typePrefix]);

  return { status, lastEvent, events, disconnect, reconnect: connect };
}
