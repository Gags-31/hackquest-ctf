import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="mx-auto max-w-xl px-5 py-24 text-center">
      <div className="font-mono text-7xl font-extrabold text-neon">404</div>
      <p className="mt-4 font-mono text-sm text-slate-400">FLAG_NOT_FOUND / ROUTE_LOCKED</p>
      <Link to="/" className="btn btn-primary mt-6">RETURN TO BASE</Link>
    </div>
  )
}
