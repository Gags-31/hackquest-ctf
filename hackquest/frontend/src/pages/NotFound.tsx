import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-lg py-20 text-center">
      <p className="font-mono text-6xl font-bold text-neon-cyan">404</p>
      <h1 className="mt-4 text-2xl font-bold text-white">Page not found</h1>
      <p className="muted mt-2">
        That route does not exist. It may have been a stale link from a previous session.
      </p>
      <div className="mt-6 flex justify-center gap-3">
        <Link className="btn-primary" to="/">Home</Link>
        <Link className="btn-ghost" to="/arena">Arena</Link>
      </div>
    </div>
  );
}