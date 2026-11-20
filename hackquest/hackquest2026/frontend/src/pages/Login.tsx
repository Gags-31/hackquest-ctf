import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { api, errorText } from '../lib/api'
import { OrganiserMark } from '../components/Brand'

export default function Login() {
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      const res = await api.post<any>('/api/auth/login', { username, password })
      if (res.must_change_password) {
        navigate('/change-password')
      } else {
        navigate(res.role === 'organizer' ? '/admin' : '/dashboard')
        window.location.reload()
      }
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }

  return (
    <div className="mx-auto flex max-w-md flex-col px-5 py-16">
      <div className="mb-8 text-center">
        <div className="font-mono text-xs uppercase tracking-[.3em] text-neon">// authentication</div>
        <h1 className="mt-2 font-display text-3xl font-bold text-white">Secure access</h1>
        <p className="mt-2 text-sm text-slate-400">Team login or organiser console</p>
      </div>
      <form onSubmit={submit} className="glass neon-border space-y-5 rounded-xl p-6">
        <div>
          <label className="label">Team name / organiser username</label>
          <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} required autoFocus />
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        {error && <div className="rounded border border-rose-500/50 bg-rose-500/10 px-3 py-2 font-mono text-xs text-rose-300">{error}</div>}
        <button className="btn btn-primary w-full" disabled={busy}>{busy ? 'AUTHENTICATING…' : 'AUTHENTICATE →'}</button>
      </form>
      <div className="mt-6 flex flex-wrap items-center justify-center gap-5">
        <OrganiserMark kind="pragyan" />
        <OrganiserMark kind="ieee" />
      </div>
      <p className="mt-6 text-center text-sm text-slate-400">
        No account yet? <Link to="/register" className="font-mono text-neon hover:underline">Register your team</Link>
      </p>
    </div>
  )
}
