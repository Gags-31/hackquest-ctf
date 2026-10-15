import { useEffect, useState } from "react";
import { get } from "../lib/api";

type Board = {
  rows: {
    rank: number;
    team: string;
    team_code: string;
    solved: number;
    attempted: number;
    points: number;
    violations: number;
    status: string;
  }[];
  max_possible: number;
  scoring_mode: string;
  frozen: boolean;
  published: boolean;
  event_timezone: string;
};

export default function Leaderboard() {
  const [b, setB] = useState<Board | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    const load = () =>
      get<Board>("/api/leaderboard").then(setB).catch((e: Error) => setErr(e.message));
    load();
    const id = setInterval(load, 20000);
    return () => clearInterval(id);
  }, []);

  if (err) return <p className="card border-neon-rose/40 text-neon-rose">{err}</p>;
  if (!b) return <p className="muted">Loading leaderboard…</p>;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="h1">Live leaderboard</h1>
          <p className="muted mt-1">
            Tie-break order: score, then earliest final solve, then fewest violations.
          </p>
        </div>
        <div className="text-right text-xs text-slate-500">
          <p>Max {b.max_possible.toLocaleString()} · mode <span className="font-mono">{b.scoring_mode}</span></p>
          <p>Times in {b.event_timezone}</p>
          {b.frozen && <p className="mt-1 font-semibold text-neon-amber">Board frozen</p>}
        </div>
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="table">
          <thead>
            <tr>
              <th>#</th><th>Team</th><th>Solved</th><th>Points</th>
              <th>Attempts</th><th>Status</th>
            </tr>
          </thead>
          <tbody>
            {b.rows.length === 0 && (
              <tr><td colSpan={6} className="py-6 text-center text-slate-500">No teams yet</td></tr>
            )}
            {b.rows.map((r) => (
              <tr key={r.team_code}>
                <td className="font-mono">{r.rank}</td>
                <td className="font-medium text-white">{r.team}</td>
                <td>{r.solved}</td>
                <td className="font-mono font-semibold text-neon-cyan">{r.points}</td>
                <td className="text-slate-400">{r.attempted}</td>
                <td>
                  {r.status === "disqualified" ? (
                    <span className="pill bg-neon-rose/15 text-neon-rose">DQ</span>
                  ) : r.violations > 0 ? (
                    <span className="pill bg-neon-amber/15 text-neon-amber">
                      {r.violations} flagged
                    </span>
                  ) : (
                    <span className="pill bg-neon-lime/15 text-neon-lime">clean</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="muted">Refreshes every 20 seconds.</p>
    </div>
  );
}