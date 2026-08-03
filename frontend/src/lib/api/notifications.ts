import { apiFetch } from "@/lib/api/client";

export type Notification = {
  id: string;
  organization_id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  href: string | null;
  read_at: string | null;
  created_at: string;
};

export type NotificationListResponse = {
  items: Notification[];
  total: number;
  page: number;
  page_size: number;
};

export function listNotifications(
  accessToken: string,
  opts?: { unreadOnly?: boolean; pageSize?: number; sync?: boolean; signal?: AbortSignal },
) {
  const q = new URLSearchParams();
  if (opts?.unreadOnly) q.set("unread_only", "true");
  if (opts?.pageSize) q.set("page_size", String(opts.pageSize));
  if (opts?.sync === false) q.set("sync", "false");
  const qs = q.toString();
  return apiFetch<NotificationListResponse>(
    `/api/v1/notifications${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    { accessToken, signal: opts?.signal },
  );
}

export function getUnreadNotificationCount(
  accessToken: string,
  opts?: { sync?: boolean; signal?: AbortSignal },
) {
  const q = new URLSearchParams();
  if (opts?.sync === false) q.set("sync", "false");
  const qs = q.toString();
  return apiFetch<{ unread: number }>(
    `/api/v1/notifications/unread-count${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    { accessToken, signal: opts?.signal },
  );
}

export function markNotificationRead(accessToken: string, id: string) {
  return apiFetch<Notification>(
    `/api/v1/notifications/${id}/read`,
    { method: "POST" },
    { accessToken },
  );
}

export function markAllNotificationsRead(accessToken: string) {
  return apiFetch<{ updated: number }>(
    "/api/v1/notifications/read-all",
    { method: "POST" },
    { accessToken },
  );
}
