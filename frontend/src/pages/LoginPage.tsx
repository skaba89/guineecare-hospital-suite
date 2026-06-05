import { useState } from "react";
import { login } from "../services/authService";

export function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("admin@guineecare.com");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await login({ email, password });
      onLogin();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Erreur inconnue";
      setError(`Connexion impossible. ${message}`);
    }
  }

  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>GuineeCare Hospital Suite</h1>
        <p className="muted">Connexion au MVP hospitalier</p>
        <form onSubmit={submit}>
          <label className="form-control">
            Email
            <input value={email} onChange={(e) => setEmail(e.target.value)} />
          </label>
          <label className="form-control">
            Mot de passe
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <p style={{ color: "crimson" }}>{error}</p>}
          <button className="primary-button" type="submit">Se connecter</button>
        </form>
        <p className="muted">Compte local : admin@guineecare.com / admin123</p>
      </div>
    </div>
  );
}
