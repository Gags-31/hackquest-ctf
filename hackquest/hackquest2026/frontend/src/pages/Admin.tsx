import { useCallback, useEffect, useState } from 'react'
import { api, errorText } from '../lib/api'
import { Badge, Empty, Stat, Timer } from '../components/Ui'
import type { AdminChallenge, ScoreRow } from '../lib/types'

type Tab = 'overview' | 'teams' | 'challenges' | 'rounds' | 'scoreboard' |
  'submissions' | 'breaks' | 'comms' | 'settings' | 'audit'
const tabs: Tab[] = ['overview', 'teams', 'challenges', 'rounds', 'scoreboard',
  'submissions', 'breaks', 'comms', 'settings', 'audit']

export default function Admin() {
  const [tab, setTab] = useState<Tab>('overview')
  const [data, setData] = useState<any>({})
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [draft, setDraft] = useState<AdminChallenge | null>(null)
  const [search, setSearch] = useState('')
  const [settingsDraft, setSettingsDraft] = useState<any>(null)

  const load = useCallback(async () => {
    try {
      const paths: Record<Tab, string> = {
        overview: '/api/admin/overview', teams: '/api/admin/teams',
        challenges: '/api/admin/challenges', rounds: '/api/admin/rounds',
        scoreboard: '/api/admin/scoreboard', submissions: '/api/admin/submissions',
        breaks: '/api/admin/riddles', comms: '/api/admin/announcements',
        settings: '/api/admin/settings', audit: '/api/admin/audit',
      }
      const res = await api.get<any>(paths[tab])
      setData(res.rows || res)
      if (tab === 'breaks') {
        const memes = await api.get<any>('/api/admin/memes')
        setData((d: any) => ({ ...d, memes }))
      }
      if (tab === 'settings') setSettingsDraft(res)
    } catch (e) { setError(errorText(e)) }
  }, [tab])

  useEffect(() => { load(); setError('') }, [load])

  async function act(path: string, body?: any) {
    setNotice(''); setError('')
    try {
      const res = await api.post<any>(path, body)
      setNotice(res?.temporary_password
        ? `Temporary password: ${res.temporary_password}`
        : 'Action completed.')
      await load()
    } catch (e) { setError(errorText(e)) }
  }

  async function saveChallenge() {
    if (!draft) return
    try {
      if (draft.id) await api.put('/api/admin/challenges/' + draft.id, draft)
      else await api.post('/api/admin/challenges', draft)
      setDraft(null); setNotice('Challenge saved.'); await load()
    } catch (e) { setError(errorText(e)) }
  }

  async function saveSettings() {
    try {
      await api.put('/api/admin/settings', settingsDraft)
      setNotice('Settings saved.'); await load()
    } catch (e) { setError(errorText(e)) }
  }

  const h = (p: string, b?: any) => () => act(p, b)
  async function remove(path: string) {
    try { await api.del(path); setNotice('Deleted.'); await load() }
    catch (e) { setError(errorText(e)) }
  }

  return (
    <div className="mx-auto max-w-7xl px-5 py-10">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-xs uppercase tracking-[.3em] text-neon">// organiser command centre</div>
          <h1 className="mt-1 font-display text-3xl font-bold text-white">HackQuest Control</h1>
          <p className="mt-1 text-sm text-slate-400">Two independent organiser accounts · full event authority</p>
        </div>
        <div className="flex gap-2">
          <a className="btn btn-ghost" href="/api/admin/scoreboard.csv">↓ CSV</a>
          <a className="btn btn-ghost" href="/api/admin/scoreboard.pdf">↓ PDF</a>
        </div>
      </div>

      {(error || notice) && (
        <div className={`mb-5 rounded-lg border px-4 py-3 font-mono text-xs ${
          error ? 'border-rose-500/50 bg-rose-500/10 text-rose-200' : 'border-neon/50 bg-neon/5 text-neon'
        }`}>{error || notice}</div>
      )}

      <div className="mb-6 flex flex-wrap gap-2">
        {tabs.map((t) => (
          <button key={t} onClick={() => setTab(t)}
                  className={`rounded border px-3 py-2 font-mono text-[10px] uppercase tracking-[.16em] ${
                    tab === t ? 'border-neon/60 bg-neon/10 text-neon' : 'border-slate-700 text-slate-400 hover:text-white'
                  }`}>{t}</button>
        ))}
      </div>

      {/* OVERVIEW */}
      {tab === 'overview' && (
        <div className="space-y-5">
          <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
            {Object.entries(data || {}).map(([k, v]) => (
              <Stat key={k} label={k.replace(/_/g, ' ')} value={String(v)} accent={k.includes('correct') ? 'green' : k.includes('pending') ? 'violet' : 'cyan'} />
            ))}
          </div>
          <div className="glass rounded-xl p-5">
            <h2 className="font-display text-lg font-bold text-white">Quick actions</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              <button className="btn btn-primary" onClick={h('/api/admin/results/publish')}>PUBLISH RESULTS</button>
              <button className="btn btn-ghost" onClick={() => setTab('rounds')}>ROUND CONTROL</button>
              <button className="btn btn-ghost" onClick={() => setTab('teams')}>APPROVE TEAMS</button>
            </div>
          </div>
        </div>
      )}

      {/* TEAMS */}
      {tab === 'teams' && (
        <div className="space-y-3">
          {(data || []).map((t: any) => (
            <div key={t.id} className="glass rounded-xl p-5">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <div className="font-display text-lg font-bold text-white">{t.name}</div>
                  <div className="font-mono text-xs text-slate-400">
                    {t.college} · {t.department} · Sem {t.semester}
                  </div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {t.members.map((m: any, i: number) => (
                      <span key={i} className="tag border-slate-600/50 text-slate-300">
                        {m.name}{m.is_leader ? ' ★' : ''} · {m.email} · {m.mobile}
                      </span>
                    ))}
                  </div>
                </div>
                <div className="text-right">
                  <Badge tone={t.status === 'approved' ? 'green' : t.status === 'pending' ? 'amber' : 'violet'}>{t.status}</Badge>
                  <div className="mt-2 font-mono text-sm text-neon">{t.code}</div>
                  <div className="font-mono text-xs text-slate-500">{t.score} pts</div>
                </div>
              </div>
              <div className="mt-4 flex flex-wrap gap-2">
                {t.status !== 'approved' && <button className="btn btn-primary" onClick={h(`/api/admin/teams/${t.id}/approve`)}>APPROVE</button>}
                {t.status !== 'rejected' && <button className="btn btn-ghost" onClick={h(`/api/admin/teams/${t.id}/reject`)}>REJECT</button>}
                <button className="btn btn-ghost" onClick={h(`/api/admin/teams/${t.id}/code/regenerate`)}>REGENERATE CODE</button>
                <button className="btn btn-ghost" onClick={h(`/api/admin/teams/${t.id}/code/revoke`)}>REVOKE CODE</button>
                <button className="font-mono text-xs text-rose-400" onClick={() => remove(`/api/admin/teams/${t.id}`)}>DELETE</button>
              </div>
            </div>
          ))}
          {!data?.length && <Empty text="No registrations yet." />}
        </div>
      )}

      {/* CHALLENGES — answers and solutions visible only here */}
      {tab === 'challenges' && (
        <div>
          <div className="mb-4 flex justify-between">
            <p className="font-mono text-xs text-violet">Flags and solutions are organiser-only. Never exposed to participants.</p>
            <button className="btn btn-primary" onClick={() => setDraft({
              id: 0, slug: '', round: 1, round_number: 1, title: '', description: '', category: '',
              difficulty: 'Medium', points: 100, flag: 'HQCTF{...}', flag_format: 'HQCTF{...}',
              hint1: '', hint2: '', solution: '', concept: '', enabled: true,
              order: 0, status: '', hint_count: 2, attachment_name: null,
              attachment_text: null, prerequisite: null, flag_case_sensitive: true,
            } as AdminChallenge)}>+ NEW CHALLENGE</button>
          </div>
          <div className="space-y-3">
            {(data || []).map((c: AdminChallenge) => (
              <div key={c.id} className="glass rounded-xl p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <div className="font-mono text-[10px] text-cyan">R{c.round} · {c.category} · {c.points} pts</div>
                    <div className="font-display font-bold text-white">{c.title} <span className="font-mono text-xs text-slate-500">[{c.slug}]</span></div>
                    <div className="mt-2 font-mono text-xs text-neon">FLAG: {c.flag}</div>
                    <div className="mt-1 text-xs text-slate-400">SOLUTION: {c.solution}</div>
                    <div className="mt-1 text-xs text-slate-500">CONCEPT: {c.concept}</div>
                    <div className="mt-1 text-xs text-slate-400">H1: {c.hint1} · H2: {c.hint2}</div>
                  </div>
                  <div className="flex gap-2">
                    <button className="btn btn-ghost" onClick={() => setDraft({ ...c })}>EDIT</button>
                    <button className="btn btn-ghost" onClick={h(`/api/admin/challenges/${c.id}/duplicate`)}>DUPLICATE</button>
                    <button className="font-mono text-xs text-rose-400" onClick={() => remove(`/api/admin/challenges/${c.id}`)}>DELETE</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* CHALLENGE EDITOR */}
      {draft && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/80 p-5 backdrop-blur" onClick={() => setDraft(null)}>
          <div className="glass violet-border mx-auto max-w-3xl rounded-xl p-6" onClick={(e) => e.stopPropagation()}>
            <div className="mb-4 flex justify-between">
              <h2 className="font-display text-lg font-bold text-white">Challenge editor</h2>
              <button className="font-mono text-xl text-slate-400" onClick={() => setDraft(null)}>×</button>
            </div>
            <div className="grid gap-3 md:grid-cols-2">
              {([
                ['slug', 'Slug'], ['title', 'Title'], ['category', 'Category'],
                ['difficulty', 'Difficulty'], ['flag', 'Flag'], ['flag_format', 'Flag format'],
              ] as const).map(([k, label]) => (
                <div key={k}>
                  <label className="label">{label}</label>
                  <input className="input" value={(draft as any)[k] || ''}
                         onChange={(e) => setDraft({ ...draft, [k]: e.target.value })} />
                </div>
              ))}
              <div>
                <label className="label">Round (1–4)</label>
                <input className="input" type="number" min={1} max={4} value={draft.round_number}
                       onChange={(e) => setDraft({ ...draft, round_number: Number(e.target.value) })} />
              </div>
              <div>
                <label className="label">Points</label>
                <input className="input" type="number" value={draft.points}
                       onChange={(e) => setDraft({ ...draft, points: Number(e.target.value) })} />
              </div>
            </div>
            {([
              ['description', 'Description'], ['hint1', 'Hint 1'], ['hint2', 'Hint 2'],
              ['solution', 'Solution (organiser-only)'], ['concept', 'Concept explanation'],
              ['attachment_name', 'Attachment filename'], ['attachment_text', 'Attachment text'],
            ] as const).map(([k, label]) => (
              <div key={k} className="mt-3">
                <label className="label">{label}</label>
                <textarea className="input min-h-[80px]" value={(draft as any)[k] || ''}
                          onChange={(e) => setDraft({ ...draft, [k]: e.target.value })} />
              </div>
            ))}
            <button className="btn btn-primary mt-5 w-full" onClick={saveChallenge}>SAVE CHALLENGE</button>
          </div>
        </div>
      )}

      {/* ROUNDS */}
      {tab === 'rounds' && (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {(data || []).map((r: any) => (
            <div key={r.number} className="glass rounded-xl p-5">
              <div className="font-mono text-3xl font-extrabold text-slate-700">0{r.number}</div>
              <h3 className="mt-1 font-display font-bold text-white">{r.name}</h3>
              <div className="mt-2 font-mono text-xs text-cyan">{r.duration_minutes} min · {r.teams} teams</div>
              <div className="mt-2"><Badge tone={r.state === 'open' ? 'green' : r.state === 'paused' ? 'amber' : 'violet'}>{r.state}</Badge></div>
              <div className="mt-4 flex flex-wrap gap-2">
                <button className="btn btn-primary" onClick={h(`/api/admin/rounds/${r.number}/start`)}>START</button>
                <button className="btn btn-ghost" onClick={h(`/api/admin/rounds/${r.number}/pause`)}>PAUSE</button>
                <button className="btn btn-ghost" onClick={h(`/api/admin/rounds/${r.number}/resume`)}>RESUME</button>
                <button className="btn btn-ghost" onClick={h(`/api/admin/rounds/${r.number}/end`)}>END</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* SCOREBOARD */}
      {tab === 'scoreboard' && (
        <div>
          <input className="input mb-4 max-w-sm" placeholder="Search teams…" value={search}
                 onChange={(e) => setSearch(e.target.value)} />
          {(data || []).filter((r: ScoreRow) => r.team.toLowerCase().includes(search.toLowerCase())).length === 0
            ? <Empty text="No approved teams." /> : (
            <div className="glass overflow-x-auto rounded-xl">
              <table className="w-full min-w-[780px] text-left text-sm">
                <thead><tr className="border-b border-slate-700 font-mono text-[10px] uppercase tracking-widest text-slate-400">
                  <th className="px-4 py-3">#</th><th className="px-4 py-3">TEAM</th><th className="px-4 py-3">R1</th>
                  <th className="px-4 py-3">R2</th><th className="px-4 py-3">R3</th><th className="px-4 py-3">FINAL</th>
                  <th className="px-4 py-3">SOLVED</th><th className="px-4 py-3 text-right">TOTAL</th>
                </tr></thead>
                <tbody>{(data || []).filter((r: ScoreRow) => r.team.toLowerCase().includes(search.toLowerCase()))
                  .map((r: ScoreRow) => (
                    <tr key={r.team_id} className="border-b border-slate-800/70">
                      <td className="px-4 py-3 font-mono text-neon">{r.rank}</td>
                      <td className="px-4 py-3"><div className="font-semibold text-white">{r.team}</div>
                        <div className="font-mono text-[10px] text-slate-500">{r.members}</div></td>
                      <td className="px-4 py-3 font-mono text-cyan">{r.round1}</td>
                      <td className="px-4 py-3 font-mono text-cyan">{r.round2}</td>
                      <td className="px-4 py-3 font-mono text-violet">{r.round3}</td>
                      <td className="px-4 py-3 font-mono text-violet">{r.final}</td>
                      <td className="px-4 py-3 font-mono">{r.solved}</td>
                      <td className="px-4 py-3 text-right font-mono font-bold text-neon">{r.total}</td>
                    </tr>
                  ))}</tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* SUBMISSIONS */}
      {tab === 'submissions' && (
        <div className="glass rounded-xl p-5">
          {(data || []).map((s: any) => (
            <div key={s.id} className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-800/70 py-2 font-mono text-xs">
              <span className="text-slate-400">{s.time}</span>
              <span className="text-white">{s.team}</span>
              <span className="text-cyan">{s.challenge}</span>
              <Badge tone={s.correct ? 'green' : 'violet'}>{s.correct ? `CORRECT +${s.points}` : 'INCORRECT'}</Badge>
            </div>
          ))}
          {!data?.length && <Empty text="No submissions yet." />}
        </div>
      )}

      {/* BREAKS */}
      {tab === 'breaks' && (
        <div className="grid gap-5 md:grid-cols-2">
          <div className="glass rounded-xl p-5">
            <h2 className="font-display font-bold text-white">Cyber riddles ({data?.length || 0})</h2>
            <div className="mt-3 max-h-[520px] space-y-2 overflow-y-auto pr-2">
              {(data || []).map((r: any) => (
                <div key={r.id} className="rounded border border-slate-800 p-3 text-xs">
                  <div className="text-white">{r.question}</div>
                  <div className="mt-1 font-mono text-neon">ANSWER: {r.answer}</div>
                  <button className="mt-2 font-mono text-[10px] text-cyan"
                          onClick={async () => {
                            try {
                              await api.put(`/api/admin/riddles/${r.id}`,
                                { ...r, reveal_enabled: !r.reveal_enabled })
                              await load()
                            } catch (e) { setError(errorText(e)) }
                          }}>
                    {r.reveal_enabled ? 'DISABLE REVEAL' : 'ENABLE REVEAL'}
                  </button>
                </div>
              ))}
            </div>
          </div>
          <div className="glass rounded-xl p-5">
            <h2 className="font-display font-bold text-white">Meme templates ({(data?.memes || []).length})</h2>
            <div className="mt-3 space-y-2">
              {(data?.memes || []).map((m: any) => (
                <div key={m.id} className="rounded border border-slate-800 p-3 text-xs">
                  <div className="font-semibold text-white">{m.title}</div>
                  <div className="mt-1 text-slate-400">{m.caption}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* COMMS */}
      {tab === 'comms' && (
        <div>
          <div className="glass mb-4 rounded-xl p-5">
            <h2 className="font-display font-bold text-white">Post announcement</h2>
            <AnnouncementForm onDone={load} />
          </div>
          {(data || []).map((a: any) => (
            <div key={a.id} className="glass mb-2 rounded-lg p-4">
              <div className="font-semibold text-white">{a.title}</div>
              <p className="mt-1 text-sm text-slate-400">{a.body}</p>
            </div>
          ))}
        </div>
      )}

      {/* SETTINGS */}
      {tab === 'settings' && settingsDraft && (
        <div className="glass rounded-xl p-6">
          <h2 className="font-display text-lg font-bold text-white">Event configuration</h2>
          <p className="mt-1 text-xs text-slate-400">Never tied to deployment date. Edit date, time, timezone, durations and breaks.</p>
          <div className="mt-5 grid gap-4 md:grid-cols-2">
            {[
              ['event_date', 'Event date'], ['event_start_time', 'Start time'],
              ['event_timezone', 'Timezone'], ['event_datetime', 'Countdown target (ISO)'],
              ['duration', 'Total duration'], ['competition_duration', 'Play duration'],
              ['team_size', 'Team size'], ['tagline', 'Tagline'],
            ].map(([k, label]) => (
              <div key={k}>
                <label className="label">{label}</label>
                <input className="input" value={settingsDraft.event?.[k] || ''}
                       onChange={(e) => setSettingsDraft({
                         ...settingsDraft,
                         event: { ...settingsDraft.event, [k]: e.target.value },
                       })} />
              </div>
            ))}
          </div>
          <div className="mt-5 grid gap-4 md:grid-cols-3">
            {[
              ['finalists_mode', 'Final access (all / shortlist)', settingsDraft.finalists_mode],
              ['finalist_count', 'Shortlist size', settingsDraft.finalist_count],
              ['hint_penalty', 'Hint penalty per hint', settingsDraft.hint_penalty],
            ].map(([k, label, value]: any) => (
              <div key={k}>
                <label className="label">{label}</label>
                <input className="input" value={value}
                       onChange={(e) => setSettingsDraft({ ...settingsDraft, [k]: e.target.value })} />
              </div>
            ))}
          </div>
          <div className="mt-5 space-y-2">
            {(settingsDraft.schedule || []).map((s: any, i: number) => (
              <div key={i} className="grid gap-2 sm:grid-cols-[180px_1fr]">
                <input className="input" value={s.time} onChange={(e) => {
                  const next = [...settingsDraft.schedule]; next[i] = { ...s, time: e.target.value }
                  setSettingsDraft({ ...settingsDraft, schedule: next })
                }} />
                <input className="input" value={s.activity} onChange={(e) => {
                  const next = [...settingsDraft.schedule]; next[i] = { ...s, activity: e.target.value }
                  setSettingsDraft({ ...settingsDraft, schedule: next })
                }} />
              </div>
            ))}
          </div>
          <button className="btn btn-primary mt-6" onClick={saveSettings}>SAVE SETTINGS</button>
          <div className="mt-6 border-t border-slate-800 pt-5">
            <h3 className="font-display font-bold text-white">Organiser accounts</h3>
            <div className="mt-3 flex flex-wrap gap-3">
              <button className="btn btn-ghost" onClick={h('/api/admin/accounts/pragyan_lead/reset-password')}>RESET PRIMARY PASSWORD</button>
              <button className="btn btn-ghost" onClick={h('/api/admin/accounts/ieee_lead/reset-password')}>RESET CO-ORGANISER PASSWORD</button>
            </div>
          </div>
        </div>
      )}

      {/* AUDIT */}
      {tab === 'audit' && (
        <div className="glass rounded-xl p-5">
          {(data || []).map((a: any) => (
            <div key={a.id} className="flex flex-wrap justify-between gap-2 border-b border-slate-800/70 py-2 font-mono text-xs">
              <span className="text-slate-500">{a.time}</span>
              <span className="text-cyan">{a.actor_type}#{a.actor_id}</span>
              <span className="text-white">{a.action}</span>
              <span className="text-slate-400">{a.detail}</span>
            </div>
          ))}
          {!data?.length && <Empty text="No audit events." />}
        </div>
      )}
    </div>
  )
}

function AnnouncementForm({ onDone }: { onDone: () => void }) {
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [error, setError] = useState('')
  async function submit(e: React.FormEvent) {
    e.preventDefault()
    try {
      await api.post('/api/admin/announcements', { title, body, pinned: true })
      setTitle(''); setBody(''); onDone()
    } catch (err) { setError(errorText(err)) }
  }
  return (
    <form onSubmit={submit} className="mt-4 grid gap-3 md:grid-cols-[220px_1fr_auto]">
      <input className="input" placeholder="Title" value={title} onChange={(e) => setTitle(e.target.value)} required />
      <input className="input" placeholder="Message" value={body} onChange={(e) => setBody(e.target.value)} required />
      <button className="btn btn-primary">POST</button>
      {error && <p className="font-mono text-xs text-rose-300 md:col-span-3">{error}</p>}
    </form>
  )
}
