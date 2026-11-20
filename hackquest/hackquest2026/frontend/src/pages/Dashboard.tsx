import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, errorText } from '../lib/api'
import { Badge, Empty, Stat, Timer } from '../components/Ui'
import { OrganiserMark } from '../components/Brand'
import type { Challenge, Team, TeamState } from '../lib/types'

export default function Dashboard() {
  const [me, setMe] = useState<any>(null)
  const [state, setState] = useState<TeamState | null>(null)
  const [challenges, setChallenges] = useState<Challenge[]>([])
  const [detail, setDetail] = useState<any>(null)
  const [flag, setFlag] = useState('')
  const [roundFilter, setRoundFilter] = useState<number | 'all'>('all')
  const [notice, setNotice] = useState<{ ok: boolean; text: string } | null>(null)
  const [error, setError] = useState('')

  const refresh = useCallback(async () => {
    try {
      const [m, s, c] = await Promise.all([
        api.get<any>('/api/team/me'),
        api.get<TeamState>('/api/team/state'),
        api.get<{ challenges: Challenge[] }>('/api/team/challenges'),
      ])
      setMe(m); setState(s); setChallenges(c.challenges)
    } catch (e) { setError(errorText(e)) }
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(() => {
      api.get<TeamState>('/api/team/state').then(setState).catch(() => {})
    }, 3000)
    return () => clearInterval(id)
  }, [refresh])

  if (error && !me) return (
    <div className="mx-auto max-w-xl px-5 py-20">
      <div className="glass rounded-xl p-8 text-center">
        <p className="font-mono text-sm text-rose-300">{error}</p>
        <Link to="/login" className="btn btn-primary mt-5">BACK TO LOGIN</Link>
      </div>
    </div>
  )
  if (!me || !state) return <div className="p-10 text-center font-mono text-sm text-slate-400">SYNCING TEAM STATE…</div>

  const team: Team = me.team
  const current = state.rounds.find((r) => r.state === 'open') ||
    state.rounds.find((r) => r.state === 'paused')
  const shown = challenges.filter((c) => roundFilter === 'all' || c.round === roundFilter)

  async function openChallenge(slug: string) {
    try {
      setDetail(await api.get('/api/team/challenge/' + slug))
      setFlag(''); setNotice(null)
    } catch (e) { setNotice({ ok: false, text: errorText(e) }) }
  }

  async function revealHint(index: number) {
    if (!detail) return
    await api.post('/api/team/hint/' + detail.slug + '/' + index)
    setDetail((d: any) => ({
      ...d,
      hints: d.hints.map((h: any) => h.index === index ? { ...h, used: true } : h),
    }))
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    if (!detail) return
    try {
      const res = await api.post<any>('/api/team/submit', { flag }, { 'x-challenge': detail.slug })
      setNotice({ ok: res.correct, text: res.message })
      if (res.correct) {
        setDetail((d: any) => ({ ...d, solved: true }))
        setTimeout(() => setDetail(null), 1400)
      }
      refresh()
    } catch (err) { setNotice({ ok: false, text: errorText(err) }) }
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-10">
      {notice && (
        <div className={`fixed right-5 top-20 z-[60] max-w-sm rounded-lg border px-5 py-4 font-mono text-sm shadow-2xl ${
          notice.ok ? 'border-neon/60 bg-emerald-950 text-neon' : 'border-rose-500/60 bg-rose-950 text-rose-200'
        }`}>
          {notice.ok ? '✓ ' : '✕ '}{notice.text}
        </div>
      )}

      {/* TEAM HEADER */}
      <div className="glass neon-border mb-6 rounded-xl p-5">
        <div className="flex flex-wrap items-start justify-between gap-5">
          <div>
            <div className="font-mono text-[10px] uppercase tracking-[.3em] text-neon">// participant arena</div>
            <h1 className="mt-1 font-display text-2xl font-bold text-white">Welcome, {team.name}</h1>
            <p className="mt-1 text-sm text-slate-400">{team.college} · {team.department} · Sem {team.semester}</p>
          </div>
          <div className="text-right">
            <div className="font-mono text-[10px] uppercase tracking-[.2em] text-slate-500">UNIQUE ACCESS CODE</div>
            <div className="mt-1 rounded border border-neon/40 bg-neon/5 px-4 py-2 font-mono text-xl font-extrabold tracking-[.2em] text-neon">
              {team.code_active ? team.code : 'REVOKED'}
            </div>
            <div className="mt-1 font-mono text-[10px] text-slate-500">TEAM ID #{team.id}</div>
          </div>
        </div>
        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          <Stat label="SCORE" value={me.score_visible ? me.score : 'HIDDEN'} />
          <Stat label="SOLVED" value={`${me.solved}/${me.total}`} accent="cyan" />
          <Stat label="STATUS" value={team.status.toUpperCase()} accent="violet" />
          <div className="glass rounded-xl p-5">
            <div className="font-mono text-[10px] uppercase tracking-[.2em] text-slate-400">CURRENT ROUND TIMER</div>
            <div className="mt-1">{current ? <Timer seconds={current.remaining_seconds} /> : <span className="font-mono text-lg text-slate-500">WAITING</span>}</div>
            <div className="font-mono text-[10px] text-slate-500">{current ? current.name : 'Awaiting organiser'}</div>
          </div>
        </div>
        <div className="mt-5 flex flex-wrap gap-2">
          {team.members.map((m: any, i: number) => (
            <span key={i} className="tag border-slate-600/60 text-slate-300">
              {m.name}{m.is_leader ? ' ★' : ''} · {m.email}
            </span>
          ))}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div>
          {/* ROUND STATUS */}
          <div className="glass mb-5 rounded-xl p-4">
            <div className="mb-3 font-mono text-[10px] uppercase tracking-[.25em] text-slate-400">// round control (server authoritative)</div>
            <div className="grid gap-2 sm:grid-cols-4">
              {state.rounds.map((r) => (
                <div key={r.number} className={`rounded-lg border px-3 py-2 ${
                  r.state === 'open' ? 'border-neon/50 bg-neon/5' : r.state === 'paused' ? 'border-amber-500/50 bg-amber-500/5' : 'border-slate-800'
                }`}>
                  <div className="font-mono text-[10px] text-slate-500">R{r.number}</div>
                  <div className="truncate font-display text-xs font-bold text-white">{r.name}</div>
                  <div className="mt-1 flex items-center justify-between font-mono text-[10px]">
                    <span className={r.state === 'open' ? 'text-neon' : r.state === 'paused' ? 'text-amber-300' : 'text-slate-500'}>
                      {r.state.toUpperCase()}
                    </span>
                    <Timer seconds={r.remaining_seconds} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* CHALLENGES */}
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
            <h2 className="font-display text-xl font-bold text-white">Challenge bank</h2>
            <div className="flex flex-wrap gap-2">
              {(['all', 1, 2, 3, 4] as const).map((n) => (
                <button key={n} onClick={() => setRoundFilter(n)}
                        className={`rounded border px-3 py-1 font-mono text-[10px] uppercase tracking-wider ${
                          roundFilter === n ? 'border-neon/60 bg-neon/10 text-neon' : 'border-slate-700 text-slate-400'
                        }`}>
                  {n === 'all' ? 'ALL' : 'R' + n}
                </button>
              ))}
            </div>
          </div>

          {shown.length === 0 ? <Empty text="No challenges in this view." /> : (
            <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
              {shown.map((c) => {
                const solved = state.solved.includes(
                  challenges.findIndex((x) => x.slug === c.slug) >= 0
                    ? (c as any).id ?? -1 : -1
                )
                const isSolved = me.solved > 0 && c.status === 'solved'
                return (
                  <button key={c.slug} onClick={() => openChallenge(c.slug)}
                          className={`glass rounded-xl p-4 text-left transition hover:-translate-y-0.5 ${
                            isSolved ? 'neon-border' : c.status === 'locked' ? 'opacity-60' : 'hover:border-cyan/50'
                          }`}>
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-[10px] text-cyan">R{c.round} · {c.category.toUpperCase()}</span>
                      {isSolved && <span className="text-neon">✓</span>}
                    </div>
                    <div className="mt-2 font-display text-sm font-bold leading-snug text-white">{c.title}</div>
                    <div className="mt-3 flex items-center justify-between font-mono text-[10px]">
                      <Badge tone={c.difficulty === 'Hard' ? 'violet' : c.difficulty === 'Medium' ? 'cyan' : 'green'}>
                        {c.difficulty}
                      </Badge>
                      <span className="text-slate-400">{c.points} pts</span>
                    </div>
                    <div className="mt-2 font-mono text-[10px] uppercase tracking-wider text-slate-500">
                      {c.status}{c.attachment_name ? ' · 📎' : ''}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>

        {/* SIDEBAR */}
        <div className="space-y-5">
          <div className="glass rounded-xl p-5">
            <div className="font-mono text-[10px] uppercase tracking-[.25em] text-neon">// announcements</div>
            <div className="mt-3 space-y-4">
              {me.announcements?.length ? me.announcements.map((a: any, i: number) => (
                <div key={i}>
                  <div className="font-display text-sm font-semibold text-white">{a.title}</div>
                  <p className="mt-1 text-xs leading-relaxed text-slate-400">{a.body}</p>
                </div>
              )) : <p className="font-mono text-xs text-slate-500">No announcements.</p>}
            </div>
          </div>
          <div className="glass rounded-xl p-5">
            <div className="font-mono text-[10px] uppercase tracking-[.25em] text-cyan">// breaks</div>
            <p className="mt-3 text-xs leading-relaxed text-slate-400">
              Cyber riddles and meme breaks run after every round. They are not part of official scoring.
            </p>
            <Link to="/break/1" className="btn btn-ghost mt-4 w-full">OPEN BREAK ROOM</Link>
          </div>
          <div className="glass rounded-xl p-5">
            <div className="font-mono text-[10px] uppercase tracking-[.25em] text-violet">// branding</div>
            <div className="mt-3 flex flex-col gap-3">
              <OrganiserMark kind="pragyan" />
              <OrganiserMark kind="ieee" />
            </div>
          </div>
        </div>
      </div>

      {/* CHALLENGE MODAL */}
      {detail && (
        <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/80 p-4 py-10 backdrop-blur-sm"
             onClick={() => setDetail(null)}>
          <div className="glass neon-border w-full max-w-2xl rounded-2xl p-6"
               onClick={(e) => e.stopPropagation()}>
            <div className="flex items-start justify-between gap-4">
              <div>
                <div className="font-mono text-[10px] uppercase tracking-[.25em] text-cyan">
                  R{detail.round} · {detail.category} · {detail.points} PTS
                </div>
                <h3 className="mt-1 font-display text-xl font-bold text-white">{detail.title}</h3>
              </div>
              <button onClick={() => setDetail(null)} className="font-mono text-xl text-slate-400 hover:text-white">×</button>
            </div>
            <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-slate-300">{detail.description}</p>
            {detail.attachment_name && (
              <a className="btn btn-ghost mt-4" href={'/api/public/attachments/' + detail.slug}>
                ↓ DOWNLOAD {detail.attachment_name}
              </a>
            )}
            <div className="mt-5 space-y-2">
              {detail.hints?.map((h: any) => (
                <div key={h.index} className="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-[10px] uppercase tracking-[.2em] text-violet">HINT {h.index}</span>
                    {!h.used && <button onClick={() => revealHint(h.index)} className="font-mono text-[10px] text-neon hover:underline">REVEAL</button>}
                  </div>
                  <p className={`mt-2 text-sm ${h.used ? 'text-slate-300' : 'select-none text-slate-600 blur-sm'}`}>
                    {h.used ? h.text : '••••••••••••••••••••'}
                  </p>
                </div>
              ))}
            </div>
            <form onSubmit={submit} className="mt-6">
              <label className="label">Submit flag · format {detail.flag_format}</label>
              <div className="flex flex-col gap-2 sm:flex-row">
                <input className="input font-mono" placeholder="HQCTF{...}" value={flag}
                       onChange={(e) => setFlag(e.target.value)} required />
                <button className="btn btn-primary shrink-0" disabled={detail.solved}>
                  {detail.solved ? 'SOLVED ✓' : 'SUBMIT'}
                </button>
              </div>
            </form>
            {notice && <p className={`mt-3 font-mono text-xs ${notice.ok ? 'text-neon' : 'text-rose-300'}`}>{notice.text}</p>}
          </div>
        </div>
      )}
    </div>
  )
}
