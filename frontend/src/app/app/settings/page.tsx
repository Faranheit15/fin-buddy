"use client";

import { useState } from "react";
import { Building2, Download, Save, User, FileSpreadsheet } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/features/auth/auth-provider";
import {
  updateOrganization,
  updateProfile,
  type OrganizationSummary,
  type ProfileResponse,
} from "@/lib/api/auth";
import { exportData } from "@/lib/api/export";
import { ApiError, apiFetch } from "@/lib/api/client";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useRouter } from "next/navigation";

function ProfileSettingsForm({
  profile,
  accessToken,
  onSaved,
}: {
  profile: ProfileResponse;
  accessToken: string;
  onSaved: () => Promise<void>;
}) {
  const [displayName, setDisplayName] = useState(profile.display_name ?? "");
  const [timezone, setTimezone] = useState(profile.timezone || "Asia/Kolkata");
  const [dueSoonDays, setDueSoonDays] = useState(profile.due_soon_days ?? 7);
  const [highUtil, setHighUtil] = useState(profile.high_utilization_percent ?? 80);
  const [emailReminders, setEmailReminders] = useState(profile.email_reminders_enabled ?? false);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    setMsg(null);
    try {
      await updateProfile(accessToken, {
        display_name: displayName.trim() || null,
        timezone: timezone.trim() || "Asia/Kolkata",
        due_soon_days: dueSoonDays,
        high_utilization_percent: highUtil,
        email_reminders_enabled: emailReminders,
      });
      await onSaved();
      setMsg("Saved profile and notification thresholds.");
    } catch (error) {
      setErr(error instanceof ApiError ? error.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(e) => void handleSave(e)} className="flex flex-col gap-4 pt-1">
      <div className="grid gap-2">
        <Label htmlFor="display_name">Display name</Label>
        <Input
          id="display_name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="Your name"
          maxLength={200}
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="timezone">Timezone</Label>
        <Input
          id="timezone"
          value={timezone}
          onChange={(e) => setTimezone(e.target.value)}
          placeholder="Asia/Kolkata"
        />
        <p className="text-xs text-muted-foreground">
          Billing dates use IST for cycle math; this is your display preference.
        </p>
      </div>

      <div className="rounded-xl border bg-muted/20 p-3">
        <p className="text-sm font-medium">In-app notification thresholds</p>
        <p className="mt-0.5 text-xs text-muted-foreground">
          Controls dashboard attention and notification sync. No email or SMS in v1.
        </p>
        <div className="mt-3 grid gap-3 sm:grid-cols-2">
          <div className="grid gap-2">
            <Label htmlFor="due_soon_days">Due soon (days)</Label>
            <Input
              id="due_soon_days"
              type="number"
              min={1}
              max={30}
              value={dueSoonDays}
              onChange={(e) => setDueSoonDays(Number(e.target.value) || 7)}
            />
            <p className="text-[11px] text-muted-foreground">
              Flag cards due within this many days (1–30).
            </p>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="high_util">High utilization (%)</Label>
            <Input
              id="high_util"
              type="number"
              min={50}
              max={100}
              value={highUtil}
              onChange={(e) => setHighUtil(Number(e.target.value) || 80)}
            />
            <p className="text-[11px] text-muted-foreground">
              Alert when a card is at or above this % (50–100).
            </p>
          </div>
        </div>
        <div className="mt-4 flex items-center gap-3">
          <input
            type="checkbox"
            id="email_reminders"
            className="size-4 rounded border-input"
            checked={emailReminders}
            onChange={(e) => setEmailReminders(e.target.checked)}
          />
          <Label htmlFor="email_reminders" className="font-normal cursor-pointer">
            Send email reminders for upcoming dues
          </Label>
        </div>
      </div>

      {err ? <p className="text-sm text-destructive">{err}</p> : null}
      {msg ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-400">{msg}</p>
      ) : null}

      <div>
        <Button type="submit" size="sm" disabled={saving}>
          <Save className="size-3.5" />
          {saving ? "Saving…" : "Save profile"}
        </Button>
      </div>
    </form>
  );
}

