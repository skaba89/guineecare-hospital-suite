import { useTheme } from "../contexts/ThemeContext";

/**
 * Theme Toggle — v2.9.2
 *
 * Bouton compact pour basculer entre mode clair et mode sombre.
 * Affiche une icône soleil/lune selon le thème actif.
 *
 * Usage :
 *   <ThemeToggle />
 *
 * Place ce composant dans la sidebar (AppLayout) ou le topbar.
 */
export function ThemeToggle({ className = "" }: { className?: string }) {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      className={`theme-toggle ${className}`}
      title={isDark ? "Passer en mode clair" : "Passer en mode sombre"}
      aria-label={isDark ? "Passer en mode clair" : "Passer en mode sombre"}
      data-testid="theme-toggle"
      style={{
        background: "transparent",
        border: "1px solid var(--border)",
        color: "var(--text)",
        padding: "6px 10px",
        borderRadius: "var(--radius-md)",
        cursor: "pointer",
        fontSize: "14px",
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        transition: "var(--transition)",
      }}
    >
      <span aria-hidden="true">{isDark ? "☀️" : "🌙"}</span>
      <span className="theme-toggle-label">
        {isDark ? "Clair" : "Sombre"}
      </span>
    </button>
  );
}
