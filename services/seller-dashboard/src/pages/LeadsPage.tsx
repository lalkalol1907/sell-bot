import { useEffect, useState } from "react";
import { sellerApi, type Lead } from "../api";

const statuses = ["", "new", "contacted", "closed", "spam"];

export function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState("");
  const [error, setError] = useState("");

  async function load(status = filter) {
    const data = await sellerApi.leads(status);
    setLeads(data.leads);
  }

  useEffect(() => {
    load().catch((e) => setError(e.message));
  }, [filter]);

  async function setStatus(id: number, status: string) {
    await sellerApi.updateLead(id, status);
    await load();
  }

  return (
    <div>
      <h2>Лиды</h2>
      {error && <p className="error">{error}</p>}

      <select value={filter} onChange={(e) => setFilter(e.target.value)}>
        {statuses.map((s) => (
          <option key={s || "all"} value={s}>
            {s || "Все"}
          </option>
        ))}
      </select>

      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Текст</th>
              <th>Уровень</th>
              <th>Статус</th>
              <th>Автор</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {leads.map((lead) => (
              <tr key={lead.id}>
                <td>{lead.raw_text}</td>
                <td>{lead.level}</td>
                <td>{lead.status}</td>
                <td>{lead.author_username || "—"}</td>
                <td className="row">
                  <button onClick={() => void setStatus(lead.id, "contacted")}>В работе</button>
                  <button className="secondary" onClick={() => void setStatus(lead.id, "closed")}>
                    Закрыть
                  </button>
                  <button className="danger" onClick={() => void setStatus(lead.id, "spam")}>
                    Спам
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
