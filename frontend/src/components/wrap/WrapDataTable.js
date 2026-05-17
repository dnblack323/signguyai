// Phase 1: A small, reusable placeholder table used by wrap tabs.
export default function WrapDataTable({ columns = [], rows = [], emptyMessage = 'No rows yet', testId }) {
  return (
    <div className="overflow-x-auto" data-testid={testId || 'wrap-data-table'}>
      <table className="w-full text-xs">
        <thead className="text-slate-500">
          <tr className="border-b border-slate-200">
            {columns.map((c, idx) => (
              <th key={idx} className="text-left py-2 px-2 font-normal uppercase tracking-wide text-[10px]">{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length === 0 ? (
            <tr>
              <td colSpan={columns.length} className="py-4 text-center text-slate-400 italic">{emptyMessage}</td>
            </tr>
          ) : (
            rows.map((row, ri) => (
              <tr key={ri} className="border-b border-slate-100 hover:bg-slate-50" data-testid={`${testId || 'wrap-row'}-${ri}`}>
                {row.map((cell, ci) => (
                  <td key={ci} className="py-2 px-2 text-slate-700">{cell ?? '—'}</td>
                ))}
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
