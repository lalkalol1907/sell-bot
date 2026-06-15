import { useEffect, useState } from "react";
import { sellerApi, type Worker } from "../api";

const miniAppUrl = import.meta.env.VITE_MINIAPP_URL ?? "/miniapp/";

export function WorkersPage() {
  const [workers, setWorkers] = useState<Worker[]>([]);
  const [error, setError] = useState("");

  async function load() {
    const data = await sellerApi.workers();
    setWorkers(data.workers);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, []);

  async function setStatus(id: number, status: string) {
    await sellerApi.updateWorkerStatus(id, status);
    await load();
  }

  return (
    <div>
      <h2>Воркеры</h2>
      {error && <p className="error">{error}</p>}

      <p>
        <a href={miniAppUrl} target="_blank" rel="noreferrer">
          <button>Добавить воркера (Mini App)</button>
        </a>
      </p>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Телефон</th>
              <th>Статус</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {workers.map((w) => (
              <tr key={w.id}>
                <td>{w.id}</td>
                <td>{w.phone || "—"}</td>
                <td>{w.status}</td>
                <td className="row">
                  {w.status === "active" ? (
                    <button className="secondary" onClick={() => void setStatus(w.id, "paused")}>
                      Pause
                    </button>
                  ) : (
                    <button onClick={() => void setStatus(w.id, "active")}>Resume</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
