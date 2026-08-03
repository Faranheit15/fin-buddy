import { apiFetch } from "@/lib/api/client";

export type Contact = {
  id: string;
  organization_id: string;
  name: string;
  phone: string | null;
  email: string | null;
  notes: string | null;
  tags: string[] | null;
  archived_at: string | null;
  outstanding_paise: number | null;
  created_at: string;
  updated_at: string;
};

export type ContactCreate = {
  name: string;
  phone?: string | null;
  email?: string | null;
  notes?: string | null;
  tags?: string[] | null;
};

export type ContactUpdate = Partial<{
  name: string;
  phone: string | null;
  email: string | null;
  notes: string | null;
  tags: string[] | null;
  archived: boolean;
}>;

export type Paginated<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export function listContacts(
  accessToken: string,
  opts: { page?: number; pageSize?: number; includeArchived?: boolean } = {},
) {
  const q = new URLSearchParams({
    page: String(opts.page ?? 1),
    page_size: String(opts.pageSize ?? 50),
  });
  if (opts.includeArchived) q.set("include_archived", "true");
  return apiFetch<Paginated<Contact>>(`/api/v1/contacts?${q}`, { method: "GET" }, { accessToken });
}

export function getContact(accessToken: string, id: string) {
  return apiFetch<Contact>(`/api/v1/contacts/${id}`, { method: "GET" }, { accessToken });
}

export function createContact(accessToken: string, body: ContactCreate) {
  return apiFetch<Contact>(
    "/api/v1/contacts",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateContact(accessToken: string, id: string, body: ContactUpdate) {
  return apiFetch<Contact>(
    `/api/v1/contacts/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}
