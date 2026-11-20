import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { BrandLock, OrganiserMark } from './Brand'

type NavProps = { role: string | null; onLogout: () => void }

export function Navbar({ role, onLogout }: NavProps) {
  const [open, setOpen] = useState(false)
  const links = [
    { to: '/', label: 'HOME' },
    { to: '/#about', label: 'ABOUT' },
    { to: '/#rounds', label: 'ROUNDS' },
    { to: '/#schedule', label: 'SCHEDULE' },
    { to: '/break/1', label: 'BREAK' },
    { to: '/results', label: 'RESULTS' },
  ]
  const privateLinks = role === 'team'
    ? [{ to: '/dashboard', label: 'ARENA' }]
    : role === 'organizer'
      ? [{ to: '/admin', label: 'COMMAND' }]
      : [{ to: '/register', label: 'REGISTER' }, { to: '/login', label: 'LOGIN' }]

  return (
    <header className="sticky top-0 z-50 border-b border-slate-800/80 bg-void/90 backdrop-blur-xl">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5">
        <BrandLock compact />
        <nav className="hidden items-center gap-5 lg:flex">
          {links.map((l) => (
            <a key={l.to} href={l.to}
               className="font-mono text-[11px] uppercase tracking-[.16em] text-slate-400 transition hover:text-neon">
              {l.label}
            </a>
          ))}
          {privateLinks.map((l) => (
            <NavLink key={l.to} to={l.to}
                     className="font-mono text-[11px] uppercase tracking-[.16em] text-slate-400 transition hover:text-neon">
              {l.label}
            </NavLink>
          ))}
          {role && (
            <button onClick={onLogout}
                    className="font-mono text-[11px] uppercase tracking-[.16em] text-rose-400 hover:text-rose-300">
              LOGOUT
            </button>
          )}
        </nav>
        <button className="lg:hidden text-slate-300" onClick={() => setOpen(!open)} aria-label="Toggle menu">
          <span className="text-2xl">☰</span>
        </button>
      </div>
      {open && (
        <div className="border-t border-slate-800 bg-void px-5 py-4 lg:hidden">
          <div className="flex flex-col gap-3">
            {[...links, ...privateLinks].map((l) => (
              <a key={l.to} href={l.to} onClick={() => setOpen(false)}
                 className="font-mono text-xs uppercase tracking-widest text-slate-300">
                {l.label}
              </a>
            ))}
            {role && <button onClick={onLogout} className="text-left font-mono text-xs text-rose-400">LOGOUT</button>}
          </div>
        </div>
      )}
    </header>
  )
}

export function Footer() {
  return (
    <footer className="border-t border-slate-800/80 bg-slate-950/60 py-10">
      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-5 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="font-display text-lg font-bold tracking-widest text-white">HACKQUEST <span className="text-neon">2026</span></div>
          <div className="mt-1 font-mono text-xs tracking-[.2em] text-neon">BREAK THE TARGET. OWN THE FLAG.</div>
          <div className="mt-3 flex flex-wrap gap-5">
            <OrganiserMark kind="pragyan" />
            <OrganiserMark kind="ieee" />
          </div>
        </div>
        <div className="font-mono text-xs leading-relaxed text-slate-500">
          <div>25 November 2026 · 11:00 IST</div>
          <div>Organised by Pragyan × IEEE-CS KLEIT Chapter</div>
          <div className="mt-2">Educational, synthetic and fully authorised CTF environment.</div>
        </div>
      </div>
    </footer>
  )
}

export function useLogout() {
  const navigate = useNavigate()
  return async () => {
    try { await api.post('/api/auth/logout') } catch { /* ignore */ }
    navigate('/')
    window.location.reload()
  }
}

export function AppShell({ role, children }: { role: string | null; children: React.ReactNode }) {
  const logout = useLogout()
  return (
    <div className="cyber-bg min-h-screen">
      <Navbar role={role} onLogout={logout} />
      <main>{children}</main>
      <Footer />
    </div>
  )
}

export { Link }
