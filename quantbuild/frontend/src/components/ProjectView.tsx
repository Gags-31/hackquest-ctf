import { useState } from "react";
import { api } from "../api";
import type { PreviewInfo, Project } from "../types";
import MermaidDiagram from "./MermaidDiagram";

const TABS = [
  "Overview", "Architecture", "Database", "API", "UI/UX", "Files",
  "Tests", "Security", "Docs", "Deploy",
] as const;

type Tab = (typeof TABS)[number];

const METHOD_COLORS: Record<string, string> = {
  GET: "bg-emerald-500/15 text-emerald-400",
  POST: "bg-sky-500/15 text-sky-400",
  PUT: "bg-amber-500/15 text-amber-400",
  DELETE: "bg-red-500/15 text-red-400",
};

function Badge({ children, color }: { children: React.ReactNode; color: string }) {
  return (
    <span className={`text-xs font-mono px-2 py-0.5 rounded ${color}`}>{children}</span>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide mb-3">
        {title}
      </h3>
      {children}
    </div>
  );
}

export default function ProjectView({
  project,
  preview,
  onModify,
  onPreviewStart,
  onPreviewStop,
  busy,
}: {
  project: Project;
  preview: PreviewInfo | null;
  onModify: (instruction: string) => void;
  onPreviewStart: () => void;
  onPreviewStop: () => void;
  busy: boolean;
}) {
  const [tab, setTab] = useState<Tab>("Overview");
  const [instruction, setInstruction] = useState("");
  const generated = project.status === "generated" || project.status === "modifying";
  const spec = project.specification;

  return (
    <div>
      {/* header */}
      <div className="flex flex-wrap items-center gap-3 mb-5">
        <div className="flex-1 min-w-0">
          <h1 className="text-2xl font-bold text-slate-100 truncate">{project.name}</h1>
          <p className="text-sm text-slate-500">
            {spec?.app_type || "…"} · mode: {project.mode} · {project.file_structure.length} files
          </p>
        </div>
        <StatusBadge status={project.status} />
        {generated && (
          <>
            {preview?.running ? (
              <>
                <a
                  href={`/preview/${project.id}`}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg px-4 py-2 transition"
                >
                  🌐 Open Website
                </a>
                <a
                  href={`${preview.url}/docs`}
                  target="_blank"
                  rel="noreferrer"
                  className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-lg px-4 py-2 transition"
                >
                  ▶ API Docs
                </a>
                <button
                  onClick={onPreviewStop}
                  className="bg-surface-800 hover:bg-surface-800/70 text-slate-300 text-sm rounded-lg px-4 py-2 transition"
                >
                  Stop
                </button>
              </>
            ) : (
              <button
                onClick={onPreviewStart}
                className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm rounded-lg px-4 py-2 transition"
              >
                ▶ Run in Sandbox
              </button>
            )}
            <a
              href={api.downloadUrl(project.id)}
              className="bg-brand-600 hover:bg-brand-700 text-white text-sm rounded-lg px-4 py-2 transition"
            >
              ⬇ Download .zip
            </a>
          </>
        )}
      </div>

      {/* modify bar */}
      {generated && (
        <div className="flex gap-2 mb-5">
          <input
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && instruction.trim() && !busy) {
                onModify(instruction.trim());
                setInstruction("");
              }
            }}
            placeholder='Modify with natural language — e.g. "Add a wishlist feature" or "Change login to Google authentication"'
            className="flex-1 bg-surface-900 border border-surface-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:border-brand-500"
          />
          <button
            onClick={() => {
              if (instruction.trim() && !busy) {
                onModify(instruction.trim());
                setInstruction("");
              }
            }}
            disabled={!instruction.trim() || busy}
            className="bg-purple-600 hover:bg-purple-700 disabled:opacity-40 text-white text-sm rounded-lg px-5 py-2.5 transition"
          >
            {busy ? "Working…" : "✨ Apply"}
          </button>
        </div>
      )}

      {/* tabs */}
      <div className="flex gap-1 mb-5 border-b border-surface-800 overflow-x-auto">
        {TABS.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 text-sm font-medium rounded-t-lg whitespace-nowrap transition ${
              tab === t
                ? "text-brand-400 border-b-2 border-brand-500 bg-surface-850"
                : "text-slate-500 hover:text-slate-300"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {!generated && project.status !== "failed" ? (
        <EmptyState text="Agents are still working — artifacts will appear here as they are produced." />
      ) : (
        <div>
          {tab === "Overview" && <OverviewTab project={project} />}
          {tab === "Architecture" && <ArchitectureTab project={project} />}
          {tab === "Database" && <DatabaseTab project={project} />}
          {tab === "API" && <ApiTab project={project} />}
          {tab === "UI/UX" && <UiUxTab project={project} />}
          {tab === "Files" && <FilesTab project={project} />}
          {tab === "Tests" && <TestsTab project={project} />}
          {tab === "Security" && <SecurityTab project={project} />}
          {tab === "Docs" && <DocsTab project={project} />}
          {tab === "Deploy" && <DeployTab project={project} />}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const map: Record<string, [string, string]> = {
    created: ["⏳ queued", "bg-slate-500/15 text-slate-400"],
    generating: ["⚙️ generating", "bg-brand-500/15 text-brand-400"],
    modifying: ["✨ modifying", "bg-purple-500/15 text-purple-400"],
    generated: ["✅ generated", "bg-emerald-500/15 text-emerald-400"],
    failed: ["❌ failed", "bg-red-500/15 text-red-400"],
  };
  const [label, cls] = map[status] ?? [status, "bg-slate-500/15 text-slate-400"];
  return <span className={`text-sm px-3 py-1.5 rounded-lg font-medium ${cls}`}>{label}</span>;
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="text-center py-16 text-slate-500">
      <div className="text-4xl mb-3">⏳</div>
      <p className="text-sm">{text}</p>
    </div>
  );
}

/* ------------------------------------------------------------------ tabs */

function OverviewTab({ project }: { project: Project }) {
  const spec = project.specification;
  if (!spec?.app_type) return <EmptyState text="Specification not available yet." />;
  return (
    <div>
      <Section title="Summary">
        <p className="text-slate-400 text-sm leading-relaxed">{spec.summary}</p>
      </Section>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title={`User Roles (${spec.users.length})`}>
          <div className="flex flex-wrap gap-2">
            {spec.users.map((u) => (
              <Badge key={u} color="bg-brand-500/15 text-brand-400">{u}</Badge>
            ))}
          </div>
        </Section>
        <Section title={`Entities (${spec.entities.length})`}>
          <div className="flex flex-wrap gap-2">
            {spec.entities.map((e) => (
              <Badge key={e.name} color="bg-emerald-500/15 text-emerald-400">{e.name}</Badge>
            ))}
          </div>
        </Section>
      </div>
      <Section title={`Features (${spec.features.length})`}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
          {spec.features.map((f) => (
            <div key={f} className="bg-surface-850 border border-surface-800 rounded-lg px-3 py-2 text-sm text-slate-300">
              {f}
            </div>
          ))}
        </div>
      </Section>
      <Section title="Security Design">
        <div className="bg-surface-850 border border-surface-800 rounded-lg p-4 text-sm space-y-1.5">
          <div><span className="text-slate-500">Authentication:</span> <span className="text-slate-300">{spec.security.authentication}</span></div>
          <div><span className="text-slate-500">Authorization:</span> <span className="text-slate-300">{spec.security.authorization}</span></div>
        </div>
      </Section>
      {project.modifications.length > 0 && (
        <Section title={`Modification History (${project.modifications.length})`}>
          <div className="space-y-2">
            {project.modifications.map((m, i) => (
              <div key={i} className="bg-surface-850 border border-surface-800 rounded-lg p-3 text-sm">
                <span className="text-purple-400 font-medium">“{m.instruction}”</span>
                <span className="text-slate-500 ml-2 text-xs">
                  intent: {m.analysis.intent}
                  {m.analysis.new_entities.length > 0 && ` · added: ${m.analysis.new_entities.join(", ")}`}
                  {m.analysis.removed_entities.length > 0 && ` · removed: ${m.analysis.removed_entities.join(", ")}`}
                </span>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

function ArchitectureTab({ project }: { project: Project }) {
  const arch = project.architecture;
  if (!arch?.style) return <EmptyState text="Architecture not designed yet." />;
  return (
    <div>
      <Section title={`Style: ${arch.style}`}>
        <p className="text-slate-400 text-sm leading-relaxed">{arch.rationale}</p>
      </Section>
      <Section title="System Diagram">
        <MermaidDiagram chart={arch.diagram} />
      </Section>
      <Section title="Layers">
        <div className="overflow-x-auto">
          <table className="min-w-full text-sm">
            <thead>
              <tr className="text-left text-slate-500 border-b border-surface-800">
                <th className="py-2 pr-4 font-medium">Layer</th>
                <th className="py-2 pr-4 font-medium">Technology</th>
                <th className="py-2 font-medium">Responsibility</th>
              </tr>
            </thead>
            <tbody>
              {arch.layers.map((l) => (
                <tr key={l.name} className="border-b border-surface-800/50">
                  <td className="py-2 pr-4 text-slate-200 font-medium">{l.name}</td>
                  <td className="py-2 pr-4 text-brand-400 font-mono text-xs">{l.technology}</td>
                  <td className="py-2 text-slate-400">{l.responsibility}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
      <Section title="Technology Stack">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {Object.entries(project.tech_stack).map(([key, value]) => (
            <div key={key} className="bg-surface-850 border border-surface-800 rounded-lg p-3">
              <div className="text-xs text-slate-500 uppercase tracking-wide">{key}</div>
              {typeof value === "string" ? (
                <div className="text-sm text-slate-300 mt-1">{value}</div>
              ) : (
                <div className="mt-1 space-y-0.5">
                  {Object.entries(value).map(([k, v]) => (
                    <div key={k} className="text-xs text-slate-400">
                      <span className="text-slate-500">{k}:</span> {v}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function DatabaseTab({ project }: { project: Project }) {
  const schema = project.database_schema;
  if (!schema?.entities) return <EmptyState text="Database schema not designed yet." />;
  return (
    <div>
      <Section title="ER Diagram">
        <MermaidDiagram chart={schema.er_diagram} />
      </Section>
      <Section title={`Relationships (${schema.relationships.length})`}>
        <div className="space-y-1">
          {schema.relationships.map((r, i) => (
            <div key={i} className="text-sm text-slate-400 font-mono">
              <span className="text-emerald-400">{r.from}</span>
              <span className="text-slate-600"> → </span>
              <span className="text-brand-400">{r.to}</span>
              <span className="text-slate-600 text-xs ml-2">({r.type})</span>
            </div>
          ))}
        </div>
      </Section>
      <Section title={`Tables (${schema.entities.length})`}>
        <div className="space-y-4">
          {schema.entities.map((ent) => (
            <div key={ent.name} className="bg-surface-850 border border-surface-800 rounded-lg overflow-hidden">
              <div className="px-4 py-2 bg-surface-800/50 flex items-center gap-3">
                <span className="font-semibold text-slate-200 text-sm">{ent.name}</span>
                <span className="text-xs text-slate-500 font-mono">{ent.table}</span>
              </div>
              <table className="min-w-full text-xs">
                <tbody>
                  {ent.fields.map((f) => (
                    <tr key={f.name} className="border-t border-surface-800/50">
                      <td className="px-4 py-1.5 font-mono text-slate-300">{f.name}</td>
                      <td className="px-4 py-1.5 font-mono text-brand-400">{f.type}</td>
                      <td className="px-4 py-1.5 text-slate-500">
                        {f.primary_key && <Badge color="bg-amber-500/15 text-amber-400">PK</Badge>}
                        {f.type === "fk" && <Badge color="bg-purple-500/15 text-purple-400">FK→{f.ref}</Badge>}
                        {f.unique && <Badge color="bg-sky-500/15 text-sky-400">unique</Badge>}
                        {f.nullable && <Badge color="bg-slate-500/15 text-slate-400">null</Badge>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ))}
        </div>
      </Section>
      <Section title="SQL DDL (migrations/0001_init.sql)">
        <pre className="code max-h-96 overflow-y-auto">{schema.sql}</pre>
      </Section>
    </div>
  );
}

function ApiTab({ project }: { project: Project }) {
  const contract = project.api_contract;
  if (!contract?.endpoints) return <EmptyState text="API contract not designed yet." />;
  const byResource = new Map<string, typeof contract.endpoints>();
  for (const ep of contract.endpoints) {
    byResource.set(ep.resource, [...(byResource.get(ep.resource) ?? []), ep]);
  }
  return (
    <div>
      <Section title={`REST Endpoints (${contract.endpoints.length})`}>
        <div className="space-y-4">
          {[...byResource.entries()].map(([resource, eps]) => (
            <div key={resource}>
              <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1.5">{resource}</h4>
              <div className="space-y-1">
                {eps.map((ep, i) => (
                  <div key={i} className="flex items-center gap-3 bg-surface-850 border border-surface-800 rounded-lg px-3 py-2">
                    <Badge color={METHOD_COLORS[ep.method] ?? "bg-slate-500/15 text-slate-400"}>
                      {ep.method}
                    </Badge>
                    <code className="text-sm text-slate-200 font-mono">{ep.path}</code>
                    <span className="text-xs text-slate-500 ml-auto hidden sm:block">{ep.summary}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
      <Section title="OpenAPI 3.0 Specification">
        <pre className="code max-h-80 overflow-y-auto">
          {JSON.stringify(contract.openapi, null, 2).slice(0, 12000)}
        </pre>
      </Section>
    </div>
  );
}

function UiUxTab({ project }: { project: Project }) {
  const design = project.ui_design;
  if (!design?.pages) return <EmptyState text="UI design not available yet." />;
  return (
    <div>
      <Section title={`Pages (${design.pages.length})`}>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {design.pages.map((p) => (
            <div key={p.name} className="bg-surface-850 border border-surface-800 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="font-medium text-slate-200 text-sm">{p.name}</span>
                <Badge color={p.public ? "bg-emerald-500/15 text-emerald-400" : "bg-amber-500/15 text-amber-400"}>
                  {p.public ? "public" : "protected"}
                </Badge>
              </div>
              <code className="text-xs text-brand-400 block mt-1">{p.path}</code>
              <p className="text-xs text-slate-500 mt-2">{p.description}</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {p.components.map((c) => (
                  <span key={c} className="text-xs bg-surface-800 text-slate-400 rounded px-1.5 py-0.5">{c}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </Section>
      <Section title="Shared Components">
        <div className="flex flex-wrap gap-2">
          {design.shared_components.map((c) => (
            <Badge key={c} color="bg-surface-800 text-slate-300">{c}</Badge>
          ))}
        </div>
      </Section>
    </div>
  );
}

function FilesTab({ project }: { project: Project }) {
  const [selected, setSelected] = useState<string | null>(null);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(false);

  const open = async (path: string) => {
    setSelected(path);
    setLoading(true);
    try {
      const resp = await api.fileContent(project.id, path);
      setContent(resp.content);
    } catch (err) {
      setContent(`Error: ${err instanceof Error ? err.message : "failed to load"}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
      <div className="bg-surface-850 border border-surface-800 rounded-lg p-2 max-h-[32rem] overflow-y-auto">
        {project.file_structure.map((path) => (
          <button
            key={path}
            onClick={() => open(path)}
            className={`block w-full text-left text-xs font-mono px-2.5 py-1.5 rounded truncate transition ${
              selected === path ? "bg-brand-600/20 text-brand-300" : "text-slate-400 hover:bg-surface-800"
            }`}
          >
            {path}
          </button>
        ))}
      </div>
      <div className="lg:col-span-2">
        {selected ? (
          <div>
            <div className="text-xs text-slate-500 font-mono mb-2">{selected}</div>
            {loading ? (
              <div className="text-slate-500 text-sm">Loading…</div>
            ) : (
              <pre className="code max-h-[30rem] overflow-auto">{content}</pre>
            )}
          </div>
        ) : (
          <EmptyState text="Select a file to view its generated content." />
        )}
      </div>
    </div>
  );
}

function TestsTab({ project }: { project: Project }) {
  const tests = project.tests;
  const validation = project.validation;
  if (!tests?.files) return <EmptyState text="Tests not generated yet." />;
  const result = tests.result ?? {};
  const stages = validation?.history?.[validation.history.length - 1]?.report?.stages ?? {};
  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        <StatCard label="Test Files" value={String(tests.files.length)} />
        <StatCard label="Passed" value={String(result.passed ?? 0)} accent="text-emerald-400" />
        <StatCard label="Failed" value={String(result.failed ?? 0)} accent="text-red-400" />
        <StatCard label="Debug Iterations" value={String(validation?.iterations ?? 0)} />
      </div>
      <Section title="Validation Pipeline">
        <div className="space-y-1.5">
          {Object.entries(stages).map(([stage, s]) => (
            <div key={stage} className="flex items-center gap-3 bg-surface-850 border border-surface-800 rounded-lg px-3 py-2 text-sm">
              <span>{s.status === "passed" ? "✅" : s.status === "failed" ? "❌" : "⏭️"}</span>
              <span className="text-slate-200 font-medium capitalize">{stage.replace("_", " ")}</span>
              <span className="text-slate-500 text-xs ml-auto">{s.detail}</span>
            </div>
          ))}
        </div>
      </Section>
      <Section title="Requirement → Test Traceability">
        <div className="space-y-1">
          {tests.traceability.map((t, i) => (
            <div key={i} className="flex items-center gap-2 text-xs">
              <span className="text-slate-300">{t.requirement}</span>
              <span className="text-slate-600">→</span>
              <code className="text-brand-400 font-mono">{t.test_file}</code>
            </div>
          ))}
        </div>
      </Section>
      <Section title="Test Files">
        <div className="space-y-1">
          {tests.files.map((f) => (
            <code key={f} className="block text-xs font-mono text-slate-400">{f}</code>
          ))}
        </div>
      </Section>
    </div>
  );
}

function StatCard({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="bg-surface-850 border border-surface-800 rounded-lg p-4 text-center">
      <div className={`text-2xl font-bold ${accent ?? "text-slate-100"}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-1">{label}</div>
    </div>
  );
}

function SecurityTab({ project }: { project: Project }) {
  const sec = project.security;
  if (!sec?.score && sec?.score !== 0) return <EmptyState text="Security analysis not run yet." />;
  const color = sec.score >= 90 ? "text-emerald-400" : sec.score >= 75 ? "text-amber-400" : "text-red-400";
  return (
    <div>
      <div className="flex items-center gap-6 mb-6">
        <div className={`text-5xl font-bold ${color}`}>{sec.score}<span className="text-lg text-slate-500">/100</span></div>
        <div>
          <Badge color="bg-brand-500/15 text-brand-400">Grade {sec.grade}</Badge>
          <p className="text-sm text-slate-400 mt-2">{sec.summary}</p>
        </div>
      </div>
      {sec.findings.length > 0 && (
        <Section title={`Findings (${sec.findings.length})`}>
          <div className="space-y-2">
            {sec.findings.map((f, i) => (
              <div key={i} className="bg-surface-850 border border-surface-800 rounded-lg p-3">
                <div className="flex items-center gap-2">
                  <Badge color={f.severity === "critical" ? "bg-red-500/15 text-red-400" : f.severity === "high" ? "bg-orange-500/15 text-orange-400" : "bg-amber-500/15 text-amber-400"}>
                    {f.severity}
                  </Badge>
                  <span className="text-sm text-slate-200 font-medium">{f.category.replace(/_/g, " ")}</span>
                </div>
                <p className="text-xs text-slate-400 mt-1.5">{f.detail}</p>
                <p className="text-xs text-emerald-400 mt-1">💡 {f.fix}</p>
              </div>
            ))}
          </div>
        </Section>
      )}
      <Section title={`Checks Passed (${sec.checks_passed.length})`}>
        <div className="space-y-1">
          {sec.checks_passed.map((c, i) => (
            <div key={i} className="text-xs text-slate-400 flex gap-2">
              <span className="text-emerald-400">✓</span> {c}
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

function DocsTab({ project }: { project: Project }) {
  const docs = project.documentation;
  const [selected, setSelected] = useState<string>(Object.keys(docs)[0] ?? "");
  if (!docs || Object.keys(docs).length === 0) return <EmptyState text="Documentation not generated yet." />;
  return (
    <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
      <div className="space-y-1">
        {Object.keys(docs).map((name) => (
          <button
            key={name}
            onClick={() => setSelected(name)}
            className={`block w-full text-left text-xs font-mono px-3 py-2 rounded-lg transition ${
              selected === name ? "bg-brand-600/20 text-brand-300" : "text-slate-400 hover:bg-surface-800"
            }`}
          >
            {name}
          </button>
        ))}
      </div>
      <div className="lg:col-span-3">
        <pre className="code max-h-[34rem] overflow-auto whitespace-pre-wrap">{docs[selected]}</pre>
      </div>
    </div>
  );
}

function DeployTab({ project }: { project: Project }) {
  const deploy = project.deployment;
  if (!deploy?.files) return <EmptyState text="Deployment config not generated yet." />;
  return (
    <div>
      <Section title="Deployment Targets">
        <div className="flex flex-wrap gap-2">
          {deploy.targets.map((t) => (
            <Badge key={t} color="bg-emerald-500/15 text-emerald-400">{t}</Badge>
          ))}
        </div>
      </Section>
      <Section title="Generated Configuration Files">
        <div className="space-y-1">
          {deploy.files.map((f) => (
            <code key={f} className="block text-xs font-mono text-slate-400">{f}</code>
          ))}
        </div>
      </Section>
      <Section title="Quick Start">
        <pre className="code">{`cd ${project.name.toLowerCase().replace(/\s+/g, "-")}
docker compose up --build
# API → http://localhost:8000/docs
# Frontend → http://localhost:5173`}</pre>
      </Section>
    </div>
  );
}
