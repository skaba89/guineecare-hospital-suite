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
  Bell,
  MessageSquare,
  LogOut,
  ChevronDown,
  ChevronRight,
  Search,
} from "lucide-react";
import { CurrentUser, getRoleLabel, getUserInitials, getUserDisplayName } from "../services/authService";
import { useNavVisibility } from "../components/ProtectedRoute";

type NavItem = {
  label: string;
  path: string;
  icon: React.ComponentType<{ size?: number }>;
  children?: NavItem[];
  accent?: boolean;
  visible?: boolean;
};

type NavSection = {
  title: string;
  items: NavItem[];
};

export function Sidebar({ onLogout, currentUser }: { onLogout: () => void | Promise<void>; currentUser: CurrentUser | null }) {
  const location = useLocation();
  const [collapsed, setCollapsed] = useState(false);
  const [expandedSection, setExpandedSection] = useState<string | null>(null);
  const navVisibility = useNavVisibility();

  const navigationSections: NavSection[] = [
    {
      title: "SOINS",
      items: [
        { label: "Dashboard", path: "/", icon: LayoutDashboard, visible: navVisibility.canSeeDashboard },
        { label: "Notifications", path: "/notifications", icon: Bell, visible: true },
        { label: "Patients", path: "/patients", icon: Users, visible: navVisibility.canSeePatients },
        { label: "Admissions", path: "/admissions", icon: ClipboardList, visible: navVisibility.canSeeAdmissions },
      ],
    },
    {
      title: "URGENCES",
      items: [
        { label: "File d'attente", path: "/emergency", icon: Siren, visible: navVisibility.canSeeEmergency },
        { label: "Triage", path: "/emergency/triage", icon: ListOrdered, visible: navVisibility.canSeeEmergency },
        { label: "Orientation", path: "/emergency/orientation", icon: Route, visible: navVisibility.canSeeEmergency },
      ],
    },
    {
      title: "SERVICES",
      items: [
        { label: "Hospitalisation", path: "/hospitalization", icon: BedDouble, visible: navVisibility.canSeeHospitalization },
        { label: "Maternité", path: "/maternity", icon: Baby, visible: navVisibility.canSeeMaternity },
        { label: "Pharmacie", path: "/pharmacy", icon: Pill, visible: navVisibility.canSeePharmacy },
        { label: "Laboratoire", path: "/lab", icon: FlaskConical, visible: navVisibility.canSeeLab },
        { label: "Imagerie", path: "/imaging", icon: Scan, visible: navVisibility.canSeeImaging },
        { label: "Bloc Opératoire", path: "/surgery", icon: Scissors, visible: navVisibility.canSeeSurgery },
      ],
    },
    {
      title: "ADMIN",
      items: [
        { label: "Facturation", path: "/billing", icon: Receipt, visible: navVisibility.canSeeBilling },
        { label: "Personnel", path: "/personnel", icon: UserCog, visible: navVisibility.canSeePersonnel },
        { label: "Qualité", path: "/quality", icon: Shield, visible: navVisibility.canSeeQuality },
        { label: "Activité", path: "/activity", icon: Activity, visible: navVisibility.canSeeActivity },
      ],
    },
    {
      title: "SYSTÈME",
      items: [
        { label: "Utilisateurs", path: "/users", icon: Users, visible: navVisibility.canSeeUsers },
        { label: "Rôles & Permissions", path: "/rbac", icon: Shield, visible: navVisibility.canSeeRbac },
        { label: "Établissements", path: "/facilities", icon: Building2, visible: navVisibility.canSeeFacilities },
        { label: "Départements", path: "/departments", icon: Building2, visible: navVisibility.canSeeDepartments },
        { label: "Journal d'audit", path: "/audit", icon: Shield, visible: navVisibility.canSeeAudit },
        { label: "SMS Admin", path: "/sms-admin", icon: MessageSquare, visible: navVisibility.canSeeSmsAdmin },
      ],
    },
    {
      title: "NATIONAL",
      items: [
        { label: "Pilotage", path: "/national", icon: Building2, accent: true, visible: navVisibility.canSeeNational },
        { label: "Reporting", path: "/reporting", icon: BarChart3, accent: true, visible: navVisibility.canSeeReporting },
      ],
    },
  ];

  // Filter out sections with no visible items
  const visibleSections = navigationSections
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => item.visible !== false),
    }))
    .filter((section) => section.items.length > 0);

  const toggleSection = (title: string) => {
    setExpandedSection((prev) => (prev === title ? null : title));
  };

  // Find which section contains the current path to auto-expand it
  const activeSection = visibleSections.find((section) =>
    section.items.some((item) => {
      if (item.path === "/") return location.pathname === "/";
      return location.pathname.startsWith(item.path);
    })
  );

  const currentExpanded = expandedSection ?? activeSection?.title ?? null;

  const initials = currentUser ? getUserInitials(currentUser) : "GC";
  const displayName = currentUser ? getUserDisplayName(currentUser) : "Utilisateur";
  const roleLabel = currentUser ? getRoleLabel(currentUser.role) : "";
  const roleBadgeClass: Record<string, string> = {
    SUPER_ADMIN: "badge-red",
    ADMIN: "badge-yellow",
    DOCTOR: "badge-blue",
    NURSE: "badge-green",
    PHARMACIST: "badge-green",
    LAB_TECH: "badge-gray",
    CASHIER: "badge-gray",
    MIDWIFE: "badge-yellow",
  };
  const badgeClass = currentUser ? roleBadgeClass[currentUser.role] || "badge-gray" : "badge-gray";

  // Facility name display
  const facilityLabel = currentUser?.facility_id ? "Établissement connecté" : "Vue nationale";

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
      {!collapsed && (
        <button
          type="button"
          className="search-trigger"
          onClick={() => window.dispatchEvent(new Event("guineecare:open-search"))}
        >
          <Search size={14} />
          <span>Rechercher…</span>
          <kbd>Ctrl K</kbd>
        </button>
      )}
      <nav className="sidebar-nav">
        {visibleSections.map((section) => (
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
            <div className="sidebar-user-avatar">{initials}</div>
            <div className="sidebar-user-info">
              <span className="sidebar-user-name">{displayName}</span>
              <span className="sidebar-user-role">
                <span className={`badge ${badgeClass}`} style={{ fontSize: "10px", padding: "1px 6px" }}>
                  {roleLabel}
                </span>
              </span>
              <span className="sidebar-user-facility" style={{ fontSize: "10px", color: "#94a3b8" }}>
                {facilityLabel}
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
