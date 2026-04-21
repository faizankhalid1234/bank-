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

  const login = useCallback(async ({ identifier, password }) => {
    await ensureCsrf();
    const data = await api.post("/auth/login/", {
      identifier: (identifier || "").trim(),
      password,
    });
    if (data.token) setAuthToken(data.token);
    setMe({ user: data.user, account: data.account });
    return data;
  }, []);

  const demoLogin = useCallback(async () => {
    await ensureCsrf();
    const data = await api.post("/auth/demo-login/", {});
    if (data.token) setAuthToken(data.token);
    setMe({ user: data.user, account: data.account });
    return data;
  }, []);

  const registerRequest = useCallback(async (payload) => {
    await ensureCsrf();
    return api.post("/auth/register/request/", payload);
  }, []);

  const registerConfirm = useCallback(async ({ pendingId, emailOtp }) => {
    await ensureCsrf();
    const data = await api.post("/auth/register/confirm/", {
      pending_id: pendingId,
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
      demoLogin,
      registerRequest,
      registerConfirm,
      logout,
    }),
    [me, loading, refreshMe, login, demoLogin, registerRequest, registerConfirm, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
