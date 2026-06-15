import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { authApi, type Seller } from "./api";

type AuthState = {
  seller: Seller | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [seller, setSeller] = useState<Seller | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      setSeller(await authApi.me());
    } catch {
      setSeller(null);
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    await authApi.logout();
    setSeller(null);
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <AuthContext.Provider value={{ seller, loading, refresh, logout }}>{children}</AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth outside AuthProvider");
  return ctx;
}
