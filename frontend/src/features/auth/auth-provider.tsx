"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import {
  clearBrowserSession,
  fetchMe,
  logoutApi,
  readBrowserSession,
  type MeResponse,
} from "@/lib/api/auth";
import { BFF_SESSION_MARKER } from "@/lib/auth/session";

type AuthContextValue = {
  ready: boolean;
  profile: MeResponse["user"] | null;
  organizations: MeResponse["organizations"];
  /** Non-secret marker for legacy client API call sites; never a bearer token. */
  accessToken: typeof BFF_SESSION_MARKER | null;
  refreshProfile: () => Promise<void>;
  signOut: () => Promise<void>;
  /** Load profile after the BFF establishes HttpOnly cookies. */
  applyEstablishedSession: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [accessToken, setAccessToken] = useState<typeof BFF_SESSION_MARKER | null>(null);
  const [profile, setProfile] = useState<MeResponse["user"] | null>(null);
  const [organizations, setOrganizations] = useState<MeResponse["organizations"]>([]);

  const loadProfile = useCallback(async () => {
    try {
      const me = await fetchMe(BFF_SESSION_MARKER);
      setProfile(me.user);
      setOrganizations(me.organizations);
    } catch {
      setProfile(null);
      setOrganizations([]);
    }
  }, []);

  const applyEstablishedSession = useCallback(async () => {
    const session = await readBrowserSession();
    if (!session) throw new Error("Session was not established");
    setAccessToken(BFF_SESSION_MARKER);
    await loadProfile();
  }, [loadProfile]);

  useEffect(() => {
    let mounted = true;

    void (async () => {
      try {
        const session = await readBrowserSession();
        if (!session) return;
        if (!mounted) return;
        setAccessToken(BFF_SESSION_MARKER);
        setReady(true);
        await loadProfile();
      } finally {
        if (mounted) setReady(true);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [loadProfile]);

  const signOut = useCallback(async () => {
    if (accessToken) {
      try {
        await logoutApi(accessToken);
      } catch {
        // Clear local cookies even when the upstream logout request is unavailable.
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
        if (accessToken) await loadProfile();
      },
      signOut,
      applyEstablishedSession,
    }),
    [ready, profile, organizations, accessToken, loadProfile, signOut, applyEstablishedSession],
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
