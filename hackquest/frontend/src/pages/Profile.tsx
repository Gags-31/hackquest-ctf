import { useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { post } from "../lib/api";
import { useSession } from "../App";

export default function Profile() {
  const { me, refresh } = useSession();
  const nav = useNavigate();
  const [params] = useSearchParams();
  const [cur, setCur] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  if (!me.authenticated) {
    return (
      <div className="card text-center">
        <p>You are not signed in.</p>
        <Link className="btn-primary mt-4" to="/login">Sign in</Link>
      </div>
    );
  }

  async function changePassword(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);
    if (next !== confirm) {
      setMsg({ ok: false, text: "New passwords do not match." });
      return;
    }
    setBusy(true);
    try {
      await post("/api/auth/change-password", {
        current_password: cur,
        new_password: next,
      });
      setMsg({ ok: true, text: "Password updated. Your session was rotated." });
      setCur(""); setNext(""); setConfirm("");
      await refresh();
    } catch (e) {
      setMsg({ ok: false, text: (e as Error).message });
    } finally {
      setBusy(false);
    }
  }

  async function logout() {
    await post("/api/auth/logout");
    await refresh();
    nav("/");
  }

  const mustChange = me.must_change_password || params.get("change") === "1";

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="h1">Profile</h1>
        <p className="muted mt-1">
          {me.role === "team" ? "Team account" : "Organizer account"}
        </p>
      </div>

      {mustChange && (
        <p className="card border-neon-amber/50 text-neon-amber">
          A password change is required before you can continue.
        </p>
      )}

      <section className="card">
        <h2 className="h2 mb-3">Details</h2>
        {me.role === "team" ? (
          <dl className="grid gap-3 sm:grid-cols-2">
            <div><dt className="label">Team</dt><dd className="text-white">{me.team_name}</dd></div>
            <div><dt className="label">Team code</dt><dd className="font-mono text-neon-cyan">{me.team_code}</dd></div>
            <div><dt className="label">Status</dt><dd className="text-white">{me.status}</dd></div>
            <div>
              <dt className="label">Email verified</dt>
              <dd className="text-white">{me.email_verified ? "Yes" : "Pending"}</dd>
            </div>
          </dl>
        ) : (
          <dl className="grid gap-3 sm:grid-cols-2">
            <div><dt className="label">Username</dt><dd className="font-mono text-neon-cyan">{me.username}</dd></div>
            <div><dt className="label">Role</dt><dd className="text-white">{me.admin_role}</dd></div>
            <div><dt className="label">Name</dt><dd className="text-white">{me.full_name}</dd></div>
            <div><dt className="label">Email</dt><dd className="text-white">{me.email}</dd></div>
          </dl>
        )}

        {me.members && me.members.length > 0 && (
          <div className="mt-4">
            <p className="label">Members</p>
            <ul className="space-y-1">
              {me.members.map((m) => (
                <li key={m.email} className="flex items-center justify-between text-sm">
                  <span className="text-slate-300">{m.name}</span>
                  <span className="text-slate-500">{m.email}</span>
                </li>
              ))}
            </ul>
            <p className="muted mt-2">
              Team membership is fixed during the competition. Contact an organizer to request a change.
            </p>
          </div>
        )}
      </section>

      <section className="card">
        <h2 className="h2 mb-3">Change password</h2>
        {msg && (
          <p className={`mb-3 text-sm ${msg.ok ? "text-neon-lime" : "text-neon-rose"}`} role="status">
            {msg.text}
          </p>
        )}
        <form onSubmit={changePassword} className="space-y-3">
          <div>
            <label className="label" htmlFor="cur">Current password</label>
            <input id="cur" className="input" type="password" required value={cur}
              onChange={(e) => setCur(e.target.value)} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="np">New password</label>
              <input id="np" className="input" type="password" required minLength={12} value={next}
                onChange={(e) => setNext(e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="np2">Confirm new password</label>
              <input id="np2" className="input" type="password" required minLength={12} value={confirm}
                onChange={(e) => setConfirm(e.target.value)} />
            </div>
          </div>
          <button className="btn-primary" disabled={busy}>Update password</button>
        </form>
      </section>

      <button className="btn-ghost" onClick={logout}>Sign out</button>
    </div>
  );
}