import { createContext, useContext, useMemo, useState } from "react";
import api from "../services/api.js";

const AuthContext = createContext(null);

const storageKeys = {
  token: "jwtToken",
  username: "username",
  role: "role",
};

export function AuthProvider({ children }) {
  const [auth, setAuth] = useState(() => ({
    token: localStorage.getItem(storageKeys.token),
    username: localStorage.getItem(storageKeys.username),
    role: localStorage.getItem(storageKeys.role),
  }));

  const login = async ({ username, password }) => {
    // Use Mock Auth ONLY in Production (for GitHub Pages demo)
    // In local development, always use the real backend
    const isProduction = import.meta.env.PROD;
    
    if (isProduction && username === "owner2" && password === "admin123") {
      const token = "mock-jwt-token";
      const responseUsername = "owner2";
      const role = "OWNER";

      localStorage.setItem(storageKeys.token, token);
      localStorage.setItem(storageKeys.username, responseUsername);
      localStorage.setItem(storageKeys.role, role);

      const nextAuth = { token, username: responseUsername, role };
      setAuth(nextAuth);
      return nextAuth;
    }

    // Real API call for local development or other production users

    const response = await api.post("/auth/login", { username, password });
    const { token, username: responseUsername, role } = response.data;

    localStorage.setItem(storageKeys.token, token);
    localStorage.setItem(storageKeys.username, responseUsername);
    localStorage.setItem(storageKeys.role, role);

    const nextAuth = { token, username: responseUsername, role };
    setAuth(nextAuth);
    return nextAuth;
  };

  const logout = () => {
    localStorage.removeItem(storageKeys.token);
    localStorage.removeItem(storageKeys.username);
    localStorage.removeItem(storageKeys.role);
    setAuth({ token: null, username: null, role: null });
  };

  const value = useMemo(
    () => ({
      ...auth,
      isAuthenticated: Boolean(auth.token),
      login,
      logout,
    }),
    [auth],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
