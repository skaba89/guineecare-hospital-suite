import type { ReactNode } from "react";
import { ToastContainer } from "../components/Toast";
import { ErrorBoundary } from "../components/ErrorBoundary";
import { CommandPalette } from "../components/CommandPalette";
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
        <ErrorBoundary>
          {children}
        </ErrorBoundary>
      </main>
      <ToastContainer />
      <CommandPalette />
    </div>
  );
}
