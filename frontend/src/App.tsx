import { useEffect, useState } from "react";

type HealthStatus = {
  status: string;
};

export default function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const response = await fetch("/api/health");
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }
        const data: HealthStatus = await response.json();
        setHealth(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Unknown error");
      }
    };

    load();
  }, []);

  return (
    <main className="page">
      <header className="hero">
        <h1>AI Recruiter Assistant</h1>
        <p>Сервис автоматизации создания вакансий и сопоставления с резюме.</p>
      </header>

      <section className="card">
        <h2>Состояние API</h2>
        {error && <p className="error">Ошибка: {error}</p>}
        {health ? <p className="ok">Статус: {health.status}</p> : <p>Загрузка...</p>}
      </section>
    </main>
  );
}
