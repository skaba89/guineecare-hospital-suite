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
type FormValues = Record<string, string>;

const defaultFacilityId = "facility-test";

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
        {page === "Patients" && (
          <ResourcePage
            title="Patients"
            path="/patients"
            form={<PatientForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
        {page === "Admissions" && (
          <ResourcePage
            title="Admissions"
            path="/admissions"
            form={<AdmissionForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
        {page === "Urgences" && (
          <ResourcePage
            title="File urgences"
            path="/emergency/queue"
            form={<EmergencyForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
        {page === "Pharmacie" && (
          <ResourcePage
            title="Stock pharmacie"
            path="/pharmacy/stock"
            form={<PharmacyForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
        {page === "Laboratoire" && (
          <ResourcePage
            title="Examens laboratoire"
            path="/laboratory/tests"
            form={<LaboratoryForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
        {page === "Facturation" && (
          <ResourcePage
            title="Factures"
            path="/billing/invoices"
            form={<BillingForm onCreated={() => window.dispatchEvent(new Event("refresh-resource"))} />}
          />
        )}
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

function ResourcePage({ title, path, form }: { title: string; path: string; form?: React.ReactNode }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState("");

  async function load() {
    setError("");
    try {
      const payload = await apiRequest<any>(path);
      setRows(Array.isArray(payload.data) ? payload.data : []);
    } catch (err) {
      setError("Impossible de charger les donnees.");
    }
  }

  useEffect(() => {
    load();
    const handler = () => load();
    window.addEventListener("refresh-resource", handler);
    return () => window.removeEventListener("refresh-resource", handler);
  }, [path]);

  const columns = rows.length ? Object.keys(rows[0]).slice(0, 7) : [];

  return (
    <section>
      <h1>{title}</h1>
      <p className="muted">Donnees chargees depuis l API backend.</p>
      {form}
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

function SimpleForm({
  title,
  fields,
  initialValues,
  onSubmit,
}: {
  title: string;
  fields: { name: string; label: string; type?: string }[];
  initialValues: FormValues;
  onSubmit: (values: FormValues) => Promise<void>;
}) {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage("");
    setError("");
    try {
      await onSubmit(values);
      setMessage("Enregistrement effectue.");
    } catch (err) {
      setError("Erreur lors de l enregistrement.");
    }
  }

  return (
    <div className="card form-card">
      <h2>{title}</h2>
      <form onSubmit={submit} className="form-grid">
        {fields.map((field) => (
          <label className="form-control" key={field.name}>
            {field.label}
            <input
              type={field.type || "text"}
              value={values[field.name] || ""}
              onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}
            />
          </label>
        ))}
        <div className="form-actions">
          <button className="primary-button" type="submit">Enregistrer</button>
          {message && <span className="success-text">{message}</span>}
          {error && <span className="error-text">{error}</span>}
        </div>
      </form>
    </div>
  );
}

function PatientForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouveau patient"
      initialValues={{ facility_id: defaultFacilityId, patient_number: "PAT-001", first_name: "", last_name: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "patient_number", label: "Numero patient" },
        { name: "first_name", label: "Prenom" },
        { name: "last_name", label: "Nom" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/patients", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function AdmissionForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouvelle admission"
      initialValues={{ facility_id: defaultFacilityId, patient_id: "", department_id: "", admission_type: "CONSULTATION" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "patient_id", label: "Patient ID" },
        { name: "department_id", label: "Service ID" },
        { name: "admission_type", label: "Type admission" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/admissions", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function EmergencyForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouveau passage urgence"
      initialValues={{ facility_id: defaultFacilityId, patient_id: "", admission_id: "", priority_level: "NORMAL", chief_complaint: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "patient_id", label: "Patient ID" },
        { name: "admission_id", label: "Admission ID" },
        { name: "priority_level", label: "Priorite" },
        { name: "chief_complaint", label: "Motif" },
      ]}
      onSubmit={async (values) => {
        const payload = { ...values, admission_id: values.admission_id || null };
        await apiRequest("/emergency/visits", { method: "POST", body: JSON.stringify(payload) });
        onCreated();
      }}
    />
  );
}

function PharmacyForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouveau produit pharmacie"
      initialValues={{ facility_id: defaultFacilityId, code: "PROD-001", name: "", category: "MEDICINE", form: "", dosage: "" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "code", label: "Code" },
        { name: "name", label: "Nom produit" },
        { name: "category", label: "Categorie" },
        { name: "form", label: "Forme" },
        { name: "dosage", label: "Dosage" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/pharmacy/products", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function LaboratoryForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouvel examen laboratoire"
      initialValues={{ facility_id: defaultFacilityId, code: "LAB-001", name: "", category: "GENERAL", sample_type: "Sample" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "code", label: "Code examen" },
        { name: "name", label: "Nom examen" },
        { name: "category", label: "Categorie" },
        { name: "sample_type", label: "Type echantillon" },
      ]}
      onSubmit={async (values) => {
        await apiRequest("/laboratory/tests", { method: "POST", body: JSON.stringify(values) });
        onCreated();
      }}
    />
  );
}

function BillingForm({ onCreated }: { onCreated: () => void }) {
  return (
    <SimpleForm
      title="Nouvelle facture"
      initialValues={{ facility_id: defaultFacilityId, patient_id: "", admission_id: "", invoice_number: "INV-001", description: "", net_amount: "0" }}
      fields={[
        { name: "facility_id", label: "Etablissement ID" },
        { name: "patient_id", label: "Patient ID" },
        { name: "admission_id", label: "Admission ID" },
        { name: "invoice_number", label: "Numero facture" },
        { name: "description", label: "Description" },
        { name: "net_amount", label: "Montant", type: "number" },
      ]}
      onSubmit={async (values) => {
        const payload = {
          ...values,
          admission_id: values.admission_id || null,
          net_amount: Number(values.net_amount || 0),
        };
        await apiRequest("/billing/invoices", { method: "POST", body: JSON.stringify(payload) });
        onCreated();
      }}
    />
  );
}
