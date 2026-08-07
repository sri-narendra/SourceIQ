"use client";

import { useCallback, useEffect, useState } from "react";

import { authApi } from "@/services/api-endpoints";
import type { IUser } from "@/types";

export function useAuth() {
  const [user, setUser] = useState<IUser | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    try {
      setUser(await authApi.me());
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const login = async (email: string, password: string) => {
    await authApi.login(email, password);
    await load();
  };

  const logout = () => {
    localStorage.removeItem("token");
    setUser(null);
  };

  return { user, loading, login, logout };
}