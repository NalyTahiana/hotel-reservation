import { createContext, useCallback, useContext, useEffect, useState } from "react";
import * as auth from "../services/auth";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      try {
        await auth.fetchCsrf(); // pose le cookie CSRF
        setUser(await auth.fetchMe());
      } catch {
        setUser(null); // non connecté
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async (email, password) => {
    const u = await auth.login(email, password);
    setUser(u);
    return u;
  }, []);
  const register = useCallback(async (payload) => {
    const u = await auth.register(payload);
    setUser(u);
    return u;
  }, []);
  const logout = useCallback(async () => {
    await auth.logout();
    setUser(null);
    await auth.fetchCsrf(); // le jeton change après la déconnexion
  }, []);
  const updateProfile = useCallback(async (payload) => {
    const u = await auth.updateProfile(payload);
    setUser(u);
    return u;
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, isAdmin: !!user?.is_staff, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
}
