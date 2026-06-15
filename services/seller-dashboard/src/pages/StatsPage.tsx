import { useEffect, useState } from "react";
import { sellerApi, type Stats } from "../api";

export function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    sellerApi
      .stats()
      .then(setStats)
      .catch((e) => setError(e.message));
  }, []);

  if (error) return <p className="error">{error}</p>;
  if (!stats) return <p>Загрузка…</p>;

  return (
    <div>
      <h2>Статистика (30 дней)</h2>
      <div className="grid">
        <div className="stat">
          <strong>{stats.total}</strong>
          <span>Всего лидов</span>
        </div>
        <div className="stat">
          <strong>{stats.new_count}</strong>
          <span>Новые</span>
        </div>
        <div className="stat">
          <strong>{stats.contacted}</strong>
          <span>В работе</span>
        </div>
        <div className="stat">
          <strong>{stats.closed}</strong>
          <span>Закрыты</span>
        </div>
        <div className="stat">
          <strong>{stats.spam}</strong>
          <span>Спам</span>
        </div>
      </div>
    </div>
  );
}
