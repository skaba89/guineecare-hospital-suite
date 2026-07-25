import { useState } from "react";
import { LoginPayload } from "../services/authService";
import { useT } from "../i18n";
import { LanguageToggle } from "../components/LanguageToggle";
import { ShieldCheck } from "lucide-react";

export function LoginPage({ onLogin }: { onLogin: (payload: LoginPayload) => Promise<void> }) {
  const t = useT();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await onLogin({ email, password });
    } catch (err) {
      const message = err instanceof Error ? err.message : t("login.error");
      // v2.8.5 — Message compréhensible pour Render cold start
      if (message.includes("Failed to fetch") || message.includes("Network Error") || message.includes("502") || message.includes("503")) {
        setError("Le serveur est en cours de démarrage (Render free tier). Veuillez réessayer dans 30 secondes.");
      } else {
        setError(`${t("login.error")}. ${message}`);
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 8 }}>
          <LanguageToggle />
        </div>

        {/* Logo + brand */}
        <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
          <div
            style={{
              width: 44,
              height: 44,
              borderRadius: 10,
              background: "var(--primary)",
              color: "white",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 800,
              fontSize: 18,
              letterSpacing: 0.5,
            }}
          >
            GC
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: "var(--text)" }}>
              {t("login.title")}
            </h1>
            <p className="muted" style={{ margin: 0, fontSize: 12 }}>
              {t("login.subtitle")}
            </p>
          </div>
        </div>

        <form onSubmit={submit}>
          <label className="form-control" htmlFor="login-email">
            {t("login.email")}
            <input
              id="login-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              placeholder="votre@email.com"
              required
              autoFocus
              autoComplete="email"
            />
          </label>
          <label className="form-control" htmlFor="login-password">
            {t("login.password")}
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </label>
          {error && (
            <p
              role="alert"
              style={{
                color: "var(--danger)",
                background: "var(--danger-light)",
                border: "1px solid #fecaca",
                padding: "10px 12px",
                borderRadius: 6,
                fontSize: 13,
                margin: "8px 0",
              }}
            >
              {error}
            </p>
          )}
          <button
            className="primary-button"
            type="submit"
            disabled={loading}
            style={{ width: "100%", marginTop: 4 }}
          >
            {loading ? t("login.connecting") : t("login.submit")}
          </button>
        </form>

        {/* Security note — visible in all environments */}
        <div
          style={{
            marginTop: 16,
            padding: "10px 12px",
            background: "var(--primary-50)",
            border: "1px solid var(--primary-100)",
            borderRadius: 6,
            fontSize: 12,
            color: "var(--text-secondary)",
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
          }}
        >
          <ShieldCheck size={14} style={{ color: "var(--primary)", flexShrink: 0, marginTop: 1 }} />
          <span>
            Plateforme sécurisée — données de santé protégées. Toute connexion est journalisée.
          </span>
        </div>

        {import.meta.env.DEV && (
          <div
            style={{
              marginTop: 12,
              fontSize: 12,
              color: "#94a3b8",
              borderTop: "1px dashed var(--border)",
              paddingTop: 8,
            }}
          >
            <p style={{ margin: 0, fontWeight: 600, marginBottom: 4 }}>Comptes démo :</p>
            <p style={{ margin: 0 }}>admin@guineecare.com / admin123</p>
            <p style={{ margin: 0 }}>dr.diallo@chu-donka.gn / doctor123</p>
          </div>
        )}
      </div>
    </div>
  );
}
