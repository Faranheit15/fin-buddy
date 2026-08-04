"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  clearBrowserSession,
  fetchMe,
  logoutApi,
  persistBrowserSession,
  readBrowserSession,
  refreshSession,
  type MeResponse,
} from "@/lib/api/auth";
import { tokensFromBackendSession } from "@/lib/auth/session";
import { env } from "@/lib/env";

type AuthContextValue = {
  ready: boolean;
  profile: MeResponse["user"] | null;
  organizations: MeResponse["organizations"];
  accessToken: string | null;
  refreshProfile: () => Promise<void>;
  signOut: () => Promise<void>;
  /** Apply tokens from a backend AuthResponse and load profile. */
  applyBackendSession: (session: {
    access_token?: string | null;
    refresh_token?: string | null;
    expires_in?: number | null;
    expires_at?: number | null;
  }) => Promise<void>;
  configured: boolean;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  // Backend API is the auth authority; configured when API URL is set.
  const configured = Boolean(env.NEXT_PUBLIC_API_URL);
  const [ready, setReady] = useState(false);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [profile, setProfile] = useState<MeResponse["user"] | null>(null);
  const [organizations, setOrganizations] = useState<MeResponse["organizations"]>(
    [],
  );

  const loadProfile = useCallback(async (token: string) => {
    try {
      const me = await fetchMe(token);
      setProfile(me.user);
      setOrganizations(me.organizations);
    } catch {
      setProfile(null);
      setOrganizations([]);
    }
  }, []);

  const applyBackendSession = useCallback(
    async (session: {
      access_token?: string | null;
      refresh_token?: string | null;
      expires_in?: number | null;
      expires_at?: number | null;
    }) => {
      const stored = tokensFromBackendSession(session);
      if (!stored) {
        throw new Error("Backend did not return an access token");
      }
      await persistBrowserSession(stored);
      setAccessToken(stored.accessToken);
      await loadProfile(stored.accessToken);
    },
    [loadProfile],
  );

  useEffect(() => {
    let mounted = true;

    void (async () => {
      try {
        const session = await readBrowserSession();
        if (!session) {
          if (mounted) setReady(true);
          return;
        }

        // Refresh if expired / near expiry
        const now = Math.floor(Date.now() / 1000);
        if (
          session.refreshToken &&
          session.expiresAt &&
          session.expiresAt < now + 60
        ) {
          try {
            const refreshed = await refreshSession(session.refreshToken);
            if (refreshed.session?.access_token) {
              await applyBackendSession(refreshed.session);
              if (mounted) setReady(true);
              return;
            }
          } catch {
            await clearBrowserSession();
            if (mounted) {
              setAccessToken(null);
              setProfile(null);
              setOrganizations([]);
              setReady(true);
            }
            return;
          }
        }

        if (!mounted) return;
        // Unblock dashboard fetches as soon as we have a token; profile loads in parallel.
        setAccessToken(session.accessToken);
        setReady(true);
        await loadProfile(session.accessToken);
      } catch {
        if (mounted) {
          setAccessToken(null);
          setProfile(null);
          setOrganizations([]);
          setReady(true);
        }
      }
    })();

    return () => {
      mounted = false;
    };
  }, [applyBackendSession, loadProfile]);

  const signOut = useCallback(async () => {
    if (accessToken) {
      try {
        await logoutApi(accessToken);
      } catch {
        // best-effort backend logout
      }
    }
    await clearBrowserSession();
    setAccessToken(null);
    setProfile(null);
    setOrganizations([]);
  }, [accessToken]);

  const value = useMemo<AuthContextValue>(
    () => ({
      ready,
      profile,
      organizations,
      accessToken,
      refreshProfile: async () => {
        if (accessToken) await loadProfile(accessToken);
      },
      signOut,
      applyBackendSession,
      configured,
    }),
    [
      ready,
      profile,
      organizations,
      accessToken,
      loadProfile,
      signOut,
      applyBackendSession,
      configured,
    ],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
