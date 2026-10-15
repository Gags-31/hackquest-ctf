import { useEffect, useState } from "react";
import { get } from "../lib/api";

type Entry = {
  id: number;
  actor: string;
  action: string;
  target: string;
  detail: string;
  at: string | null;
  ip: string;
};

export default function AuditLog() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    get<{ entries: Entry[] }>("/api/admin/audit")
      .then((d) => setEntries(d.entries))
      .catch((e: Error) => setErr(e.message));
  }, []);

  if (err) return <p className="card border-neon-rose/40 text-neon-rose">{err}</p>;

  return (
    <div className="space-y-5">
      <div>
        <h1 className="h1">Audit log</h1>
        <p className="muted mt-1">
          Append-only. Entries cannot be edited or deleted from the application.
        </p>
      </div>
      <div className="card overflow-x-auto p-0">
        <table className="table">
          <thead>
            <tr><th>#</th><th>When</th><th>Actor</th><th>Action</th><th>Target</th><th>Detail</th><th>IP</th></tr>
          </thead>
          <tbody>
            {entries.length === 0 && (
              <tr><td colSpan={7} className="py-6 text-center text-slate-500">No entries</td></tr>
            )}
            {entries.map((e) => (
              <tr key={e.id}>
                <td className="font-mono text-slate-500">{e.id}</td>
                <td className="whitespace-nowrap font-mono text-xs">{e.at ?? ""}</td>
                <td className="text-white">{e.actor}</td>
                <td><span className="pill bg-ink-700 font-mono text-neon-cyan">{e.action}</span></td>
                <td className="text-slate-400">{e.target}</td>
                <td className="max-w-xs truncate text-slate-500">{e.detail}</td>
                <td className="font-mono text-xs text-slate-600">{e.ip}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}