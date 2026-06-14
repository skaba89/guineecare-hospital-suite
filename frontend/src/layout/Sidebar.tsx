import { Link, useLocation } from "react-router-dom";

type NavItem = {
  label: string;
  path: string;
  children?: NavItem[];
  accent?: boolean;
};

const navigationItems: NavItem[] = [
  { label: "Dashboard", path: "/" },
  { label: "Patients", path: "/patients" },
  { label: "Admissions", path: "/admissions" },
  {
    label: "Urgences",
    path: "/emergency",
    children: [
      { label: "File d'attente", path: "/emergency" },
      { label: "Triage", path: "/emergency/triage" },
      { label: "Orientation", path: "/emergency/orientation" },
    ],
  },
  { label: "Hospitalisation", path: "/hospitalization" },
  { label: "Maternité", path: "/maternity" },
  { label: "Pharmacie", path: "/pharmacy" },
  { label: "Imagerie", path: "/imaging" },
  { label: "Laboratoire", path: "/lab" },
  { label: "Bloc Opératoire", path: "/surgery" },
  { label: "Facturation", path: "/billing" },
  { label: "Qualité", path: "/quality" },
  { label: "Activité", path: "/activity" },
  { label: "Personnel", path: "/personnel" },
  { label: "Pilotage National", path: "/national", accent: true },
  { label: "Reporting National", path: "/reporting", accent: true },
];

export function Sidebar({ onLogout }: { onLogout: () => void }) {
  const location = useLocation();

  return (
    <aside className="sidebar">
      <h1>GuinéeCare</h1>
      <p className="subtitle">Système Hospitalier National</p>
      {navigationItems.map((item) => {
        const isActive =
          item.path === "/"
            ? location.pathname === "/"
            : location.pathname.startsWith(item.path);

        if (item.children) {
          return (
            <div key={item.path} style={{ marginBottom: "4px" }}>
              <Link
                to={item.path}
                className={`nav-button ${isActive ? "active" : ""}`}
              >
                {item.label}
              </Link>
              {isActive && (
                <div style={{ paddingLeft: "16px" }}>
                  {item.children.map((child) => {
                    const childActive = location.pathname === child.path;
                    return (
                      <Link
                        key={child.path}
                        to={child.path}
                        className={`nav-button ${childActive ? "active" : ""}`}
                        style={{ fontSize: "14px", padding: "8px 12px" }}
                      >
                        {child.label}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          );
        }

        if (item.accent) {
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`nav-button ${isActive ? "active" : ""}`}
              style={{
                marginTop: "12px",
                borderTop: "1px solid rgba(255,255,255,0.15)",
                paddingTop: "16px",
                color: isActive ? "#f2c94c" : "rgba(242,201,76,0.85)",
                fontWeight: 700,
              }}
            >
              {item.label}
            </Link>
          );
        }

        return (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-button ${isActive ? "active" : ""}`}
          >
            {item.label}
          </Link>
        );
      })}
      <button className="nav-button" onClick={onLogout}>
        Déconnexion
      </button>
    </aside>
  );
}
