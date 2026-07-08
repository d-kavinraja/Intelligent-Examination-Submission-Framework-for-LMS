/**
 * React hooks for Student Portal data
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import {
  loginStudent,
  fetchDashboard,
  type DashboardData,
  type LoginResponse,
} from './api';

export interface PortalState {
  loading: boolean;
  initialized: boolean;
  error: string | null;
  session: LoginResponse | null;
  dashboard: DashboardData | null;
  lastUpdated: Date | null;
  refresh: () => Promise<void>;
}

export function useStudentPortal(): PortalState {
  const [loading, setLoading] = useState(true);
  const [initialized, setInitialized] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<LoginResponse | null>(null);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const sessionRef = useRef<LoginResponse | null>(null);

  const doLogin = useCallback(async (): Promise<LoginResponse> => {
    const credsStr = localStorage.getItem('student_credentials');
    if (!credsStr) {
      throw new Error('No credentials found');
    }
    const creds = JSON.parse(credsStr);
    
    const s = await loginStudent(
      creds.username,
      creds.password,
      creds.registerNumber
    );
    sessionRef.current = s;
    setSession(s);
    return s;
  }, []);

  const loadDashboard = useCallback(async (s?: LoginResponse) => {
    const activeSession = s || sessionRef.current;
    if (!activeSession) return;
    try {
      const data = await fetchDashboard(activeSession.session_id);
      setDashboard(data);
      setLastUpdated(new Date());
    } catch (err: unknown) {
      if (err instanceof Error) {
        // Session may be expired – try re-login once
        if (err.message.includes('401') || err.message.includes('session')) {
          const newSession = await doLogin();
          const data = await fetchDashboard(newSession.session_id);
          setDashboard(data);
          setLastUpdated(new Date());
        } else {
          throw err;
        }
      }
    }
  }, [doLogin]);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      await loadDashboard();
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [loadDashboard]);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        const s = await doLogin();
        if (!mounted) return;
        await loadDashboard(s);
      } catch (err: unknown) {
        if (mounted) {
          if (err instanceof Error) {
            setError(err.message);
          }
          setSession(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
          setInitialized(true);
        }
      }
    };

    init();

    // Real-time refresh every 30 seconds
    const interval = setInterval(() => {
      if (mounted && sessionRef.current) {
        loadDashboard().catch(() => {});
      }
    }, 30000);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [doLogin, loadDashboard]);

  return { loading, initialized, error, session, dashboard, lastUpdated, refresh };
}

// Simulated real-time stats that slowly drift over time
export function useRealtimeStats(baseStats: {
  totalCourses: number;
  completionRate: number;
  studyHours: number;
  avgTestScore: number;
  totalCerts: number;
}) {
  const [stats, setStats] = useState(baseStats);

  useEffect(() => {
    const interval = setInterval(() => {
      setStats(prev => ({
        ...prev,
        studyHours: prev.studyHours + Math.floor(Math.random() * 2),
        completionRate: Math.min(100, prev.completionRate + (Math.random() > 0.7 ? 1 : 0)),
      }));
    }, 60000); // update every minute

    return () => clearInterval(interval);
  }, []);

  return stats;
}
