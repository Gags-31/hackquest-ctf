import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { RoundsResponse } from "../lib/types";

export default function Arena() {
  const [data, setData] = useState<RoundsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    get<RoundsResponse>("/api/rounds").then(setData).catch((e: Error) => setErr(e.message));
  }, []);

  if (err) return <p className="card border-neon-rose/40 text-neon-rose">{err}</p>;
  if (!data) return <p className="muted">Loading arena…</p>;

  if (data.state.disqualified) {
    return (
      <div className="card border-neon-rose/50 text-center">
        <h1 className="text-2xl font-bold text-neon-rose">Disqualified</h1>
        <p className="muted mx-auto mt-2 max-w-md">
          Three proctoring violations were recorded. You may still view the leaderboard.
          To appeal, contact an organizer with your team code.
        </p>
        <Link className="btn-ghost mt-4" to="/leaderboard">View leaderboard</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="h1">Challenge arena</h1>
          <p className="muted mt-1">
            A round unlocks only when you complete the previous one AND the organizer opens it.
          </p>
        </div>
        <p className="muted font-mono">
          Max score: <span className="text-neon-cyan">{data.scoring.max_possible.toLocaleString()}</span>
          <span className="ml-2 text-slate-500">({data.scoring.mode})</span>
        </p>
      </div>

      {data.state.competition !== "running" && (
        <p className="card border-neon-amber/40 text-sm text-neon-amber">
          Competition status: <b>{data.state.competition}</b>. Submissions are only accepted
          while the competition is running.
        </p>
      )}

      <ol className="space-y-3">
        {data.rounds.map((r) => {
          const pct = r.challenges_total
            ? Math.round((r.challenges_solved / r.challenges_total) * 100)
            : 0;
          return (
            <li key={r.number}>
              <div
                className={`card flex flex-wrap items-center justify-between gap-4 ${
                  r.unlocked ? "" : "opacity-55"
                }`}
              >
                <div className="min-w-[240px] flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-xs uppercase tracking-widest text-slate-500">
                      Round {r.number}
                    </span>
                    {r.unlocked ? (
                      <span className={`pill ${
                        r.state === "open"
                          ? "bg-neon-lime/15 text-neon-lime"
                          : "bg-neon-amber/15 text-neon-amber"
                      }`}>
                        {r.state === "open" ? "open" : r.state}
                      </span>
                    ) : (
                      <span className="pill bg-ink-700 text-slate-400">locked</span>
                    )}
                  </div>
                  <h2 className="mt-1 text-lg font-semibold text-white">{r.name}</h2>
                  <p className="muted">{r.blurb}</p>
                </div>
                <div className="w-full sm:w-48">
                  <p className="mb-1 text-right font-mono text-xs text-slate-400">
                    {r.challenges_solved} / {r.challenges_total}
                  </p>
                  <div className="h-2 overflow-hidden rounded-full bg-ink-800">
                    <div className="h-full rounded-full bg-gradient-to-r from-neon-cyan to-neon-violet"
                      style={{ width: `${pct}%` }} />
                  </div>
                </div>
                {r.unlocked ? (
                  <Link className="btn-primary" to={`/round/${r.slug}`}>Enter</Link>
                ) : (
                  <span className="btn-ghost cursor-not-allowed opacity-50">Locked</span>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}