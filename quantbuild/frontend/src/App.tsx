import { useCallback, useEffect, useRef, useState } from "react";
import { api, subscribeEvents } from "./api";
import NewProject from "./components/NewProject";
import PipelineConsole from "./components/PipelineConsole";
import ProjectView from "./components/ProjectView";
import type { PipelineEvent, PreviewInfo, Project, ProjectSummary, ServerConfig } from "./types";

export default function App() {
  const [config, setConfig] = useState<ServerConfig | null>(null);
  const [projects, setProjects] = useState<ProjectSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [events, setEvents] = useState<PipelineEvent[]>([]);
  const [preview, setPreview] = useState<PreviewInfo | null>(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // ------------------------------------------------------------ data loading
  const refreshProjects = useCallback(async () => {
    try {
      setProjects(await api.listProjects());
    } catch {
      /* backend not ready */
    }
  }, []);

  useEffect(() => {
    api.config().then(setConfig).catch(() => setConfig(null));
    refreshProjects();
  }, [refreshProjects]);

  const loadProject = useCallback(async (id: string) => {
    try {
      const p = await api.getProject(id);
      setProject(p);
      return p;
    } catch {
      return null;
    }
  }, []);

  // Poll while the pipeline is running so artifact tabs fill in live.
  useEffect(() => {
    if (pollRef.current) clearInterval(pollRef.current);
    if (!selectedId) return;
    pollRef.current = setInterval(async () => {
      const p = await loadProject(selectedId);
      if (p && (p.status === "generated" || p.status === "failed")) {
        refreshProjects();
      }
    }, 2500);
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [selectedId, loadProject, refreshProjects]);

  // Live agent events over WebSocket.
  useEffect(() => {
    if (!selectedId) return;
    setEvents([]);
    const unsubscribe = subscribeEvents(
      selectedId,
      (ev) => {
        setEvents((prev) => [...prev.slice(-400), ev]);
        if (ev.agent === "Project Manager Agent" && ev.status === "finished") {
          loadProject(selectedId);
          refreshProjects();
          setBusy(false);
        }
      },
    );
    return unsubscribe;
  }, [selectedId, loadProject, refreshProjects]);

  // -------------------------------------------------------------- selections
  const select = async (id: string | null) => {
    setSelectedId(id);
    setPreview(null);
    setError("");
    if (id) {
      await loadProject(id);
      api.previewStatus(id).then(setPreview).catch(() => setPreview(null));
    } else {
      setProject(null);
    }
  };

  // ---------------------------------------------------------------- actions
  const create = async (requirement: string, name: string) => {
    setCreating(true);
    setError("");
    try {
      const resp = await api.createProject(requirement, name || undefined);
      await refreshProjects();
      await select(resp.id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create project");
    } finally {
      setCreating(false);
    }
  };

  const modify = async (instruction: string) => {
    if (!selectedId) return;
    setBusy(true);
    try {
      await api.modifyProject(selectedId, instruction);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Modification failed");
      setBusy(false);
    }
  };

  const startPreview = async () => {
    if (!selectedId) return;
    try {
      setPreview(await api.startPreview(selectedId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Preview failed");
    }
  };

  const stopPreview = async () => {
    if (!selectedId) return;
    await api.stopPreview(selectedId).catch(() => undefined);
    setPreview(null);
  };

  const remove = async (id: string) => {
    if (!window.confirm("Delete this project and its generated code?")) return;
    await api.deleteProject(id).catch(() => undefined);
    if (selectedId === id) select(null);
    refreshProjects();
  };

  // ------------------------------------------------------------------ render
  return (
    <div className="min-h-screen flex flex-col">
      {/* top bar */}
      <header className="border-b border-surface-800 bg-surface-900/80 backdrop-blur sticky top-0 z-20">
        <div className="max-w-[1600px] mx-auto px-5 h-14 flex items-center gap-3">
          <button onClick={() => select(null)} className="flex items-center gap-2.5">
            <span className="text-2xl">⚡</span>
            <span className="font-bold text-lg text-slate-100">QuantBuild</span>
          </button>
          <span className="text-xs text-slate-500 hidden sm:block">
            AI-Powered Full-Stack Architecture Designer & App Builder
          </span>
          <div className="ml-auto flex items-center gap-3">
            {config && (
              <span
                className={`text-xs px-2.5 py-1 rounded-full font-mono ${
                  config.llm_online
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "bg-amber-500/15 text-amber-400"
                }`}
                title={config.llm_model}
              >
                {config.llm_online ? `● ${config.llm_provider}` : "● offline heuristics"}
              </span>
            )}
          </div>
        </div>
      </header>

      <div className="flex-1 max-w-[1600px] mx-auto w-full px-5 py-6 flex gap-6">
        {/* sidebar */}
        <aside className="w-60 shrink-0 hidden md:block">
          <button
            onClick={() => select(null)}
            className="w-full bg-brand-600 hover:bg-brand-700 text-white text-sm font-medium rounded-lg px-4 py-2.5 transition mb-4"
          >
            + New Application
          </button>
          <div className="text-xs text-slate-500 uppercase tracking-wide mb-2">Projects</div>
          <div className="space-y-1.5">
            {projects.length === 0 && (
              <p className="text-xs text-slate-600 px-1">No projects yet — describe an app to begin.</p>
            )}
            {projects.map((p) => (
              <div
                key={p.id}
                className={`group rounded-lg border px-3 py-2.5 cursor-pointer transition ${
                  selectedId === p.id
                    ? "border-brand-500/50 bg-brand-600/10"
                    : "border-surface-800 bg-surface-850 hover:border-slate-700"
                }`}
                onClick={() => select(p.id)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium text-slate-200 truncate">{p.name}</span>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      remove(p.id);
                    }}
                    className="text-slate-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition text-xs"
                    title="Delete project"
                  >
                    ✕
                  </button>
                </div>
                <div className="text-xs text-slate-500 truncate">{p.app_type || "…"}</div>
                <div
                  className={`text-xs mt-1 ${
                    p.status === "generated"
                      ? "text-emerald-400"
                      : p.status === "failed"
                        ? "text-red-400"
                        : "text-brand-400"
                  }`}
                >
                  {p.status}
                </div>
              </div>
            ))}
          </div>
        </aside>

        {/* main */}
        <main className="flex-1 min-w-0">
          {error && (
            <div className="bg-red-500/10 border border-red-500/30 text-red-400 text-sm rounded-lg px-4 py-3 mb-4">
              {error}
              <button onClick={() => setError("")} className="ml-3 text-red-300">✕</button>
            </div>
          )}

          {!selectedId ? (
            <NewProject onSubmit={create} busy={creating} />
          ) : (
            <div className="space-y-6">
              {project && (project.status === "generating" || project.status === "modifying" || events.length > 0) && (
                <div className="bg-surface-900 border border-surface-800 rounded-xl p-4">
                  <div className="text-xs text-slate-500 uppercase tracking-wide mb-3 flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-brand-400 dot-pulse" />
                    Multi-Agent Pipeline — live
                  </div>
                  <PipelineConsole events={events} />
                </div>
              )}
              {project ? (
                <ProjectView
                  project={project}
                  preview={preview}
                  onModify={modify}
                  onPreviewStart={startPreview}
                  onPreviewStop={stopPreview}
                  busy={busy || project.status === "modifying"}
                />
              ) : (
                <div className="text-slate-500 text-sm">Loading project…</div>
              )}
            </div>
          )}
        </main>
      </div>

      <footer className="border-t border-surface-800 py-4 text-center text-xs text-slate-600">
        QuantBuild — Requirement → Architecture → Database → API → Code → Test → Debug → Secure → Deploy
      </footer>
    </div>
  );
}
