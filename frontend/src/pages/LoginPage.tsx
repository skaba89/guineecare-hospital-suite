import { useState } from "react";
import { LoginPayload } from "../services/authService";
import { useT } from "../i18n";
import { LanguageToggle } from "../components/LanguageToggle";

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
      setError(`${t("login.error")}. ${message}`);
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
        <h1>{t("login.title")}</h1>
        <p className="muted">{t("login.subtitle")}</p>
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
            />
          </label>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? t("login.connecting") : t("login.submit")}
          </button>
        </form>
        <div style={{ marginTop: "16px", fontSize: "12px", color: "#94a3b8" }}>
          <p>admin@guineecare.com / admin123</p>
          <p>dr.diallo@chu-donka.gn / doctor123</p>
        </div>
      </div>
    </div>
  );
}
