import { useEffect, useState, type ReactNode } from "react";
import { useLocation } from "react-router-dom";
import { ToastContainer } from "../components/Toast";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { CommandPalette } from "../components/CommandPalette";
import { LanguageToggle } from "../components/LanguageToggle";
import { RealtimeStatus } from "../components/RealtimeStatus";
import { ThemeToggle } from "../components/ThemeToggle";
import { Sidebar } from "./Sidebar";
import { CurrentUser } from "../services/authService";
import { useT } from "../i18n";
import { Menu, X } from "lucide-react";

/**
 * Map path → page title for the topbar breadcrumb.
 * Keeps the topbar informative without coupling to a router schema.
 */
function getPageTitle(pathname: string, t: (key: string) => string): string {
  // Exact matches first
  const exact: Record<string, string> = {
    "/": t("nav.dashboard"),
    "/patients": t("nav.patients"),
    "/admissions": t("nav.admissions"),
    "/emergency": t("nav.emergency.queue"),
    "/emergency/triage": t("nav.emergency.triage"),
    "/emergency/orientation": t("nav.emergency.orientation"),
    "/hospitalization": t("nav.hospitalization"),
    "/maternity": t("nav.maternity"),
    "/pharmacy": t("nav.pharmacy"),
    "/lab": t("nav.laboratory"),
    "/imaging": t("nav.imaging"),
    "/surgery": t("nav.surgery"),
    "/billing": t("nav.billing"),
    "/personnel": t("nav.personnel"),
    "/personnel/planning": t("nav.planning"),
    "/personnel/leaves": t("nav.leaves"),
    "/quality": t("nav.quality"),
    "/activity": t("nav.activity"),
    "/users": t("nav.users"),
    "/rbac": t("nav.rbac"),
    "/facilities": t("nav.facilities"),
    "/departments": t("nav.departments"),
    "/audit": t("nav.audit"),
    "/sms-admin": t("nav.sms_admin"),
    "/tasks-admin": t("nav.tasks_admin"),
    "/national": t("nav.national"),
    "/reporting": t("nav.reporting"),
    "/notifications": t("nav.notifications"),
  };
  if (exact[pathname]) return exact[pathname];
  // Patient detail page
  if (pathname.startsWith("/patients/")) return t("nav.patients");
  return "GuinéeCare";
}

export function AppLayout({
  onLogout,
  currentUser,
  getPatientName,
  getStaffName,
  children,
}: {
  onLogout: () => void | Promise<void>;
  currentUser: CurrentUser | null;
  getPatientName: (id: string) => string;
  getStaffName: (id: string) => string;
  children: ReactNode;
}) {
  const t = useT();
  const location = useLocation();
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);

  // Close mobile sidebar on route change
  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  // Close on Escape
  useEffect(() => {
    if (!mobileSidebarOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileSidebarOpen(false);
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [mobileSidebarOpen]);

  const pageTitle = getPageTitle(location.pathname, t);

  return (
    <div className={`app-shell ${mobileSidebarOpen ? "sidebar-drawer-active" : ""}`}>
      {/* Mobile overlay */}
      {mobileSidebarOpen && (
        <div
          className="sidebar-mobile-overlay sidebar-mobile-open"
          onClick={() => setMobileSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <Sidebar
        onLogout={onLogout}
        currentUser={currentUser}
        mobileOpen={mobileSidebarOpen}
        onMobileClose={() => setMobileSidebarOpen(false)}
      />

      <main className="main-content">
        <header className="topbar" role="banner">
          <div className="topbar-left">
            <button
              type="button"
              className="topbar-mobile-menu-btn"
              onClick={() => setMobileSidebarOpen(true)}
              aria-label="Ouvrir le menu"
              title="Menu"
            >
              <Menu size={18} />
            </button>
            <h2 className="topbar-title">{pageTitle}</h2>
          </div>
          <div className="topbar-right">
            <RealtimeStatus />
            <ThemeToggle />
            <LanguageToggle />
          </div>
        </header>
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>

      <ToastContainer />
      <CommandPalette />
    </div>
  );
}
