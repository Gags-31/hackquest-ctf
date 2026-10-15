import { useCallback, useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { get, post } from "../lib/api";
import { useProctoring } from "../lib/proctor";
import type { ChallengeView, RoundDetail, SubmitResult } from "../lib/types";

function ChallengeCard({
  ch,
  index,
  onSolved,
}: {
  ch: ChallengeView;
  index: number;
  onSolved: () => void;
}) {
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [hints, setHints] = useState<string[]>([]);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg(null);
    try {
      const res = await post<SubmitResult>("/api/submit", {
        challenge_key: ch.key,
        answer,
      });
      if (res.correct) {
        setMsg({
          ok: true,
          text: res.already_accepted
            ? "Already solved."
            : `Correct. +${res.points} points.`,
        });
        onSolved();
      } else {
        setMsg({ ok: false, text: "Not correct. Try again." });
      }
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function hint() {
    try {
      const res = await post<{ hint: string; hint_number: number; penalty: number }>(
        `/api/challenges/${ch.key}/hint`,
      );
      setHints((h) => [...h, res.hint]);
      if (res.penalty > 0) {
        setMsg({ ok: false, text: `Hint used: −${res.penalty} points.` });
      }
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    }
  }

  if (ch.solved) {
    return (
      <article className="card border-neon-lime/40 bg-neon-lime/5">
        <div className="flex items-center justify-between gap-3">
          <h3 className="font-semibold text-white">
            <span className="mr-2 text-neon-lime">✓</span>
            {index}. {ch.title}
          </h3>
          <span className="pill bg-neon-lime/15 text-neon-lime">solved</span>
        </div>
        <p className="muted mt-1">{ch.category} · {ch.difficulty} · {ch.points} pts</p>
        {ch.explanation && (
          <p className="mt-3 rounded-lg border border-ink-700 bg-ink-850 p-3 text-sm text-slate-300">
            <b className="text-neon-cyan">Explanation:</b> {ch.explanation}
          </p>
        )}
      </article>
    );
  }

  return (
    <article className="card">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-white">{index}. {ch.title}</h3>
        <span className="pill bg-ink-700 text-slate-300">{ch.points} pts</span>
      </div>
      <p className="muted mb-3">{ch.category} · {ch.difficulty}</p>
      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-200">
        {ch.description}
      </p>
      {ch.initial_clue && (
        <p className="mt-3 rounded-lg border-l-2 border-neon-violet bg-ink-850 p-2.5 text-xs text-slate-300">
          Clue: {ch.initial_clue}
        </p>
      )}
      {ch.answer_format && (
        <p className="mt-2 text-xs text-slate-500">Answer format: {ch.answer_format}</p>
      )}

      {hints.length > 0 && (
        <ol className="mt-3 space-y-1.5">
          {hints.map((h, i) => (
            <li key={i} className="rounded-lg bg-ink-850 p-2.5 text-xs text-neon-amber">
              <b>Hint {i + 1}:</b> {h}
            </li>
          ))}
        </ol>
      )}

      <form onSubmit={submit} className="mt-4 flex flex-wrap gap-2">
        <input
          className="input flex-1"
          value={answer}
          onChange={(e) => setAnswer(e.target.value)}
          placeholder="Your answer"
          aria-label={`Answer for ${ch.title}`}
        />
        <button className="btn-primary" disabled={busy}>
          {busy ? "Checking…" : "Submit"}
        </button>
        <button type="button" className="btn-ghost" onClick={hint} disabled={hints.length >= 3}>
          Hint ({3 - hints.length})
        </button>
      </form>
      {ch.hint_penalty > 0 && (
        <p className="mt-2 text-xs text-slate-500">Each hint costs {ch.hint_penalty} points.</p>
      )}
      {msg && (
        <p className={`mt-2 text-sm ${msg.ok ? "text-neon-lime" : "text-neon-rose"}`} role="status">
          {msg.text}
        </p>
      )}
    </article>
  );
}

export default function RoundPage() {
  const { slug } = useParams<{ slug: string }>();
  const [round, setRound] = useState<RoundDetail | null>(null);
  const [err, setErr] = useState<string | null>(null);
  const [left, setLeft] = useState<number | null>(null);

  const load = useCallback(() => {
    if (!slug) return;
    get<RoundDetail>(`/api/rounds/${slug}`)
      .then(setRound)
      .catch((e: Error) => setErr(e.message));
  }, [slug]);

  useEffect(load, [load]);

  const proctor = useProctoring(round?.state === "open");

  // Competition timer. The server is authoritative; this is display only.
  useEffect(() => {
    if (round?.state !== "open") return;
    const ms = 45 * 60 * 1000;
    const started = Date.now();
    setLeft(ms);
    const id = setInterval(() => {
      setLeft(Math.max(0, ms - (Date.now() - started)));
    }, 1000);
    return () => clearInterval(id);
  }, [round?.state]);

  if (err) {
    return (
      <div className="card border-neon-rose/40 text-center">
        <h1 className="text-xl font-bold text-neon-rose">Not available</h1>
        <p className="muted mt-2">{err}</p>
        <Link className="btn-ghost mt-4" to="/arena">Back to arena</Link>
      </div>
    );
  }
  if (!round) return <p className="muted">Loading round…</p>;

  if (round.state === "closed") {
    return (
      <div className="space-y-4">
        <h1 className="h1">Round {round.number} · {round.name}</h1>
        <p className="muted">This round is closed. Solutions are published below.</p>
        <div className="space-y-3">
          {round.challenges.map((c, i) => (
            <ChallengeCard key={c.key} ch={c} index={i + 1} onSolved={load} />
          ))}
        </div>
        {round.explanation && (
          <div className="card">
            <h2 className="h2 mb-2">Round notes</h2>
            <p className="whitespace-pre-wrap text-sm text-slate-300">{round.explanation}</p>
          </div>
        )}
      </div>
    );
  }

  const mm = left === null ? "--:--" : `${String(Math.floor(left / 60000)).padStart(2, "0")}:${String(Math.floor((left % 60000) / 1000)).padStart(2, "0")}`;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-mono text-xs uppercase tracking-widest text-slate-500">
            Round {round.number}
          </p>
          <h1 className="h1">{round.name}</h1>
          <p className="muted mt-1">{round.blurb}</p>
        </div>
        <div className="text-right">
          <p className="label">Time remaining</p>
          <p className={`font-mono text-2xl font-bold ${left !== null && left < 300000 ? "text-neon-rose" : "text-neon-cyan"}`}>
            {mm}
          </p>
          <p className="text-xs text-slate-500">{round.challenges_solved}/{round.challenges_total} solved</p>
        </div>
      </div>

      <div className={`card text-sm ${proctor.disqualified ? "border-neon-rose/50 text-neon-rose" : "text-slate-300"}`}>
        <p>
          Proctoring active — <b>{proctor.violations}/{proctor.limit}</b> violations.
          {!proctor.inFullscreen && (
            <button className="link ml-2" onClick={() => void proctor.requestFullscreen()}>
              Enter fullscreen
            </button>
          )}
        </p>
        {proctor.notice && <p className="mt-1 text-neon-rose">{proctor.notice}</p>}
      </div>

      <div className="space-y-3">
        {round.challenges.map((c, i) => (
          <ChallengeCard key={c.key} ch={c} index={i + 1} onSolved={load} />
        ))}
      </div>

      <Link className="btn-ghost" to="/arena">← Back to arena</Link>
    </div>
  );
}