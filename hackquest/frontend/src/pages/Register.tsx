import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { post } from "../lib/api";
import { useSession } from "../App";

type Member = { name: string; email: string; branch: string; semester: string };

const emptyMember = (): Member => ({ name: "", email: "", branch: "", semester: "" });

export default function Register() {
  const nav = useNavigate();
  const { refresh } = useSession();
  const [members, setMembers] = useState<Member[]>([emptyMember(), emptyMember(), emptyMember()]);
  const [form, setForm] = useState({
    team_name: "",
    leader_name: "",
    leader_email: "",
    college: "",
    branch: "",
    semester: "",
    password: "",
    confirm: "",
  });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const filled = members.filter((m) => m.name.trim() && m.email.trim()).length;
  const size = 1 + filled;

  const set = (k: string, v: string) => setForm((f) => ({ ...f, [k]: v }));

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    if (form.password !== form.confirm) {
      setErr("Passwords do not match.");
      return;
    }
    if (size < 2) {
      setErr("Add at least one member — teams must have 2 to 4 people.");
      return;
    }
    setBusy(true);
    try {
      await post("/api/auth/register", {
        team_name: form.team_name,
        leader_name: form.leader_name,
        leader_email: form.leader_email,
        college: form.college,
        branch: form.branch,
        semester: form.semester,
        password: form.password,
        members: members
          .filter((m) => m.name.trim() && m.email.trim())
          .map(({ name, email, branch, semester }) => ({ name, email, branch, semester })),
      });
      await refresh();
      nav("/dashboard");
    } catch (e) {
      setErr((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="h1">Register your team</h1>
        <p className="muted mt-1">
          One account per team. The team leader manages membership. Teams of 2–4 members.
        </p>
      </div>

      {err && <p className="card border-neon-rose/40 text-sm text-neon-rose">{err}</p>}

      <form onSubmit={submit} className="space-y-6">
        <section className="card space-y-3">
          <h2 className="h2">Team</h2>
          <div>
            <label className="label" htmlFor="tn">Team name</label>
            <input id="tn" className="input" required value={form.team_name}
              onChange={(e) => set("team_name", e.target.value)} placeholder="e.g. Null Pointers" />
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div>
              <label className="label" htmlFor="col">College</label>
              <input id="col" className="input" value={form.college}
                onChange={(e) => set("college", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="br">Branch</label>
              <input id="br" className="input" value={form.branch}
                onChange={(e) => set("branch", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="sem">Semester</label>
              <input id="sem" className="input" value={form.semester}
                onChange={(e) => set("semester", e.target.value)} />
            </div>
          </div>
        </section>

        <section className="card space-y-3">
          <h2 className="h2">Team leader</h2>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="ln">Full name</label>
              <input id="ln" className="input" required value={form.leader_name}
                onChange={(e) => set("leader_name", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="le">Email</label>
              <input id="le" className="input" type="email" required value={form.leader_email}
                onChange={(e) => set("leader_email", e.target.value)} />
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label className="label" htmlFor="pw">Password</label>
              <input id="pw" className="input" type="password" required minLength={8}
                value={form.password} onChange={(e) => set("password", e.target.value)} />
            </div>
            <div>
              <label className="label" htmlFor="pw2">Confirm password</label>
              <input id="pw2" className="input" type="password" required minLength={8}
                value={form.confirm} onChange={(e) => set("confirm", e.target.value)} />
            </div>
          </div>
        </section>

        <section className="card space-y-3">
          <div className="flex items-baseline justify-between">
            <h2 className="h2">Members</h2>
            <span className={`pill ${size >= 2 && size <= 4 ? "bg-neon-lime/15 text-neon-lime" : "bg-neon-rose/15 text-neon-rose"}`}>
              {size} / 4
            </span>
          </div>
          <p className="muted">Add 1 to 3 additional members. Leave a row blank to skip it.</p>
          {members.map((m, i) => (
            <div key={i} className="grid gap-3 sm:grid-cols-2">
              <div>
                <label className="label" htmlFor={`mn${i}`}>Member {i + 1} name</label>
                <input id={`mn${i}`} className="input" value={m.name}
                  onChange={(e) => {
                    const next = [...members];
                    next[i] = { ...m, name: e.target.value };
                    setMembers(next);
                  }} />
              </div>
              <div>
                <label className="label" htmlFor={`me${i}`}>Email</label>
                <input id={`me${i}`} className="input" type="email" value={m.email}
                  onChange={(e) => {
                    const next = [...members];
                    next[i] = { ...m, email: e.target.value };
                    setMembers(next);
                  }} />
              </div>
            </div>
          ))}
        </section>

        <button className="btn-primary w-full" disabled={busy}>
          {busy ? "Creating team…" : "Create team"}
        </button>
        <p className="muted text-center">
          Already registered? <Link className="link" to="/login">Sign in</Link>
        </p>
      </form>
    </div>
  );
}