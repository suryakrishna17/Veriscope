import type { AnalyticsData, CaseDetail, CaseSummary, Field, Finding, Job, Meta, Paged, User } from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public details: Record<string, unknown> = {},
    public correlationId: string | null = null,
  ) {
    super(message);
  }
}

const TOKEN_KEY = "veriscope.token";
let token: string | null = sessionStorage.getItem(TOKEN_KEY);
let onUnauthorized: () => void = () => {};

export const auth = {
  get token() { return token; },
  set(t: string | null) {
    token = t;
    if (t) sessionStorage.setItem(TOKEN_KEY, t);
    else sessionStorage.removeItem(TOKEN_KEY);
  },
  onUnauthorized(fn: () => void) { onUnauthorized = fn; },
};

const metaEnv = (import.meta as unknown as { env?: { VITE_API_BASE_URL?: string } }).env;
const API_BASE = (metaEnv?.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");

  const isUpload = init.body instanceof FormData;
  const timeoutMs = isUpload ? 45000 : 8000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1${path}`, {
      ...init,
      headers,
      signal: init.signal ?? controller.signal,
    });
  } catch (err: unknown) {
    if (err instanceof Error && err.name === "AbortError") {
      throw new ApiError(0, "TIMEOUT", "Request timed out. Please check your connection and try again.");
    }
    throw new ApiError(0, "NETWORK", "The server could not be reached. Check that the API is running and try again.");
  } finally {
    clearTimeout(timer);
  }
  if (res.status === 401 && path !== "/auth/login") {
    auth.set(null);
    onUnauthorized();
  }
  if (!res.ok) {
    let body: { error?: { code: string; message: string; details?: Record<string, unknown>; correlation_id?: string } } = {};
    try { body = await res.json(); } catch { /* non-JSON error */ }
    const e = body.error;
    throw new ApiError(res.status, e?.code ?? "HTTP_ERROR", e?.message ?? `Request failed (${res.status}).`, e?.details ?? {}, e?.correlation_id ?? null);
  }
  const type = res.headers.get("Content-Type") ?? "";
  return (type.includes("application/json") ? res.json() : res.blob()) as Promise<T>;
}

const json = (body: unknown) => JSON.stringify(body);

export const api = {
  login: (email: string, password: string) =>
    request<{ access_token: string; user: User }>("/auth/login", { method: "POST", body: json({ email, password }) }),
  me: () => request<User>("/auth/me"),
  meta: () => request<Meta>("/meta"),
  listCases: (params: { status?: string; q?: string; page?: number; page_size?: number; sort?: string }) => {
    const qs = new URLSearchParams();
    Object.entries(params).forEach(([k, v]) => { if (v !== undefined && v !== "") qs.set(k, String(v)); });
    return request<Paged<CaseSummary>>(`/cases?${qs}`);
  },
  getCase: (id: string) => request<CaseDetail>(`/cases/${encodeURIComponent(id)}`),
  createCase: (body: { applicant_ref: string; institution_ref: string; application_type: string }) =>
    request<{ id: string; case_ref: string; status: string }>("/cases", { method: "POST", body: json(body) }),
  upload: (caseId: string, docType: string, file: File) => {
    const fd = new FormData();
    fd.set("doc_type", docType);
    fd.set("file", file);
    return request<{ document_id: string; duplicate: boolean }>(`/cases/${caseId}/documents`, { method: "POST", body: fd });
  },
  process: (caseId: string, force = false) =>
    request<{ job_id: string }>(`/cases/${caseId}/process`, { method: "POST", body: json({ force }) }),
  job: (id: string) => request<Job>(`/jobs/${id}`),
  pageImage: (docId: string, page: number) => request<Blob>(`/documents/${docId}/pages/${page}/image`),
  correctField: (id: string, value: string, reason: string) =>
    request<{ field: Field; audit_event_id: string }>(`/fields/${id}`, { method: "PATCH", body: json({ value, reason }) }),
  updateFinding: (id: string, status: Finding["status"], note: string) =>
    request<Finding>(`/findings/${id}`, { method: "PATCH", body: json({ status, note }) }),
  decide: (caseId: string, outcome: string, reason_code: string, note: string) =>
    request<{ status: string }>(`/cases/${caseId}/decisions`, { method: "POST", body: json({ outcome, reason_code, note }) }),
  reopen: (caseId: string, note: string) => request<{ status: string }>(`/cases/${caseId}/reopen`, { method: "POST", body: json({ note }) }),
  pullDigiLocker: (caseId: string, docType: string) =>
    request<{ document_id: string; doc_type: string; version: number; trust_label: string; original_name: string }>(
      `/cases/${caseId}/digilocker/pull`,
      { method: "POST", body: json({ doc_type: docType }) }
    ),
  analytics: () => request<AnalyticsData>("/analytics"),
  report: (caseId: string) => request<Record<string, unknown>>(`/cases/${caseId}/report`),
  reportPdf: (caseId: string) => request<Blob>(`/cases/${caseId}/report?format=pdf`),
  auditVerify: (caseId: string) =>
    request<{ valid: boolean; event_count: number; head_hash?: string; broken_at_seq?: number; algorithm: string }>(
      `/cases/${caseId}/audit/verify`
    ),
};

export function download(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 2000);
}
