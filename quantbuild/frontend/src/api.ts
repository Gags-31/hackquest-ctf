import type { PipelineEvent, PreviewInfo, Project, ProjectSummary, ServerConfig } from "./types";

const BASE = "";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const resp = await fetch(BASE + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* ignore */
    }
    throw new Error(detail);
  }
  return (await resp.json()) as T;
}

export const api = {
  config: () => request<ServerConfig>("/api/config"),
  listProjects: () => request<ProjectSummary[]>("/api/projects"),
  createProject: (requirement: string, name?: string) =>
    request<{ id: string; name: string; status: string }>("/api/projects", {
      method: "POST",
      body: JSON.stringify({ requirement, name: name || null }),
    }),
  getProject: (id: string) => request<Project>(`/api/projects/${id}`),
  deleteProject: (id: string) =>
    request<{ status: string }>(`/api/projects/${id}`, { method: "DELETE" }),
  modifyProject: (id: string, instruction: string) =>
    request<{ status: string }>(`/api/projects/${id}/modify`, {
      method: "POST",
      body: JSON.stringify({ instruction }),
    }),
  fileContent: (id: string, path: string) =>
    request<{ path: string; content: string }>(
      `/api/projects/${id}/files/content?path=${encodeURIComponent(path)}`
    ),
  downloadUrl: (id: string) => `/api/projects/${id}/download`,
  startPreview: (id: string) =>
    request<PreviewInfo>(`/api/projects/${id}/preview`, { method: "POST" }),
  previewStatus: (id: string) => request<PreviewInfo>(`/api/projects/${id}/preview`),
  stopPreview: (id: string) =>
    request<{ stopped: boolean }>(`/api/projects/${id}/preview`, { method: "DELETE" }),
};

export function subscribeEvents(
  projectId: string,
  onEvent: (event: PipelineEvent) => void,
  onClose?: () => void
): () => void {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/projects/${projectId}`);
  ws.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as PipelineEvent);
    } catch {
      /* ignore malformed frames */
    }
  };
  ws.onclose = () => onClose?.();
  return () => ws.close();
}
