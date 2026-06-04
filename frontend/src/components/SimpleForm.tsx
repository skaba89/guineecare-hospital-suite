import { useEffect, useState } from "react";
import { FieldConfig, FormValues } from "../types";

export function SimpleForm({
  title,
  fields,
  initialValues,
  onSubmit,
}: {
  title: string;
  fields: FieldConfig[];
  initialValues: FormValues;
  onSubmit: (values: FormValues) => Promise<void>;
}) {
  const [values, setValues] = useState<FormValues>(initialValues);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    setValues((current) => ({ ...initialValues, ...current }));
  }, [JSON.stringify(initialValues)]);

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
            {field.options ? (
              <select
                value={values[field.name] || ""}
                onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}
              >
                <option value="">-- Choisir --</option>
                {field.options.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            ) : (
              <input
                type={field.type || "text"}
                value={values[field.name] || ""}
                onChange={(event) => setValues({ ...values, [field.name]: event.target.value })}
              />
            )}
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
