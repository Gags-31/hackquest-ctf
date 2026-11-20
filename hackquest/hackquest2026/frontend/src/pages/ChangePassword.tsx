import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, errorText } from '../lib/api'

export default function ChangePassword() {
  const navigate = useNavigate()
  const [current_password, setCurrent] = useState('')
  const [new_password, setNew] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setError('')
    try {
      await api.post('/api/auth/change-password', { current_password, new_password })
      navigate('/admin')
      window.location.reload()
    } catch (err) { setError(errorText(err)) } finally { setBusy(false) }
  }

  return (
    <div className="mx-auto max-w-md px-5 py-16">
      <div className="glass violet-border rounded-xl p-6">
        <div className="font-mono text-xs uppercase tracking-[.3em] text-violet">// first login</div>
        <h1 className="mt-2 font-display text-2xl font-bold text-white">Change your temporary password</h1>
        <p className="mt-2 text-sm text-slate-400">Organisers must set a private password before controlling the event.</p>
        <form onSubmit={submit} className="mt-6 space-y-4">
          <div>
            <label className="label">Temporary password</label>
            <input className="input" type="password" value={current_password}
                   onChange={(e) => setCurrent(e.target.value)} required />
          </div>
          <div>
            <label className="label">New password (min 10 characters)</label>
            <input className="input" type="password" value={new_password}
                   onChange={(e) => setNew(e.target.value)} minLength={10} required />
          </div>
          {error && <div className="font-mono text-xs text-rose-300">{error}</div>}
          <button className="btn btn-primary w-full" disabled={busy}>SET PASSWORD →</button>
        </form>
      </div>
    </div>
  )
}
