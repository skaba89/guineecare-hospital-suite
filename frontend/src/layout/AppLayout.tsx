import { Sidebar } from "./Sidebar";

export function AppLayout({
  currentPage,
  onSelectPage,
  onLogout,
  children,
}: {
  currentPage: string;
  onSelectPage: (page: string) => void;
  onLogout: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="app-shell">
      <Sidebar currentPage={currentPage} onSelectPage={onSelectPage} onLogout={onLogout} />
      <main className="main-content">{children}</main>
    </div>
  );
}
