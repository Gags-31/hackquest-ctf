import { useEffect, useState } from 'react'
import { Route, Routes } from 'react-router-dom'
import ErrorBoundary from './components/ErrorBoundary'
import { AppShell } from './components/Shell'
import { api } from './lib/api'
import Admin from './pages/Admin'
import BreakPage from './pages/Break'
import ChangePassword from './pages/ChangePassword'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Login from './pages/Login'
import NotFound from './pages/NotFound'
import Register from './pages/Register'
import Results from './pages/Results'

export default function App() {
  const [role, setRole] = useState<string | null>(null)
  const [checked, setChecked] = useState(false)

  useEffect(() => {
    api.get<any>('/api/auth/session')
      .then((s) => setRole(s.role))
      .catch(() => setRole(null))
      .finally(() => setChecked(true))
  }, [])

  if (!checked) return <div className="cyber-bg grid min-h-screen place-items-center font-mono text-sm text-neon">INITIALISING HACKQUEST…</div>

  return (
    <AppShell role={role}>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/register" element={<Register />} />
          <Route path="/login" element={<Login />} />
          <Route path="/change-password" element={<ChangePassword />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/admin" element={<Admin />} />
          <Route path="/break/:number?" element={<BreakPage />} />
          <Route path="/results" element={<Results />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </ErrorBoundary>
    </AppShell>
  )
}
