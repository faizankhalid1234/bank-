import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, ensureCsrf, setAuthToken } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [me, setMe] = useState(null);
  const [loading, setLoading] = useState(true);

  const refreshMe = useCallback(async () => {
    try {
      await ensureCsrf();
      const data = await api.get("/me/");
      setMe(data);
    } catch {
      setAuthToken(null);
      setMe(null);
    }
  }, []);

  useEffect(() => {
    (async () => {
      try {
        await ensureCsrf();
        const data = await api.get("/me/");
        setMe(data);
      } catch {
        setAuthToken(null);
        setMe(null);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const login = useCallback(async ({ username, email, password }) => {
    await ensureCsrf();
    const data = await api.post("/auth/login/", { username, email, password });
    if (data.token) setAuthToken(data.token);
    setMe({ user: data.user, account: data.account });
    return data;
  }, []);

  const registerRequest = useCallback(async (payload) => {
    await ensureCsrf();
    return api.post("/auth/register/request/", payload);
  }, []);

  const registerConfirm = useCallback(async ({ pendingId, otp, emailOtp }) => {
    await ensureCsrf();
    const data = await api.post("/auth/register/confirm/", {
      pending_id: pendingId,
      otp,
      email_otp: emailOtp,
    });
    if (data.token) setAuthToken(data.token);
    setMe({ user: data.user, account: data.account });
    return data;
  }, []);

  const logout = useCallback(async () => {
    await ensureCsrf();
    try {
      await api.post("/auth/logout/", {});
    } finally {
      setAuthToken(null);
      setMe(null);
    }
  }, []);

  const value = useMemo(
    () => ({
      me,
      loading,
      user: me?.user ?? null,
      account: me?.account ?? null,
      isAuthenticated: Boolean(me?.user),
      refreshMe,
      login,
      registerRequest,
      registerConfirm,
      logout,
    }),
    [me, loading, refreshMe, login, registerRequest, registerConfirm, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
