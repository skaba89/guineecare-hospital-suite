/**
 * Realtime status indicator — v1.3.0
 *
 * Small badge shown in the app header. Visualizes the WebSocket connection
 * state to the realtime broker:
 *   - 🟢 connected — live updates active
 *   - 🟡 connecting — establishing connection
 *   - ⚪ idle — not logged in (or disabled)
 *   - 🔴 disconnected — connection lost, retrying
 *
 * The tooltip shows the latest event type received.
 */
import { useRealtimeKPIs } from "../hooks/useRealtimeKPIs";
import { getToken } from "../services/api";

const STATUS_CONFIG = {
  connected: { color: "#10b981", label: "Live", title: "Connexion temps réel active" },
  connecting: { color: "#f59e0b", label: "…", title: "Connexion en cours" },
  disconnected: { color: "#ef4444", label: "Hors ligne", title: "Connexion perdue — reconnexion..." },
  idle: { color: "#94a3b8", label: "—", title: "Non connecté" },
} as const;

export function RealtimeStatus() {
  // Only enable the WS hook if the user is logged in
  const enabled = !!getToken();
  const { status, lastEvent } = useRealtimeKPIs({ enabled });

  const config = STATUS_CONFIG[status];

  return (
    <div
      title={lastEvent ? `${config.title} — dernier event: ${lastEvent.type}` : config.title}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: "4px 8px",
        fontSize: 12,
        color: "#475569",
        background: "#f8fafc",
        border: "1px solid #e2e8f0",
        borderRadius: 12,
      }}
    >
      <span
        aria-hidden
        style={{
          width: 8,
          height: 8,
          borderRadius: "50%",
          background: config.color,
          display: "inline-block",
          animation: status === "connecting" ? "pulse 1.4s ease-in-out infinite" : "none",
        }}
      />
      <span style={{ fontWeight: 500 }}>{config.label}</span>
      <style>{`@keyframes pulse { 0%, 100% { opacity: 1 } 50% { opacity: 0.4 } }`}</style>
    </div>
  );
}
