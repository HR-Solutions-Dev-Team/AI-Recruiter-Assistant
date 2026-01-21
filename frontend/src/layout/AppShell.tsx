import Sidebar from "../components/sidebar/Sidebar";

export default function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />
      <section className="secondary-panel" aria-hidden="true" />
      <main className="main-content" aria-label="Основной контент" />
    </div>
  );
}
