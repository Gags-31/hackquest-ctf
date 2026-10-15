import { createContext, useCallback, useContext, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Routes, Route, Navigate, Link, useLocation } from "react-router-dom";
import { get } from "./lib/api";
import type { Me } from "./lib/types";

import Landing from "./pages/Landing";
import Register from "./pages/Register";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Arena from "./pages/Arena";
import RoundPage from "./pages/RoundPage";
import UnlockScreen from "./pages/UnlockScreen";
import Leaderboard from "./pages/Leaderboard";
import Profile from "./pages/Profile";
import Admin from "./pages/Admin";
import AuditLog from "./pages/AuditLog";
import Results from "./pages/Results";
import Rules from "./pages/Rules";
import NotFound from "./pages/NotFound";

type SessionCtx = {
  me: Me;
  refresh: () => Promise<void>;
  busy: boolean;
};

const SessionContext = createContext<SessionCtx>({
  me: { authenticated: false },
  refresh: async () => {},
  busy: true,
});

export const useSession = () => useContext(SessionContext);

function Brand() {
  return (
    <Link to="/" className="flex items-center gap-2 font-mono text-sm font-bold tracking-widest text-neon-cyan">
      <span aria-hidden>▓▒░</span> HACK<span className="text-neon-violet">QUEST</span>
    </Link>
  );
}

function Header({ me }: { me: Me }) {
  const isTeam = me.authenticated && me.role === "team";
  const isOrg = me.authenticated && me.role === "organizer";
  const nav = (
    <nav className="flex flex-wrap items-center gap-1 text-sm">
      <Link className="rounded px-2.5 py-1.5 text-slate-400 hover:bg-ink-800 hover:text-neon-cyan" to="/rules">Rules</Link>
      <Link className="rounded px-2.5 py-1.5 text-slate-400 hover:bg-ink-800 hover:text-neon-cyan" to="/leaderboard">Leaderboard</Link>
      <Link className="rounded px-2.5 py-1.5 text-slate-400 hover:bg-ink-800 hover:text-neon-cyan" to="/results">Results</Link>
      {isTeam && <Link className="rounded px-2.5 py-1.5 text-slate-400 hover:bg-ink-800 hover:text-neon-cyan" to="/dashboard">Dashboard</Link>}
      {isOrg && <Link className="rounded px-2.5 py-1.5 text-slate-400 hover:bg-ink-800 hover:text-neon-cyan" to="/admin">Admin</Link>}
      {me.authenticated ? (
        <Link className="btn-ghost ml-1 px-3 py-1.5 text-xs" to="/profile">Profile</Link>
      ) : (
        <>
          <Link className="btn-ghost px-3 py-1.5 text-xs" to="/login">Sign in</Link>
          <Link className="btn-primary px-3 py-1.5 text-xs" to="/register">Register</Link>
        </>
      )}
    </nav>
  );

  return (
    <header className="sticky top-0 z-50 border-b border-ink-700 bg-ink-950/85 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Brand />
        {nav}
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="mt-16 border-t border-ink-700 py-8 text-center text-xs text-slate-500">
      <p className="font-mono tracking-wider">
        HACKQUEST CTF 2026 · PRAGYAN × IEEE-CS KLEIT CHAPTER
      </p>
      <p className="mt-1">Break the Target. Own the Flag.</p>
    </footer>
  );
}

export default function App() {
  const [me, setMe] = useState<Me>({ authenticated: false });
  const [busy, setBusy] = useState(true);
  const location = useLocation();

  const refresh = useCallback(async () => {
    try {
      const data = await get<Me>("/api/auth/me");
      setMe(data);
    } catch {
      setMe({ authenticated: false });
    } finally {
      setBusy(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const requireTeam = () => {
    if (busy) return <p className="muted">Loading…</p>;
    if (!me.authenticated) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
    if (me.role !== "team") return <Navigate to="/" replace />;
    return null;
  };
  const requireOrg = () => {
    if (busy) return <p className="muted">Loading…</p>;
    if (!me.authenticated || me.role !== "organizer") return <Navigate to="/login" replace />;
    return null;
  };

  const gated = (node: ReactNode, check: () => ReactNode) => {
    const blocked = check();
    return blocked ?? node;
  };

  return (
    <SessionContext.Provider value={{ me, refresh, busy }}>
      <div className="flex min-h-screen flex-col">
        <Header me={me} />
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-8">
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/rules" element={<Rules />} />
            <Route path="/register" element={<Register />} />
            <Route path="/login" element={<Login />} />
            <Route path="/leaderboard" element={<Leaderboard />} />
            <Route path="/results" element={<Results />} />
            <Route path="/profile" element={<Profile />} />
            <Route path="/dashboard" element={gated(<Dashboard />, requireTeam)} />
            <Route path="/arena" element={gated(<Arena />, requireTeam)} />
            <Route path="/round/:slug" element={gated(<RoundPage />, requireTeam)} />
            <Route path="/unlock/:round" element={gated(<UnlockScreen />, requireTeam)} />
            <Route path="/admin" element={gated(<Admin />, requireOrg)} />
            <Route path="/admin/audit" element={gated(<AuditLog />, requireOrg)} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </main>
        <Footer />
      </div>
    </SessionContext.Provider>
  );
}