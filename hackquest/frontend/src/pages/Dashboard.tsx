import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { RoundsResponse } from "../lib/types";
import { useSession } from "../App";
import { useHeartbeat } from "../lib/proctor";

export default function Dashboard() {
  const { me } = useSession();
  const [data, setData] = useState<RoundsResponse | null>(null);
  useHeartbeat();

  useEffect(() => {
    get<RoundsResponse>("/api/rounds").then(setData).catch(() => undefined);
  }, []);

  const team = me.authenticated && me.role === "team" ? me : null;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="h1">Team dashboard</h1>
        {team?.team_name && (
          <p className="muted mt-1">
            Signed in as <b className="text-white">{team.team_name}</b> ·{" "}
            code <span className="font-mono text-neon-cyan">{team.team_code}</span>
          </p>
        )}
      </div>

      {data?.state.disqualified && (
        <p className="card border-neon-rose/50 text-neon-rose">
          Your team is disqualified after three proctoring violations. Contact an organizer to appeal.
        </p>
      )}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="card">
              <p className="label">Competition</p>
              <p className="font-mono text-lg font-semibold text-neon-cyan">{data.state.competition}</p>
            </div>
            <div className="card">
              <p className="label">Max possible</p>
              <p className="font-mono text-lg font-semibold text-white">
                {data.scoring.max_possible.toLocaleString()}
              </p>
            </div>
            <div className="card">
              <p className="label">Scoring mode</p>
              <p className="font-mono text-lg font-semibold text-white">{data.scoring.mode}</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            <Link className="btn-primary" to="/arena">Open arena</Link>
            <Link className="btn-ghost" to="/leaderboard">Leaderboard</Link>
            <Link className="btn-ghost" to="/profile">Profile &amp; members</Link>
          </div>
        </>
      )}
    </div>
  );
}