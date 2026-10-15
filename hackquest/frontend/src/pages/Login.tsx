import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { post } from "../lib/api";
import { useSession } from "../App";

export default function Login() {
  const nav = useNavigate();
  const loc = useLocation();
  const { refresh } = useSession();
  const [identity, setIdentity] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [recovery, setRecovery] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      const res = await post<{ role: string; must_change_password?: boolean }>(
        "/api/auth/login",
        { identity, password },
      );
      await refresh();
      const from = (loc.state as { from?: string } | null)?.from;
      if (res.must_change_password) nav("/profile?change=1");
      else if (from) nav(from);
      else if (res.role === "organizer") nav("/admin");
      else nav("/dashboard");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  async function recover() {
    const email = window.prompt("Leader email address");
    if (!email) return;
    try {
      const res = await post<{ message: string }>("/api/auth/request-recovery", { email });
      setRecovery(res.message);
    } catch (e) {
      setErr((e as Error).message);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-5">
      <div className="text-center">
        <h1 className="h1">Sign in</h1>
        <p className="muted mt-1">Teams and organizers use the same form.</p>
      </div>

      {err && <p className="card border-neon-rose/40 text-sm text-neon-rose">{err}</p>}
      {recovery && <p className="card border-neon-lime/40 text-sm text-neon-lime">{recovery}</p>}

      <form onSubmit={submit} className="card space-y-3">
        <div>
          <label className="label" htmlFor="id">Team name, code or email</label>
          <input id="id" className="input" required value={identity}
            onChange={(e) => setIdentity(e.target.value)} autoComplete="username" />
        </div>
        <div>
          <label className="label" htmlFor="pw">Password</label>
          <input id="pw" className="input" type="password" required value={password}
            onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
        </div>
        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <div className="flex justify-between text-sm">
        <button className="link" onClick={recover} type="button">Forgot password?</button>
        <Link className="link" to="/register">Create a team</Link>
      </div>
    </div>
  );
}