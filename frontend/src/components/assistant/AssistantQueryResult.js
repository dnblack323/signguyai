import React from 'react';

/**
 * Renders a structured Business Assistant live-query response.
 * Shape expected:
 *   { query_type, summary, metrics, rows, suggested_actions }
 *
 * Intentionally minimal in this phase — KPI grid + compact rows table +
 * action buttons. No major UI redesign.
 */
export default function AssistantQueryResult({ data, onActionClick }) {
  if (!data) return null;
  const { summary, metrics = [], rows = [], suggested_actions = [] } = data;

  return (
    <div className="space-y-3" data-testid={`assistant-query-${data.query_type}`}>
      {summary && (
        <p className="text-sm text-gray-800 leading-snug">{summary}</p>
      )}

      {metrics.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {metrics.map((m, i) => (
            <div key={i} className="rounded-md border border-violet-100 bg-violet-50/60 px-3 py-2">
              <div className="text-[10px] uppercase tracking-wide text-violet-700 font-semibold">{m.label}</div>
              <div className="text-sm font-semibold text-gray-900">{formatMetric(m)}</div>
            </div>
          ))}
        </div>
      )}

      {rows.length > 0 && (
        <div className="rounded-md border border-gray-200 overflow-hidden">
          <div className="max-h-48 overflow-y-auto">
            <table className="w-full text-xs">
              <tbody>
                {rows.slice(0, 10).map((r, i) => (
                  <tr key={i} className="border-b border-gray-100 last:border-0 hover:bg-gray-50">
                    <td className="px-2 py-1.5 align-top">
                      {pickPrimary(r)}
                    </td>
                    <td className="px-2 py-1.5 text-right text-gray-600 whitespace-nowrap">
                      {pickSecondary(r)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {rows.length > 10 && (
            <div className="px-2 py-1 text-[10px] text-gray-500 bg-gray-50">
              Showing 10 of {rows.length}
            </div>
          )}
        </div>
      )}

      {suggested_actions.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {suggested_actions.map((a) => (
            <button
              key={a.id}
              type="button"
              onClick={() => onActionClick?.(a)}
              data-testid={`assistant-query-action-${a.id}`}
              className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-white px-3 py-1 text-[11px] font-medium text-violet-700 hover:bg-violet-50 transition"
            >
              {a.label}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function formatMetric(m) {
  const v = m?.value;
  if (v === null || v === undefined) return '—';
  if (m.format === 'currency') {
    const n = Number(v);
    return Number.isFinite(n) ? n.toLocaleString('en-US', { style: 'currency', currency: 'USD' }) : String(v);
  }
  if (m.format === 'percent') {
    const n = Number(v);
    return Number.isFinite(n) ? `${n > 0 ? '+' : ''}${n}%` : String(v);
  }
  if (typeof v === 'number') return v.toLocaleString();
  return String(v);
}

function pickPrimary(r) {
  return (
    r.invoice_number || r.order_number || r.ticket_number ||
    r.customer_name || r.employee_name || r.category ||
    r.item_name || r.source || r.id || '—'
  );
}

function pickSecondary(r) {
  if (r.balance_due !== undefined) return `$${Number(r.balance_due).toLocaleString()} · ${r.days_overdue ?? 0}d overdue`;
  if (r.total_hours !== undefined) return `${r.total_hours} hrs`;
  if (r.revenue !== undefined) return `$${Number(r.revenue).toLocaleString()} · ${r.count ?? 0} items`;
  if (r.amount !== undefined) return `$${Number(r.amount).toLocaleString()} · ${r.pct ?? 0}%`;
  if (r.due_date) return `Due ${r.due_date}${r.is_overdue ? ' ⚠' : ''}`;
  if (r.status) return r.status;
  return '';
}
