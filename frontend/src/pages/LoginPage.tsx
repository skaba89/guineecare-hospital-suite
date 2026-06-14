import { useState } from "react";
import { login } from "../services/authService";

export function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login({ email, password });
      onLogin();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erreur inconnue";
      setError(`Connexion impossible. ${message}`);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>GuinéeCare Hospital Suite</h1>
        <p className="muted">Système d'Information Hospitalier</p>
        <form onSubmit={submit}>
          <label className="form-control">
            Email
            <input
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              type="email"
              placeholder="votre@email.com"
              required
              autoFocus
            />
          </label>
          <label className="form-control">
            Mot de passe
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
            />
          </label>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="primary-button" type="submit" disabled={loading}>
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
