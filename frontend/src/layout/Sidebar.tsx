import { Link, useLocation } from "react-router-dom";

const navigationItems = [
  ["Dashboard", "/"],
  ["Patients", "/patients"],
  ["Admissions", "/admissions"],
  ["Urgences", "/emergency"],
  ["Pharmacie", "/pharmacy"],
  ["Laboratoire", "/lab"],
  ["Facturation", "/billing"],
  ["Activite", "/activity"],
];

export function Sidebar({ onLogout }: { onLogout: () => void }) {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <h1>GuineeCare</h1>
      {navigationItems.map(([label, path]) => {
        const active = path === "/" ? location.pathname === "/" : location.pathname.startsWith(path);
        return (
          <Link key={path} to={path} className={`nav-button ${active ? "active" : ""}`}>
            {label}
          </Link>
        );
      })}
      <button className="nav-button" onClick={onLogout}>
        Deconnexion
      </button>
    </aside>
  );
}
