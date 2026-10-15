import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../lib/api";

type Results = {
  published: boolean;
  message?: string;
  max_possible?: number;
  scoring_mode?: string;
  rows?: { rank: number; team: string; solved: number; points: number; status: string }[];
};

export default function Results() {
  const [r, setR] = useState<Results | null>(null);

  useEffect(() => {
    get<Results>("/api/results").then(setR).catch(() => undefined);
  }, []);

  if (!r) return <p className="muted">Loading results…</p>;

  if (!r.published) {
    return (
      <div className="mx-auto max-w-lg text-center">
        <div className="card py-10">
          <p className="font-mono text-xs uppercase tracking-[0.3em] text-neon-cyan">
            Results pending
          </p>
          <h1 className="mt-3 text-2xl font-bold text-white">Not published yet</h1>
          <p className="muted mt-2">
            {r.message ?? "Results are published once score verification is complete."}
          </p>
          <Link className="btn-ghost mt-5" to="/leaderboard">View live leaderboard</Link>
        </div>
      </div>
    );
  }

  const top = r.rows?.slice(0, 3) ?? [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="h1">Final results</h1>
        <p className="muted mt-1">
          Max {r.max_possible?.toLocaleString()} · mode <span className="font-mono">{r.scoring_mode}</span>
        </p>
      </div>

      <div className="grid gap-3 sm:grid-cols-3">
        {top.map((t) => (
          <div
            key={t.team}
            className={`card text-center ${
              t.rank === 1 ? "border-neon-amber/50 bg-neon-amber/5" : ""
            }`}
          >
            <p className="text-2xl">{["🥇", "🥈", "🥉"][t.rank - 1] ?? `#${t.rank}`}</p>
            <p className="mt-1 font-semibold text-white">{t.team}</p>
            <p className="font-mono text-neon-cyan">{t.points} pts</p>
          </div>
        ))}
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="table">
          <thead><tr><th>Rank</th><th>Team</th><th>Solved</th><th>Points</th><th>Status</th></tr></thead>
          <tbody>
            {r.rows?.map((t) => (
              <tr key={t.team}>
                <td className="font-mono">{t.rank}</td>
                <td className="text-white">{t.team}</td>
                <td>{t.solved}</td>
                <td className="font-mono text-neon-cyan">{t.points}</td>
                <td className="text-slate-400">{t.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}