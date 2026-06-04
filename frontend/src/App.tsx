import { useEffect, useState } from "react";
import { apiRequest, getToken, clearToken } from "./services/api";
import { login } from "./services/authService";

const pages = [
  "Dashboard",
  "Patients",
  "Admissions",
  "Urgences",
  "Pharmacie",
  "Laboratoire",
  "Facturation",
];

type Row = Record<string, any>;

export default function App() {
  const [tokenReady, setTokenReady] = useState(Boolean(getToken()));
  const [page, setPage] = useState("Dashboard");

  if (!tokenReady) {
    return <LoginPage onLogin={() => setTokenReady(true)} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <h1>GuineeCare</h1>
        {pages.map((item) => (
          <button
            key={item}
            className={`nav-button ${page === item ? "active" : ""}`}
            onClick={() => setPage(item)}
          >
            {item}
          </button>
        ))}
        <button
          className="nav-button"
          onClick={() => {
            clearToken();
            setTokenReady(false);
          }}
        >
          Deconnexion
        </button>
      </aside>
      <main className="main-content">
        {page === "Dashboard" && <Dashboard />}
        {page === "Patients" && <ResourcePage title="Patients" path="/patients" />}
        {page === "Admissions" && <ResourcePage title="Admissions" path="/admissions" />}
        {page === "Urgences" && <ResourcePage title="File urgences" path="/emergency/queue" />}
        {page === "Pharmacie" && <ResourcePage title="Stock pharmacie" path="/pharmacy/stock" />}
        {page === "Laboratoire" && <ResourcePage title="Examens laboratoire" path="/laboratory/tests" />}
        {page === "Facturation" && <ResourcePage title="Factures" path="/billing/invoices" />}
      </main>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("admin@guineecare.local");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await login({ email, password });
      onLogin();
    } catch (err) {
      setError("Connexion impossible. Verifiez les identifiants ou le backend.");
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
      </div>
    </div>
  );
}

function Dashboard() {
  return (
    <section>
      <h1>Dashboard hopital</h1>
      <p className="muted">Vue MVP des principaux modules hospitaliers.</p>
      <div className="grid">
        <Kpi title="Patients" value="MVP" />
        <Kpi title="Admissions" value="MVP" />
        <Kpi title="Urgences" value="MVP" />
        <Kpi title="Pharmacie" value="MVP" />
        <Kpi title="Laboratoire" value="MVP" />
        <Kpi title="Facturation" value="MVP" />
      </div>
    </section>
  );
}

function Kpi({ title, value }: { title: string; value: string }) {
  return (
    <div className="card">
      <div className="kpi">{value}</div>
      <div className="muted">{title}</div>
    </div>
  );
}

function ResourcePage({ title, path }: { title: string; path: string }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    apiRequest<any>(path)
      .then((payload) => setRows(Array.isArray(payload.data) ? payload.data : []))
      .catch(() => setError("Impossible de charger les donnees."));
  }, [path]);

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 6) : [];

  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Donnees chargees depuis l API backend.</p>
      {error && <p style={{ color: "crimson" }}>{error}</p>}
      <div className="card">
        {rows.length === 0 ? (
          <p className="muted">Aucune donnee disponible pour le moment.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>{columns.map((col) => <th key={col}>{col}</th>)}</tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={row.id || index}>
                  {columns.map((col) => <td key={col}>{String(row[col] ?? "")}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </section>
  );
}
