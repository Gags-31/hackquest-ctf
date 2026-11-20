import { useEffect, useState } from 'react'
import { api } from '../lib/api'

export function SectionTitle({ kicker, title, align = 'left' }: {
  kicker: string; title: string; align?: 'left' | 'center'
}) {
  return (
    <div className={align === 'center' ? 'mx-auto max-w-2xl text-center' : 'mb-8'}>
      <div className="mb-3 font-mono text-xs uppercase tracking-[.3em] text-neon">// {kicker}</div>
      <h2 className="font-display text-3xl font-bold tracking-tight text-white md:text-4xl">{title}</h2>
      <div className={`mt-4 h-px w-24 bg-gradient-to-r from-neon to-transparent ${align === 'center' ? 'mx-auto' : ''}`} />
    </div>
  )
}

export function Stat({ label, value, accent = 'neon' }: {
  label: string; value: string | number; accent?: 'neon' | 'cyan' | 'violet' | 'green'
}) {
  const color = accent === 'cyan' ? 'text-cyan'
    : accent === 'violet' ? 'text-violet'
      : accent === 'green' ? 'text-emerald-300' : 'text-neon'
  return (
    <div className="glass rounded-xl p-5">
      <div className={`font-mono text-3xl font-extrabold ${color}`}>{value}</div>
      <div className="mt-1 font-mono text-[10px] uppercase tracking-[.2em] text-slate-400">{label}</div>
    </div>
  )
}

export function useEvent() {
  const [event, setEvent] = useState<any>(null)
  const [schedule, setSchedule] = useState<any[]>([])
  const [marquee, setMarquee] = useState('')
  useEffect(() => {
    api.get<any>('/api/public/event')
      .then((d) => { setEvent(d.event); setSchedule(d.schedule); setMarquee(d.marquee) })
      .catch(() => {})
  }, [])
  return { event, schedule, marquee }
}

function parts(ms: number) {
  const s = Math.max(0, Math.floor(ms / 1000))
  return {
    days: Math.floor(s / 86400),
    hours: Math.floor((s % 86400) / 3600),
    minutes: Math.floor((s % 3600) / 60),
    seconds: s % 60,
  }
}

export function Countdown({ target }: { target?: string }) {
  const [now, setNow] = useState(Date.now())
  useEffect(() => {
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [])
  if (!target) return <div className="font-mono text-sm text-slate-500">Loading event clock…</div>
  const t = parts(new Date(target).getTime() - now)
  const cells = [
    [t.days, 'DAYS'], [t.hours, 'HRS'], [t.minutes, 'MIN'], [t.seconds, 'SEC'],
  ]
  return (
    <div className="flex gap-2 sm:gap-3">
      {cells.map(([v, label]) => (
        <div key={label as string} className="glass min-w-[70px] rounded-lg px-3 py-2 text-center sm:min-w-[88px]">
          <div className="font-mono text-2xl font-extrabold text-neon sm:text-3xl">
            {String(v).padStart(2, '0')}
          </div>
          <div className="font-mono text-[9px] tracking-[.25em] text-slate-500">{label}</div>
        </div>
      ))}
    </div>
  )
}

export function Marquee({ text }: { text: string }) {
  if (!text) return null
  const line = <span className="whitespace-nowrap">{text}&nbsp;&nbsp;&nbsp;</span>
  return (
    <div className="relative overflow-hidden border-y border-slate-800/70 bg-slate-950/60 py-3">
      <div className="flex w-max animate-marquee font-mono text-xs uppercase tracking-[.3em] text-slate-400">
        {line}{line}{line}{line}
      </div>
    </div>
  )
}

export function Badge({ children, tone = 'slate' }: {
  children: React.ReactNode; tone?: 'slate' | 'green' | 'cyan' | 'violet' | 'amber'
}) {
  const tones: Record<string, string> = {
    slate: 'border-slate-600/60 text-slate-300',
    green: 'border-neon/50 text-neon bg-neon/5',
    cyan: 'border-cyan/50 text-cyan bg-cyan/5',
    violet: 'border-violet/50 text-violet bg-violet/5',
    amber: 'border-amber-500/50 text-amber-300 bg-amber-500/5',
  }
  return <span className={`tag ${tones[tone]}`}>{children}</span>
}

export function Timer({ seconds }: { seconds: number | null }) {
  if (seconds === null) return <span className="font-mono text-slate-500">—</span>
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return <span className={`font-mono text-lg font-bold ${seconds < 120 ? 'text-rose-400' : 'text-neon'}`}>
    {String(m).padStart(2, '0')}:{String(s).padStart(2, '0')}
  </span>
}

export function Empty({ text }: { text: string }) {
  return <div className="glass rounded-xl p-8 text-center font-mono text-sm text-slate-400">{text}</div>
}
