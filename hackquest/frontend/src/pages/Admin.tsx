import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get, post } from "../lib/api";

type Board = {
  rows: { rank: number; team: string; solved: number; points: number; violations: number; status: string }[];
  scoring: { mode: string; max_possible: number; rounding_policy: string };
};
type Settings = {
  settings: Record<string, string>;
  limits: { proctor_violations: number };
  email_configured: boolean;
};

export default function Admin() {
  const [board, setBoard] = useState<Board | null>(null);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  const load = useCallback(() => {
    get<Board>("/api/admin/leaderboard").then(setBoard).catch(() => undefined);
    get<Settings>("/api/admin/settings").then(setSettings).catch(() => undefined);
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 20000);
    return () => clearInterval(id);
  }, [load]);

  async function act(fn: () => Promise<unknown>, okText: string) {
    setMsg(null);
    try {
      await fn();
      setMsg({ ok: true, text: okText });
      load();
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    }
  }

  if (!settings) return <p className="muted">Loading admin console…</p>;
  const s = settings.settings;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="h1">Organizer console</h1>
          <p className="muted mt-1">Control the event. Every action is written to the audit log.</p>
        </div>
        <Link className="btn-ghost" to="/admin/audit">Audit log →</Link>
      </div>

      {msg && (
        <p className={`card text-sm ${msg.ok ? "border-neon-lime/40 text-neon-lime" : "border-neon-rose/40 text-neon-rose"}`}>
          {msg.text}
        </p>
      )}

      {!settings.email_configured && (
        <p className="card border-neon-amber/40 text-sm text-neon-amber">
          Email is not configured. Teams are treated as verified automatically and password
          recovery cannot send mail. Set SMTP_* variables to enable it.
        </p>
      )}

      <section className="card space-y-3">
        <h2 className="h2">Competition control</h2>
        <div className="flex flex-wrap gap-2">
          {(["pending", "running", "paused", "ended"] as const).map((st) => (
            <button
              key={st}
              className={s.competition_state === st ? "btn-primary" : "btn-ghost"}
              onClick={() => act(() => post(`/api/admin/competition?state=${st}`), `Competition set to ${st}.`)}
            >
              {st}
            </button>
          ))}
        </div>
      </section>

      <section className="card space-y-3">
        <h2 className="h2">Round release</h2>
        <div className="flex flex-wrap gap-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <div key={n} className="flex items-center gap-1">
              <button
                className={s.open_round === String(n) ? "btn-primary" : "btn-ghost"}
                onClick={() => act(() => post("/api/admin/rounds", { number: n, state: "open" }), `Round ${n} opened.`)}
              >
                Open R{n}
              </button>
              <button
                className="btn-ghost px-2"
                onClick={() => act(() => post("/api/admin/rounds", { number: n, state: "closed" }), `Round ${n} closed (solutions published).`)}
              >
                Close
              </button>
              <button
                className="btn-ghost px-2"
                onClick={() => act(() => post("/api/admin/rounds", { number: n, state: "locked" }), `Round ${n} locked.`)}
              >
                Lock
              </button>
            </div>
          ))}
        </div>
        <p className="muted">
          Opening a round lets teams that finished the previous round proceed. Locking freezes everyone.
        </p>
      </section>

      <section className="card space-y-3">
        <h2 className="h2">Configuration</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <label className="block">
            <span className="label">Scoring mode</span>
            <select
              className="input"
              value={s.scoring_mode ?? "tier"}
              onChange={(e) => act(() => post("/api/admin/settings", { key: "scoring_mode", value: e.target.value }), "Scoring mode updated.")}
            >
              <option value="tier">Tier weighted (max 4200)</option>
              <option value="normalized">Normalized (max 3499)</option>
            </select>
          </label>
          <label className="block">
            <span className="label">Hint penalty (points per hint)</span>
            <input
              className="input"
              type="number"
              min={0}
              defaultValue={s.hint_penalty ?? "0"}
              onBlur={(e) => act(() => post("/api/admin/settings", { key: "hint_penalty", value: e.target.value }), "Hint penalty updated.")}
            />
          </label>
          <label className="block">
            <span className="label">Event date &amp; time</span>
            <input
              className="input"
              placeholder="2026-11-20T11:00"
              defaultValue={s.event_datetime ?? ""}
              onBlur={(e) => act(() => post("/api/admin/settings", { key: "event_datetime", value: e.target.value }), "Event time updated.")}
            />
          </label>
          <label className="block">
            <span className="label">Timezone</span>
            <input
              className="input"
              defaultValue={s.event_timezone ?? "Asia/Kolkata"}
              onBlur={(e) => act(() => post("/api/admin/settings", { key: "event_timezone", value: e.target.value }), "Timezone updated.")}
            />
          </label>
        </div>

        <div className="flex flex-wrap gap-2 pt-2">
          <button
            className={s.registration_open === "1" ? "btn-violet" : "btn-ghost"}
            onClick={() => act(() => post("/api/admin/settings", { key: "registration_open", value: s.registration_open === "1" ? "0" : "1" }), "Registration toggled.")}
          >
            Registration: {s.registration_open === "1" ? "open" : "closed"}
          </button>
          <button
            className={s.results_frozen === "1" ? "btn-violet" : "btn-ghost"}
            onClick={() => act(() => post("/api/admin/settings", { key: "results_frozen", value: s.results_frozen === "1" ? "0" : "1" }), "Scoreboard freeze toggled.")}
          >
            Freeze board
          </button>
          <button
            className={s.results_published === "1" ? "btn-violet" : "btn-ghost"}
            onClick={() => act(() => post("/api/admin/settings", { key: "results_published", value: s.results_published === "1" ? "0" : "1" }), "Results published toggled.")}
          >
            Publish results
          </button>
        </div>

        {board && (
          <p className="muted mt-2">
            Current mode: <b className="font-mono">{board.scoring.mode}</b> · max{" "}
            <b className="font-mono">{board.scoring.max_possible}</b>. {board.scoring.rounding_policy}
          </p>
        )}
      </section>

      <section className="card space-y-3">
        <h2 className="h2">Teams in progress</h2>
        <div className="overflow-x-auto">
          <table className="table">
            <thead>
              <tr><th>#</th><th>Team</th><th>Solved</th><th>Points</th><th>Violations</th><th>Status</th></tr>
            </thead>
            <tbody>
              {board?.rows.map((r) => (
                <tr key={r.team}>
                  <td className="font-mono">{r.rank}</td>
                  <td className="text-white">{r.team}</td>
                  <td>{r.solved}</td>
                  <td className="font-mono text-neon-cyan">{r.points}</td>
                  <td>{r.violations}</td>
                  <td>{r.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <section className="card space-y-2">
        <h2 className="h2">Exports</h2>
        <div className="flex flex-wrap gap-2">
          <a className="btn-ghost" href="/api/admin/export/leaderboard.csv">Leaderboard CSV</a>
          <a className="btn-ghost" href="/api/admin/export/registrations.csv">Registrations CSV</a>
          <a className="btn-ghost" href="/api/admin/export/submissions.csv">Submissions CSV</a>
        </div>
      </section>
    </div>
  );
}