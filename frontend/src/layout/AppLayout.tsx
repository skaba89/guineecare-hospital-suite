import type { ReactNode } from "react";
import { ToastContainer } from "../components/Toast";
import { Sidebar } from "./Sidebar";

export function AppLayout({
  onLogout,
  children,
}: {
  onLogout: () => void;
  children: ReactNode;
}) {
  return (
    <div className="app-shell">
      <Sidebar onLogout={onLogout} />
      <main className="main-content">{children}</main>
      <ToastContainer />
    </div>
  );
}
