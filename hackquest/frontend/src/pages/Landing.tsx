import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../lib/api";
import type { RoundsResponse } from "../lib/types";
import { useSession } from "../App";

const TIERS = [
  {
    n: 1,
    name: "Logic Labyrinth",
    blurb: "Sums, Fibonacci and exponentiation — answered in base-36.",
    pts: "300",
    tone: "text-neon-lime",
  },
  {
    n: 2,
    name: "Cipher Vault",
    blurb: "Caesar shift, Base64 and a reversed ROT13.",
    pts: "600",
    tone: "text-neon-cyan",
  },
  {
    n: 3,
    name: "Tech Riddles",
    blurb: "Sequences, data structures, ports and binary.",
    pts: "1,200",
    tone: "text-neon-violet",
  },
  {
    n: 4,
    name: "Capture The Flag",
    blurb: "Four web-security questions in a self-contained training lab.",
    pts: "1,600",
    tone: "text-neon-amber",
  },
  {
    n: 5,
    name: "The Debug Sprint",
    blurb: "Repair broken code until every hidden test passes.",
    pts: "500",
    tone: "text-neon-rose",
  },
];

function Countdown({ iso, tz }: { iso: string; tz: string }) {
  const [left, setLeft] = useState<number | null>(null);

  useEffect(() => {
    if (!iso) return;
    // The server sends an ISO timestamp; treat it as wall-clock in `tz`.
    const target = Date.parse(iso.length <= 16 ? `${iso}:00${tzOffset(tz)}` : iso);
    if (Number.isNaN(target)) return;
    const tick = () => setLeft(Math.max(0, target - Date.now()));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [iso, tz]);

  if (!iso || left === null) return null;

  const d = Math.floor(left / 86400000);
  const h = Math.floor((left % 86400000) / 3600000);
  const m = Math.floor((left % 3600000) / 60000);
  const s = Math.floor((left % 60000) / 1000);

  return (
    <div className="card mt-6 text-center">
      <p className="label mb-3">Competition begins in</p>
      <div className="flex justify-center gap-4 font-mono text-3xl font-bold text-neon-cyan">
        {[
          [d, "days"],
          [h, "hrs"],
          [m, "min"],
          [s, "sec"],
        ].map(([v, l]) => (
          <div key={l as string}>
            <div>{String(v).padStart(2, "0")}</div>
            <div className="text-[10px] font-normal uppercase tracking-widest text-slate-500">{l}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function tzOffset(tz: string) {
  try {
    const d = new Date();
    const s = new Intl.DateTimeFormat("en-US", { timeZone: tz, timeZoneName: "shortOffset" })
      .formatToParts(d)
      .find((p) => p.type === "timeZoneName")?.value ?? "+00:00";
    const m = s.match(/GMT([+-]\d{2}):(\d{2})/);
    return m ? `${m[1]}:${m[2]}` : "+00:00";
  } catch {
    return "+00:00";
  }
}

export default function Landing() {
  const { me } = useSession();
  const [data, setData] = useState<RoundsResponse | null>(null);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    get<RoundsResponse>("/api/rounds")
      .then(setData)
      .catch((e: Error) => setErr(e.message));
  }, []);

  const max = data?.scoring.max_possible ?? 4200;

  return (
    <div className="space-y-12">
      <section className="py-10 text-center">
        <p className="font-mono text-xs uppercase tracking-[0.35em] text-neon-violet">
          Pragyan × IEEE-CS KLEIT Chapter
        </p>
        <h1 className="mt-4 text-5xl font-black tracking-tight text-white sm:text-6xl">
          HACK<span className="text-neon-cyan">QUEST</span>
          <span className="block text-2xl font-semibold text-slate-400 sm:text-3xl">CTF 2026</span>
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-slate-300">
          Break the Target. Own the Flag. An online capture-the-flag competition
          across five escalating rounds — logic, ciphers, riddles, web security
          and live debugging.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          {me.authenticated ? (
            <Link className="btn-primary" to="/arena">Enter the arena</Link>
          ) : (
            <>
              <Link className="btn-primary" to="/register">Register your team</Link>
              <Link className="btn-ghost" to="/leaderboard">Leaderboard</Link>
            </>
          )}
          <Link className="btn-ghost" to="/rules">Rules &amp; FAQ</Link>
        </div>
        {data && <Countdown iso={data.event_datetime} tz={data.event_timezone} />}
      </section>

      {err && (
        <p className="card border-neon-rose/40 text-sm text-neon-rose">
          Could not load event configuration: {err}
        </p>
      )}

      <section>
        <h2 className="h2 mb-1">The five rounds</h2>
        <p className="muted mb-5">
          Each solved challenge yields a code segment. Collect a round&apos;s segments and
          they assemble into the code that opens the next round.
        </p>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {TIERS.map((t) => (
            <article key={t.n} className="card">
              <div className="flex items-baseline justify-between">
                <span className="font-mono text-xs uppercase tracking-widest text-slate-500">
                  Round {t.n}
                </span>
                <span className={`font-mono text-sm font-bold ${t.tone}`}>{t.pts} pts</span>
              </div>
              <h3 className="mt-1 text-lg font-semibold text-white">{t.name}</h3>
              <p className="muted mt-1">{t.blurb}</p>
            </article>
          ))}
          <article className="card border-neon-cyan/40 bg-neon-cyan/5">
            <p className="label">Maximum score</p>
            <p className="font-mono text-3xl font-bold text-neon-cyan">
              {max.toLocaleString()}
            </p>
            <p className="muted mt-1">
              Mode: <span className="font-mono">{data?.scoring.mode ?? "…"}</span>
            </p>
          </article>
        </div>
      </section>

      <section>
        <h2 className="h2 mb-4">Event format</h2>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {[
            ["Mode", "Fully online"],
            ["Duration", "4 h 30 min"],
            ["Competition window", "3 h 45 min"],
            ["Team size", "2 – 4 members"],
            ["Rounds", "5 progressive"],
            ["Challenges", "15 total"],
            ["Eligibility", "All engineering branches"],
            ["Equipment", "Any web browser"],
          ].map(([k, v]) => (
            <div key={k} className="card">
              <p className="label">{k}</p>
              <p className="font-medium text-white">{v}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h2 className="h2 mb-4">Schedule</h2>
        <div className="card overflow-x-auto p-0">
          <table className="table">
            <thead>
              <tr><th>Time</th><th>Activity</th></tr>
            </thead>
            <tbody>
              {[
                ["10:00 – 10:20", "Registration and team verification"],
                ["10:20 – 10:35", "Welcome, rules and proctoring briefing"],
                ["10:35 – 10:45", "Platform demonstration"],
                ["10:45 – 11:00", "Round 1 opening and instructions"],
                ["11:00 – 2:30", "Rounds 1–4, organizer-controlled breaks"],
                ["2:30 – 2:45", "Final round: Debug Sprint"],
                ["2:45 – 2:55", "Final submissions and scoreboard freeze"],
                ["2:55 – 3:05", "Score verification"],
                ["3:05 – 3:20", "Winner announcement"],
                ["3:20 – 3:30", "Closing remarks"],
              ].map(([t, a]) => (
                <tr key={t}><td className="whitespace-nowrap font-mono text-neon-cyan">{t}</td><td>{a}</td></tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}