import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AuthUser } from "../api/client";
import DataTable from "../components/DataTable";
import Spinner from "../components/Spinner";

export default function Admin() {
  const [users, setUsers] = useState<AuthUser[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .list<AuthUser>("users")
      .then(setUsers)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load users"));
  }, []);

  if (error) return <div className="p-10 text-center text-red-600">{error}</div>;
  if (!users) return <Spinner />;

  return (
    <div className="max-w-5xl mx-auto px-4 py-10">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Admin console</h1>
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
        <DataTable
          columns={[
            { key: "id", label: "ID" },
            { key: "email", label: "Email" },
            { key: "full_name", label: "Name" },
            { key: "role", label: "Role" },
          ]}
          rows={users as unknown as Record<string, unknown>[]}
        />
      </div>
    </div>
  );
}
