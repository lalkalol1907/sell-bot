import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../auth";

export function Layout() {
  const { seller, logout } = useAuth();

  return (
    <div className="layout">
      <aside className="sidebar">
        <h1>Sellbot</h1>
        <p style={{ opacity: 0.8, marginBottom: 16 }}>{seller?.full_name || seller?.username}</p>
        <nav>
          <NavLink to="/" end>
            Статистика
          </NavLink>
          <NavLink to="/catalog">Каталог</NavLink>
          <NavLink to="/leads">Лиды</NavLink>
          <NavLink to="/workers">Воркеры</NavLink>
        </nav>
        <button className="secondary" style={{ marginTop: 24 }} onClick={() => void logout()}>
          Выйти
        </button>
      </aside>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
