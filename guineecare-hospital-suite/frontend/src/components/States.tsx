/**
 * États réutilisables pour toutes les pages :
 * - EmptyState : aucune donnée (icône + titre + description + action optionnelle)
 * - Skeleton : chargement avec animation shimmer
 * - ErrorState : erreur avec bouton retry
 * - PageHeader : titre + sous-titre + actions à droite
 *
 * v2.1.0 — Phase 3 UX/UI premium. Aucune dépendance externe.
 * Tous les composants utilisent les classes définies dans styles.css.
 */
import type { ReactNode } from "react";
import { useT } from "../i18n";

/* ── EmptyState ─────────────────────────────────────────────── */

export function EmptyState({
  icon,
  title,
  description,
  action,
}: {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state" role="status" aria-live="polite">
      {icon && <div className="empty-state-icon">{icon}</div>}
      <p className="empty-state-title">{title}</p>
      {description && <p className="empty-state-description">{description}</p>}
      {action && <div className="empty-state-action">{action}</div>}
    </div>
  );
}

/* ── Skeleton ───────────────────────────────────────────────── */

export function Skeleton({ width, height }: { width?: string | number; height?: string | number }) {
  return (
    <span
      className="skeleton"
      style={{ width: width ?? "100%", height: height ?? 12, display: "inline-block" }}
      aria-hidden="true"
    />
  );
}

export function SkeletonLine({ width }: { width?: string }) {
  return <span className="skeleton skeleton-line" style={{ width }} aria-hidden="true" />;
}

export function SkeletonCard() {
  return (
    <div className="skeleton-card" aria-hidden="true">
      <div style={{ display: "flex", gap: 12, alignItems: "center", marginBottom: 12 }}>
        <span className="skeleton skeleton-circle" />
        <div style={{ flex: 1 }}>
          <SkeletonLine width="60%" />
          <SkeletonLine width="40%" />
        </div>
      </div>
      <SkeletonLine />
      <SkeletonLine width="80%" />
    </div>
  );
}

export function SkeletonTable({ rows = 5, cols = 4 }: { rows?: number; cols?: number }) {
  return (
    <div aria-hidden="true" style={{ padding: "8px 0" }}>
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="skeleton-row">
          {Array.from({ length: cols }).map((_, c) => (
            <SkeletonLine key={c} width={c === 0 ? "60%" : "90%"} />
          ))}
        </div>
      ))}
    </div>
  );
}

/* ── ErrorState ─────────────────────────────────────────────── */

export function ErrorState({
  title,
  description,
  onRetry,
  retryLabel,
}: {
  title?: string;
  description?: string;
  onRetry?: () => void;
  retryLabel?: string;
}) {
  const t = useT();
  return (
    <div className="error-state" role="alert">
      <div className="error-state-icon" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 9v4" />
          <path d="M12 17h.01" />
          <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        </svg>
      </div>
      <p className="error-state-title">{title ?? t("label.error")}</p>
      {description && <p className="error-state-description">{description}</p>}
      {onRetry && (
        <div className="error-state-action">
          <button className="btn btn-primary btn-sm" onClick={onRetry}>
            {retryLabel ?? t("label.retry")}
          </button>
        </div>
      )}
    </div>
  );
}

/* ── PageHeader ─────────────────────────────────────────────── */

export function PageHeader({
  title,
  subtitle,
  actions,
}: {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-header-title">{title}</h1>
        {subtitle && <p className="page-header-subtitle">{subtitle}</p>}
      </div>
      {actions && <div className="page-header-actions">{actions}</div>}
    </div>
  );
}