function OrgSettingsForm({
  org,
  accessToken,
  onSaved,
}: {
  org: OrganizationSummary;
  accessToken: string;
  onSaved: () => Promise<void>;
}) {
  const [orgName, setOrgName] = useState(org.name);
  const [msg, setMsg] = useState<string | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSave(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setErr(null);
    setMsg(null);
    try {
      await updateOrganization(accessToken, org.id, { name: orgName.trim() });
      await onSaved();
      setMsg("Workspace name updated.");
    } catch (error) {
      setErr(error instanceof ApiError ? error.message : "Failed to rename workspace");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={(e) => void handleSave(e)} className="flex flex-col gap-4 pt-1">
      <div className="flex flex-wrap items-center gap-2">
        <Badge variant="outline" className="font-mono text-[10px] uppercase">
          {org.role}
        </Badge>
        <span className="font-mono text-xs text-muted-foreground">{org.slug}</span>
      </div>
      <div className="grid gap-2">
        <Label htmlFor="org_name">Workspace name</Label>
        <Input
          id="org_name"
          value={orgName}
          onChange={(e) => setOrgName(e.target.value)}
          required
          minLength={1}
          maxLength={200}
        />
      </div>
      {err ? <p className="text-sm text-destructive">{err}</p> : null}
      {msg ? (
        <p className="text-sm text-emerald-700 dark:text-emerald-400">{msg}</p>
      ) : null}
      <div>
        <Button type="submit" size="sm" variant="outline" disabled={saving || !orgName.trim()}>
          <Save className="size-3.5" />
          {saving ? "Saving…" : "Rename workspace"}
        </Button>
      </div>
    </form>
  );
}

function ExportSettingsCard({ accessToken }: { accessToken: string }) {
  const [downloading, setDownloading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleExport() {
    setDownloading(true);
    setErr(null);
    try {
      const blob = await exportData(accessToken);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "finbuddy_export.xlsx";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      a.remove();
    } catch (error) {
      setErr(error instanceof Error ? error.message : "Failed to download export");
    } finally {
      setDownloading(false);
    }
  }

  return (
    <Card className="shadow-sm ring-1 ring-foreground/10">
      <CardHeader className="border-b pb-3!">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="size-4 text-muted-foreground" />
          <CardTitle>Data Export</CardTitle>
        </div>
        <CardDescription>
          Download your complete ledger, accounts, and obligations as an Excel workbook.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {err ? <p className="mb-4 text-sm text-destructive">{err}</p> : null}
        <Button onClick={handleExport} size="sm" variant="outline" disabled={downloading}>
          <Download className="mr-2 size-3.5" />
          {downloading ? "Downloading…" : "Download Excel Export"}
        </Button>
      </CardContent>
    </Card>
  );
}

function DeleteAccountCard({ accessToken, onDeleted }: { accessToken: string; onDeleted: () => void }) {
  const [deleting, setDeleting] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleDelete() {
    if (!window.confirm("Are you absolutely sure you want to delete your account? All your data will be permanently removed. This cannot be undone.")) {
      return;
    }
    setDeleting(true);
    setErr(null);
    try {
      await apiFetch("/api/v1/auth/me", { method: "DELETE" }, { accessToken });
      onDeleted();
    } catch (error) {
      setErr(error instanceof ApiError ? error.message : "Failed to delete account");
      setDeleting(false);
    }
  }

  return (
    <Card className="shadow-sm border-destructive/20 mt-8">
      <CardHeader className="border-b border-destructive/10 pb-3!">
        <CardTitle className="text-destructive">Danger Zone</CardTitle>
        <CardDescription>
          Permanently delete your account and all associated data.
        </CardDescription>
      </CardHeader>
      <CardContent className="pt-4">
        {err ? <p className="mb-4 text-sm text-destructive">{err}</p> : null}
        <Button onClick={handleDelete} size="sm" variant="destructive" disabled={deleting}>
          {deleting ? "Deleting…" : "Delete Account"}
        </Button>
      </CardContent>
    </Card>
  );
}

function PrivacyTermsDialog() {
  return (
    <Dialog>
      <DialogTrigger className="text-xs text-muted-foreground hover:underline">
        Privacy Policy & Terms of Service
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Privacy & Terms</DialogTitle>
          <DialogDescription>
            Fin Buddy is a self-hosted personal finance tracker.
          </DialogDescription>
        </DialogHeader>
        <div className="text-sm space-y-4 pt-4">
          <p>
            <strong>1. Data Ownership:</strong> All financial data you enter belongs to you. Since this is a self-hosted instance, data is stored on the server where it is deployed.
          </p>
          <p>
            <strong>2. Data Deletion:</strong> You have the right to permanently delete your account at any time. Using the &quot;Delete Account&quot; button will erase all your profile, organization, transactions, and settings data from the database.
          </p>
          <p>
            <strong>3. Security:</strong> Data is secured using Row Level Security (RLS) on Supabase.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}

export default function SettingsPage() {
  const { accessToken, ready, profile, organizations, refreshProfile, signOut } = useAuth();
  const router = useRouter();
  const primaryOrg = organizations[0] ?? null;

  if (!ready) {
    return <p className="text-sm text-muted-foreground">Loading…</p>;
  }

  if (!accessToken || !profile) {
    return (
      <p className="text-sm text-muted-foreground">
        Sign in to manage profile and notification preferences.
      </p>
    );
  }

  const profileFormKey = [
    profile.id,
    profile.display_name ?? "",
    profile.timezone,
    profile.due_soon_days,
    profile.high_utilization_percent,
    profile.email_reminders_enabled,
  ].join("|");

  const orgFormKey = primaryOrg ? `${primaryOrg.id}|${primaryOrg.name}` : "none";

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-4">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">Settings</h2>
        <p className="text-sm text-muted-foreground">
          Profile, workspace, and in-app notification preferences
        </p>
      </div>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <div className="flex items-center gap-2">
            <User className="size-4 text-muted-foreground" />
            <CardTitle>Profile</CardTitle>
          </div>
          <CardDescription>
            {profile.email ? (
              <span className="font-mono text-xs">{profile.email}</span>
            ) : (
              "Display name and timezone for your account"
            )}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ProfileSettingsForm
            key={profileFormKey}
            profile={profile}
            accessToken={accessToken}
            onSaved={refreshProfile}
          />
        </CardContent>
      </Card>

      <Card className="shadow-sm ring-1 ring-foreground/10">
        <CardHeader className="border-b pb-3!">
          <div className="flex items-center gap-2">
            <Building2 className="size-4 text-muted-foreground" />
            <CardTitle>Workspace</CardTitle>
          </div>
          <CardDescription>
            Personal organization for cards, contacts, and the ledger.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {primaryOrg ? (
            <OrgSettingsForm
              key={orgFormKey}
              org={primaryOrg}
              accessToken={accessToken}
              onSaved={refreshProfile}
            />
          ) : (
            <p className="text-sm text-muted-foreground">No workspace found.</p>
          )}
        </CardContent>
      </Card>

      <ExportSettingsCard accessToken={accessToken} />

      <DeleteAccountCard 
        accessToken={accessToken} 
        onDeleted={() => {
          signOut();
          router.replace("/login");
        }} 
      />

      <div className="mt-8 flex justify-center pb-8">
        <PrivacyTermsDialog />
      </div>
    </div>
  );
}
