/**
 * Auth state with Zustand.
 * Persists tokens in localStorage and exposes actions for login/logout.
 */
import { create } from "zustand";
import type { User, LoginPayload, RegisterPayload } from "@/types";
import { loginApi, logoutApi, getMeApi, registerApi } from "../api/authApi";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;

  login: (payload: LoginPayload) => Promise<void>;
  register: (payload: RegisterPayload) => Promise<void>;
  logout: () => Promise<void>;
  fetchMe: () => Promise<void>;
  hydrateFromStorage: () => Promise<void>;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: !!localStorage.getItem("access_token"),
  isLoading: false,

  login: async (payload) => {
    set({ isLoading: true });
    try {
      const data = await loginApi(payload);
      localStorage.setItem("access_token", data.access);
      localStorage.setItem("refresh_token", data.refresh);
      set({ user: data.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  register: async (payload) => {
    set({ isLoading: true });
    try {
      const data = await registerApi(payload);
      localStorage.setItem("access_token", data.tokens.access);
      localStorage.setItem("refresh_token", data.tokens.refresh);
      set({ user: data.user, isAuthenticated: true });
    } finally {
      set({ isLoading: false });
    }
  },

  logout: async () => {
    const refresh = localStorage.getItem("refresh_token") ?? "";
    try {
      await logoutApi(refresh);
    } catch {
      // Ignore errors on logout (token might already be expired)
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      set({ user: null, isAuthenticated: false });
    }
  },

  fetchMe: async () => {
    set({ isLoading: true });
    try {
      const user = await getMeApi();
      set({ user, isAuthenticated: true });
    } catch {
      set({ user: null, isAuthenticated: false });
    } finally {
      set({ isLoading: false });
    }
  },

  hydrateFromStorage: async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;
    const { fetchMe } = useAuthStore.getState();
    await fetchMe();
  },
}));
