/** Typed API client generated from the OpenAPI contract. */

const TOKEN_KEY = "token";

// When the app is embedded in the QuantBuild live preview, the API base is
// injected globally; standalone builds talk to their own origin (or the Vite
// dev-server proxy).
const API_BASE: string =
  (typeof window !== "undefined" && (window as unknown as Record<string, string>).__QB_API_BASE__) || "";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) headers["Authorization"] = "Bearer " + token;
  const resp = await fetch(API_BASE + path, { ...options, headers });
  if (resp.status === 401) {
    setToken(null);
  }
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* keep statusText */
    }
    throw new ApiError(resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return (await resp.json()) as T;
}

export interface AuthUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name }),
    }),
  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),
  me: () => request<AuthUser>("/api/users/me"),
};

export const api = {
  list: <T>(resource: string) => request<T[]>("/api/" + resource),
  get: <T>(resource: string, id: number) => request<T>("/api/" + resource + "/" + id),
  create: <T>(resource: string, data: Record<string, unknown>) =>
    request<T>("/api/" + resource, { method: "POST", body: JSON.stringify(data) }),
  update: <T>(resource: string, id: number, data: Record<string, unknown>) =>
    request<T>("/api/" + resource + "/" + id, { method: "PUT", body: JSON.stringify(data) }),
  remove: (resource: string, id: number) =>
    request<void>("/api/" + resource + "/" + id, { method: "DELETE" }),
};
