interface DataTableProps {
  columns: { key: string; label: string }[];
  rows: Record<string, unknown>[];
  onEdit?: (row: Record<string, unknown>) => void;
  onDelete?: (row: Record<string, unknown>) => void;
}

export default function DataTable({ columns, rows, onEdit, onDelete }: DataTableProps) {
  if (rows.length === 0) {
    return <div className="p-8 text-center text-slate-500">No records yet.</div>;
  }
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-2 text-left font-medium text-slate-600">
                {col.label}
              </th>
            ))}
            {(onEdit || onDelete) && <th className="px-4 py-2" />}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {rows.map((row) => (
            <tr key={String(row.id)} className="hover:bg-slate-50">
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-2 text-slate-700">
                  {formatCell(row[col.key])}
                </td>
              ))}
              {(onEdit || onDelete) && (
                <td className="px-4 py-2 text-right whitespace-nowrap">
                  {onEdit && (
                    <button
                      className="text-brand-600 hover:underline mr-3"
                      onClick={() => onEdit(row)}
                    >
                      Edit
                    </button>
                  )}
                  {onDelete && (
                    <button
                      className="text-red-600 hover:underline"
                      onClick={() => onDelete(row)}
                    >
                      Delete
                    </button>
                  )}
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}
