import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorText } from '../lib/api'
import { Badge } from '../components/Ui'
import { OrganiserMark } from '../components/Brand'

type Member = { name: string; email: string; mobile: string }

const blank = (): Member => ({ name: '', email: '', mobile: '' })

export default function Register() {
  const navigate = useNavigate()
  const [form, setForm] = useState({
    team_name: '', college: '', department: '', semester: '',
    leader_name: '', leader_email: '', leader_mobile: '', password: '',
  })
  const [members, setMembers] = useState<Member[]>([blank(), blank()])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState<string | null>(null)

  const set = (key: string, value: string) => setForm((f) => ({ ...f, [key]: value }))
  const setMember = (i: number, key: keyof Member, value: string) =>
    setMembers((list) => list.map((m, idx) => idx === i ? { ...m, [key]: value } : m))

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setError(''); setBusy(true)
    try {
      const res = await api.post<any>('/api/auth/register', {
        ...form,
        members: members.slice(0, 1 + Math.max(1, members.length - 1)),
      })
      setDone(res.team_name)
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }

  if (done) return (
    <div className="mx-auto max-w-xl px-5 py-20">
      <div className="glass neon-border rounded-2xl p-8 text-center">
        <div className="font-mono text-5xl text-neon">✓</div>
        <h1 className="mt-4 font-display text-2xl font-bold text-white">Registration received</h1>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Team <span className="font-mono text-neon">{done}</span> is pending organiser approval.
          Once approved, log in to view your unique access code and enter the lobby.
        </p>
        <Link to="/login" className="btn btn-primary mt-6">GO TO TEAM LOGIN</Link>
      </div>
    </div>
  )

  return (
    <div className="mx-auto max-w-5xl px-5 py-12">
      <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-xs uppercase tracking-[.3em] text-neon">// enrollment</div>
          <h1 className="mt-2 font-display text-3xl font-bold text-white md:text-4xl">Register your team</h1>
          <p className="mt-2 text-sm text-slate-400">2–4 participants. Unique emails. Approval required.</p>
        </div>
        <div className="flex flex-wrap gap-4"><OrganiserMark kind="pragyan" /><OrganiserMark kind="ieee" /></div>
      </div>

      <form onSubmit={submit} className="space-y-6">
        <section className="glass rounded-xl p-6">
          <h2 className="mb-5 font-display text-lg font-bold text-white">01 / TEAM DETAILS</h2>
          <div className="grid gap-4 md:grid-cols-2">
            {[
              ['team_name', 'Team name'], ['college', 'College name'],
              ['department', 'Department'], ['semester', 'Semester'],
            ].map(([key, label]) => (
              <div key={key}>
                <label className="label">{label}</label>
                <input className="input" value={(form as any)[key]}
                       onChange={(e) => set(key, e.target.value)} required />
              </div>
            ))}
          </div>
        </section>

        <section className="glass rounded-xl p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-display text-lg font-bold text-white">02 / TEAM LEADER (MEMBER 1)</h2>
            <Badge tone="green">REQUIRED</Badge>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="label">Full name</label>
              <input className="input" value={form.leader_name} onChange={(e) => set('leader_name', e.target.value)} required />
            </div>
            <div>
              <label className="label">Email</label>
              <input className="input" type="email" value={form.leader_email} onChange={(e) => set('leader_email', e.target.value)} required />
            </div>
            <div>
              <label className="label">Mobile</label>
              <input className="input" value={form.leader_mobile} onChange={(e) => set('leader_mobile', e.target.value)} required />
            </div>
          </div>
        </section>

        <section className="glass rounded-xl p-6">
          <div className="mb-5 flex items-center justify-between">
            <h2 className="font-display text-lg font-bold text-white">03 / OTHER MEMBERS</h2>
            <Badge tone="cyan">{members.length + 1} / 4 PARTICIPANTS</Badge>
          </div>
          <div className="space-y-5">
            {members.map((m, i) => (
              <div key={i} className="rounded-lg border border-slate-800 p-4">
                <div className="mb-3 font-mono text-[11px] uppercase tracking-[.2em] text-cyan">
                  MEMBER {i + 2} {i === 0 ? '(REQUIRED)' : '(OPTIONAL)'}
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <input className="input" placeholder="Full name" value={m.name}
                         onChange={(e) => setMember(i, 'name', e.target.value)} required />
                  <input className="input" type="email" placeholder="Email" value={m.email}
                         onChange={(e) => setMember(i, 'email', e.target.value)} required />
                  <input className="input" placeholder="Mobile" value={m.mobile}
                         onChange={(e) => setMember(i, 'mobile', e.target.value)} required />
                </div>
              </div>
            ))}
          </div>
          {members.length < 3 && (
            <button type="button" className="btn btn-ghost mt-4"
                    onClick={() => setMembers((l) => [...l, blank()])}>
              + ADD MEMBER {members.length + 2}
            </button>
          )}
          {members.length > 1 && (
            <button type="button" className="ml-3 mt-4 font-mono text-xs text-rose-400"
                    onClick={() => setMembers((l) => l.slice(0, -1))}>
              REMOVE LAST
            </button>
          )}
        </section>

        <section className="glass rounded-xl p-6">
          <h2 className="mb-5 font-display text-lg font-bold text-white">04 / TEAM ACCOUNT</h2>
          <div className="max-w-md">
            <label className="label">Team password (min 8 characters)</label>
            <input className="input" type="password" value={form.password}
                   onChange={(e) => set('password', e.target.value)} minLength={8} required />
            <p className="mt-2 font-mono text-[11px] leading-relaxed text-slate-500">
              All members share these credentials. The team access code is generated after approval
              and never replaces this password.
            </p>
          </div>
        </section>

        {error && <div className="rounded-lg border border-rose-500/50 bg-rose-500/10 px-4 py-3 font-mono text-sm text-rose-300">{error}</div>}
        <button className="btn btn-primary w-full" disabled={busy}>
          {busy ? 'SUBMITTING…' : 'SUBMIT REGISTRATION →'}
        </button>
      </form>
    </div>
  )
}
