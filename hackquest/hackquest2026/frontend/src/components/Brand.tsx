import { Link } from 'react-router-dom'

export function HackMark({ size = 36 }: { size?: number }) {
  return (
    <span
      className="relative inline-flex shrink-0 items-center justify-center rounded-md border border-neon/50 bg-neon/5 font-mono font-extrabold text-neon shadow-glow"
      style={{ width: size, height: size, fontSize: size * 0.42 }}
      aria-hidden="true"
    >
      HQ
      <span className="absolute -right-1 -top-1 h-2 w-2 rounded-full bg-cyan shadow-cyan" />
    </span>
  )
}

export function OrganiserMark({ kind }: { kind: 'pragyan' | 'ieee' }) {
  return (
    <div className="flex items-center gap-2.5">
      <span className={`grid h-9 w-9 place-items-center rounded-full border font-mono text-xs font-bold ${
        kind === 'pragyan'
          ? 'border-neon/60 bg-neon/10 text-neon'
          : 'border-cyan/60 bg-cyan/10 text-cyan'
      }`}>
        {kind === 'pragyan' ? 'P' : 'IE'}
      </span>
      <span className="font-display text-sm font-semibold tracking-wide text-slate-200">
        {kind === 'pragyan' ? 'PRAGYAN' : 'IEEE-CS KLEIT'}
      </span>
    </div>
  )
}

export function BrandLock({ compact = false }: { compact?: boolean }) {
  return (
    <Link to="/" className="group flex items-center gap-3">
      <HackMark size={compact ? 32 : 40} />
      <div className="leading-tight">
        <div className="font-display text-base font-bold tracking-[.16em] text-white group-hover:text-neon">
          HACKQUEST<span className="text-neon">.</span>
        </div>
        <div className="font-mono text-[9px] uppercase tracking-[.28em] text-slate-500">CTF 2026</div>
      </div>
    </Link>
  )
}
