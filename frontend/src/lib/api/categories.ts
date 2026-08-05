import { apiFetch } from "@/lib/api/client";

export type CategoryKind = "income" | "expense";

export type Category = {
  id: string;
  organization_id: string;
  name: string;
  kind: CategoryKind;
  is_default: boolean;
  created_at: string;
  updated_at: string;
};

export type CategoryCreate = {
  name: string;
  kind: CategoryKind;
};

export type CategoryUpdate = {
  name?: string;
};

export function listCategories(accessToken: string) {
  return apiFetch<Category[]>(
    "/api/v1/categories",
    { method: "GET" },
    { accessToken },
  );
}

export function createCategory(accessToken: string, body: CategoryCreate) {
  return apiFetch<Category>(
    "/api/v1/categories",
    { method: "POST", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function updateCategory(
  accessToken: string,
  id: string,
  body: CategoryUpdate,
) {
  return apiFetch<Category>(
    `/api/v1/categories/${id}`,
    { method: "PATCH", body: JSON.stringify(body) },
    { accessToken },
  );
}

export function deleteCategory(accessToken: string, id: string) {
  return apiFetch<void>(
    `/api/v1/categories/${id}`,
    { method: "DELETE" },
    { accessToken },
  );
}
