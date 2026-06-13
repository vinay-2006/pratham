import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import axios from "axios";
import {
  type DoctorNotification,
  type PatientCase,
} from "./mock-data";

const API_BASE = "http://localhost:8000/api";

export type Role = "nurse" | "doctor";

interface CaseContextValue {
  patientCase: PatientCase | null;
  theme: "light" | "dark";
  toggleTheme: () => void;

  role: Role;
  setRole: (r: Role) => void;

  notifications: DoctorNotification[];
  isLoadingNotifications: boolean;
  approveNotification: (id: string) => void;
  rejectNotification: (id: string) => void;
  requestInfoNotification: (id: string) => void;
  pushNotification: (n: Omit<DoctorNotification, "id" | "timestamp" | "status">) => void;
  refreshNotifications: () => void;
  loadIntake: (intakeId: string) => Promise<void>;
  clearPatient: () => void;

  pendingCount: number;
  activeEmergencyCount: number;
}

const CaseContext = createContext<CaseContextValue | null>(null);

export function CaseProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const [role, setRole] = useState<Role>("nurse");
  const [notifications, setNotifications] = useState<DoctorNotification[]>([]);
  const [isLoadingNotifications, setIsLoadingNotifications] = useState(true);
  const [patientCase, setPatientCase] = useState<PatientCase | null>(null);

  const fetchDbPatientCase = useCallback(async (intakeId: string) => {
    try {
      const { data } = await axios.get<PatientCase>(`${API_BASE}/intake/${intakeId}`);
      if (data) {
        setPatientCase(data);
      }
    } catch (err) {
      console.error("[PRATHAM] Failed to fetch intake from DB:", err);
    }
  }, []);

  const loadIntake = useCallback(async (intakeId: string) => {
    localStorage.setItem("current_intake_id", intakeId);
    await fetchDbPatientCase(intakeId);
  }, [fetchDbPatientCase]);

  const clearPatient = useCallback(() => {
    setPatientCase(null);
    localStorage.removeItem("current_intake_id");
    localStorage.removeItem("current_patient_id");
  }, []);

  // ── Fetch notifications from the backend on mount ─────────────────────────
  const refreshNotifications = useCallback(async () => {
    try {
      setIsLoadingNotifications(true);
      // Try history endpoint (all statuses, 72h retention)
      let data: DoctorNotification[] = [];
      try {
        const res = await axios.get<DoctorNotification[]>(
          `${API_BASE}/investigations/history`
        );
        data = res.data || [];
      } catch {
        // Fallback to pending-only endpoint
        const res = await axios.get<DoctorNotification[]>(
          `${API_BASE}/investigations/pending`
        );
        data = res.data || [];
      }
      if (data) {
        setNotifications((curr) => {
          const dbIds = new Set(data.map((n) => n.intake_id));
          // Keep local notifications that are NOT in DB (e.g. just pushed from nurse intake)
          const localOnly = curr.filter(
            (n) => !dbIds.has(n.intake_id) && !data.some(d => d.id === n.id)
          );
          return [...data, ...localOnly];
        });
      }
    } catch {
      // API unavailable — start with empty list, no mock fallback
      console.warn("[PRATHAM] Could not fetch investigations from API.");
    } finally {
      setIsLoadingNotifications(false);
    }
  }, []);

  useEffect(() => {
    refreshNotifications();
  }, [refreshNotifications]);

  useEffect(() => {
    const savedId = localStorage.getItem("current_intake_id");
    if (savedId) {
      fetchDbPatientCase(savedId);
    }
  }, [fetchDbPatientCase]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const t = localStorage.getItem("pratham-theme");
    if (t === "dark" || t === "light") setTheme(t);
    const r = localStorage.getItem("pratham-role");
    if (r === "nurse" || r === "doctor") setRole(r);
  }, []);

  useEffect(() => {
    if (typeof document === "undefined") return;
    document.documentElement.classList.toggle("dark", theme === "dark");
    localStorage.setItem("pratham-theme", theme);
  }, [theme]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    localStorage.setItem("pratham-role", role);
  }, [role]);

  const approveNotification = useCallback((id: string) => {
    setNotifications((curr) => curr.map((n) => (n.id === id ? { ...n, status: "Approved" } : n)));
  }, []);
  const rejectNotification = useCallback((id: string) => {
    setNotifications((curr) => curr.map((n) => (n.id === id ? { ...n, status: "Rejected" } : n)));
  }, []);
  const requestInfoNotification = useCallback((id: string) => {
    setNotifications((curr) => curr.map((n) => (n.id === id ? { ...n, status: "Needs Info" } : n)));
  }, []);
  const pushNotification = useCallback(
    (n: Omit<DoctorNotification, "id" | "timestamp" | "status">) => {
      const now = new Date();
      const hh = String(now.getHours()).padStart(2, "0");
      const mm = String(now.getMinutes()).padStart(2, "0");
      setNotifications((curr) => [
        {
          ...n,
          id: `ntf-${Math.random().toString(36).slice(2, 8)}`,
          timestamp: `${hh}:${mm}`,
          status: "Pending Approval",
        },
        ...curr,
      ]);
    },
    [],
  );

  const pendingCount = useMemo(
    () => notifications.filter((n) => n.status === "Pending Approval").length,
    [notifications],
  );
  const activeEmergencyCount = useMemo(
    () => notifications.filter((n) => n.severity === "critical" || n.severity === "high").length,
    [notifications],
  );

  const value = useMemo<CaseContextValue>(
    () => ({
      patientCase,
      theme,
      toggleTheme: () => setTheme((t) => (t === "dark" ? "light" : "dark")),
      role,
      setRole,
      notifications,
      isLoadingNotifications,
      approveNotification,
      rejectNotification,
      requestInfoNotification,
      pushNotification,
      refreshNotifications,
      loadIntake,
      clearPatient,
      pendingCount,
      activeEmergencyCount,
    }),
    [
      patientCase,
      theme,
      role,
      notifications,
      isLoadingNotifications,
      approveNotification,
      rejectNotification,
      requestInfoNotification,
      pushNotification,
      refreshNotifications,
      loadIntake,
      clearPatient,
      pendingCount,
      activeEmergencyCount,
    ],
  );

  return <CaseContext.Provider value={value}>{children}</CaseContext.Provider>;
}

export function useCase() {
  const ctx = useContext(CaseContext);
  if (!ctx) throw new Error("useCase must be used within CaseProvider");
  return ctx;
}
