export const navigationItems = [
  "Dashboard",
  "Patients",
  "Admissions",
  "Urgences",
  "Pharmacie",
  "Laboratoire",
  "Facturation",
];

export function Sidebar({
  currentPage,
  onSelectPage,
  onLogout,
}: {
  currentPage: string;
  onSelectPage: (page: string) => void;
  onLogout: () => void;
}) {
  return (
    <aside className="sidebar">
      <h1>GuineeCare</h1>
      {navigationItems.map((item) => (
        <button
          key={item}
          className={`nav-button ${currentPage === item ? "active" : ""}`}
          onClick={() => onSelectPage(item)}
        >
          {item}
        </button>
      ))}
      <button className="nav-button" onClick={onLogout}>
        Deconnexion
      </button>
    </aside>
  );
}
