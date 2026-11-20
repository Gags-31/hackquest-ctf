import { useEffect, useState } from 'react'
import { api } from '../lib/api'
import type { ScoreRow } from '../lib/types'
import { Empty, SectionTitle } from '../components/Ui'

const medals = ['🥇', '🥈', '🥉']

export default function Results() {
  const [rows, setRows] = useState<ScoreRow[]>([])
  const [state, setState] = useState<'loading' | 'ready' | 'hidden'>('loading')
  useEffect(() => {
    api.get<{ rows: ScoreRow[] }>('/api/public/results')
      .then((d) => { setRows(d.rows); setState('ready') })
      .catch(() => setState('hidden'))
  }, [])

  return (
    <div className="mx-auto max-w-6xl px-5 py-14">
      <SectionTitle kicker="final verdict" title="Results & leaderboard" align="center" />
      {state === 'loading' && <div className="text-center font-mono text-sm text-slate-500">CHECKING PUBLICATION STATUS…</div>}
      {state === 'hidden' && (
        <Empty text="Results are not published yet. During the competition, the live scoreboard is strictly organiser-only." />
      )}
      {state === 'ready' && (rows.length === 0 ? <Empty text="No approved teams yet." /> : (
        <div className="glass overflow-x-auto rounded-xl">
          <table className="w-full min-w-[760px] text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700 font-mono text-[10px] uppercase tracking-widest text-slate-400">
                <th className="px-5 py-4">RANK</th><th className="px-5 py-4">TEAM</th>
                <th className="px-5 py-4">R1</th><th className="px-5 py-4">R2</th>
                <th className="px-5 py-4">R3</th><th className="px-5 py-4">FINAL</th>
                <th className="px-5 py-4 text-right">TOTAL</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.team_id} className="border-b border-slate-800/70 hover:bg-slate-900/40">
                  <td className="px-5 py-4 font-mono text-lg">{medals[r.rank - 1] || `#${r.rank}`}</td>
                  <td className="px-5 py-4">
                    <div className="font-display font-semibold text-white">{r.team}</div>
                    <div className="font-mono text-[10px] text-slate-500">{r.members}</div>
                  </td>
                  <td className="px-5 py-4 font-mono text-cyan">{r.round1}</td>
                  <td className="px-5 py-4 font-mono text-cyan">{r.round2}</td>
                  <td className="px-5 py-4 font-mono text-violet">{r.round3}</td>
                  <td className="px-5 py-4 font-mono text-violet">{r.final}</td>
                  <td className="px-5 py-4 text-right font-mono text-lg font-bold text-neon">{r.total}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ))}
    </div>
  )
}
