import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth";
import { Layout } from "./components/Layout";
import { CatalogPage } from "./pages/CatalogPage";
import { LeadsPage } from "./pages/LeadsPage";
import { LoginPage } from "./pages/LoginPage";
import { StatsPage } from "./pages/StatsPage";
import { WorkersPage } from "./pages/WorkersPage";

function ProtectedRoutes() {
  const { seller, loading } = useAuth();

  if (loading) return <p style={{ padding: 24 }}>Загрузка…</p>;
  if (!seller) return <Navigate to="/login" replace />;

  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<StatsPage />} />
        <Route path="catalog" element={<CatalogPage />} />
        <Route path="leads" element={<LeadsPage />} />
        <Route path="workers" element={<WorkersPage />} />
      </Route>
    </Routes>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Routes>
        <Route path="/login" element={<LoginPageGate />} />
        <Route path="/*" element={<ProtectedRoutes />} />
      </Routes>
    </AuthProvider>
  );
}

function LoginPageGate() {
  const { seller, loading } = useAuth();
  if (loading) return <p style={{ padding: 24 }}>Загрузка…</p>;
  if (seller) return <Navigate to="/" replace />;
  return <LoginPage />;
}
