import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { entityConfigs } from "../entityConfig";
import Spinner from "../components/Spinner";

export default function Dashboard() {
  const { user } = useAuth();
  const [counts, setCounts] = useState<Record<string, number>>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all(
      entityConfigs.map((cfg) =>
        api
          .list<Record<string, unknown>>(cfg.resource)
          .then((rows) => [cfg.resource, rows.length] as const)
          .catch(() => [cfg.resource, 0] as const)
      )
    )
      .then((entries) => setCounts(Object.fromEntries(entries)))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Spinner />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900">
        Welcome back, {user?.full_name}
      </h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 mt-8">
        {entityConfigs.map((cfg) => (
          <Link
            key={cfg.resource}
            to={"/" + cfg.resource}
            className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm hover:shadow transition"
          >
            <p className="text-sm text-slate-500">{cfg.label}</p>
            <p className="text-3xl font-bold text-brand-600 mt-1">
              {counts[cfg.resource] ?? 0}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
