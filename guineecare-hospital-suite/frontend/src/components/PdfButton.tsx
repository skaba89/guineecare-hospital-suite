/**
 * v1.2.0 — Reusable PDF download / preview button.
 *
 * Triggers a GET to `/api/v1/documents/{path}` with the JWT in the
 * Authorization header (fetch can't be a simple <a href> because the
 * endpoint is JWT-protected). The returned blob is opened in a new tab
 * (preview) or pushed as a download (download=true).
 */
import { useState } from "react";
import { FileText, Loader2 } from "lucide-react";
import { getToken } from "../services/api";
import { showToast } from "./Toast";

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL || "/api/v1";

export function PdfButton({
  documentPath,
  label = "PDF",
  variant = "ghost",
  size = "sm",
}: {
  /** Path under /api/v1/documents/, e.g. "invoices/abc-123/pdf" */
  documentPath: string;
  label?: string;
  variant?: "ghost" | "primary" | "outline";
  size?: "sm" | "md";
}) {
  const [loading, setLoading] = useState(false);

  async function handleClick() {
    const token = getToken();
    if (!token) {
      showToast("Session expirée. Reconnectez-vous.", "error");
      return;
    }
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE_URL}/documents/${documentPath}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!resp.ok) {
        const txt = await resp.text();
        let msg = `HTTP ${resp.status}`;
        try {
          const j = JSON.parse(txt);
          msg = j.detail || msg;
        } catch {
          /* keep default */
        }
        showToast(`Erreur génération PDF : ${msg}`, "error");
        return;
      }
      const blob = await resp.blob();
      // Open in new tab — most browsers will display the PDF inline.
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank");
      // Revoke after 60s — enough for the user to view/download.
      setTimeout(() => URL.revokeObjectURL(url), 60_000);
    } catch (e: any) {
      showToast(`Erreur réseau : ${e?.message || e}`, "error");
    } finally {
      setLoading(false);
    }
  }

  const variantClass =
    variant === "primary"
      ? "btn-primary"
      : variant === "outline"
      ? "btn-outline"
      : "btn-ghost";
  const sizeClass = size === "sm" ? "btn-sm" : "";

  return (
    <button
      type="button"
      className={`btn ${variantClass} ${sizeClass}`}
      onClick={handleClick}
      disabled={loading}
      title="Générer et ouvrir le PDF"
      style={{ display: "inline-flex", alignItems: "center", gap: "4px" }}
    >
      {loading ? (
        <Loader2 size={14} className="spin" />
      ) : (
        <FileText size={14} />
      )}
      <span>{loading ? "…" : label}</span>
    </button>
  );
}
