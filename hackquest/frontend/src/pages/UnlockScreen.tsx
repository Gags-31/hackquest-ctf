import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { RoundsResponse } from "../lib/types";

/** Waiting screen shown when the next round is complete but not yet opened. */
export default function UnlockScreen() {
  const [data, setData] = useState<RoundsResponse | null>(null);

  useEffect(() => {
    get<RoundsResponse>("/api/rounds").then(setData).catch(() => undefined);
  }, []);

  if (!data) return <p className="muted">Loading…</p>;

  const nextRound = data.rounds.find((r) => r.unlocked);
  const dq = data.state.disqualified;

  return (
    <div className="mx-auto max-w-xl space-y-5 text-center">
      <div className="card py-10">
        <p className="font-mono text-xs uppercase tracking-[0.3em] text-neon-cyan">
          Round complete
        </p>
        <h1 className="mt-3 text-3xl font-bold text-white">Waiting for the next round</h1>
        <p className="muted mx-auto mt-3 max-w-md">
          Nice work — your team has completed this round. The next round is released by an
          organizer, so the pace stays fair for everyone. This page updates when it opens.
        </p>

        <div className="mt-6 grid gap-2 sm:grid-cols-2">
          {data.rounds.map((r) => (
            <div
              key={r.number}
              className={`rounded-lg border p-3 text-left ${
                r.unlocked
                  ? "border-neon-lime/40 bg-neon-lime/5"
                  : r.challenges_solved === r.challenges_total && r.challenges_total > 0
                    ? "border-neon-amber/40 bg-neon-amber/5"
                    : "border-ink-700 bg-ink-850"
              }`}
            >
              <p className="font-mono text-[10px] uppercase tracking-widest text-slate-500">
                Round {r.number}
              </p>
              <p className="text-sm font-medium text-white">{r.name}</p>
              <p className="text-xs text-slate-400">
                {r.challenges_solved}/{r.challenges_total} solved
              </p>
            </div>
          ))}
        </div>

        {nextRound && (
          <Link className="btn-primary mt-6" to={`/round/${nextRound.slug}`}>
            Continue to Round {nextRound.number} →
          </Link>
        )}

        {dq && (
          <p className="mt-4 text-sm text-neon-rose">
            Your team is disqualified and cannot proceed.
          </p>
        )}

        <div className="mt-6 flex justify-center gap-3 text-sm">
          <Link className="link" to="/arena">Arena</Link>
          <Link className="link" to="/leaderboard">Leaderboard</Link>
        </div>
      </div>
    </div>
  );
}