/** Typed API client.
 *  - Attaches the CSRF header on every mutating request.
 *  - Never stores tokens in localStorage; the session lives in an HttpOnly cookie.
 */

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

function readCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp("(^|;\\s*)" + name + "=([^;]*)"));
  return m ? decodeURIComponent(m[2]) : null;
}

let csrfReady: Promise<void> | null = null;

/** Ensure a CSRF cookie exists before the first mutating request. */
export async function ensureCsrf(): Promise<void> {
  if (readCookie("hq_csrf")) return;
  if (!csrfReady) {
    csrfReady = fetch("/api/auth/csrf", { credentials: "same-origin" })
      .then((r) => r.json())
      .then(() => undefined)
      .finally(() => {
        csrfReady = null;
      });
  }
  await csrfReady;
}

type Opts = {
  method?: string;
  body?: unknown;
  headers?: Record<string, string>;
};

export async function api<T = unknown>(path: string, opts: Opts = {}): Promise<T> {
  const method = opts.method ?? "GET";
  const headers: Record<string, string> = { ...(opts.headers ?? {}) };

  if (method !== "GET" && method !== "HEAD") {
    await ensureCsrf();
    const token = readCookie("hq_csrf");
    if (token) headers["X-CSRF-Token"] = token;
    if (opts.body !== undefined) headers["Content-Type"] = "application/json";
  }

  const res = await fetch(path, {
    method,
    credentials: "same-origin",
    headers,
    body: opts.body === undefined ? undefined : JSON.stringify(opts.body),
  });

  const text = await res.text();
  let data: unknown = null;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }

  if (!res.ok) {
    let msg = `Request failed (${res.status})`;
    if (data && typeof data === "object" && "detail" in data) {
      const d = (data as { detail: unknown }).detail;
      msg = Array.isArray(d)
        ? d
            .map((x) =>
              typeof x === "object" && x && "msg" in x
                ? String((x as { msg: unknown }).msg)
                : String(x),
            )
            .join(" ")
        : typeof d === "string"
          ? d
          : msg;
    }
    throw new ApiError(res.status, msg);
  }
  return data as T;
}

/** Convenience helpers. */
export const get = <T,>(p: string) => api<T>(p);
export const post = <T,>(p: string, body?: unknown) =>
  api<T>(p, { method: "POST", body: body ?? {} });