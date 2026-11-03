/**
 * PRATHAM — client auth + role-based access.
 *
 * The session (Supabase access/refresh token + user) lives in localStorage.
 * Importing this module installs interceptors so EVERY axios/fetch call to the
 * PRATHAM API automatically carries `Authorization: Bearer <token>`; a 401 clears
 * the session and sends the user to /login.
 */
import axios from "axios";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { API_BASE, API_HOST } from "./api-config";

export type Role = "nurse" | "doctor" | "admin";

export interface AuthUser {
  id: string;
  email: string;
  role: Role;
  name: string;
  department: string;
}

interface Session {
  access_token: string;
  refresh_token: string;
  expires_at: number;
  user: AuthUser;
}

const STORAGE_KEY = "pratham-session";

// ── Role → what each user may open ───────────────────────────────────────────
export const ROLE_HOME: Record<Role, string> = {
  nurse: "/nurse/dashboard",
  doctor: "/doctor/dashboard",
  admin: "/admin",
};

/** Path prefixes each role may visit inside the app. Mirrors the backend ACCESS_RULES. */
export const ROLE_PATHS: Record<Role, string[]> = {
  nurse: ["/nurse", "/investigations", "/copilot", "/command-center", "/search"],
  doctor: [
    "/doctor",
    "/nurse/registry",
    "/dashboard",
    "/copilot",
    "/imaging",
    "/differential",
    "/explainability",
    "/confidence",
    "/command-center",
    "/comparison",
    "/search",
    "/knowledge",
    "/architecture",
    "/evidence",
    "/review",
    "/investigations",
  ],
  admin: ["/admin", "/command-center", "/architecture", "/knowledge", "/copilot"],
};

export function canAccess(role: Role, pathname: string): boolean {
  return ROLE_PATHS[role].some((p) => pathname === p || pathname.startsWith(p + "/"));
}

// ── Session storage ──────────────────────────────────────────────────────────
function readSession(): Session | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Session) : null;
  } catch {
    return null;
  }
}

function writeSession(s: Session | null) {
  if (typeof window === "undefined") return;
  if (s) localStorage.setItem(STORAGE_KEY, JSON.stringify(s));
  else localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new Event("pratham-auth-change"));
}

export function getAccessToken(): string | null {
  return readSession()?.access_token ?? null;
}

function isApiUrl(url: string | undefined): boolean {
  if (!url) return false;
  return url.startsWith(API_HOST) || url.startsWith(API_BASE) || url.startsWith("/api");
}

function isAuthEndpoint(url: string | undefined): boolean {
  return !!url && /\/api\/auth\/(login|refresh)/.test(url);
}

function forceLogout() {
  writeSession(null);
  if (typeof window !== "undefined" && window.location.pathname !== "/login") {
    window.location.assign("/login");
  }
}

// ── Interceptors (installed once, client only) ───────────────────────────────
if (typeof window !== "undefined" && !(window as unknown as { __prathamAuth?: boolean }).__prathamAuth) {
  (window as unknown as { __prathamAuth?: boolean }).__prathamAuth = true;

  axios.interceptors.request.use((config) => {
    const token = getAccessToken();
    const url = config.url?.startsWith("http") || config.url?.startsWith("/") ? config.url : `${config.baseURL ?? ""}${config.url ?? ""}`;
    if (token && isApiUrl(url) && !isAuthEndpoint(url)) {
      config.headers.set("Authorization", `Bearer ${token}`);
    }
    return config;
  });
  axios.interceptors.response.use(
    (r) => r,
    (err) => {
      if (err?.response?.status === 401 && !isAuthEndpoint(err.config?.url)) forceLogout();
      return Promise.reject(err);
    },
  );

  const nativeFetch = window.fetch.bind(window);
  window.fetch = async (input, init) => {
    const url = typeof input === "string" ? input : input instanceof URL ? input.href : input.url;
    if (isApiUrl(url) && !isAuthEndpoint(url)) {
      const token = getAccessToken();
      if (token) {
        const headers = new Headers(init?.headers ?? (input instanceof Request ? input.headers : undefined));
        headers.set("Authorization", `Bearer ${token}`);
        init = { ...init, headers };
      }
    }
    const res = await nativeFetch(input, init);
    if (res.status === 401 && isApiUrl(url) && !isAuthEndpoint(url)) forceLogout();
    return res;
  };
}

// ── React context ────────────────────────────────────────────────────────────
interface AuthContextValue {
  user: AuthUser | null;
  ready: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const sync = () => setUser(readSession()?.user ?? null);
    sync();
    setReady(true);
    window.addEventListener("pratham-auth-change", sync);
    window.addEventListener("storage", sync);
    return () => {
      window.removeEventListener("pratham-auth-change", sync);
      window.removeEventListener("storage", sync);
    };
  }, []);

  // Keep the Supabase token fresh (access tokens last ~1h).
  useEffect(() => {
    if (!user) return;
    const id = window.setInterval(async () => {
      const s = readSession();
      if (!s || s.expires_at * 1000 - Date.now() > 5 * 60_000) return;
      try {
        const { data } = await axios.post<Session>(`${API_BASE}/auth/refresh`, { refresh_token: s.refresh_token });
        writeSession(data);
      } catch {
        forceLogout();
      }
    }, 60_000);
    return () => window.clearInterval(id);
  }, [user]);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await axios.post<Session>(`${API_BASE}/auth/login`, { email, password });
    writeSession(data);
    return data.user;
  }, []);

  const logout = useCallback(() => {
    writeSession(null);
    ["current_intake_id", "current_patient_id"].forEach((k) => localStorage.removeItem(k));
  }, []);

  const value = useMemo(() => ({ user, ready, login, logout }), [user, ready, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
