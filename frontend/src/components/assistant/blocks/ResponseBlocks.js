/**
 * Reusable response blocks for the Business Assistant.
 * Small, composable, styled to match the existing violet / slate palette.
 */
import { TrendingUp, TrendingDown, AlertTriangle, ExternalLink } from 'lucide-react';

const formatValue = (m) => {
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
};

export function MetricBlock({ metrics = [] }) {
  if (!metrics.length) return null;
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2" data-testid="assistant-metric-block">
      {metrics.map((m, i) => {
        const pct = m.format === 'percent' && typeof m.value === 'number';
        const Arrow = pct ? (m.value >= 0 ? TrendingUp : TrendingDown) : null;
        const tone = pct ? (m.value >= 0 ? 'text-emerald-700' : 'text-rose-700') : 'text-gray-900';
        return (
          <div key={i} className="rounded-md border border-violet-100 bg-violet-50/60 px-3 py-2">
            <div className="text-[10px] uppercase tracking-wide text-violet-700 font-semibold">{m.label}</div>
            <div className={`text-sm font-semibold flex items-center gap-1 ${tone}`}>
              {Arrow ? <Arrow className="h-3.5 w-3.5" /> : null}
              {formatValue(m)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function RecordChip({ chip, onClick }) {
  if (!chip) return null;
  return (
    <button
      type="button"
      onClick={() => onClick?.(chip)}
      data-testid={`assistant-record-chip-${chip.record_type || 'record'}`}
      className="inline-flex items-center gap-2 rounded-md border border-slate-200 bg-white px-2.5 py-1.5 text-left hover:border-violet-300 hover:bg-violet-50 transition group"
    >
      <span className="flex flex-col">
        <span className="text-xs font-semibold text-slate-800 leading-tight">{chip.label || chip.title || chip.record_id}</span>
        {chip.subtitle && (
          <span className="text-[10px] text-slate-500 leading-tight">{chip.subtitle}</span>
        )}
      </span>
      <ExternalLink className="h-3 w-3 text-slate-400 group-hover:text-violet-500" />
    </button>
  );
}

export function RecordChipList({ chips = [], onChipClick }) {
  if (!chips.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5" data-testid="assistant-record-chip-list">
      {chips.map((c, i) => (
        <RecordChip key={c.record_id || i} chip={c} onClick={onChipClick} />
      ))}
    </div>
  );
}

export function WarningBlock({ level = 'warning', title, children }) {
  const tone =
    level === 'danger'
      ? 'border-rose-200 bg-rose-50 text-rose-900'
      : level === 'info'
      ? 'border-sky-200 bg-sky-50 text-sky-900'
      : 'border-amber-200 bg-amber-50 text-amber-900';
  return (
    <div className={`rounded-md border ${tone} px-3 py-2 text-xs flex gap-2`} data-testid={`assistant-warning-${level}`}>
      <AlertTriangle className="h-4 w-4 flex-shrink-0 mt-0.5" />
      <div>
        {title && <div className="font-semibold mb-0.5">{title}</div>}
        <div>{children}</div>
      </div>
    </div>
  );
}

export function ActionRow({ actions = [], onActionClick }) {
  if (!actions.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5" data-testid="assistant-action-row">
      {actions.map((a) => (
        <button
          key={a.id}
          type="button"
          onClick={() => onActionClick?.(a)}
          data-testid={`assistant-action-${a.id}`}
          className="inline-flex items-center gap-1 rounded-full border border-violet-200 bg-white px-3 py-1 text-[11px] font-medium text-violet-700 hover:bg-violet-50 transition"
        >
          {a.label}
        </button>
      ))}
    </div>
  );
}

export function RowsTable({ rows = [], onRowClick }) {
  if (!rows.length) return null;
  return (
    <div className="rounded-md border border-gray-200 overflow-hidden">
      <div className="max-h-48 overflow-y-auto">
        <table className="w-full text-xs">
          <tbody>
            {rows.slice(0, 10).map((r, i) => (
              <tr
                key={i}
                onClick={() => onRowClick?.(r)}
                className={`border-b border-gray-100 last:border-0 ${onRowClick ? 'cursor-pointer hover:bg-violet-50/50' : 'hover:bg-gray-50'}`}
              >
                <td className="px-2 py-1.5 align-top">{pickPrimary(r)}</td>
                <td className="px-2 py-1.5 text-right text-gray-600 whitespace-nowrap">{pickSecondary(r)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length > 10 && (
        <div className="px-2 py-1 text-[10px] text-gray-500 bg-gray-50">Showing 10 of {rows.length}</div>
      )}
    </div>
  );
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

export default {
  MetricBlock, RecordChip, RecordChipList, WarningBlock, ActionRow, RowsTable,
};
