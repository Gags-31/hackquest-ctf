export const API = ''

function cookie(name: string): string | null {
  const found = document.cookie
    .split('; ')
    .find((row) => row.startsWith(name + '='))
  return found ? decodeURIComponent(found.split('=')[1]) : null
}

export async function ensureCsrf(): Promise<string> {
  const existing = cookie('hq_csrf')
  if (existing) return existing
  await fetch('/api/auth/csrf', { credentials: 'include' })
  return cookie('hq_csrf') || ''
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const method = (options.method || 'GET').toUpperCase()
  const headers: Record<string, string> = { ...(options.headers as Record<string, string> || {}) }
  if (options.body) headers['Content-Type'] = 'application/json'
  if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
    headers['x-csrf-token'] = await ensureCsrf()
  }
  const res = await fetch(path, {
    ...options,
    headers,
    credentials: 'include',
  })
  const text = await res.text()
  let data: any = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message))
  }
  return data as T
}

export const api = {
  get: <T>(path: string) => request<T>(path),
  post: <T>(path: string, body?: unknown, extra?: Record<string, string>) =>
    request<T>(path, {
      method: 'POST',
      body: body === undefined ? undefined : JSON.stringify(body),
      headers: extra,
    }),
  put: <T>(path: string, body: unknown) =>
    request<T>(path, { method: 'PUT', body: JSON.stringify(body) }),
  del: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
}

export function errorText(e: unknown): string {
  return e instanceof Error ? e.message : 'Something went wrong'
}
