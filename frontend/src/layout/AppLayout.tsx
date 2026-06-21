import type { ReactNode } from "react";
import { ToastContainer } from "../components/Toast";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { CommandPalette } from "../components/CommandPalette";
import { LanguageToggle } from "../components/LanguageToggle";
import { RealtimeStatus } from "../components/RealtimeStatus";
import { Sidebar } from "./Sidebar";
import { CurrentUser } from "../services/authService";

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
  return (
    <div className="app-shell">
      <Sidebar onLogout={onLogout} currentUser={currentUser} />
      <main className="main-content">
        <header
          className="app-header"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "flex-end",
            gap: 12,
            padding: "8px 16px",
            borderBottom: "1px solid #e2e8f0",
            background: "white",
          }}
        >
          <RealtimeStatus />
          <LanguageToggle />
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
