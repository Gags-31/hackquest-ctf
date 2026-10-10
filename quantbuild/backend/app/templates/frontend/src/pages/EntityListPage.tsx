import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/client";
import DataTable from "../components/DataTable";
import FormField from "../components/FormField";
import Spinner from "../components/Spinner";
import EmptyState from "../components/EmptyState";
import type { EntityConfig } from "../entityConfig";

export default function EntityListPage({ config }: { config: EntityConfig }) {
  const [rows, setRows] = useState<Record<string, unknown>[] | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [editing, setEditing] = useState<Record<string, unknown> | null>(null);
  const [form, setForm] = useState<Record<string, unknown>>({});
  const [formError, setFormError] = useState("");

  const load = useCallback(() => {
    api
      .list<Record<string, unknown>>(config.resource)
      .then(setRows)
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load"));
  }, [config.resource]);

  useEffect(load, [load]);

  const filtered = useMemo(() => {
    if (!rows) return [];
    if (!search.trim()) return rows;
    const needle = search.toLowerCase();
    return rows.filter((row) =>
      Object.values(row).some((v) => String(v).toLowerCase().includes(needle))
    );
  }, [rows, search]);

  const openCreate = () => {
    const initial: Record<string, unknown> = {};
    for (const field of config.fields) {
      if (field.input === "checkbox") initial[field.key] = false;
      else if (field.input === "number") initial[field.key] = 0;
      else initial[field.key] = "";
    }
    setForm(initial);
    setEditing({});
    setFormError("");
  };

  const openEdit = (row: Record<string, unknown>) => {
    setForm({ ...row });
    setEditing(row);
    setFormError("");
  };

  const save = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError("");
    const payload: Record<string, unknown> = {};
    for (const field of config.fields) {
      const value = form[field.key];
      if (field.input === "number") payload[field.key] = Number(value);
      else if (field.input === "checkbox") payload[field.key] = Boolean(value);
      else if (value === "" && !field.required) continue;
      else payload[field.key] = value;
    }
    try {
      if (editing && typeof editing.id === "number") {
        await api.update(config.resource, editing.id, payload);
      } else {
        await api.create(config.resource, payload);
      }
      setEditing(null);
      load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Save failed");
    }
  };

  const remove = async (row: Record<string, unknown>) => {
    if (!window.confirm("Delete this record?")) return;
    await api.remove(config.resource, row.id as number);
    load();
  };

  if (error) return <div className="p-10 text-center text-red-600">{error}</div>;
  if (!rows) return <Spinner />;

  return (
    <div className="max-w-7xl mx-auto px-4 py-10">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{config.label}</h1>
        <button
          onClick={openCreate}
          className="bg-brand-600 text-white rounded px-4 py-2 text-sm hover:bg-brand-700"
        >
          + New
        </button>
      </div>
      <input
        placeholder="Search…"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        className="w-full border border-slate-300 rounded px-3 py-2 mb-4"
      />
      <div className="bg-white border border-slate-200 rounded-lg shadow-sm">
        {filtered.length === 0 ? (
          <EmptyState title={"No " + config.label.toLowerCase() + " found"} hint="Create the first one." />
        ) : (
          <DataTable columns={config.columns} rows={filtered} onEdit={openEdit} onDelete={remove} />
        )}
      </div>

      {editing && (
        <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-20">
          <div className="bg-white rounded-lg shadow-xl w-full max-w-lg p-6 max-h-[85vh] overflow-y-auto">
            <h2 className="text-lg font-semibold mb-4">
              {typeof editing.id === "number" ? "Edit" : "Create"} {config.label}
            </h2>
            <form onSubmit={save}>
              {config.fields.map((field) => (
                <FormField key={field.key} label={field.label}>
                  {field.input === "textarea" ? (
                    <textarea
                      required={field.required}
                      value={String(form[field.key] ?? "")}
                      onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                      className="w-full border border-slate-300 rounded px-3 py-2"
                    />
                  ) : field.input === "checkbox" ? (
                    <input
                      type="checkbox"
                      checked={Boolean(form[field.key])}
                      onChange={(e) => setForm({ ...form, [field.key]: e.target.checked })}
                      className="h-4 w-4"
                    />
                  ) : (
                    <input
                      type={field.input}
                      required={field.required}
                      step={field.input === "number" ? "any" : undefined}
                      value={String(form[field.key] ?? "")}
                      onChange={(e) => setForm({ ...form, [field.key]: e.target.value })}
                      className="w-full border border-slate-300 rounded px-3 py-2"
                    />
                  )}
                </FormField>
              ))}
              {formError && <p className="text-sm text-red-600 mb-3">{formError}</p>}
              <div className="flex justify-end gap-2 mt-4">
                <button
                  type="button"
                  onClick={() => setEditing(null)}
                  className="border border-slate-300 rounded px-4 py-2 text-sm"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="bg-brand-600 text-white rounded px-4 py-2 text-sm hover:bg-brand-700"
                >
                  Save
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
