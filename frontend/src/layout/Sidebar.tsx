import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  ClipboardList,
  Siren,
  ListOrdered,
  Route,
  BedDouble,
  Baby,
  Pill,
  FlaskConical,
  Scan,
  Scissors,
  Receipt,
  UserCog,
  Shield,
  Activity,
  Building2,
  BarChart3,
  LogOut,
  ChevronDown,
  ChevronRight,
} from "lucide-react";

type NavItem = {
  label: string;
  path: string;
  icon: React.ComponentType<{ size?: number }>;
  children?: NavItem[];
  accent?: boolean;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

const navigationSections: NavSection[] = [
  {
    title: "SOINS",
    items: [
      { label: "Dashboard", path: "/", icon: LayoutDashboard },
      { label: "Patients", path: "/patients", icon: Users },
      { label: "Admissions", path: "/admissions", icon: ClipboardList },
    ],
  },
  {
    title: "URGENCES",
    items: [
      { label: "File d'attente", path: "/emergency", icon: Siren },
      { label: "Triage", path: "/emergency/triage", icon: ListOrdered },
      { label: "Orientation", path: "/emergency/orientation", icon: Route },
    ],
  },
  {
    title: "SERVICES",
    items: [
      { label: "Hospitalisation", path: "/hospitalization", icon: BedDouble },
      { label: "Maternité", path: "/maternity", icon: Baby },
      { label: "Pharmacie", path: "/pharmacy", icon: Pill },
      { label: "Laboratoire", path: "/lab", icon: FlaskConical },
      { label: "Imagerie", path: "/imaging", icon: Scan },
      { label: "Bloc Opératoire", path: "/surgery", icon: Scissors },
    ],
  },
  {
    title: "ADMIN",
    items: [
      { label: "Facturation", path: "/billing", icon: Receipt },
      { label: "Personnel", path: "/personnel", icon: UserCog },
      { label: "Qualité", path: "/quality", icon: Shield },
      { label: "Activité", path: "/activity", icon: Activity },
    ],
  },
  {
    title: "NATIONAL",
    items: [
      { label: "Pilotage", path: "/national", icon: Building2, accent: true },
      { label: "Reporting", path: "/reporting", icon: BarChart3, accent: true },
    ],
  },
];

export function Sidebar({ onLogout }: { onLogout: () => void }) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);

  const toggleSection = (title: string) => {
    setExpandedSection((prev) => (prev === title ? null : title));
  };

  // Find which section contains the current path to auto-expand it
  const activeSection = navigationSections.find((section) =>
    section.items.some((item) => {
      if (item.path === "/") return location.pathname === "/";
      return location.pathname.startsWith(item.path);
    })
  );

  const currentExpanded = expandedSection ?? activeSection?.title ?? null;

  return (
    <aside className={`sidebar ${collapsed ? "sidebar-collapsed" : ""}`}>
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-icon">GC</div>
        {!collapsed && (
          <div className="sidebar-logo-text">
            <span className="sidebar-logo-name">GuinéeCare</span>
            <span className="sidebar-logo-subtitle">Suite Hospitalière</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        {navigationSections.map((section) => (
          <div key={section.title} className="sidebar-section">
            {!collapsed && (
              <button
                className="sidebar-section-header"
                onClick={() => toggleSection(section.title)}
                aria-expanded={currentExpanded === section.title}
              >
                <span className="sidebar-section-title">{section.title}</span>
                {currentExpanded === section.title ? (
                  <ChevronDown size={14} />
                ) : (
                  <ChevronRight size={14} />
                )}
              </button>
            )}
            {(collapsed || currentExpanded === section.title) &&
              section.items.map((item) => {
                const isActive =
                  item.path === "/"
                    ? location.pathname === "/"
                    : location.pathname.startsWith(item.path);

                const Icon = item.icon;

                if (collapsed) {
                  return (
                    <Link
                      key={item.path}
                      to={item.path}
                      className={`sidebar-item-collapsed ${isActive ? "active" : ""} ${item.accent ? "sidebar-item-accent" : ""}`}
                      title={item.label}
                    >
                      <Icon size={20} />
                    </Link>
                  );
                }

                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`sidebar-item ${isActive ? "active" : ""} ${item.accent ? "sidebar-item-accent" : ""}`}
                  >
                    <Icon size={18} />
                    <span className="sidebar-item-label">{item.label}</span>
                    {isActive && <span className="sidebar-item-active-bar" />}
                  </Link>
                );
              })}
          </div>
        ))}
      </nav>

      {/* User info + Collapse toggle */}
      <div className="sidebar-footer">
        {!collapsed && (
          <div className="sidebar-user">
            <div className="sidebar-user-avatar">DR</div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">Dr. Utilisateur</span>
              <span className="sidebar-user-role">
                <span className="badge badge-green" style={{ fontSize: "10px", padding: "1px 6px" }}>
                  Médecin
                </span>
              </span>
            </div>
          </div>
        )}
        <div className="sidebar-footer-actions">
          <button
            className="sidebar-footer-btn sidebar-collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            title={collapsed ? "Développer" : "Réduire"}
          >
            <ChevronRight size={16} className={collapsed ? "" : "rotate-180"} />
          </button>
          <button
            className="sidebar-footer-btn sidebar-logout-btn"
            onClick={onLogout}
            title="Déconnexion"
          >
            <LogOut size={16} />
            {!collapsed && <span>Déconnexion</span>}
          </button>
        </div>
      </div>
    </aside>
  );
}
